"""Commands for rail_admin CLI"""

import asyncio

import click

from .. import __version__

from .algorithm import algorithm_group
from .catalog_tag import catalog_tag_group
from .dataset import dataset_group
from .estimator import estimator_group
from .load import load_group
from .model import model_group
from .object_ref import object_ref_group
from .request import request_group


# Build the client CLI
@click.group(
    name="pz-rail-server-client",
    commands=[
        algorithm_group,
        catalog_tag_group,
        dataset_group,
        estimator_group,
        load_group,
        model_group,
        object_ref_group,
        request_group,
    ],
)
@click.version_option(version=__version__)
def top() -> None:
    """Administrative command-line rail-pz-server commands."""


if __name__ == "__main__":
    top()
