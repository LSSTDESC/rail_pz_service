""" Database model for Request table """

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from rail_pz_service.common.errors import RAILMissingRowCreateInputError
from .algorithm import Algorithm
from .base import Base
from .catalog_tag import CatalogTag
from .row import RowMixin

if TYPE_CHECKING:
    from .estimator import Estimator


class Model(Base, RowMixin):
    """Database table to keep track of photo-z algorithms

    Each `Model` refers to a particular instance of a
    `Model`

    """

    __tablename__ = "model"
    class_string = "model"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    path: Mapped[str] = mapped_column()
    algo_id: Mapped[int] = mapped_column(
        ForeignKey("algorithm.id", ondelete="CASCADE"),
        index=True,
    )
    catalog_tag_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_tag.id", ondelete="CASCADE"),
        index=True,
    )

    algo_: Mapped[Algorithm] = relationship(
        "Algorithm",
        primaryjoin="Model.algo_id==Algorithm.id",
        viewonly=True,
    )
    catalog_tag_: Mapped[CatalogTag] = relationship(
        "CatalogTag",
        primaryjoin="Model.catalog_tag_id==CatalogTag.id",
        viewonly=True,
    )
    estimators_: Mapped[Estimator] = relationship(
        "Estimator",
        primaryjoin="Model.id==Estimator.model_id",
        viewonly=True,
    )

    col_names_for_table = ["id", "name", "algo_id", "catalog_tag_id", "path"]

    def __repr__(self) -> str:
        return f"Model {self.name} {self.id} {self.algo_id} {self.catalog_tag_id} {self.path}"

    @classmethod
    async def get_create_kwargs(
        cls,
        session: async_scoped_session,
        **kwargs: Any,
    ) -> dict:
        try:
            name = kwargs["name"]
            path = kwargs["path"]
            algo_name = kwargs["algo_name"]
            catalog_tag_name = kwargs["catalog_tag_name"]

        except KeyError as e:
            raise RAILMissingRowCreateInputError(f"Missing input to create Model: {e}") from e

        algo_ = await Algorithm.get_row_by_name(session, algo_name)
        catalog_tag_ = await CatalogTag.get_row_by_name(session, catalog_tag_name)

        return dict(
            name=name,
            path=path,
            algo_id=algo_.id,
            catalog_tag_id=catalog_tag_.id,
        )
