"""Wrappers to create functions for the various parts of the CLI

These wrappers create functions that invoke interface
functions that are defined in the db.row.RowMixin,
db.node.NodeMixin, and db.element.ElementMixin classes.

These make it easier to define router functions that
apply to all RowMixin, NodeMixin and ElementMixin classes.
"""

import json
from collections.abc import Callable, Sequence
from enum import Enum
from typing import Any, TypeAlias

import click
import yaml
from pydantic import BaseModel
from tabulate import tabulate

from ..client.client import CMClient
from ..common.enums import StatusEnum
from ..db import Job, Script, SpecBlock, Specification
from . import options


class CustomJSONEncoder(json.JSONEncoder):
    """A custom JSON decoder that can serialize Enums."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Enum):
            return {"name": o.name, "value": o.value}
        else:
            return super().default(o)


def output_pydantic_object(
    model: BaseModel,
    output: options.OutputEnum | None,
    col_names: list[str],
) -> None:
    """Render a single object as requested

    Parameters
    ----------
    model: BaseModel
        Object in question

    output: options.OutputEnum | None
        Output format

    col_names: list[str]
        Names for columns in tabular representation
    """
    match output:
        case options.OutputEnum.json:
            click.echo(json.dumps(model.model_dump(), cls=CustomJSONEncoder, indent=4))
        case options.OutputEnum.yaml:
            click.echo(yaml.dump(model.model_dump()))
        case _:
            the_table = [[getattr(model, col_) for col_ in col_names]]
            click.echo(tabulate(the_table, headers=col_names, tablefmt="plain"))


def output_pydantic_list(
    models: Sequence[BaseModel],
    output: options.OutputEnum | None,
    col_names: list[str],
) -> None:
    """Render a sequences of objects as requested

    Parameters
    ----------
    models: Sequence[BaseModel]
        Objects in question

    output: options.OutputEnum | None
        Output format

    col_names: list[str]
        Names for columns in tabular representation
    """
    json_list = []
    yaml_list = []
    the_table = []
    for model_ in models:
        match output:
            case options.OutputEnum.json:
                json_list.append(model_.model_dump())
            case options.OutputEnum.yaml:
                yaml_list.append(model_.model_dump())
            case _:
                the_table.append([str(getattr(model_, col_)) for col_ in col_names])
    match output:
        case options.OutputEnum.json:
            click.echo(json.dumps(json_list, cls=CustomJSONEncoder, indent=4))
        case options.OutputEnum.yaml:
            click.echo(yaml.dump(yaml_list))
        case _:
            click.echo(tabulate(the_table, headers=col_names, tablefmt="plain"))


def output_dict(
    the_dict: dict,
    output: options.OutputEnum | None,
) -> None:
    """Render a python dict as requested

    Parameters
    ----------
    the_dict: dict
        The dict in question

    output: options.OutputEnum | None
        Output format
    """
    match output:
        case options.OutputEnum.json:
            click.echo(json.dumps(the_dict, cls=CustomJSONEncoder, indent=4))
        case options.OutputEnum.yaml:
            click.echo(yaml.dump(the_dict))
        case _:
            for key, val in the_dict.items():
                click.echo(f"{key}: {val}")


def get_list_command(
    group_command: Callable,
    sub_client_name: str,
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

    sub_client_name: str
        Name of python API sub-client to use

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    the_function: Callable
        Function that return all the rows for the table in question
    """

    @group_command(name="list", help="list rows in table")
    @options.cmclient()
    @options.output()
    def get_rows(
        client: CMClient,
        output: options.OutputEnum | None,
    ) -> None:
        """List the existing rows"""
        sub_client = getattr(client, sub_client_name)
        result = sub_client.get_rows()
        output_pydantic_list(result, output, db_class.col_names_for_table)

    return get_rows


def get_row_command(
    group_command: Callable,
    sub_client_name: str,
    db_class: TypeAlias,
) -> Callable:
    """Return a function that gets a row from a table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    sub_client_name: str
        Name of python API sub-client to use

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    the_function: Callable
        Function that returns the row for the table in question
    """

    @group_command(name="all")
    @options.cmclient()
    @options.row_id()
    @options.output()
    def get_row(
        client: CMClient,
        row_id: int,
        output: options.OutputEnum | None,
    ) -> None:
        """Get a single row"""
        sub_client = getattr(client, sub_client_name)
        result = sub_client.get_row(row_id)
        output_pydantic_object(result, output, db_class.col_names_for_table)

    return get_row


def get_row_by_name_command(
    group_command: Callable,
    sub_client_name: str,
    db_class: TypeAlias,
) -> Callable:
    """Return a function that gets a row from a table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    sub_client_name: str
        Name of python API sub-client to use

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    the_function: Callable
        Function that returns the row for the table in question
    """

    @group_command(name="by_name")
    @options.cmclient()
    @options.name()
    @options.output()
    def get_row_by_name(
        client: CMClient,
        name: str,
        output: options.OutputEnum | None,
    ) -> None:
        """Get a single row"""
        sub_client = getattr(client, sub_client_name)
        result = sub_client.get_row_by_name(name)
        output_pydantic_object(result, output, db_class.col_names_for_table)

    return get_row_by_name

def get_delete_command(
    group_command: Callable,
    sub_client_name: str,
) -> Callable:
    """Return a function that delets a row in the table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    sub_client_name: str
        Name of python API sub-client to use

    Returns
    -------
    the_function: Callable
        Function that deletes a row in the table
    """

    @group_command(name="delete")
    @options.cmclient()
    @options.row_id()
    def delete(
        client: CMClient,
        row_id: int,
    ) -> None:
        """Delete a row"""
        sub_client = getattr(client, sub_client_name)
        sub_client.delete(row_id)

    return delete

def get_data_dict_command(
    group_command: Callable,
    sub_client_name: str,
) -> Callable:
    """Return a function that gets the data_dict
    from a row in the table and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    sub_client_name: str
        Name of python API sub-client to use

    Returns
    -------
    the_function: Callable
        Function that returns the data_dict from a row
    """

    @group_command(name="data_dict")
    @options.cmclient()
    @options.row_id()
    @options.output()
    def get_data_dict(
        client: CMClient,
        row_id: int,
        output: options.OutputEnum | None,
    ) -> None:
        """Get the data_dict parameters for a partiuclar node"""
        sub_client = getattr(client, sub_client_name)
        result = sub_client.get_data_dict(row_id)
        output_dict(result, output)

    return get_data_dict
