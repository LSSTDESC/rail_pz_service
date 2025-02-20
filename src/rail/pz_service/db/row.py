from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_scoped_session
from structlog import get_logger

from ..errors import (
    CMBadStateTransitionError,
    CMIDMismatchError,
    CMIntegrityError,
    CMMissingFullnameError,
    CMMissingIDError,
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

    @classmethod
    async def get_rows(
        cls: type[T],
        session: async_scoped_session,
        skip: int=0,
        limit: int=100,
        **kwargs: Any,
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
        """
        result = await session.get(cls, row_id)
        if result is None:
            raise CMMissingIDError(f"{cls} {row_id} not found")
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
        """
        query = select(cls).where(cls.name == name)
        rows = await session.scalars(query)
        row = rows.first()
        if row is None:
            raise CMMissingFullnameError(f"{cls} {name} not found")
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
            raise CMMissingIDError(f"{cls} {row_id} not found")
        try:
            await session.delete(row)
        except IntegrityError as msg:
            if TYPE_CHECKING:
                assert msg.orig  # for mypy
            raise CMIntegrityError(params=msg.params, orig=msg.orig, statement=msg.statement) from msg
        await cls._delete_hook(session, row_id)

    @classmethod
    async def _delete_hook(
        cls,
        session: async_scoped_session,
        row_id: int,
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
        CMIDMismatchError
            ID mismatch between row IDs

        CMMissingIDError
            Could not find row

        CMIntegrityError
            catching a IntegrityError
        """
        if kwargs.get("id", row_id) != row_id:
            raise CMIDMismatchError("ID mismatch between URL and body")
        row = await session.get(cls, row_id)
        if row is None:
            raise CMMissingIDError(f"{cls} {row_id} not found")
        async with session.begin_nested():
            try:
                for var, value in kwargs.items():
                    if not value:
                        continue
                    if isinstance(value, dict):
                        the_dict = getattr(row, var).copy()
                        the_dict.update(**value)
                        setattr(row, var, the_dict)
                    else:
                        setattr(row, var, value)
            except IntegrityError as msg:
                await session.rollback()
                if TYPE_CHECKING:
                    assert msg.orig  # for mypy
                raise CMIntegrityError(
                    params=msg.params,
                    orig=msg.orig,
                    statement=msg.statement,
                ) from msg
        await session.refresh(row)
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
        async with session.begin_nested():
            try:
                session.add(row)
            except IntegrityError as msg:
                await session.rollback()
                if TYPE_CHECKING:
                    assert msg.orig  # for mypy
                raise CMIntegrityError(params=msg.params, orig=msg.orig, statement=msg.statement) from msg
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
        try:
            async with session.begin_nested():
                for var, value in kwargs.items():
                    setattr(self, var, value)
            await session.refresh(self)
        except IntegrityError as msg:
            await session.rollback()
            if TYPE_CHECKING:
                assert msg.orig
            raise CMIntegrityError(params=msg.params, orig=msg.orig, statement=msg.statement) from msg
        return self
