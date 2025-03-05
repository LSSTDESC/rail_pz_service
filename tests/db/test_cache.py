import os
import pathlib

import pytest
import structlog
from safir.database import create_async_session
from sqlalchemy.ext.asyncio import AsyncEngine, async_scoped_session

from rail_pz_service import db

from .util_functions import (
    cleanup,
)


async def _test_cache(session: async_scoped_session) -> None:
    """Test the db.Cache object"""

    cache = db.Cache()

    if session:
        await cache.load_algorithms_from_rail_env(session)
        await cache.load_catalog_tags_from_rail_env(session)

        # make sure reloading doesn't cause problems
        await cache.load_algorithms_from_rail_env(session)
        await cache.load_catalog_tags_from_rail_env(session)

        algos = await db.Algorithm.get_rows(session)
        catalog_tags = await db.CatalogTag.get_rows(session)

        algo_class = await cache.get_algo_class(session, algos[0].id)
        assert algo_class.name in algos[0].class_name

        catalog_tag_class = await cache.get_catalog_tag_class(session, catalog_tags[0].id)
        assert catalog_tag_class.__name__ in catalog_tags[0].class_name

        the_model = await cache.load_model_from_file(
            session,
            name="com_cam_trainz_base",
            path=pathlib.Path(os.path.join("tests", "temp_data", "inputs", "model_com_cam_trainz_base.pkl")),
            algo_name="TrainZEstimator",
            catalog_tag_name="com_cam",
        )

        assert the_model.name == "com_cam_trainz_base"

        the_dataset = await cache.load_dataset_from_file(
            session,
            name="com_cam_test",
            path=pathlib.Path(os.path.join("tests", "temp_data", "inputs", "minimal_gold_test.hdf5")),
            catalog_tag_name="com_cam",
        )
        data = dict(
            u_cModelMag=24.4,
            g_cModelMag=24.4,
            r_cModelMag=24.4,
            i_cModelMag=24.4,
            z_cModelMag=24.4,
            y_cModelMag=24.4,
            u_cModelMagErr=0.5,
            g_cModelMagErr=0.5,
            r_cModelMagErr=0.5,
            i_cModelMagErr=0.5,
            z_cModelMagErr=0.5,
            y_cModelMagErr=0.5,
        )
        values_dataset = await cache.load_dataset_from_values(
            session,
            name="com_cam_values",
            data=data,
            catalog_tag_name="com_cam",
        )

        the_estimator = await cache.load_estimator(
            session,
            name="com_cam_trainz_base",
            model_name="com_cam_trainz_base",
        )

        request = await cache.create_request(
            session,
            dataset_name=the_dataset.name,
            estimator_name=the_estimator.name,
        )
        await session.refresh(request)

        estimators = await db.Estimator.get_rows(session)
        cached_estim = await cache.get_estimator(session, estimators[0].id)
        assert cached_estim

        check_request = await cache.run_request(session, request.id)

        qp_file_path = await cache.get_qp_file(session, check_request.id)
        check_qp_file_path = await cache.get_qp_file(session, check_request.id)

        assert qp_file_path == check_qp_file_path
        qp_ens = await cache.get_qp_dist(session, check_request.id)

        assert qp_ens.npdf != 0

        cache.clear()

        qp_ens_check = await cache.get_qp_dist(session, check_request.id)
        assert qp_ens_check.npdf != 0

        request2 = await cache.create_request(
            session,
            dataset_name=values_dataset.name,
            estimator_name=the_estimator.name,
        )
        await session.refresh(request2)

        check_request2 = await cache.run_request(session, request2.id)

        qp_file_path2 = await cache.get_qp_file(session, check_request2.id)
        check_qp_file_path2 = await cache.get_qp_file(session, check_request2.id)

        assert qp_file_path2 == check_qp_file_path2
        qp_ens2 = await cache.get_qp_dist(session, check_request2.id)

        assert qp_ens2.npdf != 0

        # cleanup
        await cleanup(session)


@pytest.mark.asyncio()
async def test_cache(engine: AsyncEngine, setup_test_area: int) -> None:
    """Test the db.Cache object"""
    logger = structlog.get_logger(__name__)

    assert setup_test_area == 0

    async with engine.begin():
        session = await create_async_session(engine, logger)
    try:
        await _test_cache(session)
    except Exception as e:
        await session.rollback()
        await cleanup(session)
        raise e
