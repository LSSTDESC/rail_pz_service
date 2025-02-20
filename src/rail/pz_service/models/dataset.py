"""Pydantic model for the Dataset"""

from pydantic import BaseModel, ConfigDict


class DatasetBase(BaseModel):
    """Dataset parameters that are in DB tables and also used to create new rows"""

    # Name for this Dataset, unique
    name: str

    # Path to the relevant file (could be None)
    path: str | None = None

    # Data for the dataset (could be None)
    data: dict | None = None


class DatasetCreate(DatasetBase):
    """Dataset Parameters that are used to create new rows but not in DB tables"""

    # Name of the associated catalog tag
    catalog_tag_name: str


class Dataset(DatasetBase):
    """Dataset Parameters that are in DB tables and not used to create new rows"""

    model_config = ConfigDict(from_attributes=True)

    # primary key
    id: int

    # foreign key into catalog_tag table
    catalog_tag_id: int

    # Number of objects in the dataset
    n_objects: int
