import os

import pytest
import qp
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
def test_load_client(
    uvicorn: UvicornProcess, api_version: str, engine: AsyncEngine, setup_test_area: int
) -> None:
    """Test `algorithm` CLI command"""
    assert setup_test_area == 0
    assert engine

    client_config.service_url = f"{uvicorn.url}{config.asgi.prefix}/{api_version}"
    runner = CliRunner()

    runner.invoke(admin_top, "init")

    result = runner.invoke(admin_top, "load algos-from-env --output yaml")
    algorithms = check_and_parse_result(result, list[models.Algorithm])
    assert len(algorithms) != 0, "No algorithms loaded"

    result = runner.invoke(admin_top, "load catalog-tags-from-env --output yaml")
    catalog_tags = check_and_parse_result(result, list[models.CatalogTag])
    assert len(catalog_tags) != 0, "No catalog tags loaded"

    model_path = os.path.abspath(
        os.path.join("tests", "temp_data", "inputs", "model_com_cam_trainz_base.pkl")
    )
    dataset_path = os.path.abspath(os.path.join("tests", "temp_data", "inputs", "minimal_gold_test.hdf5"))

    result = runner.invoke(
        top,
        "load model "
        "--name com_cam_trainz_base "
        f"--path {model_path} "
        "--algo-name TrainZEstimator "
        "--catalog-tag-name com_cam "
        "--output yaml",
    )
    the_model = check_and_parse_result(result, models.Model)
    assert the_model.name == "com_cam_trainz_base"

    result = runner.invoke(
        top,
        f"load dataset --name com_cam_test --path {dataset_path} --catalog-tag-name com_cam --output yaml",
    )
    the_dataset = check_and_parse_result(result, models.Dataset)
    assert the_dataset.name == "com_cam_test"

    result = runner.invoke(
        top,
        "load estimator --name com_cam_trainz_base --model-name com_cam_trainz_base --output yaml",
    )
    the_estimator = check_and_parse_result(result, models.Estimator)
    assert the_estimator.name == "com_cam_trainz_base"

    result = runner.invoke(
        top,
        "request create "
        f"--dataset-name {the_dataset.name} "
        f"--estimator-name {the_estimator.name} "
        "--output yaml",
    )
    the_request = check_and_parse_result(result, models.Request)

    result = runner.invoke(top, f"request run --row-id {the_request.id} --output yaml")

    result = runner.invoke(top, f"request get all --row-id {the_request.id} --output yaml")
    check_request = check_and_parse_result(result, models.Request)

    assert check_request.qp_file_path

    qp_path = os.path.abspath(check_request.qp_file_path)
    qp_ens = qp.read(qp_path)
    assert qp_ens.npdf != 0

    # delete everything we just made in the session
    cleanup(runner, admin_top)
