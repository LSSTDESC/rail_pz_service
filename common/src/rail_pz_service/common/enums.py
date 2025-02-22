""" Common enums for pz-rail-service related packages"""

# pylint: disable=invalid-name
from __future__ import annotations

import enum


class TableEnum(enum.Enum):
    """Keep track of the various tables"""

    algorithm = 0
    catalog_tag = 1
    estimator = 2
    model = 3
    dataset = 4
    request = 5
    object_ref = 6
