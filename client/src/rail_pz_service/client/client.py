"""Top level for python client API"""

from __future__ import annotations

from typing import Any

import httpx

from .algorithm import PZRailAlgorithmClient
from .catalog_tag import PZRailCatalogTagClient
from .dataset import PZRailDatasetClient
from .estimator import PZRailEstimatorClient
from .model import PZRailModelClient
from .request import PZRailRequestClient
from .object_ref import PZRailObjectRefClient
from .load import PZRailLoadClient

from .clientconfig import client_config

__all__ = ["CMClient"]


class PZRailClient:
    """Interface for accessing remote cm-service."""

    def __init__(self) -> None:
        client_kwargs: dict[str, Any] = {}
        client_kwargs["base_url"] = client_config.service_url
        if "auth_token" in client_config.model_fields_set:  # pragma: no cover
            client_kwargs["headers"] = {"Authorization": f"Bearer {client_config.auth_token}"}
        if "timeout" in client_config.model_fields_set:  # pragma: no cover
            client_kwargs["timeout"] = client_config.timeout
        if "cookies" in client_config.model_fields_set:  # pragma: no cover
            cookies = httpx.Cookies()
            if client_config.cookies:
                for cookie in client_config.cookies:
                    cookies.set(name=cookie.name, value=cookie.value)
            client_kwargs["cookies"] = cookies
        self._client = httpx.Client(**client_kwargs)

        self.algorithm = PZRailAlgorithmClient(self)
        self.campaign = PZRailCatalogTagClient(self)
        self.dataset = PZRailDatasetClient(self)
        self.estimator = PZRailEstimatorClient(self)
        self.model = PZRailModelClient(self)
        self.request = PZRailRequestClient(self)
        self.object_ref = PZRailObjectRefClient(self)

        self.load = PZRailLoadClient(self)

    @property
    def client(self) -> httpx.Client:
        """Return the httpx.Client"""
        return self._client
