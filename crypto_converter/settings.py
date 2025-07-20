"""Provider of project settings."""

from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TransportConfig(BaseModel):
    """Transport settings."""

    connections: dict[str, int] = Field(default_factory=lambda: {"wss": 1})
    local_queue_max_size: int = Field(
        default=10_000, description="Local queue maxsize. Used in proxy transport."
    )


class QuoteConsumerConfig(BaseModel):
    """Quotes consumer settings."""

    logs_path: Path = Field(description="Path to directory to store logs in.")

    flush_period: int = Field(
        default=30,
        description="Period of writing quotes to external storage in seconds",
    )
    delete_period: int = Field(
        default=7,
        description="Threshold for old records clean-up in external storage",
    )


class ClickHouseConfig(BaseModel):
    """ClickHouse configuration settings.

    Is a demo version without auth.
    """

    dsn: str = Field(description="Clickhouse DSN")


class Settings(BaseSettings):
    """Env settings."""

    exchange_name: str = Field(description="Name of crypto exchange to get quotes from")
    database_type: str = Field(description="External storage to read from / write to")

    transport: TransportConfig = Field(description="Transport settings")
    quote_consumer: QuoteConsumerConfig = Field(description="Quotes consumer settings")
    clickhouse: ClickHouseConfig | None = Field(
        default=None, description="ClickHouse configuration settings"
    )

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")

    def model_post_init(self, _: dict[str, Any] | None) -> None:
        """Additional validation logic for settings model."""
        if self.database_type == "clickhouse" and self.clickhouse is None:
            error_message = (
                "Expected clickhouse__* parameters in environmental variables. "
                "Please set different `database_type` or "
                "declare clickhouse env variables in your .env file."
            )
            raise ValueError(error_message)


class SettingsProvider:
    """Object able to provide parsed env settings data model.

    Should be instantiated on runtime using `get_instance` class method.
    """

    _instance: Self | None = None

    @classmethod
    def get_instance(cls) -> Self:
        """Get instance of `SettingsProvider` to communicate with.

        Creates instance only once and reuse it in further calls.

        Returns:
            `SettingsProvider`: instance able to provide `Settings`.

        """
        if (instance := cls._instance) is None:
            instance = cls()
            cls._instance = instance
        return instance

    def __init__(self) -> None:
        """Initialize `SettingsProvider`."""
        self._settings = Settings()

    def get_settings(self) -> Settings:
        """Return cached `Settings` object.

        Returns:
            `Settings`: env settings data model.

        """
        return self._settings
