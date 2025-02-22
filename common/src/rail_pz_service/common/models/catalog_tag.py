"""Pydantic model for the Catalog_tag"""

from pydantic import BaseModel, ConfigDict


class CatalogTagBase(BaseModel):
    """CatalogTag parameters that are in DB tables and also used to create new rows"""

    # Name for this Catalog_tag, unique
    name: str

    # Name for the python class implementing the catalog_tag
    class_name: str


class CatalogTagCreate(CatalogTagBase):
    """CatalogTag Parameters that are used to create new rows but not in DB tables"""


class CatalogTag(CatalogTagBase):
    """CatalogTag Parameters that are in DB tables and not used to create new rows"""

    model_config = ConfigDict(from_attributes=True)

    # primary key
    id: int
