"""Database model for Dataset table"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import tables_io
from sqlalchemy import JSON
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from .. import models
from ..common.errors import (
    RAILBadDatasetError,
    RAILFileNotFoundError,
    RAILMissingRowCreateInputError,
)
from .base import Base
from .catalog_tag import CatalogTag
from .row import RowMixin

if TYPE_CHECKING:
    from .request import Request


class Dataset(Base, RowMixin):
    pydantic_mode_class = models.Dataset
    __doc__ = pydantic_mode_class.__doc__

    __tablename__ = "dataset"
    class_string = "dataset"

    #: primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    #: Name for this Dataset, unique
    name: Mapped[str] = mapped_column(index=True, unique=True)

    #: Number of objects in the dataset
    n_objects: Mapped[int] = mapped_column()

    #: Path to the relevant file (could be None)
    path: Mapped[str | None] = mapped_column(default=None)

    #: Data for the dataset (could be None)
    data: Mapped[dict | None] = mapped_column(type_=JSON)

    #: foreign key into catalog_tag table
    catalog_tag_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_tag.id", ondelete="CASCADE"),
        index=True,
    )

    #: Access to associated `CatalogTag`
    catalog_tag_: Mapped["CatalogTag"] = relationship(
        "CatalogTag",
        primaryjoin="Dataset.catalog_tag_id==CatalogTag.id",
        viewonly=True,
    )

    #: Access to list of associated `Request`
    requests_: Mapped[list["Request"]] = relationship(
        "Request",
        primaryjoin="Dataset.id==Request.dataset_id",
        viewonly=True,
    )

    #: column names to use when printing the table
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
            raise RAILMissingRowCreateInputError(f"Missing input to create Dataset: {e}") from e

        validate_file = kwargs.get("validate_file", True)

        catalog_tag_id = kwargs.get("catalog_tag_id", None)
        if catalog_tag_id is None:
            try:
                catalog_tag_name = kwargs["catalog_tag_name"]
            except KeyError as e:
                raise RAILMissingRowCreateInputError(f"Missing input to create Dataset: {e}") from e
            catalog_tag_ = await CatalogTag.get_row_by_name(session, catalog_tag_name)
            catalog_tag_id = catalog_tag_.id
        else:
            catalog_tag_ = await CatalogTag.get_row(session, catalog_tag_id)

        if path is not None:
            if validate_file:
                n_objects = cls.validate_data_for_path(path, catalog_tag_)
            else:
                n_objects = kwargs.get("n_objects", 1)
        elif data is not None:
            n_objects, data = cls.validate_data(data, catalog_tag_)
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
            CatalogTag in question

        Returns
        -------
        int
            Size of the datset
        """
        assert catalog_tag
        if not os.path.exists(path):
            raise RAILFileNotFoundError(f"Input file {path} not found")
        try:
            n_objects = tables_io.io.getInputDataLength(path)
        except Exception as msg:
            raise RAILBadDatasetError(f"Could not read data from {path} because {msg}") from msg
        return n_objects

    @classmethod
    def validate_data(
        cls,
        data: dict,
        catalog_tag: CatalogTag,
    ) -> tuple[int, dict[str, list[float]]]:
        """Validate that these data are appropriate for the CatalogTag

        Parameters
        ----------
        data
            Data in question

        catalog_tag
            Catalog tab in question

        Returns
        -------
        tuple[int, dict[str, list[float]]]
            Size of the datset, data formatted as strings
        """
        assert catalog_tag

        n_objects: int | None = None

        out_dict: dict[str, list[float]] = {}
        for key, val in data.items():
            try:
                if isinstance(val, list):
                    float_list: list[float] = []
                    for vv in val:
                        float_list.append(float(vv))
                    out_dict[key] = float_list
                    test_len = len(float_list)
                else:
                    out_dict[key] = [float(val)]
                    test_len = 1
            except ValueError as msg:
                raise RAILBadDatasetError(f"Error parsing data for {key} {msg}") from msg
            if n_objects is None:
                n_objects = test_len
            else:
                if n_objects != test_len:
                    raise RAILBadDatasetError(
                        f"Lenghts of columns do not match {key} {test_len} != {n_objects}"
                    )
        if n_objects is None:
            raise RAILBadDatasetError("No data")
        return n_objects, out_dict
