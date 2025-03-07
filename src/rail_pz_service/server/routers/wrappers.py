"""Wrappers to create functions for the various routers

These wrappers create functions that invoke interface
functions that are defined in the db.row.RowMixin,
db.node.NodeMixin, and db.element.ElementMixin classes.

These make it easier to define router functions that
apply to all RowMixin, NodeMixin and ElementMixin classes.
"""

from collections.abc import Callable, Sequence
from typing import TypeAlias

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from safir.dependencies.db_session import db_session_dependency
from sqlalchemy.ext.asyncio import async_scoped_session
from structlog import get_logger

from ... import db
from ...common.errors import (
    RAILMissingIDError,
    RAILMissingNameError,
)

logger = get_logger(__name__)


def get_list_function(
    router: APIRouter,
    response_model_class: TypeAlias = BaseModel,
    db_class: TypeAlias = db.RowMixin,
) -> Callable:
    """Return a function that gets all the rows from a table
    and attaches that function to a router.

    This version will provide a function that always returns
    all the rows

    Parameters
    ----------
    router
        Router to attach the function to

    response_model_class
        Pydantic class used to serialize the return value

    db_class
        Underlying database class

    Returns
    -------
    Callable
        Function that return all the rows for the table in question
    """

    @router.get(
        "/list",
        response_model=list[response_model_class],
        summary=f"List all the {db_class.class_string}",
    )
    async def get_rows(
        skip: int = 0,
        limit: int = 100,
        session: async_scoped_session = Depends(db_session_dependency),
    ) -> Sequence[response_model_class]:
        """Return all the rows

        Parameters
        ----------
        skip
            Number of rows to skip at the start

        limit
            Number of rows to list

        session
            Database session

        Returns
        -------
        The rows in question
        """
        try:
            async with session.begin():
                return await db_class.get_rows(session, skip=skip, limit=limit)
        except Exception as msg:
            logger.error(msg, exc_info=True)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=500, detail=str(msg)) from msg

    return get_rows


def get_row_function(
    router: APIRouter,
    response_model_class: TypeAlias = BaseModel,
    db_class: TypeAlias = db.RowMixin,
) -> Callable:
    """Return a function that gets a single row from a table (by ID)
    and attaches that function to a router.

    Parameters
    ----------
    router: APIRouter
        Router to attach the function to

    response_model_class: TypeAlias = BaseModel,
        Pydantic class used to serialize the return value

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    the_function: Callable
        Function that returns a single row from a table by ID
    """

    @router.get(
        "/get/{row_id}",
        response_model=response_model_class,
        summary=f"Retrieve a {db_class.class_string} by name",
    )
    async def get_row(
        row_id: int,
        session: async_scoped_session = Depends(db_session_dependency),
    ) -> response_model_class:
        try:
            async with session.begin():
                return await db_class.get_row(session, row_id)
        except RAILMissingIDError as msg:
            logger.info(msg)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=404, detail=str(msg)) from msg
        except Exception as msg:
            logger.error(msg, exc_info=True)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=500, detail=str(msg)) from msg

    return get_row


def get_row_by_name_function(
    router: APIRouter,
    response_model_class: TypeAlias = BaseModel,
    db_class: TypeAlias = db.RowMixin,
) -> Callable:
    """Return a function that gets a single row from a table (by name)
    and attaches that function to a router.

    Parameters
    ----------
    router: APIRouter
        Router to attach the function to

    response_model_class: TypeAlias = BaseModel,
        Pydantic class used to serialize the return value

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    the_function: Callable
        Function that returns a single row from a table by name
    """

    @router.get(
        "/get_row_by_name",
        response_model=response_model_class,
        summary=f"Retrieve a {db_class.class_string} by name",
    )
    async def get_row_by_name(
        name: str,
        session: async_scoped_session = Depends(db_session_dependency),
    ) -> response_model_class:
        try:
            async with session.begin():
                return await db_class.get_row_by_name(session, name)
        except RAILMissingNameError as msg:
            logger.info(msg)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=404, detail=str(msg)) from msg
        except Exception as msg:
            logger.error(msg, exc_info=True)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=500, detail=str(msg)) from msg

    return get_row_by_name


