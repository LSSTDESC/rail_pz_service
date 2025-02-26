"""python for client API for managing CatalogTag tables"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from .. import models
from . import wrappers

if TYPE_CHECKING:
    from .client import PZRailClient

# Template specialization
# Specify the pydantic model for Step
ResponseModelClass = models.CatalogTag

# Construct derived templates
router_string = "catalog_tag"


class PZRailCatalogTagClient:
    """Interface for accessing remote pz-rail-service to manipulate
    CatalogTag Tables
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

    get_estimators = wrappers.get_row_attribute_list_function(
        list[models.Estimator],
        f"{router_string}/get",
        "estimators",
    )

    get_models = wrappers.get_row_attribute_list_function(
        list[models.Model], f"{router_string}/get", "models"
    )

    get_datasets = wrappers.get_row_attribute_list_function(
        list[models.Dataset], f"{router_string}/get", "datasets"
    )
