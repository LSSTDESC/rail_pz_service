import os

import qp
from click.testing import CliRunner
from sqlalchemy.ext.asyncio import AsyncEngine

from rail_pz_service import models
from rail_pz_service.db.cli.admin import admin_top

from .util_functions import (
    check_and_parse_result,
    cleanup,
)


def test_run_cli_db(engine: AsyncEngine, setup_test_area: int) -> None:
    """Test `dataset` CLI command"""

    assert setup_test_area == 0
    assert engine

    runner = CliRunner()

    runner.invoke(admin_top, "init")

    result = runner.invoke(admin_top, "load algos-from-env --output yaml")
    algorithms = check_and_parse_result(result, list[models.Algorithm])
    assert len(algorithms) != 0, "No algorithms loaded"

    result = runner.invoke(admin_top, "load catalog-tags-from-env --output yaml")
    catalog_tags = check_and_parse_result(result, list[models.CatalogTag])
    assert len(catalog_tags) != 0, "No catalog tags loaded"

    model_path = os.path.join("tests", "temp_data", "inputs", "model_com_cam_trainz_base.pkl")

    result = runner.invoke(
        admin_top,
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
        admin_top,
        "load estimator --name com_cam_trainz_base --model-name com_cam_trainz_base --output yaml",
    )
    the_estimator = check_and_parse_result(result, models.Estimator)
    assert the_estimator.name == "com_cam_trainz_base"

    data: str = ""
    data += "u_cModelMag:24.4;g_cModelMag:24.4;r_cModelMag:24.4;"
    data += "i_cModelMag:24.4;z_cModelMag:24.4;y_cModelMag:24.4;"
    data += "u_cModelMagErr:0.5;g_cModelMagErr:0.5;r_cModelMagErr:0.5;"
    data += "i_cModelMagErr:0.5;z_cModelMagErr:0.5;y_cModelMagErr:0.5;"

    result = runner.invoke(
        admin_top,
        f"dataset run --data {data} --catalog-tag-name com_cam "
        f"--estimator-name {the_estimator.name} --output yaml",
    )
    the_request = check_and_parse_result(result, models.Request)

    qp_ens = qp.read(the_request.qp_file_path)
    assert qp_ens.npdf != 0

    # delete everything we just made in the session
    cleanup(runner, admin_top)
