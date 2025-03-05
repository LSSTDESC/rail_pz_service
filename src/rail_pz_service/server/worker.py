"""Request processing worker task"""

from asyncio import create_task
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from anyio import current_time, sleep_until
from fastapi import FastAPI
from safir.database import create_async_session, create_database_engine
from safir.logging import configure_uvicorn_logging
from sqlalchemy.ext.asyncio import async_scoped_session

from .. import __version__, db
from ..config import config
from .logging import LOGGER
from .routers.healthz import health_router

configure_uvicorn_logging(config.logging.level)

logger = LOGGER.bind(module=__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # start
    app.state.tasks = set()
    worker = create_task(main_loop(), name="worker")
    app.state.tasks.add(worker)
    yield
    # stop


async def worker_iteration(
    session: async_scoped_session,
    cache: db.Cache,
) -> None:
    open_requests = await db.Request.get_open_requests(session)
    for open_request_ in open_requests:
        await cache.run_request(session, open_request_.id)


async def main_loop() -> None:
    """Worker execution loop.

    With a database session, perform a single daemon interation and then sleep
    until the next daemon appointment.
    """
    engine = create_database_engine(config.db.url, config.db.password)
    sleep_time = config.daemon.processing_interval
    cache = db.Cache.shared_cache(logger)

    async with engine.begin():
        session = await create_async_session(engine, logger)
        logger.info("Worker starting.")
        iteration_count = 0

        while True:
            iteration_count += 1
            logger.info("Worker starting iteration.")
            await worker_iteration(session, cache)
            iteration_time = current_time()
            logger.info(f"Worker completed {iteration_count} iterations at {iteration_time}.")
            next_wakeup = iteration_time + sleep_time
            logger.info(f"Worker next iteration at {next_wakeup}.")
            await sleep_until(next_wakeup)


def the_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        version=__version__,
    )

    app.include_router(health_router)
    return app


def main() -> None:
    """Main for worker loop"""
    uvicorn.run(
        "rail_pz_service.server.worker:the_app",
        host=config.asgi.host,
        port=config.asgi.port,
        reload=config.asgi.reload,
    )


if __name__ == "__main__":
    main()
