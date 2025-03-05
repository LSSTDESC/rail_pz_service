"""Pydantic model for the Algorithm"""

from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class RequestBase(BaseModel):
    """Request parameters that are in DB tables and also used to create new rows"""

    #: User who orginated this Request
    user: str | None = None


class RequestCreate(RequestBase):
    """Request Parameters that are used to create new rows but not in DB tables"""

    #: Name of the estimator
    estimator_name: str

    #: Name of the dataset
    dataset_name: str


class Request(RequestBase):
    """Basic processing unit in `rail_pz_service`.  A `Request` to generate
    per-galaxy p(z) for all of the object in a particular `Dataset`
    using specific `Estimator`.

    The output p(z) distribution will be stored in a qp file.

    This also store some metadata including timestamps and the user
    who intiated the `Request`.
    """

    model_config = ConfigDict(from_attributes=True)

    #: column names to use when printing the table
    col_names_for_table: ClassVar[list[str]] = [
        "id",
        "user",
        "estimator_id",
        "dataset_id",
        "qp_file_path",
    ]

    #: primary key
    id: int  #: primary key

    #: path to the output file
    qp_file_path: str | None = None

    #: foreign key into estimator table
    estimator_id: int

    #: foreign key into dataset table
    dataset_id: int

    #: timestamp of when the request was created in the DB
    time_created: datetime

    #: timestamp of when the request processing started by an Estimator
    time_started: datetime | None

    #: timestamp of when the request processing was finished
    time_finished: datetime | None
