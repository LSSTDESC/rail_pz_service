"""Database model for Algorithm table"""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .. import models
from .base import Base
from .row import RowMixin

if TYPE_CHECKING:
    from .estimator import Estimator
    from .model import Model


class Algorithm(Base, RowMixin):
    pydantic_mode_class = models.Algorithm
    __doc__ = pydantic_mode_class.__doc__

    __tablename__ = "algorithm"
    class_string = "algorithm"

    #: primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    #: Name for this Algorithm, unique
    name: Mapped[str] = mapped_column(index=True, unique=True)

    #: Name for the python class implementing the algorithm
    class_name: Mapped[str] = mapped_column()

    #: Access to list of associated `Estimator`
    estimators_: Mapped[list["Estimator"]] = relationship(
        "Estimator",
        primaryjoin="Algorithm.id==Estimator.algo_id",
        viewonly=True,
    )

    #: Access to list of associated `Model`
    models_: Mapped[list["Model"]] = relationship(
        "Model",
        primaryjoin="Algorithm.id==Model.algo_id",
        viewonly=True,
    )

    #: column names to use when printing the table
    col_names_for_table = pydantic_mode_class.col_names_for_table

    def __repr__(self) -> str:
        return f"Algorithm {self.name} {self.id} {self.class_name}"
