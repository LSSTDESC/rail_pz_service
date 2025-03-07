"""CLI to manage Step table"""

import click

from ... import models
from ...common import common_options
from ..client import PZRailClient
from . import client_options, wrappers


@click.group(name="request")
def request_group() -> None:
    """Manage Request table"""


# Template specialization
# Specify the cli path to attach these commands to
cli_group = request_group
# Specify the associated database table
ModelClass = models.Request
create_options = [
    client_options.pz_client(),
    common_options.name(),
    common_options.estimator_name(),
    common_options.dataset_name(),
    common_options.output(),
]

# Construct derived templates
group_command = cli_group.command
sub_client = "request"


@cli_group.group()
def get() -> None:
    """Get an attribute"""


get_command = get.command


# Add functions to the cli
get_rows = wrappers.get_list_command(group_command, sub_client, ModelClass)

create = wrappers.get_create_command(group_command, sub_client, ModelClass, create_options)

delete = wrappers.get_delete_command(group_command, sub_client)

get_row = wrappers.get_row_command(get_command, sub_client, ModelClass)

get_row_by_name = wrappers.get_row_by_name_command(get_command, sub_client, ModelClass)

get_estimators = wrappers.get_row_attribute_list_command(
    get_command, sub_client, models.Estimator, "_estimators"
)

get_models = wrappers.get_row_attribute_list_command(get_command, sub_client, models.Model, "_models")

download_command = wrappers.download_command(group_command, sub_client)


@group_command(name="run")
@client_options.pz_client()
@common_options.row_id()
@common_options.output()
def run(
    pz_client: PZRailClient,
    row_id: int,
    output: common_options.OutputEnum | None,
) -> None:
    """Get the data_dict parameters for a partiuclar node"""
    result = pz_client.request.run(row_id)
    wrappers.output_pydantic_object(result, output, ModelClass.col_names_for_table)
