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
async def test_object_ref_db(engine: AsyncEngine) -> None:
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

        with pytest.raises(errors.RAILIntegrityError):
            await db.ObjectRef.create_row(
                session,
                name=f"object_{uuid_int}",
                dataset_name=dataset_.name,
                index=0,                
            )

        rows = await db.ObjectRef.get_rows(session)
        assert len(rows) == 1
        entry = rows[0]
        
        check = await db.ObjectRef.get_row(session, entry.id)
        assert check.id == entry.id
        
        object_ref_2 = await db.ObjectRef.create_row(
            session,
            name=f"object_{uuid_int}_2",
            dataset_id=dataset_.id,
            index=1,            
        )

        rows = await db.ObjectRef.get_rows(session)
        assert len(rows) == 2

        # cleanup
        await cleanup(session)
