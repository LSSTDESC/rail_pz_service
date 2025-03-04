"""Database model for Request table"""

from __future__ import annotations

import os
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, UniqueConstraint, select
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from .. import models
from ..common.errors import RAILMissingRowCreateInputError
from .base import Base
from .dataset import Dataset
from .estimator import Estimator
from .row import RowMixin


class Request(Base, RowMixin):
    pydantic_mode_class = models.Request
    __doc__ = pydantic_mode_class.__doc__

    __tablename__ = "request"
    class_string = "request"
    __table_args__ = (UniqueConstraint("estimator_id", "dataset_id", name="request_constraint"),)

    #: primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    #: User who orginated this Request
    user: Mapped[str] = mapped_column(index=True)

    #: foreign key into estimator table
    estimator_id: Mapped[int] = mapped_column(
        ForeignKey("estimator.id", ondelete="CASCADE"),
        index=True,
    )

    #: foreign key into dataset table
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("dataset.id", ondelete="CASCADE"),
        index=True,
    )

    #: path to the output file
    qp_file_path: Mapped[str | None] = mapped_column(default=None)

    #: timestamp of when the request was created in the DB
    time_created: Mapped[datetime] = mapped_column(type_=DateTime)

    #: timestamp of when the request processing started by an `Estimator`
    time_started: Mapped[datetime | None] = mapped_column(type_=DateTime, default=None)

    #: timestamp of when the request processing was finished
    time_finished: Mapped[datetime | None] = mapped_column(type_=DateTime, default=None)

    #: Access to associated `Estimator`
    estimator_: Mapped[Estimator] = relationship(
        "Estimator",
        primaryjoin="Request.estimator_id==Estimator.id",
        viewonly=True,
    )

    #: Access to associated `Dataset`
    dataset_: Mapped[Dataset] = relationship(
        "Dataset",
        primaryjoin="Request.dataset_id==Dataset.id",
        viewonly=True,
    )

    #: column names to use when printing the table
    col_names_for_table = pydantic_mode_class.col_names_for_table

    def __repr__(self) -> str:
        return f"Request {self.id} {self.user} {self.estimator_id} {self.dataset_id} {self.qp_file_path}"

    @classmethod
    async def get_create_kwargs(
        cls,
        session: async_scoped_session,
        **kwargs: Any,
    ) -> dict:
        user = kwargs.get("user", None)
        if user is None:
            user = os.environ["USER"]

        dataset_id = kwargs.get("dataset_id", None)
        if dataset_id is None:
            try:
                dataset_name = kwargs["dataset_name"]
            except KeyError as e:
                raise RAILMissingRowCreateInputError(f"Missing input to create Group: {e}") from e
            dataset_ = await Dataset.get_row_by_name(session, dataset_name)
            dataset_id = dataset_.id

        estimator_id = kwargs.get("estimator_id", None)
        if estimator_id is None:
            try:
                estimator_name = kwargs["estimator_name"]
            except KeyError as e:
                raise RAILMissingRowCreateInputError(f"Missing input to create Group: {e}") from e
            estimator_ = await Estimator.get_row_by_name(session, estimator_name)
            estimator_id = estimator_.id

        time_created = datetime.now()

        return dict(
            user=user,
            estimator_id=estimator_id,
            dataset_id=dataset_id,
            time_created=time_created,
        )

    @classmethod
    async def get_open_requests(
        cls,
        session: async_scoped_session,
    ) -> Sequence[Request]:
        q = select(cls)
        q = q.filter(cls.time_started.is_(None)).order_by(cls.time_created.desc())
        results = await session.scalars(q)
        return results.all()
