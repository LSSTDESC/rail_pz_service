import os

import pytest
import qp
import structlog
from safir.database import create_async_session
from sqlalchemy.ext.asyncio import AsyncEngine

from rail_pz_service import db

from .util_functions import (
    cleanup,
)


@pytest.mark.asyncio()
async def test_cache(engine: AsyncEngine, setup_test_area: int) -> None:
    """Test `job` db table."""

    assert setup_test_area == 0
    # generate a uuid to avoid collisions
    logger = structlog.get_logger(__name__)

    cache = db.Cache()
    async with engine.begin():
        session = await create_async_session(engine, logger)

        await cache.load_algorithms_from_rail_env(session)
        await cache.load_catalog_tags_from_rail_env(session)

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

        check_request = await cache.run_process_request(session, request.id)

        qp_file_path = await cache.get_qp_file(session, check_request.id)
        qp_ens = qp.read(qp_file_path)

        assert qp_ens.npdf != 0

        # cleanup
        await cleanup(session)
