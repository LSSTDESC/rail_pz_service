"""Pydantic model for the ObjectRef"""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class ObjectRefBase(BaseModel):
    """ObjectRef parameters that are in DB tables and also used to create new rows"""

    # Name for this ObjectRef, unique
    name: str

    # Index of the object inside the dataset
    index: int


class ObjectRefCreate(ObjectRefBase):
    """ObjectRef Parameters that are used to create new rows but not in DB tables"""

    # Name of the associated dataset
    dataset_name: str


class ObjectRef(ObjectRefBase):
    """Objectref Parameters that are in DB tables and not used to create new rows"""

    model_config = ConfigDict(from_attributes=True)

    col_names_for_table: ClassVar[list[str]] = ["id", "name", "dataset_id", "index"]

    # primary key
    id: int

    # foreign key into dataset table
    dataset_id: int
