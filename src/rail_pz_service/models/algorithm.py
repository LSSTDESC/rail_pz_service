"""Pydantic model for the Algorithm"""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class AlgorithmBase(BaseModel):
    """Algorithm parameters that are in DB tables and also used to create new rows"""

    #: Name for this Algorithm, unique
    name: str

    #: Name for the python class implementing the algorithm
    class_name: str


class AlgorithmCreate(AlgorithmBase):
    """Algorithm Parameters that are used to create new rows but not in DB tables"""


class Algorithm(AlgorithmBase):
    """Algorithm is wrapper for a specific RAIL class
    that implements a particular p(z) estimation algorithm.

    This just defines the particular python class implementing
    the algorithm.  The selection of a particular instance of the
    training `Model` and any non-default a parameters used to
    initialze an `Estimator` are handled in their own classes.
    """

    model_config = ConfigDict(from_attributes=True)

    #: column names to use when printing the table
    col_names_for_table: ClassVar[list[str]] = ["id", "name", "class_name"]

    #: primary key
    id: int
