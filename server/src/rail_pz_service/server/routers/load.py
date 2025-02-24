"""http routers for managing Step tables"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from safir.dependencies.db_session import db_session_dependency
from sqlalchemy.ext.asyncio import async_scoped_session
from structlog import get_logger

from rail_pz_service.common.errors import (
    RAILMissingNameError,
    RAILMissingIDError,
)
from rail_pz_service.common import models
from rail_pz_service import db


logger = get_logger(__name__)

# Specify the tag in the router documentation
TAG_STRING = "Load"


# Build the router
router = APIRouter(
    prefix="/load",
    tags=[TAG_STRING],
)


@router.post(
    "/load_dataset",
    response_model=models.Dataset,
    summary=f"Load a dataset into the server",
)
async def load_dataset(
    query: models.LoadDatasetQuery,
    session: async_scoped_session = Depends(db_session_dependency),
) -> models.Dataset:

    the_cache = db.Cache.shared_cache()
    try:
        new_dataset = await the_cache.load_dataset_from_file(
            session, **query.model_dump(),
        )
    except (RAILMissingNameError, RAILMissingIDError) as msg:
        logger.info(msg)
        raise HTTPException(status_code=404, detail=str(msg)) from msg        
    except Exception as msg:
        logger.error(msg, exc_info=True)
        raise HTTPException(status_code=500, detail=str(msg)) from msg
    return new_dataset


@router.post(
    "/load_model",
    response_model=models.Model,
    summary=f"Load a model into the server",
)
async def load_model(
    query: models.LoadModelQuery,
    session: async_scoped_session = Depends(db_session_dependency),
) -> models.Model:

    the_cache = db.Cache.shared_cache()
    try:
        new_model = await the_cache.load_model_from_file(
            session, **query.model_dump(),
        )
    except (RAILMissingNameError, RAILMissingIDError) as msg:
        logger.info(msg)
        raise HTTPException(status_code=404, detail=str(msg)) from msg        
    except Exception as msg:
        logger.error(msg, exc_info=True)
        raise HTTPException(status_code=500, detail=str(msg)) from msg
    return new_model


@router.post(
    "/load_estimator",
    response_model=models.Estimator,
    summary=f"Load a estimator into the server",
)
async def load_estimator(
    query: models.LoadEstimatorQuery,
    session: async_scoped_session = Depends(db_session_dependency),
) -> models.Estimator:

    the_cache = db.Cache.shared_cache()
    try:
        new_estimator = await the_cache.load_estimator(
            session, **query.model_dump(),
        )
    except (RAILMissingNameError, RAILMissingIDError) as msg:
        logger.info(msg)
        raise HTTPException(status_code=404, detail=str(msg)) from msg        
    except Exception as msg:
        logger.error(msg, exc_info=True)
        raise HTTPException(status_code=500, detail=str(msg)) from msg
    return new_estimator
