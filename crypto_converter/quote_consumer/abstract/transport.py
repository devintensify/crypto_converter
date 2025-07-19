"""Interface of transport able to connect to given url."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from typing import Any

MessageHandler = Callable[[str], None]

JsonType = dict[str, Any] | list[Any]


class ITransport(ABC):
    """Interface of transport.

    Is able to connect to server by given url and exchange messages with it.

    Works with JSON-encoded data.

    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection with remote server.

        Raises:
            `ConnectionRefusedError`: if failed to connect to server.

        """

    @abstractmethod
    async def send(self, message: JsonType) -> None:
        """Send message to remote server.

        Args:
            message (`JsonType`): JSON-encoded message.

        Raises:
            `ConnectionResetError`: if connection is closed.

        """

    @abstractmethod
    async def listen(self) -> AsyncGenerator[JsonType]:
        """Read and yield messages from remote server.

        Returns:
            `AsyncGenerator[JsonType]`: asynchronous generator yielding messages.

        Raises:
            `ConnectionResetError`: if connection is closed.

        """
        yield {}

    @abstractmethod
    async def close(self) -> None:
        """Close connection to remote server."""
