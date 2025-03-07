"""Class to cache objects created from specific DB rows"""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path

import qp
import structlog
from ceci.errors import StageNotFound
from ceci.stage import PipelineStage
from rail.core import RailEnv, RailStage
from rail.estimation.estimator import CatEstimator
from rail.interfaces.pz_factory import PZFactory
from rail.utils.catalog_utils import CatalogConfigBase
from sqlalchemy.ext.asyncio import async_scoped_session

from ..common.errors import (
    RAILBadInputError,
    RAILImportError,
    RAILIntegrityError,
    RAILRequestError,
)
from ..config import config as global_config
from .algorithm import Algorithm
from .catalog_tag import CatalogTag
from .dataset import Dataset
from .estimator import Estimator
from .model import Model
from .request import Request


class Cache:
    """Cache for objects created from specific DB rows"""

    _shared_cache: Cache | None = None

    def __init__(self, logger: structlog.BoundLogger | None = None) -> None:
        self._logger = logger
        self._algorithms: dict[int, type[CatEstimator] | None] = {}
        self._catalog_tags: dict[int, type[CatalogConfigBase] | None] = {}
        self._estimators: dict[int, CatEstimator | None] = {}
        self._qp_files: dict[int, str | None] = {}
        self._qp_dists: dict[int, qp.Ensemble | None] = {}

    def clear(self) -> None:
        """Clear out the cache"""
        self._algorithms = {}
        self._catalog_tags = {}
        self._estimators = {}
        self._qp_files = {}
        self._qp_dists = {}

    @classmethod
    def shared_cache(cls, logger: structlog.BoundLogger) -> Cache:
        if cls._shared_cache is None:
            cls._shared_cache = Cache(logger)
        return cls._shared_cache

    def _load_algorithm_class(
        self,
        algorithm: Algorithm,
    ) -> type[CatEstimator]:
        """Load the CatEstimator class associated to an Algorithm

        Parameters
        ----------
        algorithm
            DB row describing the algorithm to load

        Returns
        -------
        type[CatEstimator]
            Associated Sub-class of CatEstimator

        Raises
        ------
        RAILImportError
            Python class could not be loaded
        """
        tokens = algorithm.class_name.split(".")
        module_name = ".".join(tokens[0:-1])
        class_name = tokens[-1]

        try:
            return PipelineStage.get_stage(class_name, module_name)
        except StageNotFound as missing_stage:
            raise RAILImportError(
                f"Failed to load stage {algorithm.class_name} because {missing_stage}"
            ) from missing_stage

    def _load_catalog_tag_class(
        self,
        catalog_tag: CatalogTag,
    ) -> type[CatalogConfigBase]:
        """Load the CatalogConfigBase class associated to an CatalogTag

        Parameters
        ----------
        catalog_tag
            DB row describing the CatalogTag to load

        Returns
        -------
        type[CatalogConfigBase]
            Associated Sub-class of CatalogConfigBase

        Raises
        ------
        RAILImportError
            Python class could not be loaded
        """
        tokens = catalog_tag.class_name.split(".")
        module_name = ".".join(tokens[0:-1])
        class_name = tokens[-1]

        try:
            return CatalogConfigBase.get_class(class_name, module_name)
        except KeyError as missing_key:
            raise RAILImportError(
                f"Failed to load catalog_tag {class_name} because {missing_key}"
            ) from missing_key

    async def _build_estimator(
        self,
        session: async_scoped_session,
        estimator: Estimator,
    ) -> CatEstimator:
        algo_class = await self.get_algo_class(session, estimator.algo_id)
        catalog_tag_class = await self.get_catalog_tag_class(session, estimator.catalog_tag_id)
        CatalogConfigBase.apply(catalog_tag_class.tag)
        model = await Model.get_row(session, estimator.model_id)
        if estimator.config is None:
            the_config = {}
        else:
            the_config = estimator.config.copy()

        estimator_instance = PZFactory.build_stage_instance(
            estimator.name,
            algo_class,
            model.path,
            **the_config,
        )
        return estimator_instance

    async def _process_request(
        self,
        session: async_scoped_session,
        request: Request,
    ) -> str:
        estimator = await Estimator.get_row(session, request.estimator_id)
        estimator_instance = await self.get_estimator(session, request.estimator_id)
        dataset = await Dataset.get_row(session, request.dataset_id)

        output_path = os.path.join(
            global_config.storage.archive,
            "qp_files",
            dataset.name,
            f"{estimator.name}.hdf5",
        )

        aliased_tag = estimator_instance.get_aliased_tag("output")
        estimator_instance._outputs[aliased_tag] = os.path.abspath(output_path)  # pylint: disable=protected-access

        if dataset.path is not None:
            result_handle = PZFactory.run_cat_estimator_stage(estimator_instance, dataset.path)
        else:
            _data_out = PZFactory.estimate_single_pz(
                estimator_instance,
                dataset.data,
                dataset.n_objects,
            )
            result_handle = estimator_instance.get_handle("output")
            result_handle.write()
            estimator_instance.finalize()

        aliased_tag = estimator_instance.get_aliased_tag("output")
        final_name = estimator_instance.get_output(aliased_tag, final_name=True)

        if not os.path.exists(result_handle.path):
            raise RuntimeError(f"Output files {output_path}, not created")

        now = datetime.now()
        await request.update_values(
            session,
            qp_file_path=final_name,
            time_finished=now,
        )
        await session.commit()
        self._qp_files[request.id] = final_name

        return result_handle.path

    async def get_algo_class(
        self,
        session: async_scoped_session,
        key: int,
    ) -> type[CatEstimator]:
        """Get a python class associated to a particular algorithm

        Parameters
        ----------
        session
            DB session manager

        key
            DB id of the algorithm in question

        Returns
        -------
        type[CatEstimator]
            Python class of the associated algorithm

        Raises
        ------
        RAILImportError
            Python class could not be loaded

        RAILMissingIDError
            ID not found in database
        """
        algo_class = self._algorithms.get(key)
        if algo_class is not None:
            return algo_class

        algo_ = await Algorithm.get_row(session, key)
        try:
            algo_class = self._load_algorithm_class(algo_)
            self._algorithms[key] = algo_class
        except RAILImportError as failed_import:
            # Set the value to None, allowing to retry later
            self._algorithms[key] = None
            raise RAILImportError(f"Import of Algorithm failed because {failed_import}") from failed_import

        return algo_class

    async def get_catalog_tag_class(
        self,
        session: async_scoped_session,
        key: int,
    ) -> type[CatalogConfigBase]:
        """Get a python class associated to a particular catalog_tag

        Parameters
        ----------
        session
            DB session manager

        key
            DB id of the catalog_tag in question

        Returns
        -------
        type[CatalogConfigBase]
            Python class of the associated algorithmcatalog_tag

        Raises
        ------
        RAILImportError
            Python class could not be loaded

        RAILMissingIDError
            ID not found in database
        """
        catalog_tag_class = self._catalog_tags.get(key)
        if catalog_tag_class is not None:
            return catalog_tag_class

        catalog_tag_ = await CatalogTag.get_row(session, key)
        try:
            catalog_tag_class = self._load_catalog_tag_class(catalog_tag_)
            self._catalog_tags[key] = catalog_tag_class
        except RAILImportError as failed_import:
            # Set the value to None, allowing to retry later
            self._catalog_tags[key] = None
            raise RAILImportError(f"Import of CatalogTag failed because {failed_import}") from failed_import
        return catalog_tag_class

    async def get_estimator(
        self,
        session: async_scoped_session,
        key: int,
    ) -> CatEstimator:
        """Get a particular CatEstimator

        Parameters
        ----------
        session
            DB session manager

        key
            DB id of the estimator in question

        Returns
        -------
        CatEstimator
            Estimator in question

        Raises
        ------
        RAILImportError
            Python class could not be loaded

        RAILMissingIDError
            ID not found in database
        """

        estimator = self._estimators.get(key)
        if estimator is not None:
            return estimator

        estimator_ = await Estimator.get_row(session, key)
        try:
            estimator = await self._build_estimator(session, estimator_)
            self._estimators[key] = estimator
        except RAILImportError as failed_import:
            # Set the value to None, allowing to retry later
            self._estimators[key] = None
            raise RAILImportError(f"Import of Estimator failed because {failed_import}") from failed_import

        return estimator

    async def get_qp_file(
        self,
        session: async_scoped_session,
        key: int,
    ) -> str:
        """Get the output file from a particular request

        Parameters
        ----------
        session
            DB session manager

        key
            DB id of the requestion in question

        Returns
        -------
        str
            Path to the file in question

        Raises
        ------
        RAILRequestError
            Requsts failed for some reason
        """

        qp_file = self._qp_files.get(key)
        if qp_file is not None:
            return qp_file

        request_ = await Request.get_row(session, key)

        if request_.qp_file_path is not None:
            if os.path.exists(request_.qp_file_path):
                self._qp_files[key] = request_.qp_file_path
                return request_.qp_file_path

        try:
            qp_file = await self._process_request(session, request_)
            self._qp_files[key] = qp_file
        except RAILRequestError as failed_request:
            # Set the value to None, allowing to retry later
            self._qp_files[key] = None
            raise RAILRequestError(f"Request failed because {failed_request}") from failed_request

        return qp_file

    async def get_qp_dist(
        self,
        session: async_scoped_session,
        key: int,
    ) -> qp.Ensemble:
        """Get the qp.Ensemble from a particular request

        Parameters
        ----------
        session
            DB session manager

        key
            DB id of the requestion in question

        Returns
        -------
        qp.Ensemble
            Ensemble in question

        Raises
        ------
        RAILRequestError
            Requsts failed for some reason
        """
        qp_file = await self.get_qp_file(session, key)

        try:
            qp_dist = qp.read(qp_file)
        except Exception as failed_read:
            raise RAILRequestError(f"Request failed because {failed_read}") from failed_read
        return qp_dist

    async def load_algorithms_from_rail_env(
        self,
        session: async_scoped_session,
    ) -> list[Algorithm]:
        """Load all of the CatEstimator algorithsm from RailEnv

        Parameters
        ----------
        session
            DB session manager

        Returns
        -------
        list[Algorithm]
            Newly created Algorithm database rows

        Raises
        ------
        RAILIntegrityError
            Rows already exist in database

        Example
        -------

        .. code-block:: python

            from structlog import get_logger
            logger = get_logger(__name__)
            cache = pz_rail_service.db.Cache.shared_cache(logger)
            algos = await cache.load_algorithms_from_rail_env(
                session,
            )

        """
        algos_: list[Algorithm] = []
        RailEnv.import_all_packages(silent=True)
        for stage_name, stage_info in RailStage.pipeline_stages.items():
            the_class = stage_info[0]

            if not issubclass(the_class, CatEstimator):
                continue
            if the_class == CatEstimator:
                continue

            full_name = f"{the_class.__module__}.{the_class.__name__}"
            try:
                new_algo = await Algorithm.create_row(
                    session,
                    name=stage_name,
                    class_name=full_name,
                )
                await session.refresh(new_algo)
                check_class = await self.get_algo_class(session, new_algo.id)
                if check_class != the_class:  # pragma: no cover
                    raise RAILIntegrityError(f"{the_class.__name__} != {check_class.__name__}")
                algos_.append(new_algo)

            except RAILIntegrityError as msg:
                if self._logger:
                    self._logger.info(msg)

        return algos_

    async def load_catalog_tags_from_rail_env(
        self,
        session: async_scoped_session,
    ) -> list[CatalogTag]:
        """Load all of the CatalogTag from RAIL classes

        Parameters
        ----------
        session
            DB session manager

        Returns
        -------
        list[CatalogTag]
            Newly created CatalogTag database rows

        Example
        -------

        .. code-block:: python

            from structlog import get_logger
            logger = get_logger(__name__)
            cache = pz_rail_service.db.Cache.shared_cache(logger)
            catalog_tags = await cache.load_catalog_tags_from_rail_env(
                session,
            )

        """
        catalog_tags_: list[CatalogTag] = []

        catalog_config_dict = CatalogConfigBase.subclasses()
        for tag, a_class in catalog_config_dict.items():
            try:
                new_catalog_tag = await CatalogTag.create_row(
                    session,
                    name=tag,
                    class_name=f"{a_class.__module__}.{a_class.__name__}",
                )
                await session.refresh(new_catalog_tag)
                check_class = await self.get_catalog_tag_class(session, new_catalog_tag.id)
                if check_class != a_class:  # pragma: no cover
                    raise RAILIntegrityError(f"{a_class.__name__} != {check_class.__name__}")
                catalog_tags_.append(new_catalog_tag)
            except RAILIntegrityError as msg:
                if self._logger:
                    self._logger.info(msg)

        return catalog_tags_

    async def load_model_from_file(
        self,
        session: async_scoped_session,
        name: str,
        path: Path,
        algo_name: str,
        catalog_tag_name: str,
    ) -> Model:
        """Import a model file to the archive area and add a Model

        Parameters
        ----------
        session
            DB session manager

        name
            Name for new Model

        path
            Path to input file.  Note that it will be copied to DB area

        algo_name
            Name of Algorithm that uses the model

        catalog_tag_name
            Name of CatalogTag that described contents of file

        Returns
        -------
        Model
            Newly created Model

        Raises
        ------
        RAILIntegrityError
            Rows already exist in database

        RAILFileNotFoundError
            Input file not found

        RAILBadModelError
            Input file failed validation checks

        Example
        -------

        .. code-block:: python

            from structlog import get_logger
            logger = get_logger(__name__)
            cache  = pz_rail_service.db.Cache.shared_cache(logger)
            new_model = await cache.load_model_from_file(
                session,
                name='my_gpz_com_cam_model',
                path='local_version_of_file.pkl',
                algo_name='GPZEstimator',
                catalog_tag_name='com_cam',
            )

        """
        # Validate the input file
        catalog_tag = await CatalogTag.get_row_by_name(session, catalog_tag_name)
        algo = await Algorithm.get_row_by_name(session, algo_name)

        Model.validate_model(path, algo, catalog_tag)

        # File looks ok, move it to the archive area
        suffix = os.path.splitext(path)[1]
        output_name = os.path.join(
            global_config.storage.archive,
            "models",
            algo_name,
            catalog_tag_name,
            f"{name}{suffix}",
        )
        output_abspath = os.path.abspath(output_name)
        output_dir = os.path.dirname(output_abspath)
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy(path, output_abspath)

        # Make a new Model row
        try:
            new_model = await Model.create_row(
                session,
                name=name,
                path=output_name,
                algo_id=algo.id,
                catalog_tag_id=catalog_tag.id,
            )
            await session.refresh(new_model)
            return new_model
        except RAILIntegrityError as msg:
            msg_str = f"Model ingest failed: removing file {output_abspath} {str(msg)}"
            if self._logger:
                self._logger.warn(msg_str)
            else:
                print(msg_str)
            os.unlink(output_abspath)
            raise RAILIntegrityError(msg) from msg

    async def load_dataset_from_file(
        self,
        session: async_scoped_session,
        name: str,
        path: Path,
        catalog_tag_name: str,
        data: dict | None = None,
    ) -> Dataset:
        """Import a data file to the archive area and add a Dataset row

        Parameters
        ----------
        session
            DB session manager

        name
            Name for new Dataset

        path
            Path to input file.  Note that it will be copied to DB area

        catalog_tag_name
            Name of CatalogTag that described contents of file

        Returns
        -------
        Dataset
            Newly created Dataset

        Raises
        ------
        RAILIntegrityError
            Rows already exist in database

        RAILFileNotFoundError
            Input file not found

        RAILBadDatasetError
            Input file failed validation checks

        Example
        -------

        .. code-block:: python

            from structlog import get_logger
            logger = get_logger(__name__)
            cache  = pz_rail_service.db.Cache.shared_cache(logger)
            new_dataset = await cache.load_dataset_from_file(
                session,
                name='my_com_cam_dataset',
                path='local_version_of_file.hdf5',
                catalog_tag_name='com_cam',
            )

        """
        if data is not None:
            raise RAILBadInputError("data should be set to None when calling load_dataset_from_file")

        # Validate the input file
        catalog_tag = await CatalogTag.get_row_by_name(session, catalog_tag_name)
        n_objects = Dataset.validate_data_for_path(path, catalog_tag)

        # File looks ok, move it to the archive area
        suffix = os.path.splitext(path)[1]
        output_name = os.path.join(
            global_config.storage.archive,
            "datasets",
            catalog_tag_name,
            f"{name}{suffix}",
        )
        output_abspath = os.path.abspath(output_name)
        output_dir = os.path.dirname(output_abspath)
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy(path, output_abspath)

        # Make a new Dataset row
        try:
            new_dataset = await Dataset.create_row(
                session,
                name=name,
                n_objects=n_objects,
                path=output_name,
                data=None,
                catalog_tag_id=catalog_tag.id,
            )
            await session.refresh(new_dataset)
            return new_dataset
        except RAILIntegrityError as msg:
            msg_str = f"Dataset ingest failed: removing file {output_abspath}: {str(msg)}"
            if self._logger:
                self._logger.warn(msg_str)
            else:
                print(msg_str)
            os.unlink(output_abspath)
            raise RAILIntegrityError(msg) from msg

    async def load_dataset_from_values(
        self,
        session: async_scoped_session,
        name: str,
        data: dict,
        catalog_tag_name: str,
        path: str | None = None,
    ) -> Dataset:
        """Import a data file to the archive area and add a Dataset row

        Parameters
        ----------
        session
            DB session manager

        name
            Name for new Dataset

        data
            Data to input

        catalog_tag_name
            Name of CatalogTag that described contents of file

        Returns
        -------
        Dataset
            Newly created Dataset

        Raises
        ------
        RAILIntegrityError
            Rows already exist in database

        RAILFileNotFoundError
            Input file not found

        RAILBadDatasetError
            Input file failed validation checks

        Example
        -------

        .. code-block:: python

            from structlog import get_logger
            logger = get_logger(__name__)
            cache  = pz_rail_service.db.Cache.shared_cache(logger)

            data = dict(
                u_cModelMag=24.4, g_cModelMag=24.4, r_cModelMag=24.4,
                i_cModelMag=24.4, z_cModelMag=24.4, y_cModelMag=24.4,
                u_cModelMagErr=0.5, g_cModelMagErr=0.5, r_cModelMagErr=0.5,
                i_cModelMagErr=0.5, z_cModelMagErr=0.5, y_cModelMagErr=0.5,
            )
            new_dataset = await cache.load_dataset_from_file(
                session,
                name='my_com_cam_dataset',
                data=data,
                catalog_tag_name='com_cam',
            )

        """
        if path is not None:
            raise RAILBadInputError("path should be set to None when calling load_dataset_from_values")

        # Validate the input file
        catalog_tag = await CatalogTag.get_row_by_name(session, catalog_tag_name)

        # Make a new Dataset row
        try:
            new_dataset = await Dataset.create_row(
                session,
                name=name,
                path=None,
                data=data,
                catalog_tag_id=catalog_tag.id,
            )
            await session.refresh(new_dataset)
            return new_dataset
        except RAILIntegrityError as msg:
            msg_str = f"Dataset ingest failed: {str(msg)}"
            if self._logger:
                self._logger.warn(msg_str)
            else:
                print(msg_str)
            raise RAILIntegrityError(msg) from msg

    async def load_estimator(
        self,
        session: async_scoped_session,
        name: str,
        model_name: str,
        config: dict | None = None,
    ) -> Estimator:
        """Create a new Estimator

        Parameters
        ----------
        session
            DB session manager

        name
            Name for new Estimator

        model_name
            Name of associated model

        config
            Extra paraemeters to use when running estimator

        Returns
        -------
        Estimator
            Newly created Estimator

        Raises
        ------
        RAILIntegrityError
            Rows already exist in database

        Example
        -------

        .. code-block:: python

            from structlog import get_logger
            logger = get_logger(__name__)
            cache  = pz_rail_service.db.Cache.shared_cache(logger)
            new_dataset = await cache.load_dataset_from_file(
                session,
                name='my_com_cam_dataset',
                path='local_version_of_data_file.hdf5',
                catalog_tag_name='com_cam',
            )

        """

        model = await Model.get_row_by_name(session, model_name)

        try:
            new_estimator = await Estimator.create_row(
                session,
                name=name,
                model_id=model.id,
                config=config,
            )
            await session.refresh(new_estimator)
            return new_estimator
        except RAILIntegrityError as msg:
            raise RAILIntegrityError(msg) from msg

    async def create_request(
        self,
        session: async_scoped_session,
        dataset_name: str,
        estimator_name: str,
    ) -> Request:
        """Run a request

        Parameters
        ----------
        session
            DB session manager

        dataset_name
            Name of associated Dataset

        estimator_name
            Name of associated Estimator

        Returns
        -------
        Request
            Request in question

        Example
        -------

        .. code-block:: python

            from structlog import get_logger
            logger = get_logger(__name__)
            cache  = pz_rail_service.db.Cache.shared_cache(logger)
            new_request = await cache.create_request(
                session,
                dataset_name='my_com_cam_dataset',
                estimator_name='my_gpz_com_cam_estimaor',
            )

        """
        request_ = await Request.create_row(
            session,
            dataset_name=dataset_name,
            estimator_name=estimator_name,
        )
        await session.commit()
        return request_

    async def run_request(
        self,
        session: async_scoped_session,
        request_id: int,
    ) -> Request:
        """Run a request

        Parameters
        ----------
        session
            DB session manager

        request_id
            Id of the request in the Request table

        Returns
        -------
        Request
            Request in question

        Example
        -------

        .. code-block:: python

            from structlog import get_logger
            logger = get_logger(__name__)
            cache  = pz_rail_service.db.Cache.shared_cache(logger)
            new_request = await cache.create_request(
                session,
                dataset_name='my_com_cam_dataset',
                estimator_name='my_gpz_com_cam_estimaor',
            )
            await cache.run_request(
                session,
                new_request.id,
            )

        """
        request_ = await Request.get_row(session, request_id)
        await self.get_qp_file(session, request_.id)
        return request_
