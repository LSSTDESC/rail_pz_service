from collections.abc import Callable
from enum import Enum, auto
from functools import partial, wraps
from typing import Any, cast

import click
from click.decorators import FC

from rail_pz_service.client.client import PZRailClient


def pz_client() -> Callable[[FC], FC]:
    """Pass a freshly constructed PZRailClient to a decorated click Command without
    adding/requiring a corresponding click Option"""

    def decorator(f: FC) -> FC:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            kwargs["client"] = PZRailClient()
            return f(*args, **kwargs)

        return cast(FC, wrapper)

    return decorator
