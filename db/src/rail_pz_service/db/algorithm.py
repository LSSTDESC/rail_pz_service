"""Database model for Algorithm table"""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from rail_pz_service.common import models

from .base import Base
from .row import RowMixin

if TYPE_CHECKING:
    from .estimator import Estimator
    from .model import Model


class Algorithm(Base, RowMixin):
    """Database table to keep track of photo-z algorithms

    Each `Algorithm` refers to a particular `CatEstimator`
    subclass
    """

    __tablename__ = "algorithm"
    class_string = "algorithm"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True, unique=True)
    class_name: Mapped[str] = mapped_column()

    estimators_: Mapped["Estimator"] = relationship(
        "Estimator",
        primaryjoin="Algorithm.id==Estimator.algo_id",
        viewonly=True,
    )
    models_: Mapped["Model"] = relationship(
        "Model",
        primaryjoin="Algorithm.id==Model.algo_id",
        viewonly=True,
    )

    pydantic_mode_class = models.Algorithm

    col_names_for_table = pydantic_mode_class.col_names_for_table

    def __repr__(self) -> str:
        return f"Algorithm {self.name} {self.id} {self.class_name}"
