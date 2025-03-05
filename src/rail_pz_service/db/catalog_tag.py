"""Database model for CatalogTag table"""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .. import models
from .base import Base
from .row import RowMixin

if TYPE_CHECKING:
    from .dataset import Dataset
    from .estimator import Estimator
    from .model import Model


class CatalogTag(Base, RowMixin):
    pydantic_mode_class = models.CatalogTag
    __doc__ = pydantic_mode_class.__doc__

    __tablename__ = "catalog_tag"
    class_string = "catalog_tag"

    #: primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    #: Name for this CatalogTag, unique
    name: Mapped[str] = mapped_column(index=True, unique=True)

    #: Name for the python class implementing the CatalogTag
    class_name: Mapped[str] = mapped_column()

    #: Access to list of associated `Estimator`
    estimators_: Mapped[list["Estimator"]] = relationship(
        "Estimator",
        primaryjoin="CatalogTag.id==Estimator.catalog_tag_id",
        viewonly=True,
    )

    #: Access to list of associated `Model`
    models_: Mapped[list["Model"]] = relationship(
        "Model",
        primaryjoin="CatalogTag.id==Model.catalog_tag_id",
        viewonly=True,
    )

    #: Access to list of associated `Dataset`
    datasets_: Mapped[list["Dataset"]] = relationship(
        "Dataset",
        primaryjoin="CatalogTag.id==Dataset.catalog_tag_id",
        viewonly=True,
    )

    #: column names to use when printing the table
    col_names_for_table = pydantic_mode_class.col_names_for_table

    def __repr__(self) -> str:
        return f"CatalogTag {self.name} {self.id} {self.class_name}"
