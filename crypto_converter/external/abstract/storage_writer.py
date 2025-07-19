"""Interface of quotes writer."""

from abc import ABC, abstractmethod

from crypto_converter.quote_consumer.types import QuotesContainer


class IQuotesWriter(ABC):
    """Interface of quotes writer.

    Able to serialize info from `QuotesContainer` and dump it to external storage.
    """

    @abstractmethod
    async def write(self, quotes: QuotesContainer) -> None:
        """Serialize and write records to external source.

        Args:
            quotes (`QuotesContainer`): quotes arrays by instrument name.

        """

    @abstractmethod
    async def delete_old_records(self, later_than_timestamp: int) -> None:
        """Delete records older than given timestamp from external source.

        Args:
            later_than_timestamp (`int`): given timestamp.

        """
