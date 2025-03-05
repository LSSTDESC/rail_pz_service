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
    pydantic_mode_class = models.Estimator
    __doc__ = pydantic_mode_class.__doc__

    __tablename__ = "estimator"
    class_string = "estimator"

    #: primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    #: Name of the model, unique
    name: Mapped[str] = mapped_column(index=True, unique=True)

    #: foreign key into 'Algorithm' table
    algo_id: Mapped[int] = mapped_column(
        ForeignKey("algorithm.id", ondelete="CASCADE"),
        index=True,
    )

    #: foreign key into 'CatalogTag' table
    catalog_tag_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_tag.id", ondelete="CASCADE"),
        index=True,
    )

    #: foreign key into 'Model' table
    model_id: Mapped[int] = mapped_column(
        ForeignKey("model.id", ondelete="CASCADE"),
        index=True,
    )

    #: Configuration parameters for this estimator
    config: Mapped[dict | None] = mapped_column(type_=JSON)

    #: Access to associated `Algorithm`
    algo_: Mapped["Algorithm"] = relationship(
        "Algorithm",
        primaryjoin="Estimator.algo_id==Algorithm.id",
        viewonly=True,
    )

    #: Access to associated `CatalogTag`
    catalog_tag_: Mapped["CatalogTag"] = relationship(
        "CatalogTag",
        primaryjoin="Estimator.catalog_tag_id==CatalogTag.id",
        viewonly=True,
    )

    #: Access to associated `Model`
    model_: Mapped["Model"] = relationship(
        "Model",
        primaryjoin="Estimator.model_id==Model.id",
        viewonly=True,
    )

    #: Access to list of associated `Request`
    requests_: Mapped[list["Request"]] = relationship(
        "Request",
        primaryjoin="Estimator.id==Request.estimator_id",
        viewonly=True,
    )

    #: column names to use when printing the table
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
            raise RAILMissingRowCreateInputError(f"Missing input to create Estimator: {e}") from e

        model_id = kwargs.get("model_id", None)
        if model_id is None:
            try:
                model_name = kwargs["model_name"]
            except KeyError as e:
                raise RAILMissingRowCreateInputError(f"Missing input to create Estimator: {e}") from e
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
