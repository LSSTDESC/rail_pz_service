"""Pydantic model for the Algorithm"""

from pydantic import BaseModel


class NameQuery(BaseModel):
    """Parameters needed to ask for a row my name"""

    # Name of the row, unique
    name: str


class LoadDatasetQuery(BaseModel):
    """Parameters needed to laod an dataset"""

    # Name for this Dataset, unique
    name: str

    # Path to the input file
    path: str

    # Associated catalog tag name
    catalog_tag_name: str


class LoadModelQuery(BaseModel):
    """Parameters needed to laod a model"""

    # Name for this Model, unique
    name: str

    # Path to the input file
    path: str

    # Associated algorithm name
    algo_name: str

    # Associated catalog tag name
    catalog_tag_name: str


class LoadEstimatorQuery(BaseModel):
    """Parameters needed to laod an estimator"""

    # Name for this Estimator, unique
    name: str

    # Associated model name
    model_name: str

    # configuration paramters
    config: dict | None = None
