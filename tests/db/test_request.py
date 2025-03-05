import uuid
from datetime import datetime

import pytest
import structlog
from safir.database import create_async_session
from sqlalchemy.ext.asyncio import AsyncEngine, async_scoped_session

from rail_pz_service import db
from rail_pz_service.common import errors

from .util_functions import (
    cleanup,
)


async def _test_request_db(session: async_scoped_session) -> None:
    """Test `Request` db table."""
    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    if session:
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
            model_name=model_.name,
        )

        dataset_ = await db.Dataset.create_row(
            session,
            name=f"dataset_{uuid_int}",
            n_objects=2,
            path="not/really/a/path",
            data=None,
            catalog_tag_name=catalog_tag_.name,
            validate_file=False,
        )

        await db.Request.create_row(
            session,
            estimator_name=estimator_.name,
            dataset_name=dataset_.name,
        )

        with pytest.raises(errors.RAILMissingRowCreateInputError):
            await db.Request.create_row(
                session,
                dataset_name=dataset_.name,
            )

        with pytest.raises(errors.RAILMissingRowCreateInputError):
            await db.Request.create_row(
                session,
                estimator_name=estimator_.name,
            )

        with pytest.raises(errors.RAILIntegrityError):
            await db.Request.create_row(
                session,
                estimator_name=estimator_.name,
                dataset_name=dataset_.name,
            )

        rows = await db.Request.get_rows(session)
        assert len(rows) == 1
        entry = rows[0]

        check = await db.Request.get_row(session, entry.id)
        assert check.id == entry.id

        estimator2_ = await db.Estimator.create_row(
            session,
            name=f"estimator_{uuid_int}_2",
            model_name=model_.name,
        )

        await db.Request.create_row(
            session,
            estimator_id=estimator2_.id,
            dataset_id=dataset_.id,
        )

        rows = await db.Request.get_rows(session)
        assert len(rows) == 2

        open_requests_ = await db.Request.get_open_requests(session)
        assert len(open_requests_) == 2

        check_update = await db.Request.update_row(session, check.id, time_started=datetime.now())
        assert check_update.time_started is not None

        with pytest.raises(errors.RAILIDMismatchError):
            await db.Request.update_row(session, check.id, id=113413, time_started=datetime.now())

        with pytest.raises(errors.RAILMissingIDError):
            await db.Request.update_row(session, row_id=113413, time_started=datetime.now())

        # FIXME, this is not working
        # with pytest.raises(errors.RAILStatementError):
        #    await db.Request.update_row(session, row_id=check.id, time_started="aaa")

        check_update = await db.Request.update_row(session, check.id, time_finished=datetime.now())
        assert check_update.time_finished is not None

        open_requests_ = await db.Request.get_open_requests(session)
        assert len(open_requests_) == 1

        await check.update_values(session, time_started=None)

        open_requests_ = await db.Request.get_open_requests(session)
        assert len(open_requests_) == 2

        # cleanup
        await cleanup(session)


@pytest.mark.asyncio()
async def test_request_db(engine: AsyncEngine) -> None:
    """Test `Request` db table."""
    logger = structlog.get_logger(__name__)

    async with engine.begin():
        session = await create_async_session(engine, logger)
    try:
        await _test_request_db(session)
    except Exception as e:
        await session.rollback()
        await cleanup(session)
        raise e
