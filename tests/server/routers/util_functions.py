from typing import TypeAlias, TypeVar

from httpx import Response
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import async_scoped_session

from rail_pz_service import db

T = TypeVar("T")


def check_and_parse_response(
    response: Response,
    return_class: type[T],
) -> T:
    if not response.is_success:
        raise ValueError(f"{response.request} failed with {response.text}")
    return_obj = TypeAdapter(return_class).validate_python(response.json())
    return return_obj


def expect_failed_response(
    response: Response,
    expected_code: int = 500,
) -> None:
    if response.status_code != expected_code:
        raise ValueError(f"{response.request} did not fail as expected {response.status_code}")


async def delete_all_rows(
    session: async_scoped_session,
    table_class: TypeAlias = db.RowMixin,
) -> None:
    rows = await table_class.get_rows(session)
    for row_ in rows:
        await table_class.delete_row(session, row_.id)

    rows_check = await table_class.get_rows(session)
    assert len(rows_check) == 0, f"Failed to delete all {table_class}"


async def delete_all_stuff(
    session: async_scoped_session,
) -> None:
    await delete_all_rows(session, db.Algorithm)
    await delete_all_rows(session, db.CatalogTag)
    await delete_all_rows(session, db.Dataset)
    await delete_all_rows(session, db.Estimator)
    await delete_all_rows(session, db.Model)
    await delete_all_rows(session, db.Request)


async def cleanup(
    session: async_scoped_session,
) -> None:
    await delete_all_stuff(session)

    await session.commit()
    await session.close()
    await session.remove()
