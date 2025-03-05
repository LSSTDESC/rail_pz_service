import os
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
import pytest_asyncio
import structlog
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pytest import TempPathFactory
from safir.database import create_database_engine, initialize_database
from safir.testing.uvicorn import UvicornProcess, spawn_uvicorn
from sqlalchemy.ext.asyncio import AsyncEngine

from rail_pz_service import db
from rail_pz_service.common import test_files
from rail_pz_service.config import config as config_
from rail_pz_service.server import main


@pytest_asyncio.fixture(name="engine")
async def engine_fixture() -> AsyncIterator[AsyncEngine]:
    """Return a SQLAlchemy AsyncEngine configured to talk to the app db."""
    logger = structlog.get_logger(__name__)
    the_engine = create_database_engine(config_.db.url, config_.db.password)
    await initialize_database(the_engine, logger, schema=db.Base.metadata, reset=True)
    yield the_engine
    await the_engine.dispose()


@pytest_asyncio.fixture(name="app")
async def app_fixture() -> AsyncIterator[FastAPI]:
    """Return a configured test application.

    Wraps the application in a lifespan manager so that startup and shutdown
    events are sent during test execution.
    """
    async with LifespanManager(main.the_app):
        yield main.the_app


@pytest_asyncio.fixture(name="client")
async def client_fixture(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https:") as the_client:
        yield the_client


@pytest_asyncio.fixture(name="uvicorn")
async def uvicorn_fixture(
    tmp_path_factory: TempPathFactory,
) -> AsyncIterator[UvicornProcess]:
    """Spawn and return a uvicorn process hosting the test app."""
    my_uvicorn = spawn_uvicorn(
        working_directory=tmp_path_factory.mktemp("uvicorn"),
        app="rail_pz_service.server.main:the_app",
        timeout=10,
    )
    yield my_uvicorn
    my_uvicorn.process.terminate()


@pytest.fixture(name="setup_test_area", scope="session")
def setup_test_area(request: pytest.FixtureRequest) -> int:
    ret_val = test_files.setup_test_area()

    config_.storage.archive = os.path.abspath(
        os.path.join("tests", "temp_data"),
    )

    request.addfinalizer(test_files.teardown_test_area)

    return ret_val


def pytest_addoption(parser: Any) -> None:
    parser.addoption(
        "--run-playwright",
        action="store_true",
        default=False,
        help="run playwright tests",
    )


def pytest_configure(config: Any) -> None:
    config.addinivalue_line("markers", "playwright: mark test as a playwright test")


def pytest_collection_modifyitems(config: Any, items: Iterator) -> None:
    if config.getoption("--run-playwright"):
        # --run-playwright given in cli: do not skip playwright
        return
    skip_playwright = pytest.mark.skip(reason="need --run-playwright option to run")
    for item in items:
        if "playwright" in item.keywords:
            item.add_marker(skip_playwright)
