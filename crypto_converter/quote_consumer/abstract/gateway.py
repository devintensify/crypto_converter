"""Interface of exchange client."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from crypto_converter.quote_consumer.abstract.transport import JsonType
    from crypto_converter.quote_consumer.utils import QuotesContainer


class IGateway(ABC):
    """Interface of exchange client.

    Is able to subscribe to specific market data and handle messages from exchange.

    Owns `ITransport` instances and controls their lifetime.
    """

    @abstractmethod
    async def start(self) -> None:
        """Start gateway."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop gateway."""

    @abstractmethod
    def handle_message(self, message: JsonType) -> None:
        """Handle message from exchange.

        Args:
            message (`JsonType`): JSON-encoded message.

        """

    @abstractmethod
    def as_publisher(self) -> GatewayPublisherP:
        """Represent self as object implementing `GatewayPublisherP`."""


class GatewayObserverP(Protocol):
    """Observer protocol to be implemented by concrete `GatewayPublisherP` observers."""

    _gateway: GatewayPublisherP

    def on_quotes_update(self) -> None:
        """Pull and process new quotes from GatewayPublisherP."""


class GatewayPublisherP(Protocol):
    """Publisher protocol to be implemented by concrete `IGateway` instance."""

    _observers: list[GatewayObserverP]

    def get_quotes(self) -> QuotesContainer:
        """Get actual state of quotes container.

        Returns:
            `QuotesContainer`: newly received quotes by instrument name.

        """

    def register(self, observer: GatewayObserverP) -> None:
        """Register new observer of `GatewayPublisherP` quotes events.

        Args:
            observer (`GatewayObserverP`): object implementing observer protocol.

        """

    def _on_quotes_update(self) -> None:
        """Notify all observers on quotes update event."""
