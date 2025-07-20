from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientWebSocketResponse

from crypto_converter.quote_consumer.transport.websocket import WebSocketTransport


@pytest.fixture
def ws_url() -> str:
    return "wss://example.com/ws"


@pytest.fixture
def websocket_transport(ws_url: str) -> WebSocketTransport:
    return WebSocketTransport(ws_url)


@pytest.mark.asyncio
async def test_connect_success(
    websocket_transport: WebSocketTransport, ws_url: str
) -> None:
    mock_session = AsyncMock()
    mock_ws = AsyncMock(spec=ClientWebSocketResponse)
    mock_ws.closed = False
    mock_session.ws_connect.return_value = mock_ws

    with patch(
        "crypto_converter.external.session_pool.ClientSessionPool.get_instance"
    ) as get_pool:
        get_pool.return_value.get_session = AsyncMock(return_value=mock_session)

        await websocket_transport.connect()

        assert websocket_transport._connection is mock_ws
        mock_session.ws_connect.assert_called_once_with(url=ws_url)


@pytest.mark.asyncio
async def test_connect_failure(websocket_transport: WebSocketTransport) -> None:
    session = AsyncMock()
    session.ws_connect.side_effect = RuntimeError("fail")

    with patch(
        "crypto_converter.external.session_pool.ClientSessionPool.get_instance"
    ) as get_pool:
        get_pool.return_value.get_session = AsyncMock(return_value=session)

        with pytest.raises(ConnectionRefusedError):
            await websocket_transport.connect()


@pytest.mark.asyncio
async def test_send_success(websocket_transport: WebSocketTransport) -> None:
    mock_ws = AsyncMock()
    mock_ws.closed = False
    websocket_transport._connection = mock_ws

    message = {"type": "ping"}
    await websocket_transport.send(message)

    mock_ws.send_json.assert_awaited_once_with(message)


@pytest.mark.asyncio
async def test_send_disconnected(websocket_transport: WebSocketTransport) -> None:
    with pytest.raises(ConnectionResetError):
        await websocket_transport.send({"type": "ping"})


@pytest.mark.asyncio
async def test_send_fail_runtime(websocket_transport: WebSocketTransport) -> None:
    mock_ws = AsyncMock()
    mock_ws.closed = False
    mock_ws.send_json.side_effect = RuntimeError("fail")

    websocket_transport._connection = mock_ws
    with pytest.raises(ConnectionResetError):
        await websocket_transport.send({"type": "ping"})


@pytest.mark.asyncio
async def test_listen_yields_messages(websocket_transport: WebSocketTransport) -> None:
    mock_ws = AsyncMock()
    mock_ws.closed = False

    messages = [{"data": 1}, {"data": 2}]
    receive_json = AsyncMock(side_effect=messages)
    mock_ws.receive_json = receive_json

    websocket_transport._connection = mock_ws

    results = []
    async for msg in websocket_transport.listen():
        results.append(msg)
        if len(results) == len(messages):
            break

    assert results == messages


@pytest.mark.asyncio
async def test_listen_fail(websocket_transport: WebSocketTransport) -> None:
    mock_ws = AsyncMock()
    mock_ws.closed = False
    mock_ws.receive_json.side_effect = RuntimeError("fail")

    websocket_transport._connection = mock_ws

    with pytest.raises(ConnectionResetError):
        async for _ in websocket_transport.listen():
            pass


@pytest.mark.asyncio
async def test_close_success(websocket_transport: WebSocketTransport) -> None:
    mock_ws = AsyncMock()
    mock_ws.closed = False
    websocket_transport._connection = mock_ws

    await websocket_transport.close()

    mock_ws.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_already_closed(websocket_transport: WebSocketTransport) -> None:
    mock_ws = MagicMock()
    mock_ws.closed = True
    websocket_transport._connection = mock_ws

    await websocket_transport.close()  # should silently do nothing

    assert not hasattr(mock_ws, "close") or not mock_ws.close.called
