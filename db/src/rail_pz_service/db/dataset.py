"""Database model for Dataset table"""

import os
from pathlib import Path
from typing import Any

import tables_io
from sqlalchemy import JSON
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from rail_pz_service.common import models
from rail_pz_service.common.errors import (
    RAILBadDatasetError,
    RAILFileNotFoundError,
    RAILMissingRowCreateInputError,
)

from .base import Base
from .catalog_tag import CatalogTag
from .row import RowMixin


class Dataset(Base, RowMixin):
    """Database table to keep track of photo-z algorithms

    Each `Dataset` refers to a particular instance of a
    `CatEstimator`

    """

    __tablename__ = "dataset"
    class_string = "dataset"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True, unique=True)
    n_objects: Mapped[int] = mapped_column()
    path: Mapped[str | None] = mapped_column(default=None)
    data: Mapped[dict | None] = mapped_column(type_=JSON)
    catalog_tag_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_tag.id", ondelete="CASCADE"),
        index=True,
    )
    catalog_tag_: Mapped["CatalogTag"] = relationship(
        "CatalogTag",
        primaryjoin="Dataset.catalog_tag_id==CatalogTag.id",
        viewonly=True,
    )

    pydantic_mode_class = models.Dataset

    col_names_for_table = pydantic_mode_class.col_names_for_table

    def __repr__(self) -> str:
        return f"Dataset {self.name} {self.id} {self.n_objects} {self.catalog_tag_id} {self.path}"

    @classmethod
    async def get_create_kwargs(
        cls,
        session: async_scoped_session,
        **kwargs: Any,
    ) -> dict:
        try:
            name = kwargs["name"]
            path = kwargs.get("path", None)
            data = kwargs.get("data", None)
        except KeyError as e:
            raise RAILMissingRowCreateInputError(f"Missing input to create Group: {e}") from e

        validate_file = kwargs.get("validate_file", True)

        catalog_tag_id = kwargs.get("catalog_tag_id", None)
        if catalog_tag_id is None:
            try:
                catalog_tag_name = kwargs["catalog_tag_name"]
            except KeyError as e:
                raise RAILMissingRowCreateInputError(f"Missing input to create Group: {e}") from e
            catalog_tag_ = await CatalogTag.get_row_by_name(session, catalog_tag_name)
            catalog_tag_id = catalog_tag_.id
        else:
            catalog_tag_ = await CatalogTag.get_row(session, catalog_tag_id)

        if path is not None:
            if validate_file:
                n_objects = cls.validate_data_for_path(path, catalog_tag_)
            else:
                n_objects = kwargs.get("n_objects", 1)
        elif data:
            if validate_file:
                n_objects = cls.validate_data(data, catalog_tag_)
            else:
                n_objects = kwargs.get("n_objects", 1)
        else:
            raise RAILMissingRowCreateInputError(
                "When creating a Dataset either 'path' to a file must be set or "
                "the `data` must be provided explicitly."
            )

        return dict(
            name=name,
            path=path,
            n_objects=n_objects,
            data=data,
            catalog_tag_id=catalog_tag_id,
        )

    @classmethod
    def validate_data_for_path(
        cls,
        path: Path,
        catalog_tag: CatalogTag,
    ) -> int:
        """Validate that these data are appropriate for the CatalogTag

        Parameters
        ----------
        path
            File with the data

        catalog_tag
            Catalog tab in question

        Returns
        -------
        int
            Size of the datset
        """
        if not os.path.exists(path):
            raise RAILFileNotFoundError(f"Input file {path} not found")
        n_objects = tables_io.io.getInputDataLength(path)
        if n_objects == 0:
            raise RAILBadDatasetError(f"Could not find data in input file {path}")
        return n_objects

    @classmethod
    def validate_data(
        cls,
        data: dict,
        catalog_tag: CatalogTag,
    ) -> int:
        """Validate that these data are appropriate for the CatalogTag

        Parameters
        ----------
        data
            Data in question

        catalog_tag
            Catalog tab in question

        Returns
        -------
        int
            Size of the datset
        """
        raise NotImplementedError()
