"""CLI to manage Job table"""

import asyncio
from collections.abc import Callable

import click
from safir.database import create_async_session
from sqlalchemy.ext.asyncio import AsyncEngine

from ... import db
from ...common import common_options
from . import admin_options, wrappers


@click.group(name="request")
def request_group() -> None:
    """Manage Request table"""


# Template specialization
# Specify the cli path to attach these commands to
cli_group = request_group
DbClass = db.Request
# Specify the options for the create command
create_options = [
    admin_options.db_engine(),
    common_options.name(),
    common_options.estimator_name(),
    common_options.dataset_name(),
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


@group_command(name="run")
@admin_options.db_engine()
@common_options.row_id()
@common_options.output()
def run(
    db_engine: Callable[[], AsyncEngine],
    row_id: int,
    output: common_options.OutputEnum | None,
) -> None:
    """Run a particular request"""

    async def _the_func() -> None:
        engine = db_engine()
        session = await create_async_session(engine)
        the_cache = db.cache.Cache()
        request = await the_cache.run_request(session, request_id=row_id)
        wrappers.output_db_object(request, output, db.Request.col_names_for_table)
        await session.commit()
        await session.remove()
        await engine.dispose()

    asyncio.run(_the_func())
