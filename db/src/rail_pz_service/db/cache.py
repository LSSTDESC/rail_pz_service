"""Class to cache objects created from specific DB rows"""

from __future__ import annotations

import os
import shutil
from datetime import datetime

from ceci.errors import StageNotFound
from ceci.stage import PipelineStage
from rail.core import RailEnv, RailStage
from rail.estimation.estimator import CatEstimator
from rail.interfaces.pz_factory import PZFactory
from rail.utils.catalog_utils import CatalogConfigBase
from sqlalchemy.ext.asyncio import async_scoped_session

from rail_pz_service.common.config import config
from rail_pz_service.common.errors import RAILImportError, RAILIntegrityError, RAILRequestError

from .algorithm import Algorithm
from .catalog_tag import CatalogTag
from .dataset import Dataset
from .estimator import Estimator
from .model import Model
from .request import Request


class Cache:
    """Cache for objects created from specific DB rows"""

    _shared_cache: Cache | None = None

    def __init__(self) -> None:
        self._algorithms: dict[int, type[CatEstimator] | None] = {}
        self._catalog_tags: dict[int, type[CatalogConfigBase] | None] = {}
        self._estimators: dict[int, CatEstimator | None] = {}
        self._qp_files: dict[int, str | None] = {}

    def clear(self) -> None:
        """Clear out the cache"""
        self._algorithms = {}
        self._catalog_tags = {}
        self._estimators = {}
        self._qp_files = {}

    @classmethod
    def shared_cache(cls) -> Cache:
        if cls._shared_cache is None:
            cls._shared_cache = Cache()
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
            config = {}
        else:
            config = estimator.config.copy()

        estimator_instance = PZFactory.build_stage_instance(
            estimator.name,
            algo_class,
            model.path,
            **config,
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

        output_path = os.path.join("qp_files", dataset.name, f"{estimator.name}.hdf5")

        aliased_tag = estimator_instance.get_aliased_tag("output")
        estimator_instance._outputs[aliased_tag] = output_path

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

        now = datetime.now()
        await request.update_values(
            session,
            qp_file_path=result_handle.path,
            time_finished=now,
        )

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
        if key in self._algorithms:
            algo_class = self._algorithms[key]
            if algo_class is None:
                algo_ = await Algorithm.get_row(session, key)
                raise RAILImportError(f"Failed to load alogrithm {algo_}")
            return algo_class

        algo_ = await Algorithm.get_row(session, key)
        try:
            algo_class = self._load_algorithm_class(algo_)
        except RAILImportError as failed_import:
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
        if key in self._catalog_tags:
            catalog_tag_class = self._catalog_tags[key]
            if catalog_tag_class is None:
                catalog_tag_ = await CatalogTag.get_row(session, key)
                raise RAILImportError(f"Failed to load catalog_tags {catalog_tag_}")
            return catalog_tag_class

        catalog_tag_ = await CatalogTag.get_row(session, key)
        try:
            catalog_tag_class = self._load_catalog_tag_class(catalog_tag_)
        except RAILImportError as failed_import:
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

        if key in self._estimators:
            estimator = self._estimators[key]
            if estimator is None:
                estimator_ = await Estimator.get_row(session, key)
                raise RAILImportError(f"Failed to load Estimator {estimator_}")
            return estimator

        estimator_ = await Estimator.get_row(session, key)
        try:
            estimator = await self._build_estimator(session, estimator_)
        except RAILImportError as failed_import:
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

        if key in self._qp_files:
            qp_file = self._qp_files[key]
            if qp_file is None:
                request_ = await Request.get_row(session, key)
                raise RAILRequestError(f"Request failed {request_}")
            return qp_file

        request_ = await Request.get_row(session, key)
        try:
            qp_file = await self._process_request(session, request_)
        except RAILRequestError as failed_request:
            self._qp_files[key] = None
            raise RAILRequestError(f"Request failed because {failed_request}") from failed_request

        return qp_file

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
        """
        algos_: list[Algorithm] = []
        RailEnv.import_all_packages()
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

            except RAILIntegrityError:
                continue

            await session.refresh(new_algo)
            check_class = await self.get_algo_class(session, new_algo.id)
            if check_class != the_class:
                raise RAILIntegrityError(f"{the_class.__name__} != {check_class.__name__}")
            algos_.append(new_algo)
        return algos_

    async def load_catalog_tags_from_rail_env(
        self,
        session: async_scoped_session,
    ) -> list[CatalogTag]:
        """Load all of the CatalogConfig tags from

        Parameters
        ----------
        session
            DB session manager

        Returns
        -------
        list[CatalogTag]
            Newly created CatalogTag database rows

        Raises
        ------
        RAILIntegrityError
            Rows already exist in database
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
            except RAILIntegrityError:
                pass
            await session.refresh(new_catalog_tag)
            check_class = await self.get_catalog_tag_class(session, new_catalog_tag.id)
            if check_class != a_class:
                raise RAILIntegrityError(f"{a_class.__name__} != {check_class.__name__}")
            catalog_tags_.append(new_catalog_tag)
        return catalog_tags_

    async def load_model_from_file(
        self,
        session: async_scoped_session,
        name: str,
        file_path: str,
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

        file_path
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
        """
        # Validate the input file
        catalog_tag = await CatalogTag.get_row_by_name(session, catalog_tag_name)
        algo = await Algorithm.get_row_by_name(session, algo_name)

        Model.validate_model(file_path, algo, catalog_tag)

        # File looks ok, move it to the archive area
        suffix = os.path.splitext(file_path)[1]
        output_name = os.path.join(
            config.storage.archive, "models", algo_name, catalog_tag_name, f"{name}{suffix}"
        )
        output_abspath = os.path.abspath(output_name)
        output_dir = os.path.dirname(output_abspath)
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy(file_path, output_abspath)

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
            print(f"Model ingest failed: removing file {output_abspath}")
            os.unlink(output_abspath)
            raise RAILIntegrityError(msg) from msg

    async def load_dataset_from_file(
        self,
        session: async_scoped_session,
        name: str,
        file_path: str,
        catalog_tag_name: str,
    ) -> Dataset:
        """Import a data file to the archive area and add a Dataset row

        Parameters
        ----------
        session
            DB session manager

        name
            Name for new Dataset

        file_path
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
        """
        # Validate the input file
        catalog_tag = await CatalogTag.get_row_by_name(session, catalog_tag_name)
        n_objects = Dataset.validate_data_for_path(file_path, catalog_tag)

        # File looks ok, move it to the archive area
        suffix = os.path.splitext(file_path)[1]
        output_name = os.path.join(config.storage.archive, "datasets", catalog_tag_name, f"{name}{suffix}")
        output_abspath = os.path.abspath(output_name)
        output_dir = os.path.dirname(output_abspath)
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy(file_path, output_abspath)

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
            print(f"Dataset ingest failed: removing file {output_abspath}")
            os.unlink(output_abspath)
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
        """

        model = await Model.get_row_by_name(session, model_name)

        try:
            new_estimator = await Estimator.create_row(
                session,
                name=name,
                algo_id=model.algo_id,
                catalog_tag_id=model.catalog_tag_id,
                model_id=model.id,
                config=config,
            )
            await session.refresh(new_estimator)
            return new_estimator
        except RAILIntegrityError as msg:
            raise RAILIntegrityError(msg) from msg

    async def run_process_request(
        self,
        session: async_scoped_session,
        request_id: int,
    ) -> Request:
        """Create a Request to process Dataset with a particular Estimator

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
        """
        request_ = await Request.get_row(session, request_id)
        await self.get_qp_file(session, request_.id)
        return request_
