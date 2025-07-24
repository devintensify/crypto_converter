"""Quotes consumer."""

import asyncio
import time
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from crypto_converter.external import get_quotes_io_factory
from crypto_converter.log import log_awaitable_method, log_method
from crypto_converter.quote_consumer.abstract.gateway import GatewayPublisherP
from crypto_converter.settings import SettingsProvider
from crypto_converter.utils import cancel_and_wait

if TYPE_CHECKING:
    from crypto_converter.external.abstract.storage_writer import IQuotesWriter
    from crypto_converter.quote_consumer.utils import QuotesContainer


class QuoteConsumer:
    """Quotes consumer object.

    Implements top-level logic of `quote_consumer` service.
    """

    @log_method(
        logger_name="quote_consumer", level_on_attempt="info", log_kwargs=["gateway"]
    )
    def __init__(self, gateway: GatewayPublisherP) -> None:
        """Initialize `QuoteConsumer`.

        Initialize external storage writer.

        Args:
            gateway (`GatewayPublisherP`): object to receive quotes updates from.

        """
        self._gateway = gateway

        settings = SettingsProvider.get_instance().get_settings()
        self._writer: IQuotesWriter = get_quotes_io_factory(
            settings.database_type
        ).get_writer()

        self._local_queue: asyncio.Queue[QuotesContainer] = asyncio.Queue()
        self._flush_interval = settings.quote_consumer.flush_interval
        self._last_flushed: float | None = None

    @log_awaitable_method(logger_name="quote_consumer", level_on_attempt="info")
    async def run(self) -> None:
        """Run `QuoteConsumer`.

        Register self in quotes events publisher. Maintain quotes writer lifetime.
        """
        writer = self._writer
        self._gateway.register(self)

        delete_old_records_task: asyncio.Task[None] | None = None
        reconnect_interval = 5
        try:
            while True:
                try:
                    await writer.open()
                    delete_old_records_task = asyncio.create_task(
                        self._delete_old_records_task()
                    )
                    await self._listen_local_queue()
                except (ConnectionRefusedError, ConnectionResetError):
                    await self._cancel_and_wait(delete_old_records_task)
                    await asyncio.sleep(reconnect_interval)
        finally:
            await writer.close()

    @log_method(logger_name="quote_consumer")
    def on_quotes_update(self) -> None:
        """Pull and put new quotes to local queue."""
        quotes = self._gateway.get_quotes()
        self._local_queue.put_nowait(quotes)

    @log_awaitable_method(logger_name="quote_consumer")
    async def _delete_old_records_task(self) -> None:
        """Periodically delete old records from external storage."""
        writer = self._writer
        delete_interval = (
            SettingsProvider.get_instance()
            .get_settings()
            .quote_consumer.delete_interval
        )
        delete_interval_timedelta = timedelta(days=delete_interval)
        delete_interval = 10 * 60  # 10 minutes
        while True:
            datetime_left_boundary = datetime.now(tz=UTC) - delete_interval_timedelta
            timestamp_left_boundary = int(datetime_left_boundary.timestamp() * 1e3)
            await asyncio.gather(
                writer.delete_old_records(later_than_timestamp=timestamp_left_boundary),
                asyncio.sleep(delete_interval),
            )

    @log_awaitable_method(logger_name="quote_consumer")
    async def _listen_local_queue(self) -> None:
        """Listen local queue in infinite loop.

        Flush updates after specific interval.
        """
        flush_interval = self._flush_interval

        while True:
            now = time.monotonic()
            last_flushed = self._last_flushed
            quotes = await self._local_queue.get()
            if last_flushed is None or now - last_flushed > flush_interval:
                await self._writer.write(quotes)
                self._last_flushed = now

    @log_awaitable_method(logger_name="quote_consumer")
    async def _cancel_and_wait(self, *tasks: asyncio.Task | None) -> None:
        await cancel_and_wait(*tasks)
