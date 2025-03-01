"""Database model for Estimator table"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from .. import models
from ..common.errors import RAILMissingRowCreateInputError
from .algorithm import Algorithm
from .base import Base
from .catalog_tag import CatalogTag
from .model import Model
from .row import RowMixin

if TYPE_CHECKING:
    from .request import Request


class Estimator(Base, RowMixin):
    """Database table to keep track of photo-z algorithms

    Each `Estimator` refers to a particular instance of a
    `CatEstimator`

    """

    __tablename__ = "estimator"
    class_string = "estimator"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True, unique=True)
    algo_id: Mapped[int] = mapped_column(
        ForeignKey("algorithm.id", ondelete="CASCADE"),
        index=True,
    )
    catalog_tag_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_tag.id", ondelete="CASCADE"),
        index=True,
    )
    model_id: Mapped[int] = mapped_column(
        ForeignKey("model.id", ondelete="CASCADE"),
        index=True,
    )
    config: Mapped[dict | None] = mapped_column(type_=JSON)

    algo_: Mapped["Algorithm"] = relationship(
        "Algorithm",
        primaryjoin="Estimator.algo_id==Algorithm.id",
        viewonly=True,
    )
    catalog_tag_: Mapped["CatalogTag"] = relationship(
        "CatalogTag",
        primaryjoin="Estimator.catalog_tag_id==CatalogTag.id",
        viewonly=True,
    )
    model_: Mapped["Model"] = relationship(
        "Model",
        primaryjoin="Estimator.model_id==Model.id",
        viewonly=True,
    )
    requests_: Mapped[list["Request"]] = relationship(
        "Request",
        primaryjoin="Estimator.id==Request.estimator_id",
        viewonly=True,
    )

    pydantic_mode_class = models.Estimator

    col_names_for_table = pydantic_mode_class.col_names_for_table

    def __repr__(self) -> str:
        return f"Estimator {self.name} {self.id} {self.algo_id} {self.catalog_tag_id} {self.model_id}"

    @classmethod
    async def get_create_kwargs(
        cls,
        session: async_scoped_session,
        **kwargs: Any,
    ) -> dict:
        try:
            name = kwargs["name"]
            config = kwargs.get("config", {})
        except KeyError as e:
            raise RAILMissingRowCreateInputError(f"Missing input to create Group: {e}") from e

        model_id = kwargs.get("model_id", None)
        if model_id is None:
            try:
                model_name = kwargs["model_name"]
            except KeyError as e:
                raise RAILMissingRowCreateInputError(f"Missing input to create Group: {e}") from e
            model_ = await Model.get_row_by_name(session, model_name)
            model_id = model_.id
        else:
            model_ = await Model.get_row(session, model_id)

        return dict(
            name=name,
            config=config,
            algo_id=model_.algo_id,
            catalog_tag_id=model_.catalog_tag_id,
            model_id=model_id,
        )
