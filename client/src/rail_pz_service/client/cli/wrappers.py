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

from rail_pz_service.client.client import PZRailClient
from rail_pz_service.common import common_options

from . import client_options


class CustomJSONEncoder(json.JSONEncoder):
    """A custom JSON decoder that can serialize Enums."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Enum):
            return {"name": o.name, "value": o.value}
        else:
            return super().default(o)


def output_pydantic_object(
    model: BaseModel,
    output: common_options.OutputEnum | None,
    col_names: list[str],
) -> None:
    """Render a single object as requested

    Parameters
    ----------
    model
        Object in question

    output
        Output format

    col_names: list[str]
        Names for columns in tabular representation
    """
    match output:
        case common_options.OutputEnum.json:
            click.echo(json.dumps(model.model_dump(), cls=CustomJSONEncoder, indent=4))
        case common_options.OutputEnum.yaml:
            click.echo(yaml.dump(model.model_dump()))
        case _:
            the_table = [[getattr(model, col_) for col_ in col_names]]
            click.echo(tabulate(the_table, headers=col_names, tablefmt="plain"))


def output_pydantic_list(
    models: Sequence[BaseModel],
    output: common_options.OutputEnum | None,
    col_names: list[str],
) -> None:
    """Render a sequences of objects as requested

    Parameters
    ----------
    models: Sequence[BaseModel]
        Objects in question

    output:
        Output format

    col_names: list[str]
        Names for columns in tabular representation
    """
    json_list = []
    yaml_list = []
    the_table = []
    for model_ in models:
        match output:
            case common_options.OutputEnum.json:
                json_list.append(model_.model_dump())
            case common_options.OutputEnum.yaml:
                yaml_list.append(model_.model_dump())
            case _:
                the_table.append([str(getattr(model_, col_)) for col_ in col_names])
    match output:
        case common_options.OutputEnum.json:
            click.echo(json.dumps(json_list, cls=CustomJSONEncoder, indent=4))
        case common_options.OutputEnum.yaml:
            click.echo(yaml.dump(yaml_list))
        case _:
            click.echo(tabulate(the_table, headers=col_names, tablefmt="plain"))


def output_dict(
    the_dict: dict,
    output: common_options.OutputEnum | None,
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
        case common_options.OutputEnum.json:
            click.echo(json.dumps(the_dict, cls=CustomJSONEncoder, indent=4))
        case common_options.OutputEnum.yaml:
            click.echo(yaml.dump(the_dict))
        case _:
            for key, val in the_dict.items():
                click.echo(f"{key}: {val}")


def get_list_command(
    group_command: Callable,
    sub_client_name: str,
    model_class: TypeAlias,
) -> Callable:
    """Return a function that gets all the rows from a table
    and attaches that function to the cli.

    This version will provide a function that always returns
    all the rows

    Parameters
    ----------
    group_command
        CLI decorator from the CLI group to attach to

    sub_client_name
        Name of python API sub-client to use

    model_class
        Underlying database class

    Returns
    -------
    the_function: Callable
        Function that return all the rows for the table in question
    """

    @group_command(name="list", help="list rows in table")
    @client_options.pz_client()
    @common_options.output()
    def get_rows(
        pz_client: PZRailClient,
        output: common_options.OutputEnum | None,
    ) -> None:
        """List the existing rows"""
        sub_client = getattr(pz_client, sub_client_name)
        result = sub_client.get_rows()
        output_pydantic_list(result, output, model_class.col_names_for_table)

    return get_rows


def get_row_command(
    group_command: Callable,
    sub_client_name: str,
    model_class: TypeAlias,
) -> Callable:
    """Return a function that gets a row from a table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command
        CLI decorator from the CLI group to attach to

    sub_client_name
        Name of python API sub-client to use

    model_class
        Underlying database class

    Returns
    -------
    Callable
        Function that returns the row for the table in question
    """

    @group_command(name="all")
    @client_options.pz_client()
    @common_options.row_id()
    @common_options.output()
    def get_row(
        pz_client: PZRailClient,
        row_id: int,
        output: common_options.OutputEnum | None,
    ) -> None:
        """Get a single row"""
        sub_client = getattr(pz_client, sub_client_name)
        result = sub_client.get_row(row_id)
        output_pydantic_object(result, output, model_class.col_names_for_table)

    return get_row


def get_row_by_name_command(
    group_command: Callable,
    sub_client_name: str,
    model_class: TypeAlias,
) -> Callable:
    """Return a function that gets a row from a table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command
        CLI decorator from the CLI group to attach to

    sub_client_name
        Name of python API sub-client to use

    model_class
        Underlying database class

    Returns
    -------
    Callable
        Function that returns the row for the table in question
    """

    @group_command(name="by_name")
    @client_options.pz_client()
    @common_options.name()
    @common_options.output()
    def get_row_by_name(
        pz_client: PZRailClient,
        name: str,
        output: common_options.OutputEnum | None,
    ) -> None:
        """Get a single row"""
        sub_client = getattr(pz_client, sub_client_name)
        result = sub_client.get_row_by_name(name)
        output_pydantic_object(result, output, model_class.col_names_for_table)

    return get_row_by_name


def get_delete_command(
    group_command: Callable,
    sub_client_name: str,
) -> Callable:
    """Return a function that delets a row in the table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command
        CLI decorator from the CLI group to attach to

    sub_client_name
        Name of python API sub-client to use

    Returns
    -------
    Callable
        Function that deletes a row in the table
    """

    @group_command(name="delete")
    @client_options.pz_client()
    @common_options.row_id()
    def delete(
        pz_client: PZRailClient,
        row_id: int,
    ) -> None:
        """Delete a row"""
        sub_client = getattr(pz_client, sub_client_name)
        sub_client.delete(row_id)

    return delete


def get_row_attribute_list_command(
    group_command: Callable,
    sub_client_name: str,
    model_class: TypeAlias,
    query: str,
) -> Callable:
    """Return a function that gets the data_dict
    from a row in the table and attaches that function to the cli.

    Parameters
    ----------
    group_command
        CLI decorator from the CLI group to attach to

    sub_client_name
        Name of python API sub-client to use

    Returns
    -------
    Callable
        Function that returns the data_dict from a row
    """

    @group_command(name=f"get-{query}")
    @client_options.pz_client()
    @common_options.row_id()
    @common_options.output()
    def get_row_attribute(
        pz_client: PZRailClient,
        row_id: int,
        output: common_options.OutputEnum | None,
    ) -> None:
        """Get the data_dict parameters for a partiuclar node"""
        sub_client = getattr(pz_client, sub_client_name)
        result = sub_client.get_row_attribute_list_function(row_id, query)
        output_pydantic_list(result, output, model_class.col_names_for_table)

    return get_row_attribute
