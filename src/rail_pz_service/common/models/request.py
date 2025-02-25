"""Pydantic model for the Algorithm"""

from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class RequestBase(BaseModel):
    """Request parameters that are in DB tables and also used to create new rows"""

    # User who orginated this Request
    user: str | None = None


class RequestCreate(RequestBase):
    """Request Parameters that are used to create new rows but not in DB tables"""

    # Name of the estimator
    estimator_name: str

    # Name of the dataset
    dataset_name: str


class Request(RequestBase):
    """Request Parameters that are in DB tables and not used to create new rows"""

    model_config = ConfigDict(from_attributes=True)

    col_names_for_table: ClassVar[list[str]] = [
        "id",
        "user",
        "estimator_id",
        "dataset_id",
        "qp_file_path",
    ]

    # primary key
    id: int

    # path to the output file
    qp_file_path: str | None = None

    # foreign key into estimator table
    estimator_id: int

    # foreign key into dataset table
    dataset_id: int

    # timestamps
    time_created: datetime
    time_started: datetime | None
    time_finished: datetime | None
