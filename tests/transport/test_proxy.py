import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest

from crypto_converter.quote_consumer.abstract.transport import ITransport, JsonType
from crypto_converter.quote_consumer.transport.proxy import _SENTINEL, ProxyTransport


@pytest.fixture
def mock_transport() -> ITransport:
    t = AsyncMock(spec=ITransport)
    t.listen = AsyncMock()
    return t


@pytest.fixture
def proxy_transport(mock_transport: ITransport) -> ProxyTransport:
    return ProxyTransport(transports={"a": mock_transport, "b": mock_transport})


@pytest.mark.asyncio
async def test_connect_all_transports_called() -> None:
    t1 = AsyncMock(spec=ITransport)
    t2 = AsyncMock(spec=ITransport)
    proxy = ProxyTransport({"t1": t1, "t2": t2})

    await proxy.connect()

    t1.connect.assert_awaited_once()
    t2.connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_all_transports_called() -> None:
    t1 = AsyncMock(spec=ITransport)
    t2 = AsyncMock(spec=ITransport)
    proxy = ProxyTransport({"t1": t1, "t2": t2})

    await proxy.close()

    t1.close.assert_awaited_once()
    t2.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_all_transports_called() -> None:
    t1 = AsyncMock(spec=ITransport)
    t2 = AsyncMock(spec=ITransport)
    proxy = ProxyTransport({"t1": t1, "t2": t2})
    message = {"type": "ping"}

    await proxy.send(message)

    t1.send.assert_awaited_once_with(message)
    t2.send.assert_awaited_once_with(message)


@pytest.mark.asyncio
async def test_listen_yields_messages() -> None:
    t1 = AsyncMock(spec=ITransport)
    t2 = AsyncMock(spec=ITransport)

    async def mock_stream(messages: list[JsonType]) -> AsyncGenerator[JsonType]:
        for msg in messages:
            yield msg
        await asyncio.sleep(1)

    t1.listen.return_value = mock_stream([{"msg": "1"}])
    t2.listen.return_value = mock_stream([{"msg": "2"}])

    proxy = ProxyTransport({"t1": t1, "t2": t2})

    messages = []
    expected_len_messages = 2
    async for m in proxy.listen():
        messages.append(m)
        if len(messages) == expected_len_messages:
            break

    assert {"msg": "1"} in messages
    assert {"msg": "2"} in messages


@pytest.mark.asyncio
async def test_listen_raises_on_sentinel() -> None:
    t1 = AsyncMock(spec=ITransport)

    async def broken_stream() -> AsyncGenerator[JsonType]:
        yield _SENTINEL  # симулируем закрытие

    t1.listen.return_value = broken_stream()
    proxy = ProxyTransport({"t1": t1})

    with pytest.raises(ConnectionResetError):
        async for _ in proxy.listen():
            pass


@pytest.mark.asyncio
async def test_background_listen_connection_reset_handled() -> None:
    t1 = AsyncMock(spec=ITransport)

    async def broken_stream() -> AsyncGenerator[JsonType]:
        raise ConnectionResetError
        yield

    t1.listen.side_effect = broken_stream

    proxy = ProxyTransport({"t1": t1})
    await proxy._background_listen(t1)

    item = proxy._local_messages_queue.get_nowait()
    assert item is _SENTINEL


def test_put_in_local_queue_fallback(capfd: pytest.CaptureFixture[str]) -> None:
    proxy = ProxyTransport({}, local_queue_max_size=1)
    proxy._local_messages_queue.put_nowait({"num": "first"})

    proxy._put_in_local_queue({"num": "second"})

    out, _ = capfd.readouterr()
    assert "local queue is full" in out
