"""python for client API for managing Request tables"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

import httpx
from rail_pz_server.common import models

from . import wrappers

if TYPE_CHECKING:
    from .client import PZRailClient

# Template specialization
# Specify the pydantic model for Step
ResponseModelClass = models.Request

# Construct derived templates
router_string = "request"


class PZRailRequestClient:
    """Interface for accessing remote pz-rail-service to manipulate
    Request Tables
    """

    def __init__(self, parent: PZRailClient) -> None:
        self._client = parent.client

    @property
    def client(self) -> httpx.Client:
        """Return the httpx.Client"""
        return self._client

    # Add functions to the client class
    get_rows = wrappers.get_rows_function(ResponseModelClass, f"{router_string}/list")

    get_row = wrappers.get_row_function(ResponseModelClass, f"{router_string}/get")

    get_row_by_name = wrappers.get_row_by_name_function(
        ResponseModelClass, f"{router_string}/get_row_by_name"
    )

    def run(self, row_id: int) -> models.Request:
        full_query = f"run/{row_id}"
        results = self.client.post(full_query).raise_for_status().json()
        return TypeAdapter(ResponseModelClass).validate_python(results)
