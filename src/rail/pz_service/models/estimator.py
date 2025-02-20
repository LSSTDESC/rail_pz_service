"""Pydantic model for the Algorithm"""

from pydantic import BaseModel, ConfigDict


class EstimatorBase(BaseModel):
    """Estimator parameters that are in DB tables and also used to create new rows"""

    # Name for this Estimator, unique
    name: str

    # Configuration parameters for this estimator
    config: dict | None = None


class EstimatorCreate(EstimatorBase):
    """Estimator Parameters that are used to create new rows but not in DB tables"""

    # Name of the algorithm
    algo_name: str

    # Name of the catalog_tag
    catalog_tag_name: str

    # Name of the model
    model_name: str


class Estimator(EstimatorBase):
    """Estimator Parameters that are in DB tables and not used to create new rows"""

    model_config = ConfigDict(from_attributes=True)

    # primary key
    id: int

    # foreign key into catalog_tag table
    catalog_id: int

    # foreign key into catalog_tag table
    catalog_tag_id: int

    # foreign key into algorithm table
    algo_id: int
