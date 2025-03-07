"""CLI to manage Step table"""

import uuid

import click

from ... import models
from ...common import common_options
from ..client import PZRailClient
from . import client_options, wrappers


@click.group(name="dataset")
def dataset_group() -> None:
    """Manage Dataset table"""


# Template specialization
# Specify the cli path to attach these commands to
cli_group = dataset_group
# Specify the associated database table
ModelClass = models.Dataset

# Construct derived templates
group_command = cli_group.command
sub_client = "dataset"


@cli_group.group()
def get() -> None:
    """Get an attribute"""


get_command = get.command


# Add functions to the cli
get_rows = wrappers.get_list_command(group_command, sub_client, ModelClass)

get_row = wrappers.get_row_command(get_command, sub_client, ModelClass)

get_row_by_name = wrappers.get_row_by_name_command(get_command, sub_client, ModelClass)

get_requests = wrappers.get_row_attribute_list_command(get_command, sub_client, models.Request, "requests")

download_command = wrappers.download_command(group_command, sub_client)


@group_command(name="run")
@client_options.pz_client()
@common_options.data()
@common_options.catalog_tag_name()
@common_options.estimator_name()
@common_options.filename()
@common_options.output()
def run(
    pz_client: PZRailClient,
    data: dict,
    catalog_tag_name: str,
    estimator_name: str,
    filename: str,
    output: common_options.OutputEnum | None,
) -> None:
    """Create a dataset and run it with the given estimator"""
    name = str(uuid.uuid1())
    dataset = pz_client.load.dataset(
        name=name,
        data=data,
        path=None,
        catalog_tag_name=catalog_tag_name,
    )
    estimator = pz_client.estimator.get_row_by_name(
        estimator_name,
    )
    request = pz_client.request.create(
        dataset_name=dataset.name,
        estimator_name=estimator.name,
    )
    check_request = pz_client.request.run(
        request.id,
    )
    _result = pz_client.request.download(
        check_request.id,
        filename=filename,
    )
    wrappers.output_pydantic_object(check_request, output, models.Request.col_names_for_table)
