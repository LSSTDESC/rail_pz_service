from sqlalchemy import Enum as saEnum
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from ..enums import (
    TableEnum,
)
from ..config import config


class Base(DeclarativeBase):
    """Base class for DB tables"""

    metadata = MetaData(schema=config.db.table_schema)
    type_annotation_map = {
        TableEnum: saEnum(
            TableEnum, length=20, native_enum=False, create_constraint=False
        ),
    }
