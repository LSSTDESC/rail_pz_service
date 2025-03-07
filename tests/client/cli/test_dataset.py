import uuid

import pytest
from click.testing import CliRunner
from safir.testing.uvicorn import UvicornProcess
from sqlalchemy.ext.asyncio import AsyncEngine

from rail_pz_service import models
from rail_pz_service.client.cli.main import top
from rail_pz_service.client.clientconfig import client_config
from rail_pz_service.config import config
from rail_pz_service.db.cli.admin import admin_top

from .util_functions import (
    check_and_parse_result,
    cleanup,
)


@pytest.mark.parametrize("api_version", ["v1"])
def test_dataset_client(uvicorn: UvicornProcess, api_version: str, engine: AsyncEngine) -> None:
    """Test `dataset` CLI command"""

    assert engine
    client_config.service_url = f"{uvicorn.url}{config.asgi.prefix}/{api_version}"

    runner = CliRunner()

    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    result = runner.invoke(top, "dataset list --output yaml")
    datasets = check_and_parse_result(result, list[models.Dataset])
    assert len(datasets) == 0, "Dataset list not empty"

    result = runner.invoke(
        admin_top,
        f"catalog-tag create --name cat_{uuid_int} --class-name not.really.a.class --output yaml",
    )
    catalog_tag_ = check_and_parse_result(result, models.CatalogTag)

    result = runner.invoke(
        admin_top,
        "dataset create "
        f"--name data_{uuid_int} "
        "--n-objects 2 "
        "--path not/really/a/path "
        f"--catalog-tag-name {catalog_tag_.name} "
        "--output yaml",
    )
    check_and_parse_result(result, models.Dataset)

    result = runner.invoke(top, "dataset list --output yaml")
    datasets = check_and_parse_result(result, list[models.Dataset])
    entry = datasets[0]

    # test other output cases
    result = runner.invoke(top, "dataset list --output json")
    assert result.exit_code == 0

    result = runner.invoke(top, "dataset list")
    assert result.exit_code == 0

    result = runner.invoke(top, f"dataset get all --row-id {entry.id} --output json")
    assert result.exit_code == 0

    result = runner.invoke(top, f"dataset get all --row-id {entry.id}")
    assert result.exit_code == 0

    # delete everything we just made in the session
    cleanup(runner, admin_top)
