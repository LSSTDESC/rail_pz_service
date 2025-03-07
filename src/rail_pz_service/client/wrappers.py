from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeAlias

from httpx import Response
from pydantic import BaseModel, TypeAdapter

from .. import models

if TYPE_CHECKING:
    from .client import PZRailClient


def get_rows_function(
    response_model_class: TypeAlias = BaseModel,
    query: str = "",
) -> Callable:
    """Return a function that gets all the rows from a table
    and attaches that function to a client.

    This version will provide a function which can be filtered
    based on the id of the parent node.

    FIXME: we aren't using this version, but might want to

    Parameters
    ----------
    response_model_class: TypeAlias = BaseModel,
        Pydantic class used to serialize the return value

    query: str
        http query

    Returns
    -------
    the_function: Callable
        Function that return all the rows for the table in question
    """

    def get_rows(
        obj: PZRailClient,
    ) -> list[response_model_class]:
        results: list[response_model_class] = []
        params: dict[str, Any] = {"skip": 0}
        adapter = TypeAdapter(list[response_model_class])
        while (paged_results := obj.client.get(f"{query}", params=params).raise_for_status().json()) != []:
            results.extend(adapter.validate_python(paged_results))
            params["skip"] += len(paged_results)
        return results

    return get_rows


def get_row_function(
    response_model_class: TypeAlias = BaseModel,
    query: str = "",
) -> Callable:
    """Return a function that gets a single row from a table (by ID)
    and attaches that function to a client.

    Parameters
    ----------
    response_model_class: TypeAlias = BaseModel,
        Pydantic class used to serialize the return value

    query: str
        http query

    Returns
    -------
    the_function: Callable
        Function that returns a single row from a table by ID
    """

    def row_get(
        obj: PZRailClient,
        row_id: int,
    ) -> response_model_class:
        full_query = f"{query}/{row_id}"
        results = obj.client.get(full_query).raise_for_status().json()
        return TypeAdapter(response_model_class).validate_python(results)

    return row_get


def delete_row_function(
    query: str = "",
) -> Callable:
    """Return a function that deletes a single row in a table
    and attaches that function to a client.

    Parameters
    ----------
    query: str
        http query

    Returns
    -------
    the_function: Callable
        Function that delete a single row from a table by ID
    """

    def row_delete(
        obj: PZRailClient,
        row_id: int,
    ) -> None:
        full_query = f"{query}/{row_id}"
        obj.client.delete(full_query).raise_for_status()

    return row_delete


def get_row_by_name_function(
    response_model_class: TypeAlias = BaseModel,
    query: str = "",
) -> Callable:
    """Return a function that gets a single row from a table (by name)
    and attaches that function to a client.

    Parameters
    ----------
    response_model_class: TypeAlias = BaseModel,
        Pydantic class used to serialize the return value

    query: str
        http query

    Returns
    -------
    the_function: Callable
        Function that returns a single row from a table by name
    """

    def get_row_by_name(
        obj: PZRailClient,
        name: str,
    ) -> response_model_class | None:
        params = models.NameQuery(name=name).model_dump()
        response = obj.client.get(query, params=params)
        results = response.raise_for_status().json()
        return TypeAdapter(response_model_class).validate_python(results)

    return get_row_by_name


def get_row_attribute_list_function(
    response_model_class: TypeAlias,
    query: str = "",
    query_suffix: str = "",
) -> Callable:
    """Return a function that gets a property of a single row of a table
    and attaches that function to a client.

    Parameters
    ----------
    response_model_class: TypeAlias = BaseModel,
        Pydantic class used to serialize the return value

    query
        http query

    query_suffix
        Rest of the query

    Returns
    -------
    the_function: Callable
        Function that returns a property of a single row from a table by name
    """

    def get_row_attribute_list(
        obj: PZRailClient,
        row_id: int,
    ) -> response_model_class:
        full_query = f"{query}/{row_id}/{query_suffix}"
        results = obj.client.get(full_query).raise_for_status().json()
        return TypeAdapter(response_model_class).validate_python(results)

    return get_row_attribute_list


def create_row_function(
    response_model_class: TypeAlias = BaseModel,
    create_model_class: TypeAlias = BaseModel,
    query: str = "",
) -> Callable:
    """Return a function that creates a single row in a table
    and attaches that function to a client.

    Parameters
    ----------
    response_model_class
        Pydantic class used to serialize the return value

    create_model_class
        Pydantic class used to serialize the inputs value

    query
        http query

    Returns
    -------
    the_function: Callable
        Function that returns a single row from a table by ID
    """

    def row_create(obj: PZRailClient, **kwargs: Any) -> response_model_class:
        content = create_model_class(**kwargs).model_dump_json()
        results = obj.client.post(query, content=content).raise_for_status().json()
        return TypeAdapter(response_model_class).validate_python(results)

    return row_create


def download_file_function(
    query: str = "",
) -> Callable:
    """Download a file associated to DB object.

    Parameters
    ----------
    query
        http query

    Returns
    -------
    Callable
        Function that downloads a file associated to DB object
    """

    def download_file(
        obj: PZRailClient,
        row_id: int,
        filename: str,
    ) -> Response:
        full_query = f"{query}/{row_id}"
        params = models.DownloadQuery(filename=filename).model_dump()
        results = obj.client.get(full_query, params=params).raise_for_status()
        filename = results.headers["content-disposition"].split("=")[1].replace('"', "")
        with open(filename, mode="wb") as fout:
            fout.write(results.content)
        return results

    return download_file