def delete_row_function(
    router: APIRouter,
    db_class: TypeAlias = db.RowMixin,
) -> Callable:
    """Return a function that deletes a single row in a table
    and attaches that function to a router.

    Parameters
    ----------
    router: APIRouter
        Router to attach the function to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    the_function: Callable
        Function that delete a single row from a table by ID
    """

    @router.delete(
        "/{row_id}",
        status_code=204,
        summary=f"Delete a {db_class.class_string}",
    )
    async def delete_row(
        row_id: int,
        session: async_scoped_session = Depends(db_session_dependency),
    ) -> None:
        try:
            async with session.begin():
                await db_class.delete_row(session, row_id)
                await session.commit()
                return
        except RAILMissingIDError as msg:
            logger.info(msg)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=404, detail=str(msg)) from msg
        except Exception as msg:
            logger.error(msg, exc_info=True)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=500, detail=str(msg)) from msg

    return delete_row


def get_row_attribute_list_function(
    router: APIRouter,
    response_model_class: TypeAlias = BaseModel,
    db_class: TypeAlias = db.RowMixin,
    attr_name: str = "",
    list_response_model_class: TypeAlias = BaseModel,
) -> Callable:
    """Return a function gets collection names associated to a Node.

    Parameters
    ----------
    router: APIRouter
        Router to attach the function to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    attr_name
        Requested attribute

    list_response_model_class: TypeAlias = BaseModel,
        Pydantic class used to serialize the return value

    Returns
    -------
    Callable
        Function that gets the collection names associated to a Node
    """
    route_str = "/get/{row_id}/" + attr_name[:-1]

    @router.get(
        route_str,
        response_model=list[list_response_model_class],
        summary=f"Get an attribute associated to a {db_class.class_string}",
    )
    async def get_row_attribute_list(
        row_id: int,
        session: async_scoped_session = Depends(db_session_dependency),
    ) -> list[list_response_model_class]:
        try:
            async with session.begin():
                the_node = await db_class.get_row(session, row_id)
                await session.refresh(the_node, attribute_names=[attr_name])
                the_list = getattr(the_node, attr_name)
            return the_list
        except RAILMissingIDError as msg:
            logger.info(msg)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=404, detail=str(msg)) from msg
        except Exception as msg:
            logger.error(msg, exc_info=True)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=500, detail=str(msg)) from msg

    assert response_model_class
    return get_row_attribute_list


def create_row_function(
    router: APIRouter,
    response_model_class: TypeAlias = BaseModel,
    create_model_class: TypeAlias = BaseModel,
    db_class: TypeAlias = db.RowMixin,
) -> Callable:
    """Return a function that creates a single row in a table
    and attaches that function to a router.

    Parameters
    ----------
    router
        Router to attach the function to

    response_model_class
        Pydantic class used to serialize the return value

    create_model_class
        Pydantic class used to serialize the inputs value

    db_class
        Underlying database class

    Returns
    -------
    Callable
        Function that creates a single row in a table
    """

    @router.post(
        "/create",
        status_code=201,
        response_model=response_model_class,
        summary=f"Create a {db_class.class_string}",
    )
    async def create_row(
        row_create: create_model_class,
        session: async_scoped_session = Depends(db_session_dependency),
    ) -> db_class:
        try:
            async with session.begin_nested():
                the_row = await db_class.create_row(session, **row_create.model_dump())
                await session.commit()
                return the_row
        except Exception as msg:
            logger.error(msg, exc_info=True)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=500, detail=str(msg)) from msg

    return create_row


def download_file_function(
    router: APIRouter,
    db_class: TypeAlias = db.RowMixin,
    attr_name: str = "",
) -> Callable:
    """Return a function gets collection names associated to a Node.

    Parameters
    ----------
    router: APIRouter
        Router to attach the function to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    attr_name
        Requested attribute

    Returns
    -------
    Callable
        Function that gets the collection names associated to a Node
    """

    @router.get(
        "/download/{row_id}",
        summary="Downlaod a file",
    )
    async def download_file(
        row_id: int,
        filename: str,
        session: async_scoped_session = Depends(db_session_dependency),
    ) -> FileResponse:
        try:
            async with session.begin():
                the_node = await db_class.get_row(session, row_id)
                await session.refresh(the_node, attribute_names=[attr_name])
                the_path = getattr(the_node, attr_name)
            return FileResponse(path=the_path, filename=filename)
        except RAILMissingIDError as msg:
            logger.info(msg)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=404, detail=str(msg)) from msg
        except Exception as msg:
            logger.error(msg, exc_info=True)
            await session.close()
            await session.remove()
            raise HTTPException(status_code=500, detail=str(msg)) from msg

    return download_file
