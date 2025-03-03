import os

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
            path=os.path.join("tests", "temp_data", "inputs", "model_com_cam_trainz_base.pkl"),
            algo_name="TrainZEstimator",
            catalog_tag_name="com_cam",
        )

        assert the_model.name == "com_cam_trainz_base"

        the_dataset = await cache.load_dataset_from_file(
            session,
            name="com_cam_test",
            path=os.path.join("tests", "temp_data", "inputs", "minimal_gold_test.hdf5"),
            catalog_tag_name="com_cam",
        )

        the_estimator = await cache.load_estimator(
            session,
            name="com_cam_trainz_base",
            model_name="com_cam_trainz_base",
        )

        request = await db.Request.create_row(
            session,
            dataset_id=the_dataset.id,
            estimator_id=the_estimator.id,
        )
        await session.refresh(request)

        estimators = await db.Estimator.get_rows(session)
        cached_estim = await cache.get_estimator(session, estimators[0].id)
        assert cached_estim

        check_request = await cache.run_process_request(session, request.id)

        qp_file_path = await cache.get_qp_file(session, check_request.id)
        check_qp_file_path = await cache.get_qp_file(session, check_request.id)

        assert qp_file_path == check_qp_file_path
        qp_ens = await cache.get_qp_dist(session, check_request.id)

        assert qp_ens.npdf != 0

        cache.clear()

        qp_ens_check = await cache.get_qp_dist(session, check_request.id)
        assert qp_ens_check.npdf != 0

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
