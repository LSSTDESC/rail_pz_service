"""CLI to manage Job table"""

import click

from rail_pz_service import db
from rail_pz_service.common import common_options

from . import admin_options, wrappers


@click.group(name="model")
def model_group() -> None:
    """Manage Model table"""


# Template specialization
# Specify the cli path to attach these commands to
cli_group = model_group
DbClass = db.Model
# Specify the options for the create command
create_options = [
    admin_options.db_engine(),
    common_options.name(),
    common_options.path(),
    common_options.catalog_tag_name(),
    common_options.algo_name(),
    common_options.output(),
]

# Construct derived templates
group_command = cli_group.command


@cli_group.group()
def get() -> None:
    """Get an attribute"""


get_command = get.command


# Add functions to the router
get_rows = wrappers.get_list_command(group_command, DbClass)

create = wrappers.get_create_command(group_command, DbClass, create_options)

delete = wrappers.get_delete_command(group_command, DbClass)

get_row = wrappers.get_row_command(get_command, DbClass)

get_row_by_name = wrappers.get_row_by_name_command(get_command, DbClass)

get_estimators = wrappers.get_row_attribute_list_command(get_command, DbClass, "_estimators", db.Estimator)
