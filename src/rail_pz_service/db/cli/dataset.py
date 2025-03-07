"""CLI to manage Job table"""

import asyncio
import uuid
from collections.abc import Callable

import click
from safir.database import create_async_session
from sqlalchemy.ext.asyncio import AsyncEngine

from ... import db
from ...common import common_options
from . import admin_options, wrappers


@click.group(name="dataset")
def dataset_group() -> None:
    """Manage Dataset table"""


# Template specialization
# Specify the cli path to attach these commands to
cli_group = dataset_group
DbClass = db.Dataset
# Specify the options for the create command
create_options = [
    admin_options.db_engine(),
    common_options.name(),
    common_options.path(),
    common_options.data(),
    common_options.catalog_tag_name(),
    common_options.n_objects(),
    common_options.validate_file(),
    common_options.output(),
]

# Construct derived templates
group_command = cli_group.command
sub_client = DbClass.class_string


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

get_requests = wrappers.get_row_attribute_list_command(get_command, DbClass, "request_", db.Request)


@group_command(name="run")
@admin_options.db_engine()
@common_options.data()
@common_options.catalog_tag_name()
@common_options.estimator_name()
@common_options.output()
def run(
    db_engine: Callable[[], AsyncEngine],
    data: dict,
    catalog_tag_name: str,
    estimator_name: str,
    output: common_options.OutputEnum | None,
) -> None:
    """Create a dataset and in using a particular esimator"""

    async def _the_func() -> None:
        engine = db_engine()
        session = await create_async_session(engine)
        the_cache = db.cache.Cache()
        name = str(uuid.uuid1())
        dataset = await the_cache.load_dataset_from_values(
            session,
            name=name,
            data=data,
            catalog_tag_name=catalog_tag_name,
        )
        the_request = await the_cache.create_request(
            session,
            dataset_name=dataset.name,
            estimator_name=estimator_name,
        )
        check_request = await the_cache.run_request(session, request_id=the_request.id)
        wrappers.output_db_object(check_request, output, db.Request.col_names_for_table)
        await session.commit()
        await session.remove()
        await engine.dispose()

    asyncio.run(_the_func())
