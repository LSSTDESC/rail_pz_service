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
def test_algorithm_client(uvicorn: UvicornProcess, api_version: str, engine: AsyncEngine) -> None:
    """Test `algorithm` CLI command"""

    assert engine

    client_config.service_url = f"{uvicorn.url}{config.asgi.prefix}/{api_version}"
    runner = CliRunner()

    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    # result = runner.invoke(top, "algorithm list --output yaml")
    # algorithms = check_and_parse_result(result, list[models.Algorithm])
    # assert len(algorithms) == 0, "Algorithm list not empty"

    result = runner.invoke(
        admin_top,
        f"algorithm create --name algo_{uuid_int} --class-name not.really.a.class --output yaml",
    )
    check_and_parse_result(result, models.Algorithm)

    result = runner.invoke(top, "algorithm list --output yaml")
    algorithms = check_and_parse_result(result, list[models.Algorithm])
    entry = algorithms[0]

    # test other output cases
    result = runner.invoke(top, "algorithm list --output json")
    assert result.exit_code == 0

    result = runner.invoke(top, "algorithm list")
    assert result.exit_code == 0

    result = runner.invoke(top, f"algorithm get all --row-id {entry.id} --output json")
    assert result.exit_code == 0

    result = runner.invoke(top, f"algorithm get all --row-id {entry.id}")
    assert result.exit_code == 0

    # delete everything we just made in the session
    cleanup(runner, admin_top)
