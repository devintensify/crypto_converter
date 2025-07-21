"""Implementation of `ITransport` using websockets."""

from collections.abc import AsyncGenerator
from contextlib import suppress

from aiohttp import ClientWebSocketResponse

from crypto_converter.external.session_pool import ClientSessionPool
from crypto_converter.log import log_awaitable_method
from crypto_converter.quote_consumer.abstract.transport import ITransport, JsonType
from crypto_converter.quote_consumer.log import get_logger

logger = get_logger()


class WebSocketTransport(ITransport):
    """Implementation of `ITransport` using websockets."""

    def __init__(self, url: str) -> None:
        """Initialize `WebSocketTransport`."""
        self._connection: ClientWebSocketResponse | None = None
        self._url = url

    @property
    def connection(self) -> ClientWebSocketResponse:
        """Get `_connection` attribute."""
        assert self._connection  # noqa: S101
        return self._connection

    def __repr__(self) -> str:
        """Represent `WebSocketTransport` as connection url."""
        return f"{self.__class__.__name__}({self._url})"

    @log_awaitable_method(
        logger_name="quote_consumer", level_on_attempt="info", use_class_repr=True
    )
    async def connect(self) -> None:
        """Connect to external resource using wss protocol.

        1. Initialize `ClientSession` if not initialized yet.
        2. Connect using this session.

        """
        if self._disconnected():
            session = await ClientSessionPool.get_instance().get_session()
            try:
                connection = await session.ws_connect(url=self._url)
            except Exception as exc:
                raise ConnectionRefusedError from exc

            self._connection = connection

    @log_awaitable_method(logger_name="quote_consumer", use_class_repr=True)
    async def send(self, message: JsonType) -> None:
        """Send message to external resourse using websocket channel."""
        if self._disconnected():
            raise ConnectionResetError

        try:
            await self.connection.send_json(message)
        except Exception as exc:
            raise ConnectionResetError from exc

    async def listen(self) -> AsyncGenerator[JsonType]:
        """Read and yield messages from websocket connection."""
        if self._disconnected():
            raise ConnectionResetError

        logger.debug("`%s`: Start listening to incoming messages..", repr(self))
        try:
            while True:
                try:
                    message = await self.connection.receive_json()
                except Exception as exc:
                    raise ConnectionResetError from exc
                yield message
        finally:
            logger.debug("`%s`: Stopped listening to incoming messages", repr(self))

    @log_awaitable_method(
        logger_name="quote_consumer", level_on_attempt="info", use_class_repr=True
    )
    async def close(self) -> None:
        """Close underlying websocket connection."""
        if self._disconnected():
            return
        with suppress(Exception):
            await self.connection.close()

    def _disconnected(self) -> bool:
        return (connection := self._connection) is None or connection.closed
