"""Logger setup function to be called at entrypoint."""

import logging
from datetime import UTC, datetime

from crypto_converter.settings import SettingsProvider


def setup_logger() -> None:
    """Set up logger for `quote_consumer` service."""
    logger = logging.getLogger("quote_consumer")
    logger.setLevel(logging.DEBUG)

    now = datetime.now(tz=UTC)
    file_path = (
        SettingsProvider.get_instance()
        .get_settings()
        .quote_consumer.logs_path.as_posix()
        + "/quote_consumer_"
        + now.strftime("%Y-%m-%d-%H_%M_%S")
        + f"_{now.microsecond:06d}"
        + ".log"
    )
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)


def get_logger() -> logging.Logger:
    """Get `quote_consumer` logger.

    Returns:
        `logging.Logger`: `quote_consumer` logger.

    """
    return logging.getLogger("quote_consumer")
