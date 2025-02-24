"""Database model for Request table"""

import os
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from rail_pz_service.common import models

from rail_pz_service.common.errors import RAILMissingRowCreateInputError

from .base import Base
from .dataset import Dataset
from .estimator import Estimator
from .row import RowMixin


class Request(Base, RowMixin):
    """Database table to keep track of photo-z algorithms

    Each `Request` refers to a particular instance of a
    `Request`

    """

    __tablename__ = "request"
    class_string = "request"

    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[str] = mapped_column(index=True)
    estimator_id: Mapped[int] = mapped_column(
        ForeignKey("estimator.id", ondelete="CASCADE"),
        index=True,
    )
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("dataset.id", ondelete="CASCADE"),
        index=True,
    )
    qp_file_path: Mapped[str | None] = mapped_column(default=None)

    time_created: Mapped[datetime] = mapped_column(type_=DateTime)
    time_finished: Mapped[datetime | None] = mapped_column(type_=DateTime, default=None)

    estimator_: Mapped["Estimator"] = relationship(
        "Estimator",
        primaryjoin="Request.estimator_id==Estimator.id",
        viewonly=True,
    )
    dataset_: Mapped["Dataset"] = relationship(
        "Dataset",
        primaryjoin="Request.dataset_id==Dataset.id",
        viewonly=True,
    )

    pydantic_mode_class = models.Request

    col_names_for_table = pydantic_mode_class.col_names_for_table

    def __repr__(self) -> str:
        return f"Request {self.id} {self.user} {self.estimator_id} {self.dataset_id} {self.qp_file_path}"

    @classmethod
    async def get_create_kwargs(
        cls,
        session: async_scoped_session,
        **kwargs: Any,
    ) -> dict:
        user = kwargs.get("user", os.environ["USER"])

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
