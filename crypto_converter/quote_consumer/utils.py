"""Module with types, utils and data models."""

from typing import TypedDict


class Quote(TypedDict):
    """Data model of ticker price for instrument.

    Do not use models with validation as it is redundant in case
    of one-way dumps.
    """

    timestamp: int
    """Received timestamp (in milliseconds)."""

    value: float
    """Ticker mid-price value."""


QuotesContainer = dict[str, list[Quote]]
"""Mapping (instrument -> array of received quotes.)"""
