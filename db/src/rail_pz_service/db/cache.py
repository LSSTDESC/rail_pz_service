from datetime import datetime

from ceci.errors import StageNotFound
from ceci.stage import Stage
from sqlalchemy.ext.asyncio import async_scoped_session

from rail.core.estimator import CatEstimator
from rail.interfaces.pz_factory import PZFactory
from rail.utils.catalog_utils import CatalogConfigBase

from ..errors import RAILImportError, RAILRequestError
from .algorithm import Algorithm
from .catalog_tag import CatalogTag
from .dataset import Dataset
from .estimator import Estimator
from .model import Model
from .request import Request


class Cache:
    def __init__(self) -> None:
        self._algorithms: dict[int, type[CatEstimator] | None] = {}
        self._catalog_tags: dict[int, type[CatalogConfigBase] | None] = {}
        self._estimators: dict[int, CatEstimator | None] = {}
        self._qp_files: dict[int, str | None] = {}

    def clear(self) -> None:
        self._algorithms = {}
        self._catalog_tags = {}
        self._estimators = {}
        self._qp_files = {}

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
            return Stage.get_stage(class_name, module_name)
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
        _class_name = tokens[-1]

        try:
            return CatalogConfigBase.get_class(catalog_tag.name, module_name)
        except KeyError as missing_key:
            raise RAILImportError(
                f"Failed to load catalog_tag {catalog_tag.name} because {missing_key}"
            ) from missing_key

    async def _build_estimator(
        self,
        session: async_scoped_session,
        estimator: Estimator,
    ) -> CatEstimator:
        algo_class = await self.get_algo_class(session, estimator.algo_id)
        catalog_tag_class = await self.get_catalog_tag_class(session, estimator.catalog_tag_id)
        CatalogConfigBase.apply_class(catalog_tag_class)
        model = await Model.get_row(session, estimator.model_id)
        estimator_instance = PZFactory.build_stage_instance(
            estimator.name,
            algo_class,
            model.path,
            **estimator.config,
        )
        return estimator_instance

    async def _process_request(
        self,
        session: async_scoped_session,
        request: Request,
    ) -> str:
        estimator = await self.get_estimator(session, request.estimator_id)
        dataset = await Dataset.get_row(session, request.dataset_id)

        if dataset.path is not None:
            result_handle = PZFactory.run_cat_estimator_stage(estimator, dataset.path)

            now = datetime.now()

        else:
            _data_out = PZFactory.estimate_single_pz(
                estimator,
                dataset.data,
                dataset.n_objects,
            )
            result_handle = estimator.get_handle("output")
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
            estimator = self._build_estimator(session, estimator_)
        except RAILImportError as failed_import:
            self._estimators[key] = None
            raise RAILImportError(f"Import of Estimator failed because {failed_import}") from failed_import

        return estimator

    async def get_qp_file(
        self,
        session: async_scoped_session,
        key: int,
    ) -> str:
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
