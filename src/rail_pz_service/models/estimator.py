"""Pydantic model for the Algorithm"""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class EstimatorBase(BaseModel):
    """Estimator parameters that are in DB tables and also used to create new rows"""

    #: Name for this Estimator, unique
    name: str

    #: Configuration parameters for this estimator
    config: dict | None = None


class EstimatorCreate(EstimatorBase):
    """Estimator Parameters that are used to create new rows but not in DB tables"""

    #: Name of the model, unique
    model_name: str


class Estimator(EstimatorBase):
    """Combinination of an `Algorithm` to run a trained `Model` to apply to the
    data, and any specific configuration overrides.
    """

    model_config = ConfigDict(from_attributes=True)

    #: column names to use when printing the table
    col_names_for_table: ClassVar[list[str]] = [
        "id",
        "name",
        "algo_id",
        "catalog_tag_id",
        "model_id",
    ]

    #: primary key
    id: int

    #: foreign key into algorithm table
    algo_id: int

    #: foreign key into catalog_tag table
    catalog_tag_id: int

    #: foreign key into model table
    model_id: int
