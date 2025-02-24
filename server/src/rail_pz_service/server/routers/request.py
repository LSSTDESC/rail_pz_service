"""http routers for managing Step tables"""

from fastapi import APIRouter, Depends, HTTPException
from safir.dependencies.db_session import db_session_dependency
from sqlalchemy.ext.asyncio import async_scoped_session
from structlog import get_logger

from rail_pz_service import db
from rail_pz_service.common import models
from rail_pz_service.common.errors import (
    RAILMissingIDError,
    RAILMissingNameError,
)

from . import wrappers

logger = get_logger(__name__)


# Template specialization
# Specify the pydantic model for the table
ResponseModelClass = models.Request
# Specify the associated database table
DbClass = db.Request
# Specify the tag in the router documentation
TAG_STRING = "Request"


# Build the router
router = APIRouter(
    prefix=f"/{DbClass.class_string}",
    tags=[TAG_STRING],
)


# Attach functions to the router
get_rows = wrappers.get_list_function(router, ResponseModelClass, DbClass)
get_row = wrappers.get_row_function(router, ResponseModelClass, DbClass)
get_row_by_name = wrappers.get_row_by_name_function(router, ResponseModelClass, DbClass)


@router.post(
    "/run/{row_id}",
    response_model=models.Request,
    summary="Force running of a particular request",
)
async def run_request(
    row_id: int,
    session: async_scoped_session = Depends(db_session_dependency),
) -> models.Dataset:
    the_cache = db.Cache.shared_cache()
    try:
        request = await the_cache.run_process_request(
            session,
            request_id=row_id,
        )
    except (RAILMissingNameError, RAILMissingIDError) as msg:
        logger.info(msg)
        raise HTTPException(status_code=404, detail=str(msg)) from msg
    except Exception as msg:
        logger.error(msg, exc_info=True)
        raise HTTPException(status_code=500, detail=str(msg)) from msg
    return request
