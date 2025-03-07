"""http routers for managing Step tables"""

from fastapi import APIRouter, Depends, HTTPException
from safir.dependencies.db_session import db_session_dependency
from sqlalchemy.ext.asyncio import async_scoped_session
from structlog import get_logger

from ... import db, models
from ...common.errors import (
    RAILMissingIDError,
    RAILMissingNameError,
)

logger = get_logger(__name__)

# Specify the tag in the router documentation
TAG_STRING = "Load"


# Build the router
router = APIRouter(
    prefix="/load",
    tags=[TAG_STRING],
)


@router.post(
    "/dataset",
    response_model=models.Dataset,
    summary="Load a dataset into the server",
)
async def load_dataset(
    query: models.LoadDatasetQuery,
    session: async_scoped_session = Depends(db_session_dependency),
) -> db.Dataset:
    the_cache = db.Cache.shared_cache(logger)
    try:
        if query.path is not None:
            new_dataset = await the_cache.load_dataset_from_file(
                session,
                **query.model_dump(),
            )
        else:
            new_dataset = await the_cache.load_dataset_from_values(
                session,
                **query.model_dump(),
            )
        return new_dataset
    except (RAILMissingNameError, RAILMissingIDError) as msg:
        logger.info(msg)
        raise HTTPException(status_code=404, detail=str(msg)) from msg
    except Exception as msg:
        logger.error(msg, exc_info=True)
        raise HTTPException(status_code=500, detail=str(msg)) from msg


@router.post(
    "/model",
    response_model=models.Model,
    summary="Load a model into the server",
)
async def load_model(
    query: models.LoadModelQuery,
    session: async_scoped_session = Depends(db_session_dependency),
) -> db.Model:
    the_cache = db.Cache.shared_cache(logger)
    try:
        new_model = await the_cache.load_model_from_file(
            session,
            **query.model_dump(),
        )
        return new_model
    except (RAILMissingNameError, RAILMissingIDError) as msg:
        logger.info(msg)
        raise HTTPException(status_code=404, detail=str(msg)) from msg
    except Exception as msg:
        logger.error(msg, exc_info=True)
        raise HTTPException(status_code=500, detail=str(msg)) from msg


@router.post(
    "/estimator",
    response_model=models.Estimator,
    summary="Load a estimator into the server",
)
async def load_estimator(
    query: models.LoadEstimatorQuery,
    session: async_scoped_session = Depends(db_session_dependency),
) -> db.Estimator:
    the_cache = db.Cache.shared_cache(logger)
    try:
        new_estimator = await the_cache.load_estimator(
            session,
            **query.model_dump(),
        )
        return new_estimator
    except (RAILMissingNameError, RAILMissingIDError) as msg:
        logger.info(msg)
        raise HTTPException(status_code=404, detail=str(msg)) from msg
    except Exception as msg:
        logger.error(msg, exc_info=True)
        raise HTTPException(status_code=500, detail=str(msg)) from msg
