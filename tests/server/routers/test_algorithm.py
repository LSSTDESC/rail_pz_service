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
async def test_algorithm_routes(
    client: AsyncClient,
    api_version: str,
    engine: AsyncEngine,
) -> None:
    """Test `/algorithm` API endpoint."""

    logger = structlog.get_logger(__name__)

    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    async with engine.begin():
        session = await create_async_session(engine, logger)

        algo_ = await db.Algorithm.create_row(
            session,
            name=f"algo_{uuid_int}",
            class_name="not.really.a.class",
        )

        response = await client.get(f"{config.asgi.prefix}/{api_version}/algorithm/list")
        algorithms = check_and_parse_response(response, list[models.Algorithm])
        entry = algorithms[0]

        assert entry.id == algo_.id

        response = await client.get(f"{config.asgi.prefix}/{api_version}/algorithm/get/{entry.id}")
        check = check_and_parse_response(response, models.Algorithm)

        assert check.id == algo_.id

        params = models.NameQuery(name=algo_.name).model_dump()

        response = await client.get(
            f"{config.asgi.prefix}/{api_version}/algorithm/get_row_by_name",
            params=params,
        )
        check = check_and_parse_response(response, models.Algorithm)
        assert check.id == algo_.id

        # delete everything we just made in the session
        await cleanup(session)
