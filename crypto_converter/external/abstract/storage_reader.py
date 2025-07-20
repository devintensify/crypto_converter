"""Interface of quotes reader."""

from abc import ABC, abstractmethod


class IQuotesReader(ABC):
    """Interface of quotes reader.

    Able to query external storage for ticker price for instrument and timestamp.
    """

    @abstractmethod
    async def open(self) -> None:
        """Open connection to external storage.

        Raises:
            `ConnectionRefusedError`: if unable to connect to external storage.

        """

    @abstractmethod
    async def query(self, instrument: str, timestamp: int | None = None) -> None:
        """Query external storage for ticker price.

        Args:
            instrument (`str`): instrument name in BASE/QUOTE notation.
            timestamp (`Optional[int]`): timestamp to query for.

        """

    @abstractmethod
    async def close(self) -> None:
        """Close quotes reader. Close connection to external storage."""
