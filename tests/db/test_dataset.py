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
async def test_dataset_db(engine: AsyncEngine) -> None:
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

        with pytest.raises(errors.RAILIntegrityError):
            await db.Dataset.create_row(
                session,
                name=f"dataset_{uuid_int}",
                n_objects=2,
                path="not/really/a/path",
                data=None,
                catalog_tag_name=catalog_tag_.name,
                validate=False,                
            )

        rows = await db.Dataset.get_rows(session)
        assert len(rows) == 1
        entry = rows[0]
        
        check = await db.Dataset.get_row(session, entry.id)
        assert check.id == entry.id
        
        check = await db.Dataset.get_row_by_name(session, entry.name)
        assert check.id == entry.id

        dataset_2 = await db.Dataset.create_row(
            session,
            name=f"dataset_{uuid_int}_2",
            n_objects=2,            
            path="not/really/a/path/2",
            data=None,
            catalog_tag_id=catalog_tag_.id,
            validate=False,            
        )

        rows = await db.Dataset.get_rows(session)
        assert len(rows) == 2
        
        dataset_3 = await db.Dataset.create_row(
            session,
            name=f"dataset_{uuid_int}_3",
            n_objects=2,           
            path=None,
            data=dict(
                u=[25., 25.],
                g=[25., 25.],
                r=[25., 25.],
                i=[25., 25.],
                z=[25., 25.],
                y=[25., 25.],
            ),
            catalog_tag_id=catalog_tag_.id,
            validate=False,
        )


        # cleanup
        await cleanup(session)
