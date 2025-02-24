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


def test_request_cli_db(engine: AsyncEngine) -> None:
    """Test `request` CLI command"""

    assert engine
    
    runner = CliRunner()

    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    result = runner.invoke(admin_top, "request list --output yaml")
    requests_ = check_and_parse_result(result, list[models.Request])
    assert len(requests_) == 0, "Request list not empty"

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

    result = runner.invoke(
        admin_top,
        "estimator create "
        f"--name estimator_{uuid_int} "
        f"--catalog_tag_name {catalog_tag_.name} "
        f"--algo_name {algorithm_.name} "
        f"--model_name {model_.name} "
        "--output yaml",
    )
    estimator_ = check_and_parse_result(result, models.Estimator)

    result = runner.invoke(
        admin_top,
        "dataset create "
        f"--name data_{uuid_int} "
        "--n_objects 2 "
        "--path not/really/a/path "
        "--class_name not.really.a.class "
        f"--catalog_tag_name {catalog_tag_.name} "
        "--output yaml",
    )
    dataset_ = check_and_parse_result(result, models.Dataset)
    
    result = runner.invoke(
        admin_top,
        "request create "
        f"--estimator_name {estimator_.name} "
        f"--dataset_name {dataset_.name} "
        "--output yaml",
    )
    request_ = check_and_parse_result(result, models.Request)

    result = runner.invoke(admin_top, "request list --output yaml")
    requests_ = check_and_parse_result(result, list[models.Request])
    entry = requests_[0]

    # test other output cases
    # result = runner.invoke(admin_top, "request list --output json")
    # assert result.exit_code == 0

    result = runner.invoke(admin_top, "request list")
    assert result.exit_code == 0

    # result = runner.invoke(admin_top, f"request get all --row_id {entry.id} --output json")
    # assert result.exit_code == 0

    result = runner.invoke(admin_top, f"request get all --row_id {entry.id}")
    assert result.exit_code == 0  

    # delete everything we just made in the session
    cleanup(runner, admin_top, check_cascade=True)
