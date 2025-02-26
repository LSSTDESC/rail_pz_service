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
async def test_dataset_routes(
    client: AsyncClient,
    api_version: str,
    engine: AsyncEngine,
) -> None:
    """Test `/dataset` API endpoint."""

    logger = structlog.get_logger(__name__)

    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    async with engine.begin():
        session = await create_async_session(engine, logger)

        catalog_tag_ = await db.CatalogTag.create_row(
            session,
            name=f"catalog_{uuid_int}",
            class_name="not.really.a.class",
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

        response = await client.get(f"{config.asgi.prefix}/{api_version}/dataset/list")
        datasets = check_and_parse_response(response, list[models.Dataset])
        entry = datasets[0]

        assert entry.id == dataset_.id

        response = await client.get(f"{config.asgi.prefix}/{api_version}/dataset/get/{entry.id}")
        check = check_and_parse_response(response, models.Dataset)

        assert check.id == dataset_.id

        params = models.NameQuery(name=dataset_.name).model_dump()

        response = await client.get(
            f"{config.asgi.prefix}/{api_version}/dataset/get_row_by_name", params=params
        )
        check = check_and_parse_response(response, models.Dataset)
        assert check.id == dataset_.id

        # delete everything we just made in the session
        await cleanup(session)
