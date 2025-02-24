"""CLI to manage Job table"""

import asyncio
from collections.abc import Callable

import click

from rail_pz_service import db

from ..client.client import PZRailClient

from . import admin_options, wrappers


@click.group(name="load")
def load_group() -> None:
    """Load object into the DB tables"""


@load_group.command(name="dataset")
@admin_options.pz_client()
@admin_options.name()
@admin_options.path()
@admin_options.catalog_tag_name()
@admin_options.output()
def dataset_command(
    pz_client: PZRailClient,
    name: str,
    path: click.Path(),
    catalog_tag_name: str,
    output: admin_options.OutputEnum | None,
) -> None:
    """Load CatalogTags from RailEnv"""

    result = pz_client().load.dataset(
        name=name,
        path=path,
        catalog_tag_name=catalog_tag_name,
    )
    output_pydantic_list(result, output, models.Dataset.col_names_for_table)



@load_group.command(name="model")
@admin_options.pz_client()
@admin_options.name()
@admin_options.path()
@admin_options.algo_name()
@admin_options.catalog_tag_name()
@admin_options.output()
def model_command(
    pz_client: PZRailClient,
    name: str,
    path: click.Path(),
    algo_name: str,
    catalog_tag_name: str,
    output: admin_options.OutputEnum | None,
) -> None:
    """Load CatalogTags from RailEnv"""
    result = pz_client().load.model(
        name=name,
        path=path,
        algo_name=algo_name,
        catalog_tag_name=catalog_tag_name,
    )
    output_pydantic_list(result, output, models.Dataset.col_names_for_table)


@load_group.command(name="estimator")
@admin_options.pz_client()
@admin_options.name()
@admin_options.model_name()
@admin_options.config()
@admin_options.output()
def estimator_command(
    pz_client: PZRailClient,
    name: str,
    model_name: str,
    config: dict | None,
    output: admin_options.OutputEnum | None,
) -> None:
    """Load CatalogTags from RailEnv"""
    result = pz_client().load.estimator(
        name=name,
        model_name=model_name,
        config=config,
    )
    output_pydantic_list(result, output, models.Dataset.col_names_for_table)

