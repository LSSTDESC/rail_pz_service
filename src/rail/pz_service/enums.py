# pylint: disable=invalid-name
from __future__ import annotations

import enum


class TableEnum(enum.Enum):
    """Keep track of the various tables"""

    algorithm = 0
    catalog_tag = 1
    estimator = 2
    model = 3
    request = 4
