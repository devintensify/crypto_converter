"""Data models to be used by app requests handlers."""

import re
from typing import Any

from pydantic import BaseModel, Field

_ASSET_PATTERN = r"^[A-Z0-9]+$"


def _validate_asset(asset_value: str) -> bool:
    return re.fullmatch(_ASSET_PATTERN, asset_value) is not None


class ConvertQueryParams(BaseModel):
    """Input params for `GET` `/convert`."""

    amount: float
    from_asset: str
    to_asset: str
    timestamp: int | None = Field(default=None)

    def model_post_init(self, _: dict[str, Any]) -> None:
        """Require assets to consist only of uppercase letters or digits."""
        error_message: str | None = None
        if not _validate_asset(from_asset := self.from_asset):
            error_message = f"Invalid asset name: {from_asset}"
        elif not _validate_asset(to_asset := self.to_asset):
            error_message = f"Invalid asset name: {to_asset}"
        if error_message:
            raise ValueError(error_message)


class ConvertResponse(BaseModel):
    """Response of successful conversion request processing."""

    amount: float = Field(description="Amount in the target currency")
    conversion_rate: float = Field(description="Conversion rate used.")


class ConvertResponseError(BaseModel):
    """Base response of conversion request error.

    Contains `code` corresponding to each subclass model and optional message.
    """

    code: str = Field(description="Short message about error type.")
    message: str | None = Field(
        default=None, description="Additional information about error."
    )


class ConvertResponseQuoteOutdatedError(ConvertResponseError):
    """Response for error in case if requested ticker data is stale."""

    code: str = Field(default="Quotes outdated.", frozen=True)


class ConvertResponseNoQuotesError(ConvertResponseError):
    """Response for error in case if requested ticker data is absent."""

    code: str = Field(default="No data for ticker.", frozen=True)


class ConvertResponseInternalError(ConvertResponseError):
    """Response for internal server error."""

    code: str = Field(default="Internal error.", frozen=True)


class ConvertResponseInvalidQueryError(ConvertResponseError):
    """Response for invalid query params."""

    code: str = Field(default="Bad request.", frozen=True)


class HealthCheckResponse(BaseModel):
    """Response of successful health check."""

    status: str = Field(default="OK", description="Application status.", frozen=True)
