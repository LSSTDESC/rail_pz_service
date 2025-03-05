import uuid

import pytest
import structlog
from safir.database import create_async_session
from sqlalchemy.ext.asyncio import AsyncEngine, async_scoped_session

from rail_pz_service import db
from rail_pz_service.common import errors

from .util_functions import (
    cleanup,
)


async def _test_catalog_tag_db(session: async_scoped_session) -> None:
    """Test `job` db table."""
    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    if session:
        await db.CatalogTag.create_row(
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

        with pytest.raises(errors.RAILMissingIDError):
            await db.CatalogTag.get_row(session, 13134)

        with pytest.raises(errors.RAILMissingIDError):
            await db.CatalogTag.delete_row(session, 13134)

        # cleanup
        await cleanup(session)


@pytest.mark.asyncio()
async def test_catalog_tag_db(engine: AsyncEngine) -> None:
    """Test `CatalogTag` db table."""
    logger = structlog.get_logger(__name__)

    async with engine.begin():
        session = await create_async_session(engine, logger)
    try:
        await _test_catalog_tag_db(session)
    except Exception as e:
        await session.rollback()
        await cleanup(session)
        raise e
