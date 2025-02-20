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
    from .catalog_tag import CatalogTag
    from .model import Model


class Estimator(Base, RowMixin):
    """Database table to keep track of photo-z algorithms

    Each `Estimator` refers to a particular instance of a
    `CatEstimator`
    
    """

    __tablename__ = "estimator"
    class_string = "estimator"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    algo_id: = mapped_column(
        ForeignKey("algorithm.id", ondelete="CASCADE"),
        index=True,
    )
    catalog_tag_id: = mapped_column(
        ForeignKey("catalog_tag.id", ondelete="CASCADE"),
        index=True,
    )
    model_id: = mapped_column(
        ForeignKey("model.id", ondelete="CASCADE"),
        index=True,
    )
    config: Mapped[dict | None] = mapped_column(type_=JSON)

    algo_:  Mapped["Algorithm"] = relationship(
        "Algorithm",
        primaryjoin="Estimator.algo_id==Algorithm.id",
        viewonly=True,
    )
    catalog_tag_:  Mapped["CatalogTag"] = relationship(
        "CatalogTag",
        primaryjoin="Estimator.catalog_tag_id==CatalogTag.id",
        viewonly=True,
    )
    model_:  Mapped["Model"] = relationship(
        "Model",
        primaryjoin="Estimator.model_id==Model.id",
        viewonly=True,
    )

    col_names_for_table = ["id", "name"]

    def __repr__(self) -> str:
        return f"Estimator {self.name} {self.id}"
