from typing import TypeAlias

from sqlalchemy.ext.asyncio import async_scoped_session

from rail_pz_service import db


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
