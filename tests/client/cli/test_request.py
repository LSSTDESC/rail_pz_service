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
def test_request_client(uvicorn: UvicornProcess, api_version: str, engine: AsyncEngine) -> None:
    """Test `request` CLI command"""

    assert engine
    client_config.service_url = f"{uvicorn.url}{config.asgi.prefix}/{api_version}"

    runner = CliRunner()

    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    result = runner.invoke(admin_top, "request list --output yaml")
    requests_ = check_and_parse_result(result, list[models.Request])
    assert len(requests_) == 0, "Request list not empty"

    result = runner.invoke(
        admin_top,
        f"algorithm create --name algo_{uuid_int} --class-name not.really.a.class --output yaml",
    )
    algorithm_ = check_and_parse_result(result, models.Algorithm)

    result = runner.invoke(
        admin_top,
        f"catalog-tag create --name cat_{uuid_int} --class-name not.really.a.class --output yaml",
    )
    catalog_tag_ = check_and_parse_result(result, models.CatalogTag)

    result = runner.invoke(
        admin_top,
        "model create "
        f"--name model_{uuid_int} "
        "--path not/really/a/path "
        f"--algo-name {algorithm_.name} "
        f"--catalog-tag-name {catalog_tag_.name} "
        "--output yaml",
    )
    model_ = check_and_parse_result(result, models.Model)

    result = runner.invoke(
        admin_top,
        f"estimator create --name estimator_{uuid_int} --model-name {model_.name} --output yaml",
    )
    estimator_ = check_and_parse_result(result, models.Estimator)

    result = runner.invoke(
        admin_top,
        "dataset create "
        f"--name data_{uuid_int} "
        "--n-objects 2 "
        "--path not/really/a/path "
        f"--catalog-tag-name {catalog_tag_.name} "
        "--output yaml",
    )
    dataset_ = check_and_parse_result(result, models.Dataset)

    result = runner.invoke(
        admin_top,
        f"request create --estimator-name {estimator_.name} --dataset-name {dataset_.name} --output yaml",
    )
    check_and_parse_result(result, models.Request)

    result = runner.invoke(top, "request list --output yaml")
    requests_ = check_and_parse_result(result, list[models.Request])
    entry = requests_[0]

    # test other output cases
    # result = runner.invoke(top, "request list --output json")
    # assert result.exit_code == 0

    result = runner.invoke(top, "request list")
    assert result.exit_code == 0

    # result = runner.invoke(top, f"request get all
    # --row_id {entry.id} --output json")
    # assert result.exit_code == 0

    result = runner.invoke(top, f"request get all --row-id {entry.id}")
    assert result.exit_code == 0

    result = runner.invoke(top, f"request get all --row-id {entry.id}")
    assert result.exit_code == 0

    result = runner.invoke(top, f"request delete --row-id {entry.id}")
    assert result.exit_code == 0

    result = runner.invoke(top, "request list --output yaml")
    requests_ = check_and_parse_result(result, list[models.Request])
    assert len(requests_) == 0

    # delete everything we just made in the session
    cleanup(runner, admin_top)
