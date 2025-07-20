"""Provider of project settings."""

from typing import Self

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TransportConfig(BaseModel):
    """Transport settings."""

    connections: dict[str, int] = Field(default_factory=lambda: {"wss": 1})


class QuoteConsumerConfig(BaseModel):
    """Settings for quotes dumper."""

    flush_period: int = Field(
        default=30,
        description="Period of writing quotes to external storage in seconds",
    )
    delete_period: int = Field(
        default=7,
        description="Threshold for old records clean-up in external storage",
    )


class Settings(BaseSettings):
    """Env settings."""

    exchange_name: str = Field(description="Name of crypto exchange to get quotes from")
    database_type: str = Field(description="External storage to read from / write to")

    transport: TransportConfig = Field(default_factory=TransportConfig)
    quote_consumer: QuoteConsumerConfig = Field(default_factory=QuoteConsumerConfig)

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")


class SettingsProvider:
    """Object able to provide parsed env settings data model.

    Should be instantiated on runtime using `get_instance` class method.
    """

    _instance: Self

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
