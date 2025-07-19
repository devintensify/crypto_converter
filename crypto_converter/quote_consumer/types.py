"""Module with types and data models."""

import msgspec


class Quote(msgspec.Struct):
    """Data model of ticker price for instrument."""

    timestamp: str
    instrument: str
    value: float


QuotesContainer = dict[str, list[Quote]]
"""Mapping (instrument -> array of received quotes.)"""
