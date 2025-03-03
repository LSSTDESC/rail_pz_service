import uuid

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
async def test_request_routes(
    client: AsyncClient,
    api_version: str,
    engine: AsyncEngine,
) -> None:
    """Test `/request` API endpoint."""

    logger = structlog.get_logger(__name__)

    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    async with engine.begin():
        session = await create_async_session(engine, logger)

        algorithm_ = await db.Algorithm.create_row(
            session,
            name=f"algorithm_{uuid_int}",
            class_name="not.really.a.class",
        )

        catalog_tag_ = await db.CatalogTag.create_row(
            session,
            name=f"catalog_{uuid_int}",
            class_name="not.really.a.class",
        )

        model_ = await db.Model.create_row(
            session,
            name=f"model_{uuid_int}",
            path="not/really/a/path",
            algo_name=algorithm_.name,
            catalog_tag_name=catalog_tag_.name,
            validate_file=False,
        )

        estimator_ = await db.Estimator.create_row(
            session,
            name=f"estimator_{uuid_int}",
            algo_name=algorithm_.name,
            catalog_tag_name=catalog_tag_.name,
            model_name=model_.name,
        )

        dataset_ = await db.Dataset.create_row(
            session,
            name=f"dataset_{uuid_int}",
            n_objects=2,
            path="not/really/a/path",
            data=None,
            catalog_tag_name=catalog_tag_.name,
            validate_file=False,
        )

        request_ = await db.Request.create_row(
            session,
            estimator_name=estimator_.name,
            dataset_name=dataset_.name,
        )

        response = await client.get(f"{config.asgi.prefix}/{api_version}/request/list")
        requests = check_and_parse_response(response, list[models.Request])
        entry = requests[0]

        assert entry.id == request_.id

        response = await client.get(f"{config.asgi.prefix}/{api_version}/request/get/{entry.id}")
        check = check_and_parse_response(response, models.Request)

        assert check.id == request_.id

        response = await client.delete(f"{config.asgi.prefix}/{api_version}/request/{request_.id}")
        assert response.status_code == 204

        response = await client.delete(f"{config.asgi.prefix}/{api_version}/request/13412")
        assert response.status_code == 404

        response = await client.get(f"{config.asgi.prefix}/{api_version}/request/list")
        requests = check_and_parse_response(response, list[models.Request])
        assert len(requests) == 0

        # delete everything we just made in the session
        await cleanup(session)
