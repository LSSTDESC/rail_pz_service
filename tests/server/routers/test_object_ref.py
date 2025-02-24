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
async def test_object_ref_routes(
    client: AsyncClient,
    api_version: str,
    engine: AsyncEngine,
) -> None:
    """Test `/object_ref` API endpoint."""

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
            validate=False,            
        )

        object_ref_ = await db.ObjectRef.create_row(
            session,
            name=f"object_{uuid_int}",
            dataset_name=dataset_.name,
            index=0,
        )

        response = await client.get(f"{config.asgi.prefix}/{api_version}/object_ref/list")
        object_refs = check_and_parse_response(response, list[models.ObjectRef])
        entry = object_refs[0]
        
        assert entry.id == object_ref_.id

        response = await client.get(f"{config.asgi.prefix}/{api_version}/object_ref/get/{entry.id}")
        check = check_and_parse_response(response, models.ObjectRef)

        assert check.id == object_ref_.id

        params = models.NameQuery(name=object_ref_.name).model_dump()
        
        response = await client.get(f"{config.asgi.prefix}/{api_version}/object_ref/get_row_by_name", params=params)
        check = check_and_parse_response(response, models.ObjectRef)
        assert check.id == object_ref_.id
        
        # delete everything we just made in the session
        await cleanup(session)
