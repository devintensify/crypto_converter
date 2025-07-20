"""Proxy implementation of `ITransport` using multiple transport instances."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import cast

from crypto_converter.quote_consumer.abstract.transport import ITransport, JsonType

logger = logging.getLogger("quote_consumer")

_SENTINEL = cast("dict", object())


class ProxyTransport(ITransport):
    """Proxy implementation of `ITransport` using multiple underlying transports.

    Supposed to be used on runtime.

    Is a simple demo version.
    """

    def __init__(
        self, transports: dict[str, ITransport], local_queue_max_size: int = 10_000
    ) -> None:
        """Initialize `ProxyTransport`.

        Args:
            transports (`dict[str, ITransport]`): transport instances mapping. \
                Key=unique transport identifier, Value=ITransport instance.
            local_queue_max_size (`int`): max size of local queue for messages \
                to be buffered into. Default value is `10_000`.

        """
        self._transports = transports
        self._local_messages_queue: asyncio.Queue[JsonType] = asyncio.Queue(
            maxsize=local_queue_max_size
        )
        self._closing: bool = False

    async def connect(self) -> None:
        """Call `connect()` method in all underlying transports.

        If any of them fails to connect, propagate raised exceptions.

        """
        await asyncio.gather(
            *[transport.connect() for transport in self._transports.values()]
        )

    async def send(self, message: JsonType) -> None:
        """Call `send()` method in all underlying transports with given `message`.

        If any of them fails to send, propagate raised exceptions.

        """
        await asyncio.gather(
            *[transport.send(message) for transport in self._transports.values()]
        )

    async def listen(self) -> AsyncGenerator[JsonType]:
        """Listen for incoming messages through all transports in background.

        Read local queue and yield messages from it.

        Raise `ConnectionResetError` if `_SENTINEL` received.
        """
        background_tasks = [
            asyncio.create_task(self._background_listen(transport))
            for transport in self._transports.values()
        ]
        try:
            while True:
                message = await self._local_messages_queue.get()
                if message is _SENTINEL:
                    raise ConnectionResetError
                yield message
        finally:
            running_background_tasks = [
                task for task in background_tasks if not task.done()
            ]
            if running_background_tasks:
                await asyncio.gather(*running_background_tasks)

    async def close(self) -> None:
        """Call `close()` method in all underlying transports."""
        await asyncio.gather(
            *[transport.close() for transport in self._transports.values()],
        )

    async def _background_listen(self, transport: ITransport) -> None:
        """Listen to transport and put incoming messages to local queue.

        Put `_SENTINEL` to local queue if transport disconnected.
        """
        try:
            async for message in transport.listen():
                self._put_in_local_queue(message)
        except ConnectionResetError:
            pass
        finally:
            self._put_in_local_queue(_SENTINEL)

    def _put_in_local_queue(self, object_: JsonType) -> None:
        """Put object to local queue with handling of `QueueFull` case."""
        try:
            self._local_messages_queue.put_nowait(object_)
        except asyncio.QueueFull:
            logger.critical(
                "`_put_in_local_queue`; local queue is full. "
                "This must not happen on runtime. "
                "Consider greater `local_queue_max_size` setting."
            )
