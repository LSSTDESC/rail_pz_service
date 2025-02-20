from collections.abc import Iterable from typing import TYPE_CHECKING,
Any

from sqlalchemy import JSON
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey, UniqueConstraint

from .base import Base
from .row import RowMixin

if TYPE_CHECKING:
    from .estimator import Estimator


class Request(Base, ElementMixin):
    """Database table to keep track of photo-z algorithms

    Each `Request` refers to a particular instance of a
    `Request`
    
    """

    __tablename__ = "request"
    class_string = "request"

    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[str] = mapped_column(index=True)    
    estimator_id: = mapped_column(
        ForeignKey("estimator.id", ondelete="CASCADE"),
        index=True,
    )
    data: Mapped[dict | None] = mapped_column(type_=JSON)
    qp_file: Mapped[str | None] = mapped_column(default=None)

    time_created: Mapped[datetime] = mapped_column(type_=DateTime)
    time_updated: Mapped[datetime] = mapped_column(type_=DateTime)
    time_finished: Mapped[datetime | None] = mapped_column(type_=DateTime, default=None)

    col_names_for_table = ["id", "user", "estimator_id", "qp_file"]

    def __repr__(self) -> str:
        return f"Request {self.id} {self.user} {self.estimator_id} {self.qp_file}"
