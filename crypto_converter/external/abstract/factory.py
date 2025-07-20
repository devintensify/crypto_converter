"""Interface of quotes i/o tools factory."""

from abc import ABC, abstractmethod

from crypto_converter.external.abstract.storage_reader import IQuotesReader
from crypto_converter.external.abstract.storage_writer import IQuotesWriter


class IQuotesIOFactory(ABC):
    """Interface of quotes i/o tools factory."""

    @abstractmethod
    def get_reader(self) -> IQuotesReader:
        """Get quotes reader.

        Returns:
            `IQuotesReader`: object implementing `IQuotesReader`.

        """

    @abstractmethod
    def get_writer(self) -> IQuotesWriter:
        """Get quotes writer.

        Returns:
            `IQuotesWriter`: object implementing `IQuotesWriter`.

        """
