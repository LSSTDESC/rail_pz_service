"""Commands for rail_admin CLI"""

import asyncio

import click
import structlog
from safir.database import create_database_engine, initialize_database

from rail_pz_service import db
from rail_pz_service.common.config import config

from .algorithm import algorithm_group
from .catalog_tag import catalog_tag_group
from .dataset import dataset_group
from .estimator import estimator_group
from .model import model_group
from .object_ref import object_ref_group
from .request import request_group


@click.command(name="init")
@click.option("--reset", is_flag=True, help="Delete all existing database data.")
def init(*, reset: bool) -> None:
    """Initialize the DB"""
    logger = structlog.get_logger(config.logging.handle)
    # engine = create_database_engine(config.db.url, config.db.password)

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.schema import CreateSchema

    async def _init_db() -> None:
        engine = create_async_engine(config.db.url)
        try:
            conn = engine.connect()
        except Exception as msg:
            await engine.dispose()
            raise RuntimeError(f"{msg}") from msg
        try:
            await conn.start()

            if db.Base.metadata.schema is not None:
                await conn.execute(CreateSchema(db.Base.metadata.schema, True))
            if reset:
                await conn.run_sync(db.Base.metadata.drop_all)
            await conn.run_sync(db.Base.metadata.create_all)
        except Exception as msg:
            await conn.rollback()
            await conn.close()
            await engine.dispose()
            raise RuntimeError(f"{msg}") from msg

        await conn.close()
        await engine.dispose()

    # async def _init_db() -> None:
    #    await initialize_database(engine, logger, schema=Base.metadata, reset=reset)
    #    await engine.dispose()

    asyncio.run(_init_db())


# Build the client CLI
@click.group(
    name="admin",
    commands=[
        init,
        algorithm_group,
        catalog_tag_group,
        dataset_group,
        estimator_group,
        model_group,
        object_ref_group,
        request_group,
    ],
)
@click.version_option(version=db.__version__)
def admin_top() -> None:
    """Administrative command-line rail-pz-server commands."""


if __name__ == "__main__":
    admin_top()
