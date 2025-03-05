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


async def _test_dataset_db(session: async_scoped_session) -> None:
    """Test `Dataset` db table."""
    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    if session:
        catalog_tag_ = await db.CatalogTag.create_row(
            session,
            name=f"catalog_{uuid_int}",
            class_name="not.really.a.class",
        )

        await db.Dataset.create_row(
            session,
            name=f"dataset_{uuid_int}",
            n_objects=2,
            path="not/really/a/path",
            data=None,
            catalog_tag_name=catalog_tag_.name,
            validate_file=False,
        )

        with pytest.raises(errors.RAILIntegrityError):
            await db.Dataset.create_row(
                session,
                name=f"dataset_{uuid_int}",
                n_objects=2,
                path="not/really/a/path",
                data=None,
                catalog_tag_name=catalog_tag_.name,
                validate_file=False,
            )

        with pytest.raises(errors.RAILFileNotFoundError):
            await db.Dataset.create_row(
                session,
                name=f"dataset_{uuid_int}",
                n_objects=2,
                path="not/really/a/path",
                data=None,
                catalog_tag_name=catalog_tag_.name,
            )

        with pytest.raises(errors.RAILBadDatasetError):
            await db.Dataset.create_row(
                session,
                name=f"dataset_{uuid_int}",
                n_objects=2,
                path=None,
                data={},
                catalog_tag_name=catalog_tag_.name,
            )

        with pytest.raises(errors.RAILBadDatasetError):
            await db.Dataset.create_row(
                session,
                name=f"dataset_{uuid_int}",
                path=None,
                data={"a": "adf"},
                catalog_tag_name=catalog_tag_.name,
            )

        with pytest.raises(errors.RAILBadDatasetError):
            await db.Dataset.create_row(
                session,
                name=f"dataset_{uuid_int}",
                path=None,
                data={"a": [24.5], "b": [24.5, 24.5]},
                catalog_tag_name=catalog_tag_.name,
            )

        with pytest.raises(errors.RAILMissingRowCreateInputError):
            await db.Dataset.create_row(
                session,
            )

        with pytest.raises(errors.RAILMissingRowCreateInputError):
            await db.Dataset.create_row(
                session,
                name=f"dataset_{uuid_int}",
                n_objects=2,
                path="not/really/a/path",
                data=None,
                validate_file=False,
            )

        with pytest.raises(errors.RAILMissingRowCreateInputError):
            await db.Dataset.create_row(
                session,
                name=f"dataset_{uuid_int}",
                n_objects=2,
                path=None,
                data=None,
                catalog_tag_name=catalog_tag_.name,
                validate_file=False,
            )

        with pytest.raises(errors.RAILMissingNameError):
            await db.Dataset.create_row(
                session,
                name=f"dataset_{uuid_int}",
                n_objects=2,
                path="not/really/a/path",
                data=None,
                catalog_tag_name="bad",
                validate_file=False,
            )

        with pytest.raises(errors.RAILIntegrityError):
            await db.Dataset.create_row(
                session,
                name=f"dataset_{uuid_int}",
                n_objects=2,
                path="not/really/a/path",
                data=None,
                catalog_tag_name=catalog_tag_.name,
                validate_file=False,
            )

        rows = await db.Dataset.get_rows(session)
        assert len(rows) == 1
        entry = rows[0]

        check = await db.Dataset.get_row(session, entry.id)
        assert check.id == entry.id

        check = await db.Dataset.get_row_by_name(session, entry.name)
        assert check.id == entry.id

        await db.Dataset.create_row(
            session,
            name=f"dataset_{uuid_int}_2",
            n_objects=2,
            path="not/really/a/path/2",
            data=None,
            catalog_tag_id=catalog_tag_.id,
            validate_file=False,
        )

        rows = await db.Dataset.get_rows(session)
        assert len(rows) == 2

        await db.Dataset.create_row(
            session,
            name=f"dataset_{uuid_int}_3",
            n_objects=2,
            path=None,
            data=dict(
                u=[25.0, 25.0],
                g=[25.0, 25.0],
                r=[25.0, 25.0],
                i=[25.0, 25.0],
                z=[25.0, 25.0],
                y=[25.0, 25.0],
            ),
            catalog_tag_id=catalog_tag_.id,
            validate_file=False,
        )

        # cleanup
        await cleanup(session)


@pytest.mark.asyncio()
async def test_dataset_db(engine: AsyncEngine) -> None:
    """Test `Dataset` db table."""
    # generate a uuid to avoid collisions
    logger = structlog.get_logger(__name__)

    async with engine.begin():
        session = await create_async_session(engine, logger)
    try:
        await _test_dataset_db(session)
    except Exception as e:
        await session.rollback()
        await cleanup(session)
        raise e
