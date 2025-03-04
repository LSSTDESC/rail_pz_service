"""Pydantic model for the Dataset"""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class DatasetBase(BaseModel):
    """Dataset parameters that are in DB tables and also used to create new rows"""

    #: Name for this Dataset, unique
    name: str

    #: Path to the relevant file (could be None)
    path: str | None = None

    #: Data for the dataset (could be None)
    data: dict | None = None

    #: Number of objects in the dataset
    n_objects: int | None


class DatasetCreate(DatasetBase):
    """Dataset Parameters that are used to create new rows but not in DB tables"""

    #: Name of the associated catalog tag
    catalog_tag_name: str

    #: Validate the files before loading
    validate_file: bool = False


class Dataset(DatasetBase):
    """Color data about set of objects that can be used to obtain
    p(z) esimates.

    It is asscoated with a `CatalogTag` that defines which columns
    names to expect.

    It can either be stored in a file (for larger datasets) or as a
    python dict (for small datasets of a few objects, useful when
    uploading things on the fly
    """

    model_config = ConfigDict(from_attributes=True)

    #: column names to use when printing the table
    col_names_for_table: ClassVar[list[str]] = [
        "id",
        "name",
        "n_objects",
        "catalog_tag_id",
        "path",
    ]

    #: primary key
    id: int

    #: foreign key into catalog_tag table
    catalog_tag_id: int
