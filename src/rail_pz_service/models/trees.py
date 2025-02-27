"""Pydantic model for the Catalog_tag"""

from __future__ import annotations

from pydantic import BaseModel

from .algorithm import Algorithm
from .catalog_tag import CatalogTag
from .dataset import Dataset
from .estimator import Estimator
from .model import Model
from .request import Request


class EstimatorLeaf(BaseModel):
    estimator: Estimator
    request: Request | None = None


class ModelLeaf(BaseModel):
    estimators: dict[int, EstimatorLeaf]

    model: Model


class AlgoLeaf(BaseModel):
    models: dict[int, ModelLeaf]

    algo: Algorithm


class CatalogTagDatasetTree(BaseModel):
    algos: dict[int, AlgoLeaf]

    dataset: Dataset | None
    catalog_tag: CatalogTag | None
    request_by_estimator: dict[int, Request]


class DatasetLeaf(BaseModel):
    requests: dict[int, Request]

    dataset: Dataset


class CatalogTagLeaf(BaseModel):
    algos: dict[int, AlgoLeaf]
    datasets: dict[int, DatasetLeaf]

    catalog_tag: CatalogTag | None

    def filter_for_dataset(
        self,
        dataset_id: int | None,
    ) -> CatalogTagDatasetTree:
        requests_for_dataset: dict[int, Request] = {}
        request_by_estimator: dict[int, Request] = {}
        if dataset_id is not None and dataset_id in self.datasets:
            the_dataset = self.datasets[dataset_id].dataset
            requests_for_dataset = self.datasets[dataset_id].requests
        else:
            the_dataset = None

        for request_ in requests_for_dataset.values():
            request_by_estimator[request_.estimator_id] = request_

        the_copy = CatalogTagDatasetTree(
            algos=self.algos,
            dataset=the_dataset,
            catalog_tag=self.catalog_tag,
            request_by_estimator=request_by_estimator,
        )

        if the_dataset is not None:
            for algo_ in the_copy.algos.values():
                for models_ in algo_.models.values():
                    for estimator_id, estimator_ in models_.estimators.items():
                        estimator_.request = request_by_estimator.get(estimator_id, None)
        return the_copy


class CatalogTagTree(BaseModel):
    catalog_tags: dict[str, CatalogTagLeaf]
