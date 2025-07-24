"""Logger setup function to be called at entrypoint.

Is a demo version with basic file handler.
"""

import logging
from datetime import UTC, datetime

from crypto_converter.settings import SettingsProvider


def setup_logger() -> None:
    """Set up logger for `converter_api` service."""
    logger = logging.getLogger("converter_api")
    logger.setLevel(logging.DEBUG)

    now = datetime.now(tz=UTC)
    file_path = (
        SettingsProvider.get_instance().get_settings().quote_reader.logs_path.as_posix()
        + "/api_"
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
    """Get `converter_api` logger.

    Returns:
        `logging.Logger`: `converter_api` logger.

    """
    return logging.getLogger("converter_api")
