"""python for client API for loading dataing into pz-rail-service"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from rail_pz_server.common import models
from rail_pz_server import db

from . import wrappers


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
        return
    
        
    def model(self) -> models.Model:
        return


    def estimator(self) -> models.Estimator:
        return

