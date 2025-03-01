"""Common configuration parameters for pz-rail-service related packages"""

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Configuration", "config"]

load_dotenv()


class AsgiConfiguration(BaseModel):
    """Configuration for the application's ASGI web server."""

    title: str = Field(
        description="Title of the ASGI application",
        default="pz-rail-service",
    )

    host: str = Field(
        description="The host address to which the asgi server should bind",
        default="0.0.0.0",
    )

    port: int = Field(
        description="Port number for the asgi server to listen on",
        default=8080,
    )

    prefix: str = Field(
        description="The URL prefix for the pz-rail-service API",
        default="/pz-rail-service",
    )

    frontend_prefix: str = Field(
        description="The URL prefix for the frontend web app",
        default="/rail",
    )

    reload: bool = Field(
        description="Whether to support ASGI server reload on content change.",
        default=True,
    )


class LoggingConfiguration(BaseModel):
    """Configuration for the application's logging facility."""

    handle: str = Field(
        default="pz-rail",
        title="Handle or name of the root logger",
    )

    level: str = Field(
        default="INFO",
        title="Log level of the application's logger",
    )

    profile: str = Field(
        default="development",
        title="Application logging profile",
    )


class DaemonConfiguration(BaseModel):
    """Settings for the Daemon nested model.

    Set according to DAEMON__FIELD environment variables.
    """

    processing_interval: int = Field(
        default=30,
        description=(
            "The maximum wait time (seconds) between daemon processing intervals "
            "and the minimum time between element processing attepts. This "
            "duration may be lengthened depending on the element type."
        ),
    )


class DatabaseConfiguration(BaseModel):
    """Database configuration nested model.

    Set according to DB__FIELD environment variables.
    """

    url: str = Field(
        default="",
        description="The URL for the pz-rail-service database",
    )

    password: str | None = Field(
        default=None,
        description="The password for the pz-rail-service database",
    )

    table_schema: str | None = Field(
        default=None,
        description="Schema to use for pz-rail-service database",
    )

    echo: bool = Field(
        default=False,
        description="SQLAlchemy engine echo setting for the pz-rail-service database",
    )


class StorageConfiguration(BaseModel):
    """Database storage configuration nested model.

    Set according to STORAGE__FIELD environment variables.
    """

    archive: str = Field(
        default="archive",
        description="The path for the archived files for pz-rail-service database",
    )

    import_area: str = Field(
        default="import",
        description="The path for the import area for files for pz-rail-service database",
    )


class Configuration(BaseSettings):
    """Configuration for pz-rail-service.

    Nested models may be consumed from environment variables named according to
    the pattern 'NESTED_MODEL__FIELD' or via any `validation_alias` applied to
    a field.
    """

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        case_sensitive=False,
        extra="ignore",
    )

    # Nested Models
    asgi: AsgiConfiguration = AsgiConfiguration()
    daemon: DaemonConfiguration = DaemonConfiguration()
    db: DatabaseConfiguration = DatabaseConfiguration()
    logging: LoggingConfiguration = LoggingConfiguration()
    storage: StorageConfiguration = StorageConfiguration()


config = Configuration()
"""Configuration for pz-rail-service."""
