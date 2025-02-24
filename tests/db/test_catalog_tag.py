import importlib
import os
import uuid

import pytest
import structlog
from safir.database import create_async_session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from rail_pz_service import db
from rail_pz_service.common import errors

from .util_functions import (
    cleanup,
)


@pytest.mark.asyncio()
async def test_catalog_tag_db(engine: AsyncEngine) -> None:
    """Test `job` db table."""
    cache = importlib.import_module("rail_pz_service.db.cache")
    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int
    logger = structlog.get_logger(__name__)
    async with engine.begin():
        session = await create_async_session(engine, logger)

        catalog_tag_ = await db.CatalogTag.create_row(
            session,
            name=f"catalog_{uuid_int}",
            class_name="not.really.a.class",
        )

        with pytest.raises(errors.RAILIntegrityError):
            await db.CatalogTag.create_row(
                session,
                name=f"catalog_{uuid_int}",
                class_name="some_other_class",
            )

        rows = await db.CatalogTag.get_rows(session)
        assert len(rows) == 1
        entry = rows[0]
        
        check = await db.CatalogTag.get_row(session, entry.id)
        assert check.id == entry.id
        
        check = await db.CatalogTag.get_row_by_name(session, entry.name)
        assert check.id == entry.id

        # cleanup
        await cleanup(session)
