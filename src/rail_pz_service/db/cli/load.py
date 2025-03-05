"""CLI to manage Job table"""

import asyncio
from collections.abc import Callable
from pathlib import Path

import click
from safir.database import create_async_session
from sqlalchemy.ext.asyncio import AsyncEngine

from ... import db
from ...common import common_options
from . import admin_options, wrappers


@click.group(name="load")
def load_group() -> None:
    """Manage Request table"""


@load_group.command(name="algos-from-env")
@admin_options.db_engine()
@common_options.output()
def algos_from_env_command(
    db_engine: Callable[[], AsyncEngine],
    output: common_options.OutputEnum | None,
) -> None:
    """Load algorithms from RailEnv"""

    async def _the_func() -> None:
        engine = db_engine()
        session = await create_async_session(engine)
        the_cache = db.Cache()
        new_algos = await the_cache.load_algorithms_from_rail_env(session)
        wrappers.output_db_obj_list(new_algos, output, db.Algorithm.col_names_for_table)
        await session.remove()
        await engine.dispose()

    asyncio.run(_the_func())


@load_group.command(name="catalog-tags-from-env")
@admin_options.db_engine()
@common_options.output()
def catalog_tags_from_env_command(
    db_engine: Callable[[], AsyncEngine],
    output: common_options.OutputEnum | None,
) -> None:
    """Load CatalogTags from RailEnv"""

    async def _the_func() -> None:
        engine = db_engine()
        session = await create_async_session(engine)
        the_cache = db.Cache()
        new_catalog_tags = await the_cache.load_catalog_tags_from_rail_env(session)
        wrappers.output_db_obj_list(new_catalog_tags, output, db.CatalogTag.col_names_for_table)
        await session.remove()
        await engine.dispose()

    asyncio.run(_the_func())


@load_group.command(name="dataset")
@admin_options.db_engine()
@common_options.name()
@common_options.path()
@common_options.data()
@common_options.catalog_tag_name()
@common_options.output()
def dataset_command(
    db_engine: Callable[[], AsyncEngine],
    name: str,
    path: Path | None,
    data: dict | None,
    catalog_tag_name: str,
    output: common_options.OutputEnum | None,
) -> None:
    """Load CatalogTags from RailEnv"""

    async def _the_func() -> None:
        engine = db_engine()
        session = await create_async_session(engine)
        the_cache = db.Cache()
        if path is not None:
            new_dataset = await the_cache.load_dataset_from_file(
                session,
                name,
                path=path,
                catalog_tag_name=catalog_tag_name,
            )
        elif data is not None:
            new_dataset = await the_cache.load_dataset_from_values(
                session,
                name,
                data=data,
                catalog_tag_name=catalog_tag_name,
            )
        else:  # pragma: no cover
            raise ValueError("Either --path or --data must be used")
        wrappers.output_db_object(new_dataset, output, db.Dataset.col_names_for_table)
        await session.remove()
        await engine.dispose()

    asyncio.run(_the_func())


@load_group.command(name="model")
@admin_options.db_engine()
@common_options.name()
@common_options.path()
@common_options.algo_name()
@common_options.catalog_tag_name()
@common_options.output()
def model_command(
    db_engine: Callable[[], AsyncEngine],
    name: str,
    path: Path,
    algo_name: str,
    catalog_tag_name: str,
    output: common_options.OutputEnum | None,
) -> None:
    """Load CatalogTags from RailEnv"""

    async def _the_func() -> None:
        engine = db_engine()
        session = await create_async_session(engine)
        the_cache = db.Cache()
        new_model = await the_cache.load_model_from_file(
            session,
            name,
            path=path,
            algo_name=algo_name,
            catalog_tag_name=catalog_tag_name,
        )
        wrappers.output_db_object(new_model, output, db.Model.col_names_for_table)
        await session.remove()
        await engine.dispose()

    asyncio.run(_the_func())


@load_group.command(name="estimator")
@admin_options.db_engine()
@common_options.name()
@common_options.model_name()
@common_options.config()
@common_options.output()
def estimator_command(
    db_engine: Callable[[], AsyncEngine],
    name: str,
    model_name: str,
    config: dict | None,
    output: common_options.OutputEnum | None,
) -> None:
    """Load CatalogTags from RailEnv"""

    async def _the_func() -> None:
        engine = db_engine()
        session = await create_async_session(engine)
        the_cache = db.Cache()
        new_estimator = await the_cache.load_estimator(
            session,
            name,
            model_name=model_name,
            config=config,
        )
        wrappers.output_db_object(new_estimator, output, db.Estimator.col_names_for_table)
        await session.remove()
        await engine.dispose()

    asyncio.run(_the_func())
