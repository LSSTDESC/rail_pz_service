from typing import TypeAlias, TypeVar

import yaml
from click import BaseCommand
from click.testing import CliRunner, Result
from pydantic import TypeAdapter

from rail_pz_service import models

T = TypeVar("T")


def check_and_parse_result(
    result: Result,
    return_class: type[T],
) -> T:
    if not result.exit_code == 0:
        raise ValueError(f"{result} failed with {result.exit_code} {result.output}")
    return_obj = TypeAdapter(return_class).validate_python(yaml.unsafe_load(result.stdout))
    return return_obj


def expect_failed_result(
    result: Result,
    expected_code: int = 1,
) -> None:
    if result.exit_code != expected_code:
        raise ValueError(f"{result} did not fail as expected {result.exit_code}")


def delete_all_rows(
    runner: CliRunner,
    client_top: BaseCommand,
    entry_class_name: str,
    entry_class: TypeAlias,
) -> None:
    result = runner.invoke(client_top, f"{entry_class_name} list --output yaml")
    rows = check_and_parse_result(result, list[entry_class])

    for row_ in rows:
        result = runner.invoke(client_top, f"{entry_class_name} delete --row-id {row_.id}")
        if not result.exit_code == 0:
            raise ValueError(f"{result} failed with {result.exit_code} {result.output}")


def delete_all_stuff(
    runner: CliRunner,
    client_top: BaseCommand,
) -> None:
    delete_all_rows(runner, client_top, "algorithm", models.Algorithm)
    delete_all_rows(runner, client_top, "catalog-tag", models.CatalogTag)
    delete_all_rows(runner, client_top, "dataset", models.Dataset)
    delete_all_rows(runner, client_top, "estimator", models.Estimator)
    delete_all_rows(runner, client_top, "model", models.Model)
    delete_all_rows(runner, client_top, "request", models.Request)


def cleanup(
    runner: CliRunner,
    client_top: BaseCommand,
) -> None:
    delete_all_stuff(runner, client_top)
