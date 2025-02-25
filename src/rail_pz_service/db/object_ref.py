"""Database model for ObjectRef table"""

from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from rail_pz_service.common import models
from rail_pz_service.common.errors import RAILMissingRowCreateInputError

from .base import Base
from .dataset import Dataset
from .row import RowMixin

if TYPE_CHECKING:
    pass


class ObjectRef(Base, RowMixin):
    """Database table to keep track of photo-z algorithms

    Each `ObjectRef` refers to a particular instance of a
    `CatEstimator`

    """

    __tablename__ = "object_ref"
    class_string = "object_ref"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True, unique=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("dataset.id", ondelete="CASCADE"),
        index=True,
    )
    index: Mapped[int] = mapped_column()
    dataset_: Mapped["Dataset"] = relationship(
        "Dataset",
        primaryjoin="ObjectRef.dataset_id==Dataset.id",
        viewonly=True,
    )

    pydantic_mode_class = models.ObjectRef

    col_names_for_table = pydantic_mode_class.col_names_for_table

    def __repr__(self) -> str:
        return f"ObjectRef {self.name} {self.id} {self.dataset_id} {self.index}"

    @classmethod
    async def get_create_kwargs(
        cls,
        session: async_scoped_session,
        **kwargs: Any,
    ) -> dict:
        try:
            name = kwargs["name"]
            index = kwargs["index"]
        except KeyError as e:
            raise RAILMissingRowCreateInputError(f"Missing input to create Group: {e}") from e

        dataset_id = kwargs.get("dataset_id", None)
        if dataset_id is None:
            try:
                dataset_name = kwargs["dataset_name"]
            except KeyError as e:
                raise RAILMissingRowCreateInputError(f"Missing input to create Group: {e}") from e
            dataset_ = await Dataset.get_row_by_name(session, dataset_name)
            dataset_id = dataset_.id

        return dict(
            name=name,
            index=index,
            dataset_id=dataset_id,
        )
