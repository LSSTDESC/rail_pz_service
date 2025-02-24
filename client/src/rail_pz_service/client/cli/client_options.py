from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from click.decorators import FC

from rail_pz_service.client.client import PZRailClient


def pz_client() -> Callable[[FC], FC]:
    """Pass a freshly constructed PZRailClient to a decorated click Command without
    adding/requiring a corresponding click Option"""

    def decorator(f: FC) -> FC:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            kwargs["pz_client"] = PZRailClient()
            return f(*args, **kwargs)

        return cast(FC, wrapper)

    return decorator
