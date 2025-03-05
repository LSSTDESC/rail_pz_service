"""Database model for Request table"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rail.core import Model as RailModel
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from .. import models
from ..common.errors import (
    RAILBadModelError,
    RAILFileNotFoundError,
    RAILMissingRowCreateInputError,
)
from .algorithm import Algorithm
from .base import Base
from .catalog_tag import CatalogTag
from .row import RowMixin

if TYPE_CHECKING:
    from .estimator import Estimator


class Model(Base, RowMixin):
    pydantic_mode_class = models.Model
    __doc__ = pydantic_mode_class.__doc__

    __tablename__ = "model"
    class_string = "model"

    #: primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    #: Name for this Model, unique
    name: Mapped[str] = mapped_column(index=True, unique=True)

    #: Path to the relevant file
    path: Mapped[str] = mapped_column()

    #: foreign key into `Algorithm` table
    algo_id: Mapped[int] = mapped_column(
        ForeignKey("algorithm.id", ondelete="CASCADE"),
        index=True,
    )

    #: foreign key into `CatalogTag` table
    catalog_tag_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_tag.id", ondelete="CASCADE"),
        index=True,
    )

    #: Access to associated `Algorithm`
    algo_: Mapped[Algorithm] = relationship(
        "Algorithm",
        primaryjoin="Model.algo_id==Algorithm.id",
        viewonly=True,
    )

    #: Access to associated `CatalogTag`
    catalog_tag_: Mapped[CatalogTag] = relationship(
        "CatalogTag",
        primaryjoin="Model.catalog_tag_id==CatalogTag.id",
        viewonly=True,
    )

    #: Access to list of associated `Estimator`
    estimators_: Mapped[list[Estimator]] = relationship(
        "Estimator",
        primaryjoin="Model.id==Estimator.model_id",
        viewonly=True,
    )

    #: column names to use when printing the table
    col_names_for_table = pydantic_mode_class.col_names_for_table

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
        except KeyError as e:
            raise RAILMissingRowCreateInputError(f"Missing input to create Model: {e}") from e

        validate_file = kwargs.get("validate_file", True)

        algo_id = kwargs.get("algo_id", None)
        if algo_id is None:
            try:
                algo_name = kwargs["algo_name"]
            except KeyError as e:
                raise RAILMissingRowCreateInputError(f"Missing input to create Model: {e}") from e
            algo_ = await Algorithm.get_row_by_name(session, algo_name)
            algo_id = algo_.id
        else:
            algo_ = await Algorithm.get_row(session, algo_id)

        catalog_tag_id = kwargs.get("catalog_tag_id", None)
        if catalog_tag_id is None:
            try:
                catalog_tag_name = kwargs["catalog_tag_name"]
            except KeyError as e:
                raise RAILMissingRowCreateInputError(f"Missing input to create Model: {e}") from e
            catalog_tag_ = await CatalogTag.get_row_by_name(session, catalog_tag_name)
            catalog_tag_id = catalog_tag_.id
        else:
            catalog_tag_ = await CatalogTag.get_row(session, catalog_tag_id)

        if validate_file:
            cls.validate_model(path, algo_, catalog_tag_)

        return dict(
            name=name,
            path=path,
            algo_id=algo_id,
            catalog_tag_id=catalog_tag_id,
        )

    @classmethod
    def validate_model(
        cls,
        path: Path,
        algo: Algorithm,
        catalog_tag: CatalogTag,
    ) -> None:
        """Validate that the model is appropriate for the Algorithm and CatalogTag

        Parameters
        ----------
        path
            File with the data

        algo
            Algorithm in question

        catalog_tag
            Catalog tag in question

        """
        if not os.path.exists(path):
            raise RAILFileNotFoundError(f"Input file {path} not found")

        the_model = RailModel.read(path)
        if the_model.catalog_tag:
            if the_model.catalog_tag != catalog_tag.name:
                raise RAILBadModelError(
                    f"CatalogTag does not match: {the_model.catalog_tag} != {catalog_tag.name}"
                )

        if the_model.creation_class_name:
            expected_estimator_class = the_model.creation_class_name.replace("Informer", "Estimator")
            if algo.class_name != expected_estimator_class:
                raise RAILBadModelError(
                    f"Algorithm does not match: {expected_estimator_class} != {algo.class_name}"
                )
