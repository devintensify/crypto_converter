"""Routers for requests handling."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import ValidationError

from crypto_converter.api.handler import ConversionHandler
from crypto_converter.api.models import (
    BaseResponseModel,
    ConvertQueryParams,
    ConvertResponseInvalidQueryError,
    HealthCheckResponse,
)

convert_router = APIRouter(prefix="/convert", tags=["convert"])
"""Router for conversion requests."""

system_router = APIRouter(prefix="/health_check", tags=["health_check"])
"""Router for system requests."""


def _get_conversion_handler(request: Request) -> ConversionHandler:
    return request.app.state.conversion_handler


@convert_router.get("")
async def convert(
    conversion_handler: Annotated[ConversionHandler, Depends(_get_conversion_handler)],
    amount: Annotated[float, Query(alias="amount")],
    from_asset: Annotated[str, Query(alias="from")],
    to_asset: Annotated[str, Query(alias="to")],
    timestamp: Annotated[int | None, Query(alias="timestamp")] = None,
) -> Response:
    """Execute handler for `GET` `/convert` request."""
    response_model: BaseResponseModel
    try:
        valid_query_model = ConvertQueryParams(
            amount=amount, from_asset=from_asset, to_asset=to_asset, timestamp=timestamp
        )
    except (ValidationError, ValueError) as exc:
        response_model = ConvertResponseInvalidQueryError(message=str(exc))
    else:
        response_model = await conversion_handler.convert(valid_query_model)
    return Response(
        content=response_model.model_dump_json(), status_code=response_model.http_code
    )


@system_router.get("")
async def health_check() -> Response:
    """Execute handler for `GET` `/health_check` request."""
    response_model = HealthCheckResponse()
    return Response(
        content=response_model.model_dump_json(), status_code=response_model.http_code
    )
