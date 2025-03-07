import uuid

from click.testing import CliRunner
from sqlalchemy.ext.asyncio import AsyncEngine

from rail_pz_service import models
from rail_pz_service.db.cli.admin import admin_top

from .util_functions import (
    check_and_parse_result,
    cleanup,
)


def test_dataset_cli_db(engine: AsyncEngine) -> None:
    """Test `dataset` CLI command"""

    assert engine

    runner = CliRunner()

    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    result = runner.invoke(admin_top, "dataset list --output yaml")
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

    result = runner.invoke(admin_top, "dataset list --output yaml")
    datasets = check_and_parse_result(result, list[models.Dataset])
    entry = datasets[0]

    # test other output cases
    result = runner.invoke(admin_top, "dataset list --output json")
    assert result.exit_code == 0

    result = runner.invoke(admin_top, "dataset list")
    assert result.exit_code == 0

    result = runner.invoke(admin_top, f"dataset get all --row-id {entry.id} --output json")
    assert result.exit_code == 0

    result = runner.invoke(admin_top, f"dataset get all --row-id {entry.id}")
    assert result.exit_code == 0

    # delete everything we just made in the session
    cleanup(runner, admin_top)
