import os

import pytest
import structlog
from httpx import AsyncClient
from safir.database import create_async_session
from sqlalchemy.ext.asyncio import AsyncEngine

from rail_pz_service import db, models
from rail_pz_service.config import config

from .util_functions import (
    check_and_parse_response,
    cleanup,
)


@pytest.mark.asyncio()
@pytest.mark.parametrize("api_version", ["v1"])
async def test_load_routes(
    client: AsyncClient,
    api_version: str,
    engine: AsyncEngine,
    setup_test_area: int,
) -> None:
    """Test `/load` API endpoint."""
    assert setup_test_area == 0

    logger = structlog.get_logger(__name__)

    cache = db.Cache()

    async with engine.begin():
        session = await create_async_session(engine, logger)

        await cache.load_algorithms_from_rail_env(session)
        await cache.load_catalog_tags_from_rail_env(session)

        model_path = os.path.join("tests", "temp_data", "inputs", "model_com_cam_trainz_base.pkl")
        dataset_path = os.path.join("tests", "temp_data", "inputs", "minimal_gold_test.hdf5")

        model_params = models.LoadModelQuery(
            name="com_cam_trainz_base",
            path=model_path,
            algo_name="TrainZEstimator",
            catalog_tag_name="com_cam",
        ).model_dump_json()
        response = await client.post(f"{config.asgi.prefix}/{api_version}/load/model", content=model_params)
        the_model = check_and_parse_response(response, models.Model)
        assert the_model.name == "com_cam_trainz_base"

        dataset_params = models.LoadDatasetQuery(
            name="com_cam_test",
            path=dataset_path,
            catalog_tag_name="com_cam",
        ).model_dump_json()
        response = await client.post(
            f"{config.asgi.prefix}/{api_version}/load/dataset", content=dataset_params
        )
        the_dataset = check_and_parse_response(response, models.Dataset)
        assert the_dataset.name == "com_cam_test"

        estimator_params = models.LoadEstimatorQuery(
            name="com_cam_trainz_base",
            model_name="com_cam_trainz_base",
        ).model_dump_json()
        response = await client.post(
            f"{config.asgi.prefix}/{api_version}/load/estimator",
            content=estimator_params,
        )
        the_estimator = check_and_parse_response(response, models.Estimator)
        assert the_estimator.name == "com_cam_trainz_base"

        request_create = models.RequestCreate(
            dataset_name=the_dataset.name,
            estimator_name=the_estimator.name,
        ).model_dump_json()
        response = await client.post(
            f"{config.asgi.prefix}/{api_version}/request/create", content=request_create
        )
        the_request = check_and_parse_response(response, models.Request)

        response = await client.post(f"{config.asgi.prefix}/{api_version}/request/run/{the_request.id}")
        check_request = check_and_parse_response(response, models.Request)

        params = models.DownloadQuery(filename="tests/temp_data/model_check.pkl").model_dump()
        response = await client.get(
            f"{config.asgi.prefix}/{api_version}/model/download/{the_model.id}",
            params=params,
        )
        filename = response.headers["content-disposition"].split("=")[1].replace('"', "")
        assert filename == "tests/temp_data/model_check.pkl"

        params = models.DownloadQuery(filename="tests/temp_data/dataset_check.hdf5").model_dump()
        response = await client.get(
            f"{config.asgi.prefix}/{api_version}/dataset/download/{the_dataset.id}",
            params=params,
        )
        filename = response.headers["content-disposition"].split("=")[1].replace('"', "")
        assert filename == "tests/temp_data/dataset_check.hdf5"

        params = models.DownloadQuery(filename="tests/temp_data/qp_out.hdf5").model_dump()
        response = await client.get(
            f"{config.asgi.prefix}/{api_version}/request/download/{check_request.id}",
            params=params,
        )
        filename = response.headers["content-disposition"].split("=")[1].replace('"', "")
        assert filename == "tests/temp_data/qp_out.hdf5"

        # delete everything we just made in the session
        await cleanup(session)
