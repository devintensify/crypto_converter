"""Interface of exchange client."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from crypto_converter.quote_consumer.abstract.transport import ITransport, JsonType
    from crypto_converter.quote_consumer.types import QuotesContainer


class IGateway(ABC):
    """Interface of exchange client.

    Is able to subscribe to specific market data and handle messages from exchange.

    Owns `ITransport` and controls its lifetime.
    """

    _transport: ITransport

    @abstractmethod
    async def subscribe_to_quotes(self) -> None:
        """Send subscription message to exchange using underlying transport."""

    @abstractmethod
    def handle_message(self, message: JsonType) -> None:
        """Handle message from exchange.

        Args:
            message (`JsonType`): JSON-encoded message.

        """


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

    def on_quotes_update(self) -> None:
        """Notify all observers on quotes update event."""
