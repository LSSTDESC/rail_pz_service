"""Wrappers to create functions for the various parts of the CLI

These wrappers create functions that invoke interface
functions that are defined in the db.row.RowMixin.

"""

# import json
from collections.abc import Callable, Sequence
from typing import Any, TypeAlias

import click
import yaml
from sqlalchemy.ext.asyncio import async_scoped_session
from tabulate import tabulate

from rail.pz_service import db

from . import admin_options


def output_db_object(
    db_obj: db.RowMixin,
    output: admin_options.OutputEnum | None,
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
        case admin_options.OutputEnum.json:
            pass
        case admin_options.OutputEnum.yaml:
            pass
        case _:
            the_table = [[getattr(db_obj, col_) for col_ in col_names]]
            click.echo(tabulate(the_table, headers=col_names, tablefmt="plain"))


def output_db_obj_list(
    db_objs: Sequence[db.RowMixin],
    output: admin_options.OutputEnum | None,
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
    _json_list: list = []
    _yaml_list: list = []
    the_table = []
    for db_obj_ in db_objs:
        match output:
            case admin_options.OutputEnum.json:
                pass
            case admin_options.OutputEnum.yaml:
                pass
            case _:
                the_table.append([str(getattr(db_obj_, col_)) for col_ in col_names])
    match output:
        case admin_options.OutputEnum.json:
            pass
        case admin_options.OutputEnum.yaml:
            pass
        case _:
            click.echo(tabulate(the_table, headers=col_names, tablefmt="plain"))


def output_dict(
    the_dict: dict,
    output: admin_options.OutputEnum | None,
) -> None:
    """Render a python dict as requested

    Parameters
    ----------
    the_dict:
        The dict in question

    output:
        Output format
    """
    match output:
        case admin_options.OutputEnum.json:
            pass
        case admin_options.OutputEnum.yaml:
            click.echo(yaml.dump(the_dict))
        case _:
            for key, val in the_dict.items():
                click.echo(f"{key}: {val}")


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
    @admin_options.db_session()
    @admin_options.output()
    async def get_rows(
        db_session: async_scoped_session,
        output: admin_options.OutputEnum | None,
    ) -> None:
        """List the existing rows"""
        result = db_class.get_rows(db.session())
        output_db_obj_list(result, output, db_class.col_names_for_table)
        await db_session.close()

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
    @admin_options.db_session()
    @admin_options.row_id()
    @admin_options.output()
    async def get_row(
        db_session: async_scoped_session,
        row_id: int,
        output: admin_options.OutputEnum | None,
    ) -> None:
        """Get a single row"""
        result = db_class.get_row(db.session(), row_id)
        output_db_object(result, output, db_class.col_names_for_table)
        await db_session.close()

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

    @group_command(name="by_name")
    @admin_options.db_session()
    @admin_options.name()
    @admin_options.output()
    async def get_row_by_name(
        db_session: async_scoped_session,
        name: str,
        output: admin_options.OutputEnum | None,
    ) -> None:
        """Get a single row"""
        result = db_class.get_row_by_name(db.session(), name)
        output_db_object(result, output, db_class.col_names_for_table)
        await db_session.close()

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

    Returns
    -------
    Callable
        Function that returns the row for the table in question
    """

    @group_command(name="by_name")
    @admin_options.db_session()
    @admin_options.row_id()
    @admin_options.output()
    async def get_row_attribute_list(
        db_session: async_scoped_session,
        row_id: int,
        output: admin_options.OutputEnum | None,
    ) -> None:
        """Get a single row"""
        result = db_class.get_row(db_session, row_id)
        await db_session.refresh(result, attribute_names=[attribute])
        the_list = getattr(result, attribute)
        output_db_obj_list(result, the_list, output_db_class.col_names_for_table)
        await db_session.close()

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

    async def create(
        db_session: async_scoped_session,
        output: admin_options.OutputEnum | None,
        **kwargs: Any,
    ) -> None:
        """Create a new row"""
        result = db_class.create_row(db.session(), **kwargs)
        output_db_object(result, output, db_class.col_names_for_table)
        await db_session.close()

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
    @admin_options.db_session()
    @admin_options.row_id()
    async def delete(
        db_session: async_scoped_session,
        row_id: int,
    ) -> None:
        """Delete a row"""
        db_class.delete_row(db_session, row_id)
        await db_session.close()

    return delete
