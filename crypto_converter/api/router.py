"""Routers for requests handling."""

from typing import Annotated, Union

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ValidationError

from crypto_converter.api import models
from crypto_converter.api.handler import ConversionHandler

_ConvertEndpointResponseModel = Union[
    models.ConvertResponse,
    models.ConvertResponseQuoteOutdatedError,
    models.ConvertResponseNoQuotesError,
    models.ConvertResponseInternalError,
    models.ConvertResponseInvalidQueryError,
]

convert_router = APIRouter(prefix="/convert", tags=["convert"])
"""Router for conversion requests."""

system_router = APIRouter(prefix="/health_check", tags=["health_check"])
"""Router for system requests."""


def _get_conversion_handler(request: Request) -> ConversionHandler:
    return request.app.state.conversion_handler


@convert_router.get(
    "",
    response_model=_ConvertEndpointResponseModel,
    responses={
        400: {"model": models.ConvertResponseInvalidQueryError},
        500: {"model": models.ConvertResponseInternalError},
    },
)
async def convert(
    conversion_handler: Annotated[ConversionHandler, Depends(_get_conversion_handler)],
    amount: Annotated[float, Query(alias="amount", description="Amount to convert")],
    from_asset: Annotated[str, Query(alias="from", description="Source asset")],
    to_asset: Annotated[str, Query(alias="to", description="Target asset")],
    timestamp: Annotated[
        int | None, Query(alias="timestamp", description="Date timestamp")
    ] = None,
) -> BaseModel:
    """Execute handler for `GET` `/convert` request."""
    response_model: BaseModel
    try:
        valid_query_model = models.ConvertQueryParams(
            amount=amount, from_asset=from_asset, to_asset=to_asset, timestamp=timestamp
        )
    except (ValidationError, ValueError) as exc:
        response_model = models.ConvertResponseInvalidQueryError(message=str(exc))
    else:
        response_model = await conversion_handler.convert(valid_query_model)
    return response_model


@system_router.get("", response_model=models.HealthCheckResponse)
async def health_check() -> models.HealthCheckResponse:
    """Execute handler for `GET` `/health_check` request."""
    return models.HealthCheckResponse()
