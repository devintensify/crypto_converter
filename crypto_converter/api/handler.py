"""Handler backend for conversion requests."""

import asyncio

from crypto_converter.api import models
from crypto_converter.external.abstract.errors import (
    InstrumentNotFoundError,
    TickerOutdatedError,
)
from crypto_converter.external.abstract.storage_reader import IQuotesReader
from crypto_converter.log import log_awaitable_method, log_method
from crypto_converter.utils import cancel_and_wait


class ConversionHandler:
    """Object owning `IQuotesReader` able to serve conversion requests."""

    @log_method(logger_name="converter_api")
    def __init__(self, quotes_reader: IQuotesReader) -> None:
        """Initialize `ConversionHandler`.

        Args:
            quotes_reader (`IQuotesReader`): quotes reader able to query for quotes.

        """
        self._quotes_reader = quotes_reader
        self._reconnect_event = asyncio.Event()
        self._reconnect_task: asyncio.Task[None] | None = None

    @log_awaitable_method(logger_name="converter_api", level_on_attempt="info")
    async def open(self) -> None:
        """Open and maintain connection to quotes source in background."""
        self._reconnect_task = asyncio.create_task(self._storage_reconnect_loop())

    @log_awaitable_method(logger_name="converter_api")
    async def convert(
        self, params: models.ConvertQueryParams
    ) -> models.BaseResponseModel:
        """Execute valid conversion request.

        Args:
            params (`ConvertQueryParams`): valid data model of conversion request.

        Returns:
            `BaseResponseModel`: `Response` or `Error` data model.

        """
        instrument_name = f"{params.from_asset}/{params.to_asset}"
        response: models.BaseResponseModel
        try:
            conversion_rate = await self._quotes_reader.query(
                instrument_name, timestamp=params.timestamp
            )
        except ConnectionResetError:
            self._reconnect_event.set()
            response = models.ConvertResponseInternalError(
                message="No connection to quotes storage."
            )
        except InstrumentNotFoundError:
            response = models.ConvertResponseNoQuotesError()
        except TickerOutdatedError:
            response = models.ConvertResponseQuoteOutdatedError()
        except Exception as exc:
            response = models.ConvertResponseInternalError(
                message=f"Unexpected error while querying quotes source: `{exc}`"
            )
        else:
            conversion_amount = params.amount * conversion_rate
            response = models.ConvertResponse(
                amount=conversion_amount, conversion_rate=conversion_rate
            )
        return response

    @log_awaitable_method(logger_name="converter_api", level_on_attempt="info")
    async def close(self) -> None:
        """Close connection to quotes source. Stop maintaining it."""
        await cancel_and_wait(self._reconnect_task)
        await self._quotes_reader.close()

    @log_awaitable_method(logger_name="converter_api")
    async def _storage_reconnect_loop(self) -> None:
        """Monitor condition of quotes_reader connection through event.

        Reconnect if event is set from `convert()` method.
        """
        await self._quotes_reader.open()

        reconnect_interval = 1
        while True:
            await self._reconnect_event.wait()
            try:
                await self._quotes_reader.open()
            except ConnectionRefusedError:
                await asyncio.sleep(reconnect_interval)
            else:
                self._reconnect_event.clear()
