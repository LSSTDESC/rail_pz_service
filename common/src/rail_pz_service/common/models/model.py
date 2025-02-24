"""Pydantic model for the Algorithm"""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class ModelBase(BaseModel):
    """Model parameters that are in DB tables and also used to create new rows"""

    # Name for this Model, unique
    name: str

    # path to associated file
    path: str


class ModelCreate(ModelBase):
    """Model Parameters that are used to create new rows but not in DB tables"""

    # Name of the algorithm
    algo_name: str

    # Name of the associated catalog tag
    catalog_tag_name: str


class Model(ModelBase):
    """Model Parameters that are in DB tables and not used to create new rows"""

    model_config = ConfigDict(from_attributes=True)

    col_names_for_table: ClassVar[list[str]] = [
        "id",
        "name",
        "algo_id",
        "catalog_tag_id",
        "path",
    ]

    # primary key
    id: int

    # foreign key into algorithm table
    algo_id: int

    # foreign key into catalog_tag table
    catalog_tag_id: int
