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
from pathlib import Path
from typing import Any, TypeAlias

import click
import yaml
from pydantic import BaseModel
from tabulate import tabulate

from ...common import common_options
from ..client import PZRailClient
from . import client_options


class CustomJSONEncoder(json.JSONEncoder):
    """A custom JSON decoder that can serialize Enums."""

    def default(self, o: Any) -> Any:  # pragma: no cover
        if isinstance(o, Enum):
            return {"name": o.name, "value": o.value}
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

    @group_command(name="by-name")
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

    @group_command(name=query)
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
        the_func = getattr(sub_client, f"get_{query}")
        result = the_func(row_id)
        output_pydantic_list(result, output, model_class.col_names_for_table)

    return get_row_attribute


def get_create_command(
    group_command: Callable,
    sub_client_name: str,
    model_class: TypeAlias,
    create_options: list[Callable],
) -> Callable:
    """Return a function that creates a new row in the table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command
        CLI decorator from the CLI group to attach to

    sub_client_name
        Name of python API sub-client to use

    model_class
        Pydantic model class

    create_options
        Command line options for the create function

    Returns
    -------
    the_function: Callable
        Function that creates a row in the table
    """

    def create(
        pz_client: PZRailClient,
        output: common_options.OutputEnum | None,
        **kwargs: Any,
    ) -> None:
        """Create a new row"""
        sub_client = getattr(pz_client, sub_client_name)
        result = sub_client.create(**kwargs)
        output_pydantic_object(result, output, model_class.col_names_for_table)

    for option_ in create_options:
        create = option_(create)

    create = group_command(name="create")(create)
    return create


def download_command(
    group_command: Callable,
    sub_client_name: str,
) -> Callable:
    """Return a function downloads a file

    Parameters
    ----------
    group_command
        CLI decorator from the CLI group to attach to

    sub_client_name
        Name of python API sub-client to use

    Returns
    -------
    Callable
        Function that downloads a file
    """

    @group_command(name="download")
    @client_options.pz_client()
    @common_options.row_id()
    @common_options.filename()
    def download(
        pz_client: PZRailClient,
        row_id: int,
        filename: Path,
    ) -> None:
        """Get the data_dict parameters for a partiuclar node"""
        sub_client = getattr(pz_client, sub_client_name)
        _result = sub_client.download(row_id, filename)

    return download
