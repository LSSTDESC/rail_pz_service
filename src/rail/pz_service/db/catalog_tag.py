from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .row import RowMixin

if TYPE_CHECKING:
    from .estimator import Estimator


class CatalogTag(Base, RowMixin):
    """Database table to keep track of photo-z catalog_tags

    Each `CatalogTag` refers to a particular `CatalogConfigBase`
    """

    __tablename__ = "catalog_tag"
    class_string = "catalog_tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    class_name: Mapped[str] = mapped_column()

    estimators_: Mapped["Estimator"] = relationship(
        "Estimator",
        primaryjoin="CatalogTag.id==Estimator.catalog_tag_id",
        viewonly=True,
    )

    col_names_for_table = ["id", "name", "class_name"]

    def __repr__(self) -> str:
        return f"CatalogTag {self.name} {self.id} {self.class_name}"
