"""CLI to manage Job table"""

import click

from rail.pz_service import db
from . import admin_options, wrappers


@click.group(name="algorithm")
def algorithm_group() -> None:
    """Manage Algorithm table"""


# Template specialization
# Specify the cli path to attach these commands to
cli_group = algorithm_group
DbClass = db.Algorithm
# Specify the options for the create command
create_options = [
    options.db(),
    admin_options.name(),
    admin_options.class_name(),
    options.output(),
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

delete = wrappers.get_delete_command(group_command)

get_row = wrappers.get_row_command(get_command, DbClass)

get_row_by_name = wrappers.get_row_by_name_command(get_command, DbClass)

get_estimators = wrappers.get_estimators_command(get_command, DbClass)

get_models = wrappers.get_models_command(get_command, DbClass)
