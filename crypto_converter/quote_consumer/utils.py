"""Module with types, utils and data models."""

import msgspec


class Quote(msgspec.Struct):
    """Data model of ticker price for instrument."""

    timestamp: int
    """Received timestamp."""

    value: float
    """Ticker mid-price value."""


QuotesContainer = dict[str, list[Quote]]
"""Mapping (instrument -> array of received quotes.)"""
