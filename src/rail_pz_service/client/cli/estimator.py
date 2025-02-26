"""CLI to manage Step table"""

import click

from ... import models
from . import wrappers


@click.group(name="estimator")
def estimator_group() -> None:
    """Manage Estimator table"""


# Template specialization
# Specify the cli path to attach these commands to
cli_group = estimator_group
# Specify the associated database table
ModelClass = models.Estimator

# Construct derived templates
group_command = cli_group.command
sub_client = "estimator"


@cli_group.group()
def get() -> None:
    """Get an attribute"""


get_command = get.command


# Add functions to the cli
get_rows = wrappers.get_list_command(group_command, sub_client, ModelClass)

get_row = wrappers.get_row_command(get_command, sub_client, ModelClass)

get_row_by_name = wrappers.get_row_by_name_command(get_command, sub_client, ModelClass)

get_requests = wrappers.get_row_attribute_list_command(get_command, sub_client, models.Request, "requests")
