"""Wrappers to create functions for the various parts of the CLI

These wrappers create functions that invoke interface
functions that are defined in the db.row.RowMixin.

"""

# import json
import asyncio
import json
from collections.abc import Callable, Sequence
from typing import Any, TypeAlias

import click
import yaml
from safir.database import create_async_session
from sqlalchemy.ext.asyncio import AsyncEngine
from tabulate import tabulate

from ... import db
from ...common import common_options
from . import admin_options


def output_db_object(
    db_obj: db.RowMixin,
    output: common_options.OutputEnum | None,
    col_names: list[str],
) -> None:
    """Render a single object as requested

    Parameters
    ----------
    db_obj:
        Object in question

    output:
        Output format

    col_names:
        Names for columns in tabular representation
    """
    match output:
        case common_options.OutputEnum.json:
            model = db_obj.to_model()
            click.echo(json.dumps(model.model_dump(), indent=4))
        case common_options.OutputEnum.yaml:
            model = db_obj.to_model()
            click.echo(yaml.dump(model.model_dump()))
        case _:
            the_table = [[getattr(db_obj, col_) for col_ in col_names]]
            click.echo(tabulate(the_table, headers=col_names, tablefmt="plain"))


def output_db_obj_list(
    db_objs: Sequence[db.RowMixin],
    output: common_options.OutputEnum | None,
    col_names: list[str],
) -> None:
    """Render a sequences of objects as requested

    Parameters
    ----------
    db_objs:
        Objects in question

    output:
        Output format

    col_names:
        Names for columns in tabular representation
    """
    json_list: list = []
    yaml_list: list = []
    the_table = []
    for db_obj_ in db_objs:
        match output:
            case common_options.OutputEnum.json:
                model_ = db_obj_.to_model()
                json_list.append(model_.model_dump())
            case common_options.OutputEnum.yaml:
                model_ = db_obj_.to_model()
                yaml_list.append(model_.model_dump())
            case _:
                the_table.append([str(getattr(db_obj_, col_)) for col_ in col_names])
    match output:
        case common_options.OutputEnum.json:
            click.echo(json.dumps(json_list, indent=4))
        case common_options.OutputEnum.yaml:
            click.echo(yaml.dump(yaml_list))
        case _:
            click.echo(tabulate(the_table, headers=col_names, tablefmt="plain"))


def get_list_command(
    group_command: Callable,
    db_class: TypeAlias,
) -> Callable:
    """Return a function that gets all the rows from a table
    and attaches that function to the cli.

    This version will provide a function that always returns
    all the rows

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    Callable
        Function that return all the rows for the table in question
    """

    @group_command(name="list", help="list rows in table")
    @admin_options.db_engine()
    @common_options.output()
    def get_rows(
        db_engine: Callable[[], AsyncEngine],
        output: common_options.OutputEnum | None,
    ) -> None:
        """List the existing rows"""

        async def _the_func() -> None:
            engine = db_engine()
            session = await create_async_session(engine)
            result = await db_class.get_rows(session)
            output_db_obj_list(result, output, db_class.col_names_for_table)
            await session.remove()
            await engine.dispose()

        asyncio.run(_the_func())

    return get_rows


def get_row_command(
    group_command: Callable,
    db_class: TypeAlias,
) -> Callable:
    """Return a function that gets a row from a table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    Callable
        Function that returns the row for the table in question
    """

    @group_command(name="all")
    @admin_options.db_engine()
    @common_options.row_id()
    @common_options.output()
    def get_row(
        db_engine: Callable[[], AsyncEngine],
        row_id: int,
        output: common_options.OutputEnum | None,
    ) -> None:
        """Get a single row"""

        async def _the_func() -> None:
            engine = db_engine()
            session = await create_async_session(engine)
            result = await db_class.get_row(session, row_id)
            output_db_object(result, output, db_class.col_names_for_table)
            await session.remove()
            await engine.dispose()

        asyncio.run(_the_func())

    return get_row


def get_row_by_name_command(
    group_command: Callable,
    db_class: TypeAlias,
) -> Callable:
    """Return a function that gets a row from a table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    the_function: Callable
        Function that returns the row for the table in question
    """

    @group_command(name="by-name")
    @admin_options.db_engine()
    @common_options.name()
    @common_options.output()
    def get_row_by_name(
        db_engine: Callable[[], AsyncEngine],
        name: str,
        output: common_options.OutputEnum | None,
    ) -> None:
        """Get a single row"""

        async def _the_func() -> None:
            engine = db_engine()
            session = await create_async_session(engine)
            result = await db_class.get_row_by_name(session, name)
            output_db_object(result, output, db_class.col_names_for_table)
            await session.remove()
            await engine.dispose()

        asyncio.run(_the_func())

    return get_row_by_name


def get_row_attribute_list_command(
    group_command: Callable,
    db_class: TypeAlias,
    attribute: str,
    output_db_class: TypeAlias,
) -> Callable:
    """Return a function that gets a row from a table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command:
        CLI decorator from the CLI group to attach to

    db_class:
        Underlying database class

    attribute:
        The attribute to get

    output_db_class
        Db class for the output type

    Returns
    -------
    Callable
        Function that returns the row for the table in question
    """

    @group_command(name=f"{attribute[:-1]}")
    @admin_options.db_engine()
    @common_options.row_id()
    @common_options.output()
    def get_row_attribute_list(
        db_engine: Callable[[], AsyncEngine],
        row_id: int,
        output: common_options.OutputEnum | None,
    ) -> None:
        """Get a single row"""

        async def _the_func() -> None:
            engine = db_engine()
            session = await create_async_session(engine)
            result = await db_class.get_row(session, row_id)
            await session.refresh(result, attribute_names=[attribute])
            the_list = list(getattr(result, attribute))
            output_db_obj_list(the_list, output, output_db_class.col_names_for_table)
            await session.remove()
            await engine.dispose()

        asyncio.run(_the_func())

    return get_row_attribute_list


def get_create_command(
    group_command: Callable,
    db_class: TypeAlias,
    create_options: list[Callable],
) -> Callable:
    """Return a function that creates a new row in the table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    create_options: list[Callable]
        Command line options for the create function

    Returns
    -------
    Callable
        Function that creates a row in the table
    """

    def create(
        db_engine: Callable[[], AsyncEngine],
        output: common_options.OutputEnum | None,
        **kwargs: Any,
    ) -> None:
        """Create a new row"""

        async def _the_func() -> None:
            engine = db_engine()
            session = await create_async_session(engine)
            result = await db_class.create_row(session, **kwargs)
            output_db_object(result, output, db_class.col_names_for_table)
            await session.remove()
            await engine.dispose()

        asyncio.run(_the_func())

    for option_ in create_options:
        create = option_(create)

    create = group_command(name="create")(create)
    return create


def get_delete_command(
    group_command: Callable,
    db_class: TypeAlias,
) -> Callable:
    """Return a function that delets a row in the table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    Callable
        Function that deletes a row in the table
    """

    @group_command(name="delete")
    @admin_options.db_engine()
    @common_options.row_id()
    def delete(
        db_engine: Callable[[], AsyncEngine],
        row_id: int,
    ) -> None:
        """Delete a row"""

        async def _the_func() -> None:
            engine = db_engine()
            session = await create_async_session(engine)
            await db_class.delete_row(session, row_id)
            await session.commit()
            await session.remove()
            await engine.dispose()

        asyncio.run(_the_func())

    return delete
