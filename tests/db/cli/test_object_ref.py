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


def test_object_ref_cli_db(engine: AsyncEngine) -> None:
    """Test `object-ref` CLI command"""

    assert engine
    
    runner = CliRunner()

    # generate a uuid to avoid collisions
    uuid_int = uuid.uuid1().int

    result = runner.invoke(admin_top, "object-ref list --output yaml")
    object_refs = check_and_parse_result(result, list[models.ObjectRef])
    assert len(object_refs) == 0, "ObjectRef list not empty"

    result = runner.invoke(
        admin_top,
        f"catalog-tag create --name cat_{uuid_int} --class_name not.really.a.class --output yaml",
    )
    catalog_tag_ = check_and_parse_result(result, models.CatalogTag)

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
    dataset = check_and_parse_result(result, models.Dataset)

    result = runner.invoke(
        admin_top,
        "object-ref create "
        f"--name data_{uuid_int} "
        "--index 0 "
        f"--dataset_name {dataset.name} "
        "--output yaml",
    )
    object_ref = check_and_parse_result(result, models.ObjectRef)

    result = runner.invoke(admin_top, "object-ref list --output yaml")
    object_refs = check_and_parse_result(result, list[models.ObjectRef])
    entry = object_refs[0]

    # test other output cases
    result = runner.invoke(admin_top, "object-ref list --output json")
    assert result.exit_code == 0

    result = runner.invoke(admin_top, "object-ref list")
    assert result.exit_code == 0

    result = runner.invoke(admin_top, f"object-ref get all --row_id {entry.id} --output json")
    assert result.exit_code == 0

    result = runner.invoke(admin_top, f"object-ref get all --row_id {entry.id}")
    assert result.exit_code == 0  

    # delete everything we just made in the session
    cleanup(runner, admin_top, check_cascade=True)
