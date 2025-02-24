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
async def test_request_db(engine: AsyncEngine) -> None:
    """Test `job` db table."""
    cache = importlib.import_module("rail_pz_service.db.cache")
    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int
    logger = structlog.get_logger(__name__)
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
        )
        
        estimator_ = await db.Estimator.create_row(
            session,
            name=f"estimator_{uuid_int}",
            algo_name=algorithm_.name,
            catalog_tag_name=catalog_tag_.name,
            model_name=model_.name,
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
        
        request_ = await db.Request.create_row(
            session,
            estimator_name=estimator_.name,
            dataset_name=dataset_.name,
        )

        rows = await db.Request.get_rows(session)
        assert len(rows) == 1
        entry = rows[0]
        
        check = await db.Request.get_row(session, entry.id)
        assert check.id == entry.id
        
        request_2 = await db.Request.create_row(
            session,
            estimator_id=estimator_.id,
            dataset_id=dataset_.id,
        )

        rows = await db.Request.get_rows(session)
        assert len(rows) == 2

        # cleanup
        await cleanup(session)
