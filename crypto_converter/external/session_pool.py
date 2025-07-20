"""Object able to provide access to aiohttp sessions."""

from typing import Self

from aiohttp import ClientSession, TCPConnector


class ClientSessionPool:
    """Object managing `ClientSession(-s)`.

    Able to provide opened `ClientSession` instances for creating connections.

    Controls all sessions' lifetimes.

    Should be instantiated on runtime using `get_instance` class method.
    """

    _instance: Self

    @classmethod
    def get_instance(cls) -> Self:
        """Get instance of `ClientSessionPool` to communicate with.

        Creates instance only once and reuse it in further calls.

        Returns:
            `ClientSessionPool`: instance able to provide `ClientSession`.

        """
        if (instance := cls._instance) is None:
            instance = cls()
            cls._instance = instance
        return instance

    def __init__(self) -> None:
        """Initialize `ClientSessionPool`."""
        self._session: ClientSession | None = None

    async def get_session(self) -> ClientSession:
        """Get running `ClientSession` instance.

        Returns:
            `ClientSession`: not-closed aiohttp session instance.

        """
        if (session := self._session) is None or session.closed:
            session = ClientSession(connector=TCPConnector(verify_ssl=False))
            self._session = session
        return session

    @classmethod
    async def shutdown(cls) -> None:
        """Release all resources of `ClientSessionPool` if it was initialized."""
        if (instance := cls._instance) is None:
            return
        await instance.close()

    async def close(self) -> None:
        """Close all owned `ClientSession` instances."""
        if (session := self._session) is None:
            return
        self._session = None
        if not session.closed:
            await session.close()
