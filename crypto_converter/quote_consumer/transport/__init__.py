from crypto_converter.quote_consumer.abstract.transport import ITransport
from crypto_converter.quote_consumer.transport.proxy import ProxyTransport
from crypto_converter.quote_consumer.transport.websocket import WebSocketTransport
from crypto_converter.settings import SettingsProvider


def _get_simple_transport(url: str, transport_protocol: str) -> ITransport:
    """Create simple transport based on given `transport_protocol`.

    Args:
        url (`str`): external resource identifier to be given to transport.
        transport_protocol (`str`): protocol of transport to work within.

    Returns:
        `ITransport`: transport instance.

    Raises:
        `NotImplementedError`: if cannot handle given `transport_protocol`

    """
    result: ITransport
    match transport_protocol:
        case "wss":
            result = WebSocketTransport(url)
        case _:
            raise NotImplementedError
    return result


def get_transport(url: str) -> ITransport:
    """Create transport based on settings to be used on runtime.

    Args:
        url (`str`): external resource identifier to be given to transport.

    Returns:
        `ITransport`: transport instance.

    Raises:
        `NotImplementedError`: if cannot handle any of `transport_protocol`-s

    """
    transport_config = SettingsProvider.get_instance().get_settings().transport
    connections = transport_config.connections
    transports: dict[str, ITransport] = {}
    for connection_protocol, number_of_connections in connections.items():
        for index in range(number_of_connections):
            transports[f"{connection_protocol}-{index}"] = _get_simple_transport(
                url, connection_protocol
            )
    return ProxyTransport(
        transports, local_queue_max_size=transport_config.local_queue_max_size
    )
