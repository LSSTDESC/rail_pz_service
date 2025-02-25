"""Options for rail_admin CLI"""

from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from click.decorators import FC

# using safir to set things up
# from safir.database import create_database_engine
# setting stuff up directly from sqlalchemy
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ...config import config as db_config


def _make_engine() -> AsyncEngine:
    # engine = create_database_engine(db_config.database_url,
    # db_config.database_password)
    engine = create_async_engine(db_config.db.url)
    return engine


def db_engine() -> Callable[[FC], FC]:
    """Pass a freshly constructed DB session to a decorated click Command without
    adding/requiring a corresponding click Option"""

    def decorator(f: FC) -> FC:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            kwargs["db_engine"] = _make_engine
            return f(*args, **kwargs)

        return cast(FC, wrapper)

    return decorator
