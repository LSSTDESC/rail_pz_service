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


async def _test_algorithm_db(session: async_scoped_session) -> None:
    """Test `job` db table."""
    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    if session:
        await db.Algorithm.create_row(
            session,
            name=f"algo_{uuid_int}",
            class_name="not.really.a.class",
        )

        with pytest.raises(errors.RAILIntegrityError):
            await db.Algorithm.create_row(
                session,
                name=f"algo_{uuid_int}",
                class_name="some_other_class",
            )

        rows = await db.Algorithm.get_rows(session)
        assert len(rows) == 1
        entry = rows[0]

        check = await db.Algorithm.get_row(session, entry.id)
        assert check.id == entry.id

        check = await db.Algorithm.get_row_by_name(session, entry.name)
        assert check.id == entry.id

        # cleanup
        await cleanup(session)


@pytest.mark.asyncio()
async def test_algorithm_db(engine: AsyncEngine) -> None:
    """Test `Algorithm` db table."""
    logger = structlog.get_logger(__name__)

    async with engine.begin():
        session = await create_async_session(engine, logger)
    try:
        await _test_algorithm_db(session)
    except Exception as e:
        await session.rollback()
        await cleanup(session)
        raise e
