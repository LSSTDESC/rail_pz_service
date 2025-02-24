"""python for client API for loading dataing into pz-rail-service"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

import httpx
from rail_pz_server.common import models

if TYPE_CHECKING:
    from .client import PZRailClient


class PZRailLoadClient:
    """Interface for accessing remote pz-rail-service to load data"""

    def __init__(self, parent: PZRailClient) -> None:
        self._client = parent.client

    @property
    def client(self) -> httpx.Client:
        """Return the httpx.Client"""
        return self._client

    def dataset(self) -> models.Dataset:
        full_query = "load/dataset"
        results = self.client.post(full_query).raise_for_status().json()
        return TypeAdapter(models.Dataset).validate_python(results)

    def model(self) -> models.Model:
        full_query = "load/model"
        results = self.client.post(full_query).raise_for_status().json()
        return TypeAdapter(models.Dataset).validate_python(results)

    def estimator(self) -> models.Estimator:
        full_query = "load/estimator"
        results = self.client.post(full_query).raise_for_status().json()
        return TypeAdapter(models.Estimator).validate_python(results)
