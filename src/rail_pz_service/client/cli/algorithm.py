"""CLI to manage Step table"""

import click

from ... import models
from . import wrappers


@click.group(name="algorithm")
def algorithm_group() -> None:
    """Manage Algorithm table"""


# Template specialization
# Specify the cli path to attach these commands to
cli_group = algorithm_group
# Specify the associated database table
ModelClass = models.Algorithm

# Construct derived templates
group_command = cli_group.command
sub_client = "algorithm"


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
