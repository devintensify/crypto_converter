"""Errors raised in `IQuotesReader.query()` method."""


class InstrumentNotFoundError(Exception):
    """Raised if no ticker data found for instrument."""


class TickerOutdatedError(Exception):
    """Raised if ticker data is outdated."""
