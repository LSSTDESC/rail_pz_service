"""CLI to manage Job table"""

import click

from rail.pz_service import db

from . import admin_options, wrappers


@click.group(name="catalog-tag")
def request_group() -> None:
    """Manage Request table"""


# Template specialization
# Specify the cli path to attach these commands to
cli_group = request_group
DbClass = db.Request
# Specify the options for the create command
create_options = [
    options.db(),
    admin_options.name(),
    admin_options.estimator_name(),
    admin_options.dataset_name(),
    admin_options.output(),
]

# Construct derived templates
group_command = cli_group.command
sub_client = DbClass.class_string


@cli_group.group()
def get() -> None:
    """Get an attribute"""


get_command = get.command


# Add functions to the router
get_rows = wrappers.get_list_command(group_command, sub_client, DbClass)

create = wrappers.get_create_command(group_command, sub_client, DbClass, create_options)

delete = wrappers.get_delete_command(group_command, sub_client)

get_row = wrappers.get_row_command(get_command, sub_client, DbClass)

get_row_by_name = wrappers.get_row_by_name_command(get_command, sub_client, DbClass)


@group_command(name="run")
@options.db()
@options.row_id()
@options.output()
def run(
    row_id: int,
    output: options.OutputEnum | None,
) -> None:

    the_cache = db.Cache()
    qp_file = the_cache.get_qp_file(session, row_id)

    
    
    
