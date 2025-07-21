"""Provider of project settings."""

import argparse
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


class ClickHouseConfig(BaseModel):
    """ClickHouse configuration settings.

    Is a demo version without auth.
    """

    dsn: str = Field(description="Clickhouse DSN")


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


class QuoteReaderConfig(BaseModel):
    """Quotes reader settings."""

    outdated_interval: int = Field(
        default=60, description="Time window threshold to check for outdated quotes"
    )


class Settings(BaseSettings):
    """Env settings."""

    exchange_name: str = Field(description="Name of crypto exchange to get quotes from")
    database_type: str = Field(description="External storage to read from / write to")

    transport: TransportConfig = Field(description="Transport settings")
    clickhouse: ClickHouseConfig | None = Field(
        default=None, description="ClickHouse configuration settings"
    )

    quote_consumer: QuoteConsumerConfig = Field(description="Quotes consumer settings")
    quote_reader: QuoteReaderConfig = Field(description="Quotes reader settings")

    model_config = SettingsConfigDict(env_nested_delimiter="__")

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
        env_file = self._get_env_file()
        Settings.model_config["env_file"] = env_file
        self._settings = Settings()

    def get_settings(self) -> Settings:
        """Return cached `Settings` object.

        Returns:
            `Settings`: env settings data model.

        """
        return self._settings

    @staticmethod
    def _get_env_file() -> str:
        """Get env file name based on command line args.

        Returns:
            `str`: env file name to load settings from.

        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--env",
            choices=["default", "docker"],
            default="default",
            help="Select .env file to load: 'default' = .env, 'docker' = .env.docker",
        )
        namespace = parser.parse_args()
        env_file: str
        match namespace.env:
            case "default":
                env_file = ".env"
            case "docker":
                env_file = ".env.docker"
            case _:
                message = "Code supposed to be unreachable."
                raise RuntimeError(message)
        return env_file
