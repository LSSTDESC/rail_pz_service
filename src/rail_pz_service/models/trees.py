"""Pydantic model for the Catalog_tag"""

from __future__ import annotations

from pydantic import BaseModel

from .algorithm import Algorithm
from .catalog_tag import CatalogTag
from .dataset import Dataset
from .estimator import Estimator
from .model import Model
from .request import Request


class ModelLeaf(BaseModel):
    estimators: dict[int, Estimator]

    model: Model


class AlgoLeaf(BaseModel):
    models: dict[int, ModelLeaf]

    algo: Algorithm


class DatasetLeaf(BaseModel):
    requests: dict[int, Request]

    dataset: Dataset


class CatalogTagLeaf(BaseModel):
    algos: dict[int, AlgoLeaf]
    datasets: dict[int, DatasetLeaf]

    catalog_tag: CatalogTag | None


class CatalogTagTree(BaseModel):
    catalog_tags: dict[str, CatalogTagLeaf]
