"""python for client API for loading dataing into pz-rail-service"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
from pydantic import TypeAdapter

from .. import models

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

    def dataset(self, **kwargs: Any) -> models.Dataset:
        full_query = "load/dataset"
        content = models.LoadDatasetQuery(**kwargs).model_dump_json()
        results = self.client.post(full_query, content=content).raise_for_status().json()
        return TypeAdapter(models.Dataset).validate_python(results)

    def model(self, **kwargs: Any) -> models.Model:
        full_query = "load/model"
        content = models.LoadModelQuery(**kwargs).model_dump_json()
        results = self.client.post(full_query, content=content).raise_for_status().json()
        return TypeAdapter(models.Model).validate_python(results)

    def estimator(self, **kwargs: Any) -> models.Estimator:
        full_query = "load/estimator"
        content = models.LoadEstimatorQuery(**kwargs).model_dump_json()
        results = self.client.post(full_query, content=content).raise_for_status().json()
        return TypeAdapter(models.Estimator).validate_python(results)
