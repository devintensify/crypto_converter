"""Data models to be used by app requests handlers."""

import re
from abc import ABC
from typing import Any, ClassVar

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


class BaseResponseModel(BaseModel, ABC):
    """Base model for handler response.

    Has class variable `http_code` for routing logic.
    """

    http_code: ClassVar[int]


class ConvertResponse(BaseResponseModel):
    """Response of successful conversion request processing."""

    http_code = 200

    amount: float
    conversion_rate: float


class ConvertResponseError(BaseResponseModel):
    """Base response of conversion request error.

    Contains `code` corresponding to each subclass model and optional message.
    """

    code: str
    message: str | None = Field(default=None)


class ConvertResponseQuoteOutdatedError(ConvertResponseError):
    """Response for error in case if requested ticker data is stale."""

    http_code = 201
    code: str = Field(default="Quotes outdated.", frozen=True)


class ConvertResponseNoQuotesError(ConvertResponseError):
    """Response for error in case if requested ticker data is absent."""

    http_code = 201
    code: str = Field(default="No data for ticker.", frozen=True)


class ConvertResponseInternalError(ConvertResponseError):
    """Response for internal server error."""

    http_code = 500
    code: str = Field(default="Internal error.", frozen=True)


class ConvertResponseInvalidQueryError(ConvertResponseError):
    """Response for invalid query params."""

    http_code = 400
    code: str = Field(default="Bad request.", frozen=True)


class HealthCheckResponse(BaseResponseModel):
    """Response of successful health check."""

    http_code = 200
    status: str = Field(default="OK", frozen=True)
