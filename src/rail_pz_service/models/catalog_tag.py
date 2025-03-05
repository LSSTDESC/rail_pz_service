"""Pydantic model for the Catalog_tag"""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class CatalogTagBase(BaseModel):
    """CatalogTag parameters that are in DB tables and also used to create new rows"""

    #: Name for this Catalog_tag, unique
    name: str

    #: Name for the python class implementing the catalog_tag
    class_name: str


class CatalogTagCreate(CatalogTagBase):
    """CatalogTag Parameters that are used to create new rows but not in DB tables"""


class CatalogTag(CatalogTagBase):
    """Defines what kind of catalog we are analyzing data from.
    Specifically what to expect for the names of the magnitude columns.

    This is implemented in the `rail.utils.catalog_utils` module,
    which uses a catalog tag to set the default parameters for
    RAIL modules to match the catalog.
    """

    model_config = ConfigDict(from_attributes=True)

    #: column names to use when printing the table
    col_names_for_table: ClassVar[list[str]] = ["id", "name", "class_name"]

    #: primary key
    id: int
