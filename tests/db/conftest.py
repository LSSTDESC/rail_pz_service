import importlib
import sys
from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True, scope="function")
def import_deps() -> Generator:
    _ = importlib.import_module("rail_pz_service.common")
    yield
    del sys.modules["rail_pz_service.common"]
