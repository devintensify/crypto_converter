from crypto_converter.quote_consumer.abstract.gateway import IGateway
from crypto_converter.quote_consumer.gateway.bybit import BybitGateway


def get_gateway(exchange_name: str) -> IGateway:
    """Create gateway based on given `exchange_name`.

    Args:
        exchange_name (`str`): exchange name to connect to.

    Returns:
        `IGateway`: object implementing `IGateway` for specific exchange.

    Raises:
        `NotImplementedError`: if cannot handle given `exchange_name`.

    """
    result: IGateway
    match exchange_name:
        case "bybit":
            result = BybitGateway()
        case _:
            raise NotImplementedError
    return result
