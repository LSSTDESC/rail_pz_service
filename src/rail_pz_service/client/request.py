"""python for client API for managing Request tables"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from pydantic import TypeAdapter

from .. import models
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

    create = wrappers.create_row_function(ResponseModelClass, models.RequestCreate, f"{router_string}/create")
    delete = wrappers.delete_row_function(f"{router_string}")

    download = wrappers.download_file_function(f"{router_string}/download")

    def run(self, row_id: int) -> models.Request:
        """Run a request

        Parameters
        ----------
        request_id
            Id of the request in the Request table

        Returns
        -------
        Request
            Request in question

        Example
        -------

        .. code-block:: python

            client = RZRailClient()

            new_request = client.request.create(
                dataset_name='my_com_cam_dataset',
                estimator_name='my_gpz_com_cam_estimaor',
            )
            updated_request = client.request.run(
                new_request.id,
            )

        """

        full_query = f"{router_string}/run/{row_id}"
        results = self.client.post(full_query).raise_for_status().json()
        return TypeAdapter(ResponseModelClass).validate_python(results)
