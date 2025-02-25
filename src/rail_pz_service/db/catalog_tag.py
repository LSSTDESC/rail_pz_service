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
    """Database table to keep track of photo-z catalog_tags

    Each `CatalogTag` refers to a particular `CatalogConfigBase`
    """

    __tablename__ = "catalog_tag"
    class_string = "catalog_tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True, unique=True)
    class_name: Mapped[str] = mapped_column()

    estimators_: Mapped["Estimator"] = relationship(
        "Estimator",
        primaryjoin="CatalogTag.id==Estimator.catalog_tag_id",
        viewonly=True,
    )
    models_: Mapped["Model"] = relationship(
        "Model",
        primaryjoin="CatalogTag.id==Model.catalog_tag_id",
        viewonly=True,
    )
    datasets_: Mapped["Dataset"] = relationship(
        "Dataset",
        primaryjoin="CatalogTag.id==Dataset.catalog_tag_id",
        viewonly=True,
    )

    pydantic_mode_class = models.CatalogTag

    col_names_for_table = pydantic_mode_class.col_names_for_table

    def __repr__(self) -> str:
        return f"CatalogTag {self.name} {self.id} {self.class_name}"
