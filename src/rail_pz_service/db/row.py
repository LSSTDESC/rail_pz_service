"""Mixin functionality for Database tables"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel, TypeAdapter
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.ext.asyncio import async_scoped_session
from structlog import get_logger

from ..common.errors import (
    RAILIDMismatchError,
    RAILIntegrityError,
    RAILMissingIDError,
    RAILMissingNameError,
    RAILStatementError,
)

logger = get_logger(__name__)

T = TypeVar("T", bound="RowMixin")


class RowMixin:
    """Mixin class to define common features of database rows
    for all the tables we use in rail_server

    Here we a just defining the interface to manipulate
    any sort of table.
    """

    id: Any  # Primary Key, typically an int
    name: Any  # Human-readable name for row
    class_string: str  # Name to use for help functions and descriptions
    pydantic_mode_class: type[BaseModel]  # Pydantic model class

    @classmethod
    async def get_rows(
        cls: type[T],
        session: async_scoped_session,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[T]:
        """Get rows associated to a particular table

        Parameters
        ----------
        session
            DB session manager

        skip
            Number of rows to skip before returning results

        limit
            Number of row to return

        Returns
        -------
        Sequence[T]
            All the matching rows
        """
        q = select(cls)
        q = q.offset(skip).limit(limit)
        results = await session.scalars(q)
        return results.all()

    @classmethod
    async def get_row(
        cls: type[T],
        session: async_scoped_session,
        row_id: int,
    ) -> T:
        """Get a single row, matching row.id == row_id

        Parameters
        ----------
        session
            DB session manager

        row_id
            PrimaryKey of the row to return

        Returns
        -------
        T
            The matching row

        Raises
        ------
        RAILMissingIDError
             Row with ID does not exist
        """
        result = await session.get(cls, row_id)
        if result is None:
            raise RAILMissingIDError(f"{cls} {row_id} not found")
        return result

    @classmethod
    async def get_row_by_name(
        cls: type[T],
        session: async_scoped_session,
        name: str,
    ) -> T:
        """Get a single row, with row.name == name

        Parameters
        ----------
        session
            DB session manager

        name
            name of the row to return

        Returns
        -------
        T
            Matching row

        Raises
        ------
        RAILMissingNameError
             Row with ID does not exist
        """
        query = select(cls).where(cls.name == name)
        rows = await session.scalars(query)
        row = rows.first()
        if row is None:
            raise RAILMissingNameError(f"{cls} {name} not found")
        return row

    @classmethod
    async def delete_row(
        cls,
        session: async_scoped_session,
        row_id: int,
    ) -> None:
        """Delete a single row, matching row.id == row_id

        Parameters
        ----------
        session
            DB session manager

        row_id
            PrimaryKey of the row to delete

        Raises
        ------
        CMMissingIDError
            Row does not exist

        CMIntegrityError
            sqlalchemy.IntegrityError raised
        """
        row = await session.get(cls, row_id)
        if row is None:
            raise RAILMissingIDError(f"{cls} {row_id} not found")
        try:
            await session.delete(row)
        except IntegrityError as msg:
            if TYPE_CHECKING:
                assert msg.orig  # for mypy
            raise RAILIntegrityError(msg) from msg
        await cls._delete_hook(session, row_id)

    @classmethod
    async def _delete_hook(
        cls,
        session: async_scoped_session,  # pylint: disable=unused-argument
        row_id: int,  # pylint: disable=unused-argument
    ) -> None:
        """Hook called during delete_row

        Parameters
        ----------
        session
            DB session manager

        row_id
            PrimaryKey of the row to delete

        """
        return

    @classmethod
    async def update_row(
        cls: type[T],
        session: async_scoped_session,
        row_id: int,
        **kwargs: Any,
    ) -> T:
        """Update a single row, matching row.id == row_id

        Parameters
        ----------
        session
            DB session manager

        row_id
            PrimaryKey of the row to return

        **kwargs
            Columns and associated new values

        Returns
        -------
        T:
            Updated row

        Raises
        ------
        RAILIDMismatchError
            ID mismatch between row IDs

        RAILMissingIDError
            Could not find row

        RAILIntegrityError
            catching a IntegrityError
        """
        if kwargs.get("id", row_id) != row_id:
            raise RAILIDMismatchError("ID mismatch between URL and body")

        row = await session.get(cls, row_id)
        if row is None:
            raise RAILMissingIDError(f"{cls} {row_id} not found")

        try:
            async with session.begin_nested():
                for var, value in kwargs.items():
                    if isinstance(value, dict):  # pragma: no cover
                        the_dict = getattr(row, var).copy()
                        the_dict.update(**value)
                        setattr(row, var, the_dict)
                    else:
                        setattr(row, var, value)
        except StatementError as msg:
            if TYPE_CHECKING:
                assert msg.orig  # for mypy
            raise RAILStatementError(msg) from msg
        return row

    @classmethod
    async def create_row(
        cls: type[T],
        session: async_scoped_session,
        **kwargs: Any,
    ) -> T:
        """Create a single row

        Parameters
        ----------
        session
            DB session manager

        **kwargs: Any
            Columns and associated values for the new row

        Returns
        -------
        T
            Newly created row

        Raises
        ------
        CMIntegrityError
            catching a IntegrityError
        """
        create_kwargs = await cls.get_create_kwargs(session, **kwargs)
        row = cls(**create_kwargs)
        try:
            async with session.begin_nested():
                session.add(row)
        except IntegrityError as msg:
            if TYPE_CHECKING:
                assert msg.orig  # for mypy
            raise RAILIntegrityError(msg) from msg
        await session.refresh(row)
        return row

    @classmethod
    async def get_create_kwargs(
        cls: type[T],
        session: async_scoped_session,
        **kwargs: Any,
    ) -> dict:
        """Get additional keywords needed to create a row

        This should be overridden by sub-classes as needed

        The default is to just return the original keywords

        Parameters
        ----------
        session
            DB session manager

        **kwargs
            Columns and associated values for the new row

        Returns
        -------
        dict
            Keywords needed to create a new row
        """
        assert session
        return kwargs

    async def update_values(
        self: T,
        session: async_scoped_session,
        **kwargs: Any,
    ) -> T:
        """Update values in a row

        Parameters
        ----------
        session
            DB session manager

        **kwargs
            Columns and associated new values

        Returns
        -------
        T
            Updated row

        Raises
        ------
        CMIntegrityError
            Catching a IntegrityError
        """
        return await self.update_row(session, self.id, **kwargs)

    def to_model(self) -> BaseModel:
        """Return a reow as a pydantic model"""
        return_obj = TypeAdapter(self.pydantic_mode_class).validate_python(self)
        return return_obj
