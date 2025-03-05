from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from safir.dependencies.db_session import db_session_dependency
from safir.dependencies.http_client import http_client_dependency
from safir.logging import configure_logging, configure_uvicorn_logging
from safir.middleware.x_forwarded import XForwardedMiddleware

from .. import __version__
from ..config import config
from .logging import LOGGER
from .routers import (
    healthz,
    index,
    v1,
)
from .web_app import web_app

configure_uvicorn_logging(config.logging.level)
configure_logging(
    profile=config.logging.profile,
    log_level=config.logging.level,
    name=config.asgi.title,
)
logger = LOGGER.bind(module=__name__)


tags_metadata = [
    {
        "name": "Load",
        "description": "Operations that load Objects in to the DB.",
    },
    {
        "name": "Request",
        "description": "Operations with `Request`s. A `Request` runs a single `Estimator` or a single "
        "`Dataset` and keeps track of the resulting data products.",
    },
    {
        "name": "Algorithm",
        "description": "Operations with `Algorithms`s. An `Algorithm` is a particular python class "
        "that implements a p(z) estimation algorithm. `Algorithm`s must be uniquely named.",
    },
    {
        "name": "CatalogTag",
        "description": "Operations with `CatalogTag`s. A `CatalogTag` is a particular python class that "
        "ensapsulates the information needed to configure `Algorithm`s to run on particular `Dataset`s, "
        "such as the names of the columns with magntidue information. `CatalogTag`s must be uniquely named.",
    },
    {
        "name": "Model",
        "description": "Operations with `Model`s. A `Model` is a specfic machine-learning model trained "
        "for a particular `Algorithms` and applicable to a particular `Dataset`. `Models`s must be uniquely "
        "named.",
    },
    {
        "name": "Estimator",
        "description": "Operations with `Estimator`s. An `Estimator` is a particular instance of an "
        "`Algorithm` associated to a particular `Model` and `CatalogTag` and possibly overridding some "
        "configuration parameters.  `Estimator`s must be uniquely named.",
    },
    {
        "name": "Dataset",
        "description": "Operations with `Dataset`s. A `Dataset` contains the photometric information about "
        "several objects, and can be passed to to an `Estimator` to obtain p(z) estimates. `Dataset`s must "
        "be uniquely named.",
    },
    {
        "name": "ObjectRef",
        "description": "Operations with `ObjectRef`s.  And `ObjectRef` is a single object within a dataset.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Hook FastAPI init/cleanups."""
    app.state.tasks = set()
    # Dependency inits before app starts running
    await db_session_dependency.initialize(config.db.url, config.db.password)
    assert db_session_dependency._engine is not None  # pylint: disable=protected-access
    db_session_dependency._engine.echo = (  # pylint: disable=protected-access
        config.db.echo
    )

    # App runs here...
    yield

    # Dependency cleanups after app is finished
    await db_session_dependency.aclose()
    await http_client_dependency.aclose()


the_app = FastAPI(
    lifespan=lifespan,
    title=config.asgi.title,
    version=__version__,
    openapi_url="/docs/openapi.json",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url=None,
)

the_app.add_middleware(XForwardedMiddleware)

the_app.include_router(healthz.health_router, prefix="")
the_app.include_router(index.router, prefix="")
the_app.include_router(v1.router, prefix=config.asgi.prefix)

# Start the frontend web application.
the_app.mount(config.asgi.frontend_prefix, web_app)


def main() -> None:
    logger.info(f"Server starting {config.asgi.host}:{config.asgi.port}{config.asgi.frontend_prefix}")
    uvicorn.run(
        "rail_pz_service.server.main:the_app",
        host=config.asgi.host,
        port=config.asgi.port,
        reload=config.asgi.reload,
    )


if __name__ == "__main__":
    main()
