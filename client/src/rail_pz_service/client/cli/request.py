"""CLI to manage Step table"""

import click

from rail_pz_service.common import models

from . import wrappers


@click.group(name="request")
def request_group() -> None:
    """Manage Request table"""


# Template specialization
# Specify the cli path to attach these commands to
cli_group = request_group
# Specify the associated database table
ModelClass = models.Request

# Construct derived templates
group_command = cli_group.command
sub_client = "request"


@cli_group.group()
def get() -> None:
    """Get an attribute"""


get_command = get.command


# Add functions to the cli
get_rows = wrappers.get_list_command(group_command, sub_client, ModelClass)

get_row = wrappers.get_row_command(get_command, sub_client, ModelClass)

get_row_by_name = wrappers.get_row_by_name_command(get_command, sub_client, ModelClass)

get_estimators = wrappers.get_row_attribute_list_command(
    get_command, sub_client, models.Estimator, "_estimators"
)

get_models = wrappers.get_row_attribute_list_command(get_command, sub_client, models.Model, "_models")
