"""CLI to manage Job table"""

import asyncio
from collections.abc import Callable

import click
import yaml
from safir.database import create_async_session
from sqlalchemy.ext.asyncio import AsyncEngine

from ... import db
from ...common import common_options
from . import admin_options, wrappers


@click.group(name="catalog-tag")
def catalog_tag_group() -> None:
    """Manage Catalog_tag table"""


# Template specialization
# Specify the cli path to attach these commands to
cli_group = catalog_tag_group
DbClass = db.CatalogTag
# Specify the options for the create command
create_options = [
    admin_options.db_engine(),
    common_options.name(),
    common_options.class_name(),
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

get_estimators = wrappers.get_row_attribute_list_command(get_command, DbClass, "estimators_", db.Estimator)

get_models = wrappers.get_row_attribute_list_command(get_command, DbClass, "models_", db.Model)

get_datasets = wrappers.get_row_attribute_list_command(get_command, DbClass, "datasets_", db.Dataset)


@get_command(name="tree")
@admin_options.db_engine()
def run(
    db_engine: Callable[[], AsyncEngine],
) -> None:
    """Run a particular request"""

    async def _the_func() -> None:
        engine = db_engine()
        session = await create_async_session(engine)
        the_cache = db.cache.Cache()
        request = await the_cache.get_catalog_tag_tree(session)
        click.echo(yaml.dump(request.model_dump()))
        await session.remove()
        await engine.dispose()

    asyncio.run(_the_func())
