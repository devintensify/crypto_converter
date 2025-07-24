"""Implementation of `IGateway` working with bybit.

Is a demo version without unit tests.
"""

import asyncio
import time
from collections import defaultdict

from crypto_converter.external.session_pool import ClientSessionPool
from crypto_converter.log import log_awaitable_method, log_method
from crypto_converter.quote_consumer.abstract.gateway import (
    GatewayObserverP,
    GatewayPublisherP,
    IGateway,
)
from crypto_converter.quote_consumer.abstract.transport import ITransport, JsonType
from crypto_converter.quote_consumer.transport import get_transport
from crypto_converter.quote_consumer.utils import Quote, QuotesContainer
from crypto_converter.utils import cancel_and_wait


class BybitGateway(IGateway):
    """Implementation of `IGateway` working with bybit.

    Is a demo version without handling arbitraged messages, \
        rate limiter, runtime markets fetching \
        and subscription status handling.
    """

    def __repr__(self) -> str:
        """Represent self as class name."""
        return self.__class__.__name__

    @log_method(logger_name="quote_consumer", level_on_attempt="info")
    def __init__(self) -> None:
        """Initialize `BybitGateway`."""
        self._transport: ITransport = get_transport(url_factory=self._get_transport_url)

        # map: (instrument_name -> base/quote instrument_name)
        self._markets_map: dict[str, str] = {}

        self._message_listener_task: asyncio.Task[None] | None = None

        self._observers: list[GatewayObserverP] = []

        self._buffered_quotes: QuotesContainer = defaultdict(list)
        self._quotes: QuotesContainer = {}

        self._last_pong: float | None = None
        self._last_callback: float | None = None

    @log_awaitable_method(logger_name="quote_consumer", level_on_attempt="info")
    async def start(self) -> None:
        """Start gateway.

        Load markets.
        Send subscription message to exchange using underlying transport.
        Listen to messages in background task and handle them.

        """
        await self._load_markets()
        self._message_listener_task = asyncio.create_task(self._connect_and_listen())

    @log_awaitable_method(logger_name="quote_consumer", level_on_attempt="info")
    async def stop(self) -> None:
        """Stop gateway.

        Stop task listening to messages. Clean cache.
        """
        await self._cancel_and_wait(self._message_listener_task)
        self._markets_map.clear()

    def handle_message(self, message: JsonType) -> None:
        """Handle message from exchange."""
        assert isinstance(message, dict)  # noqa: S101

        if message.get("ret_msg") == "pong":
            self._handle_pong()

        topic = message.get("topic")
        if isinstance(topic, str) and topic.startswith("tickers"):
            self._handle_ticker(message)

    def as_publisher(self) -> GatewayPublisherP:
        """Represent as object implementing `GatewayPublisherP`."""
        return self

    def get_quotes(self) -> QuotesContainer:
        """Get quotes from self cache."""
        return self._quotes

    def register(self, observer: GatewayObserverP) -> None:
        """Register new observer of quotes events."""
        self._observers.append(observer)

    @log_method(logger_name="quote_consumer")
    def _on_quotes_update(self) -> None:
        """Notify all observers on quotes update event."""
        self._quotes = self._buffered_quotes
        self._buffered_quotes = defaultdict(list)
        for observer in self._observers:
            observer.on_quotes_update()

    @staticmethod
    def _get_transport_url(protocol: str) -> str:
        match protocol:
            case "wss":
                return "wss://stream.bybit.com/v5/public/spot"
            case _:
                raise NotImplementedError

    @log_awaitable_method(logger_name="quote_consumer")
    async def _connect_and_listen(self) -> None:
        """Connect to exchange using underlying transport.

        Send subscriptions requests. Listen and handle incoming messages.
        Reconnect if connection is reset.

        Stop trying to listen messages if gateway was stopped via `stop()` method.
        """
        transport = self._transport
        callback_loop_task = asyncio.create_task(self._callback_loop())
        reconnect_interval = 5
        try:
            while True:
                ping_loop_task: asyncio.Task[None] | None = None
                try:
                    await transport.connect()
                    ping_loop_task = asyncio.create_task(self._ping_loop())
                    await asyncio.gather(
                        *[
                            transport.send(subscribe_message)
                            for subscribe_message in self._create_subscribe_messages()
                        ]
                    )
                    async for message in transport.listen():
                        self.handle_message(message)
                except (ConnectionRefusedError, ConnectionResetError):
                    await self._cancel_and_wait(ping_loop_task)
                    await asyncio.sleep(reconnect_interval)
        except asyncio.CancelledError:
            await self._cancel_and_wait(callback_loop_task, ping_loop_task)
        finally:
            await transport.close()

    @log_awaitable_method(logger_name="quote_consumer", level_on_attempt="info")
    async def _load_markets(self) -> None:
        """Load instruments info.

        Create map to resolve instrument names into base+quote pairs.

        Is a demo version without retries and handling of asset name changing.
        """
        if self._markets_map:
            return

        session = await ClientSessionPool.get_instance().get_session()
        async with session.get(
            "https://api.bybit.com/v5/market/instruments-info?category=spot"
        ) as resp:
            content = await resp.json()

        raw_instruments = content.get("result", {}).get("list", [])
        for raw_instrument in raw_instruments:
            self._markets_map[raw_instrument["symbol"]] = (
                f"{raw_instrument['baseCoin']}/{raw_instrument['quoteCoin']}"
            )

    def _create_subscribe_messages(self) -> list[JsonType]:
        """Create messages to be sent to exchange as subscription requests.

        Returns:
            `list[JsonType]`: array of JSON-formatted objects.

        """
        subscribe_items_per_message = 10
        subscribe_items = [f"tickers.{name}" for name in list(self._markets_map.keys())]

        result: list[JsonType] = []
        for start_index in range(0, len(subscribe_items), subscribe_items_per_message):
            batched_subscribe_items = subscribe_items[
                start_index : start_index + subscribe_items_per_message
            ]
            result.append(
                {
                    "op": "subscribe",
                    "args": batched_subscribe_items,
                }
            )
        return result

    @log_awaitable_method(logger_name="quote_consumer")
    async def _ping_loop(self) -> None:
        """Send ping message to exchange in loop.

        Close transport if ping-pong keepalive missing on time.
        """
        ping = lambda: {"op": "ping"}  # noqa: E731
        interval = 20
        max_misses = 2
        transport = self._transport
        while True:
            await asyncio.gather(transport.send(ping()), asyncio.sleep(interval))
            last_pong = self._last_pong
            if last_pong is not None and (
                time.monotonic() - last_pong > interval * max_misses
            ):
                await transport.close()
                break

    def _handle_pong(self) -> None:
        """Mark latest pong timestamp in cache."""
        self._last_pong = time.monotonic()

    def _handle_ticker(self, message: dict) -> None:
        """Parse `Quote` from ticker message and update `_buffered_quotes`."""
        data = message["data"]
        instrument = self._markets_map.get(data["symbol"])
        if instrument is not None:
            self._buffered_quotes[instrument].append(
                Quote(timestamp=message["ts"], value=float(data["lastPrice"]))
            )

    @log_awaitable_method(logger_name="quote_consumer")
    async def _callback_loop(self) -> None:
        """Periodically check for new buffered quotes.

        If new buffered quotes occur, notify all observers.
        """
        callback_interval = 5
        while True:
            if self._buffered_quotes:
                self._on_quotes_update()
            await asyncio.sleep(callback_interval)

    @log_awaitable_method(logger_name="quote_consumer")
    async def _cancel_and_wait(self, *tasks: asyncio.Task | None) -> None:
        await cancel_and_wait(*tasks)
