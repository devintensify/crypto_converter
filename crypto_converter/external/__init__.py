from crypto_converter.external.abstract.factory import IQuotesIOFactory
from crypto_converter.external.clickhouse import ChQuotesIOFactory


def get_quotes_io_factory(database_type: str) -> IQuotesIOFactory:
    """Create quotes i/o factory based on given `database_type`.

    Args:
        database_type (`str`): type of database to create i/o tools for.

    Returns:
        `IQuotesIOFactory`: object implementing `IQuotesIOFactory`.

    Raises:
        `NotImplementedError`: if cannot handle given `database_type`.

    """
    result: IQuotesIOFactory
    match database_type:
        case "clickhouse":
            result = ChQuotesIOFactory()
        case _:
            raise NotImplementedError
    return result
