import os
import uuid

import pytest
from click.testing import CliRunner
from sqlalchemy.ext.asyncio import AsyncEngine

from rail_pz_service.common import models
from rail_pz_service import db
from rail_pz_service.common import errors
from rail_pz_service.cli.admin.admin import admin_top

from .util_functions import (
    check_and_parse_result,
    cleanup,
)


def test_model_cli_db(engine: AsyncEngine) -> None:
    """Test `model` CLI command"""

    assert engine
    
    runner = CliRunner()

    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    result = runner.invoke(admin_top, "model list --output yaml")
    models_ = check_and_parse_result(result, list[models.Model])
    assert len(models_) == 0, "Model list not empty"

    result = runner.invoke(
        admin_top,
        f"algorithm create --name algo_{uuid_int} --class_name not.really.a.class --output yaml",
    )
    algorithm_ = check_and_parse_result(result, models.Algorithm)

    result = runner.invoke(
        admin_top,
        f"catalog-tag create --name cat_{uuid_int} --class_name not.really.a.class --output yaml",
    )
    catalog_tag_ = check_and_parse_result(result, models.CatalogTag)

    result = runner.invoke(
        admin_top,
        "model create "
        f"--name model_{uuid_int} "
        "--path not/really/a/path "
        f"--algo_name {algorithm_.name} "
        f"--catalog_tag_name {catalog_tag_.name} "
        "--output yaml",
    )
    model_ = check_and_parse_result(result, models.Model)
    
    result = runner.invoke(admin_top, "model list --output yaml")
    models_ = check_and_parse_result(result, list[models.Model])
    entry = models_[0]

    # test other output cases
    result = runner.invoke(admin_top, "model list --output json")
    assert result.exit_code == 0

    result = runner.invoke(admin_top, "model list")
    assert result.exit_code == 0

    result = runner.invoke(admin_top, f"model get all --row_id {entry.id} --output json")
    assert result.exit_code == 0

    result = runner.invoke(admin_top, f"model get all --row_id {entry.id}")
    assert result.exit_code == 0  

    # delete everything we just made in the session
    cleanup(runner, admin_top, check_cascade=True)
