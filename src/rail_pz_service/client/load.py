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
        """Load a `Dataset` into the database

        Parameters
        ----------
        **kwargs
            Input parameter.  Must match `LoadDatasetQuery`

        Returns
        -------
        models.Dataset
            Newly created and loaded dataset

        Example
        -------

        .. code-block:: python

            client = RZRailClient()
            new_dataset = client.load.dataset(
                name='my_com_cam_dataset',
                path='local_version_of_data_file.hdf5',
                catalog_tag_name='com_cam',
            )

            or

            data = dict(
                LSST_Obs_u=24.5,
                LSST_Obs_g=24.5,
                LSST_Obs_r=24.5,
                LSST_Obs_i=24.5,
                LSST_Obs_z=24.5,
                LSST_Obs_y=24.5,
                LSST_Obs_u_err=0.5,
                LSST_Obs_g_err=0.5,
                LSST_Obs_r_err=0.5,
                LSST_Obs_i_err=0.5,
                LSST_Obs_z_err=0.5,
                LSST_Obs_y_err=0.5,
            )
            client = RZRailClient()
            new_dataset = client.load.dataset(
                name='my_com_cam_dataset',
                data=data,
                catalog_tag_name='com_cam',
            )


        """
        full_query = "load/dataset"
        content = models.LoadDatasetQuery(**kwargs).model_dump_json()
        results = self.client.post(full_query, content=content).raise_for_status().json()
        return TypeAdapter(models.Dataset).validate_python(results)

    def model(self, **kwargs: Any) -> models.Model:
        """Load a `Model` into the database

        Parameters
        ----------
        **kwargs
            Input parameter.  Must match `LoadModelQuery`

        Returns
        -------
        models.Model
            Newly created and loaded model

        Example
        -------

        .. code-block:: python

            client = RZRailClient()
            new_model = client.load.model(
                name='my_gpz_com_cam_model',
                path='local_version_of_file.pkl',
                algo_name='GPZEstimator',
                catalog_tag_name='com_cam',
            )
        """
        full_query = "load/model"
        content = models.LoadModelQuery(**kwargs).model_dump_json()
        results = self.client.post(full_query, content=content).raise_for_status().json()
        return TypeAdapter(models.Model).validate_python(results)

    def estimator(self, **kwargs: Any) -> models.Estimator:
        """Load a `Estimator` into the database

        Parameters
        ----------
        **kwargs
            Input parameter.  Must match `LoadEstimatorQuery`

        Returns
        -------
        models.Estimator
            Newly created and loaded estimator

        Example
        -------

        .. code-block:: python

            client = RZRailClient()
            new_estimator = client.load.estimator(
                name='my_gpz_com_cam_estimator',
                model_name='my_gpz_com_cam_model',
            )
        """
        full_query = "load/estimator"
        content = models.LoadEstimatorQuery(**kwargs).model_dump_json()
        results = self.client.post(full_query, content=content).raise_for_status().json()
        return TypeAdapter(models.Estimator).validate_python(results)
