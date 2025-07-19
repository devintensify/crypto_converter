"""Interface of quotes reader."""

from abc import ABC, abstractmethod


class IQuotesReader(ABC):
    """Interface of quotes reader.

    Able to query external storage for ticker price for instrument and timestamp.
    """

    @abstractmethod
    async def query(self, instrument: str, timestamp: int | None = None) -> None:
        """Query external resource for ticker price.

        Args:
            instrument (`str`): instrument name in BASE/QUOTE notation.
            timestamp (`Optional[int]`): timestamp to query for.

        """
