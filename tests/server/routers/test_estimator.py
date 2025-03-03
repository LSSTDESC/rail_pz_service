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
async def test_estimator_routes(
    client: AsyncClient,
    api_version: str,
    engine: AsyncEngine,
) -> None:
    """Test `/estimator` API endpoint."""

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

        response = await client.get(f"{config.asgi.prefix}/{api_version}/estimator/list")
        estimators = check_and_parse_response(response, list[models.Estimator])
        entry = estimators[0]

        assert entry.id == estimator_.id

        response = await client.get(f"{config.asgi.prefix}/{api_version}/estimator/get/{entry.id}")
        check = check_and_parse_response(response, models.Estimator)

        assert check.id == estimator_.id

        params = models.NameQuery(name=estimator_.name).model_dump()

        response = await client.get(
            f"{config.asgi.prefix}/{api_version}/estimator/get_row_by_name",
            params=params,
        )
        check = check_and_parse_response(response, models.Estimator)
        assert check.id == estimator_.id

        # delete everything we just made in the session
        await cleanup(session)
