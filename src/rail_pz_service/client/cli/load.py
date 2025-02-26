"""CLI to manage Job table"""

import click

from ... import models
from ...common import common_options
from ..client import PZRailClient
from . import client_options, wrappers


@click.group(name="load")
def load_group() -> None:
    """Load object into the DB tables"""


@load_group.command(name="dataset")
@client_options.pz_client()
@common_options.name()
@common_options.path()
@common_options.catalog_tag_name()
@common_options.output()
def dataset_command(
    pz_client: PZRailClient,
    name: str,
    path: click.Path,
    catalog_tag_name: str,
    output: common_options.OutputEnum | None,
) -> None:
    """Load CatalogTags from RailEnv"""

    result = pz_client.load.dataset(
        name=name,
        path=path,
        catalog_tag_name=catalog_tag_name,
    )
    wrappers.output_pydantic_object(result, output, models.Dataset.col_names_for_table)


@load_group.command(name="model")
@client_options.pz_client()
@common_options.name()
@common_options.path()
@common_options.algo_name()
@common_options.catalog_tag_name()
@common_options.output()
def model_command(
    pz_client: PZRailClient,
    name: str,
    path: click.Path,
    algo_name: str,
    catalog_tag_name: str,
    output: common_options.OutputEnum | None,
) -> None:
    """Load CatalogTags from RailEnv"""
    result = pz_client.load.model(
        name=name,
        path=path,
        algo_name=algo_name,
        catalog_tag_name=catalog_tag_name,
    )
    wrappers.output_pydantic_object(result, output, models.Dataset.col_names_for_table)


@load_group.command(name="estimator")
@client_options.pz_client()
@common_options.name()
@common_options.model_name()
@common_options.config()
@common_options.output()
def estimator_command(
    pz_client: PZRailClient,
    name: str,
    model_name: str,
    config: dict | None,
    output: common_options.OutputEnum | None,
) -> None:
    """Load CatalogTags from RailEnv"""
    result = pz_client.load.estimator(
        name=name,
        model_name=model_name,
        config=config,
    )
    wrappers.output_pydantic_object(result, output, models.Dataset.col_names_for_table)
