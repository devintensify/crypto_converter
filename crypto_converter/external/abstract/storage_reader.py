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
    async def query(self, instrument: str, timestamp: int | None = None) -> float:
        """Query external storage for ticker price.

        Args:
            instrument (`str`): instrument name in BASE/QUOTE notation.
            timestamp (`Optional[int]`): timestamp to query for.

        Returns:
            `float`: ticker price from table (if found).

        Raises:
            `ConnectionResetError`: if unable to connect to external storage.
            `InstrumentNotFoundError`: if no ticker data found for instrument.
            `TickerOutdatedError`: if latest stored ticker data is outdated.

        """

    @abstractmethod
    async def close(self) -> None:
        """Close quotes reader. Close connection to external storage."""
