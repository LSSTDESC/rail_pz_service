import os
import uuid

import structlog

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_scoped_session, AsyncEngine
from safir.database import create_async_session

from rail_pz_service import db
from rail_pz_service.common import models
from rail_pz_service.common.config import config

from .util_functions import (
    check_and_parse_response,
    cleanup,
)


@pytest.mark.asyncio()
@pytest.mark.parametrize("api_version", ["v1"])
async def test_model_routes(
    client: AsyncClient,
    api_version: str,
    engine: AsyncEngine,
) -> None:
    """Test `/model` API endpoint."""

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

        catalog_tag_ = await db.CatalogTag.create_row(
            session,
            name=f"catalog_{uuid_int}",
            class_name="not.really.a.class",
        )
        
        model_ = await db.Model.create_row(
            session,
            name=f"model_{uuid_int}",
            path="not/really/a/path",
            algo_name=algo_.name,
            catalog_tag_name=catalog_tag_.name,
        )
        
        response = await client.get(f"{config.asgi.prefix}/{api_version}/model/list")
        models_ = check_and_parse_response(response, list[models.Model])
        entry = models_[0]
        
        assert entry.id == model_.id

        response = await client.get(f"{config.asgi.prefix}/{api_version}/model/get/{entry.id}")
        check = check_and_parse_response(response, models.Model)

        assert check.id == model_.id

        params = models.NameQuery(name=model_.name).model_dump()
        
        response = await client.get(f"{config.asgi.prefix}/{api_version}/model/get_row_by_name", params=params)
        check = check_and_parse_response(response, models.Model)
        assert check.id == model_.id
        
        # delete everything we just made in the session
        await cleanup(session)
