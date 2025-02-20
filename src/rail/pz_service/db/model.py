from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey, UniqueConstraint

from .base import Base
from .row import RowMixin

if TYPE_CHECKING:
    from .algorithm import Algorithm
    from .estimator import Estimator


class Model(Base, ElementMixin):
    """Database table to keep track of photo-z algorithms

    Each `Model` refers to a particular instance of a
    `Model`
    
    """

    __tablename__ = "model"
    class_string = "model"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)    
    algo_id: = mapped_column(
        ForeignKey("algorithm.id", ondelete="CASCADE"),
        index=True,
    )

    algo_:  Mapped["Algorithm"] = relationship(
        "Algorithm",
        primaryjoin="Model.algo_id==Algorithm.id",
        viewonly=True,
    )
    estimators_:  Mapped["Estimator"] = relationship(
        "Estimator",
        primaryjoin="Model.id==Estimator.model_id",
        viewonly=True,
    )

    col_names_for_table = ["id", "name"]

    def __repr__(self) -> str:
        return f"Model {self.name} {self.id} {self.python_class}"
