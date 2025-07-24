"""Quotes i/o tools working with clickhouse."""

import time
from contextlib import suppress

from aiochclient import ChClient
from aiohttp import ClientSession
from pydantic import AnyHttpUrl
from yarl import URL

from crypto_converter.external.abstract.errors import (
    InstrumentNotFoundError,
    TickerOutdatedError,
)
from crypto_converter.external.abstract.factory import IQuotesIOFactory
from crypto_converter.external.abstract.storage_reader import IQuotesReader
from crypto_converter.external.abstract.storage_writer import IQuotesWriter
from crypto_converter.log import log_awaitable_method
from crypto_converter.quote_consumer.utils import QuotesContainer
from crypto_converter.settings import SettingsProvider

_TABLE_NAME = "quotes"
_CREATE_QUOTES_TABLE_COMMAND = f"""
CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
    instrument String,
    timestamp UInt64,
    price Float64
) ENGINE = MergeTree()
ORDER BY (instrument, timestamp)
"""


class ChClientBase:
    """Base class for clickhouse storage client."""

    def __init__(self, dsn: AnyHttpUrl) -> None:
        """Initialize `ChQuotesWriter`.

        Args:
            dsn (`AnyHttpUrl`): storage url to connect to.

        """
        self._parsed_url = parsed_url = URL(dsn.encoded_string())
        self._session: ClientSession | None = None
        self._client: ChClient | None = None
        self._url_without_creds = (
            f"{parsed_url.scheme}://{parsed_url.host}:{parsed_url.port}"
        )

    @property
    def client(self) -> ChClient:
        """Get `_client` attribute."""
        assert self._client  # noqa: S101
        return self._client

    async def _open(self) -> None:
        """Create session to connect to clickhouse storage.

        Do nothing if session already exists and is not closed.
        """
        if (session := self._session) is not None and not session.closed:
            return
        self._session = new_session = ClientSession()

        parsed_url = self._parsed_url
        self._client = ChClient(
            session=new_session,
            url=self._url_without_creds,
            user=parsed_url.user,
            password=parsed_url.password,
            database=parsed_url.path.lstrip("/"),
        )

    async def close(self) -> None:
        """Close quotes writer. Close connection to clickhouse storage."""
        if (session := self._session) is None or session.closed:
            return

        self._session = None
        with suppress(Exception):
            await session.close()

        if (ch_client := self._client) is not None:
            self._client = None
            with suppress(Exception):
                await ch_client.close()


class ChQuotesWriter(ChClientBase, IQuotesWriter):
    """Implementation of `IQuotesWriter` working with clickhouse."""

    @log_awaitable_method(logger_name="quote_consumer")
    async def open(self) -> None:
        """Initialize underlying session and create table."""
        await self._open()
        await self._create_table()

    async def write(self, quotes: QuotesContainer) -> None:
        """Serialize and write records to clickhouse table."""
        table_rows: list[tuple[str, int, float]] = [
            (
                instrument,
                quote_record["timestamp"],
                quote_record["value"],
            )
            for instrument, quote_array in quotes.items()
            for quote_record in quote_array
        ]

        if not table_rows:
            return

        try:
            await self.client.execute(
                f"INSERT INTO {_TABLE_NAME} (instrument, timestamp, price) VALUES",
                *table_rows,
            )
        except Exception as exc:
            raise ConnectionResetError from exc

    @log_awaitable_method(logger_name="quote_consumer")
    async def delete_old_records(self, later_than_timestamp: int) -> None:
        """Drop old records from clickhouse table."""
        try:
            await self.client.execute(
                f"ALTER TABLE {_TABLE_NAME} DELETE WHERE "
                f"timestamp < {later_than_timestamp}"
            )
        except Exception as exc:
            raise ConnectionResetError from exc

    @log_awaitable_method(logger_name="quote_consumer")
    async def close(self) -> None:
        """Close quotes writer. Close connection to clickhouse storage."""
        await super().close()

    async def _create_table(self) -> None:
        """Create quotes table to write records to."""
        try:
            await self.client.execute(query=_CREATE_QUOTES_TABLE_COMMAND)
        except Exception as exc:
            raise ConnectionRefusedError from exc


class ChQuotesReader(ChClientBase, IQuotesReader):
    """Implementation of `IQuotesReader` working with clickhouse."""

    def __init__(self, dsn: str) -> None:
        """Initialize `ChQuotesReader`."""
        super().__init__(dsn)
        self._outdated_interval_ms: int = int(
            (
                SettingsProvider.get_instance()
                .get_settings()
                .quote_reader.outdated_interval
            )
            * 1e3
        )

    async def open(self) -> None:
        """Initialize underlying session."""
        await self._open()

    async def query(self, instrument: str, timestamp: int | None = None) -> float:
        """Query clickhouse table for ticker price."""
        query_timestamp = timestamp or int(time.time() * 1e3)
        # Query parameters validated in `converter_api`.
        rows = await self.client.fetch(
            f"""
            SELECT timestamp, price
            FROM {_TABLE_NAME}
            WHERE instrument = {self._quote_string(instrument)}
            AND timestamp < {query_timestamp}
            ORDER BY timestamp DESC
            LIMIT 1
        """  # noqa: S608
        )

        if not rows:
            raise InstrumentNotFoundError

        record = rows[0]
        latest_stored_timestamp = record["timestamp"]

        if query_timestamp - latest_stored_timestamp > self._outdated_interval_ms:
            raise TickerOutdatedError

        return record["price"]

    @staticmethod
    def _quote_string(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"


class ChQuotesIOFactory(IQuotesIOFactory):
    """Implementation of `IQuotesIOFactory` creating Ch-clients."""

    def get_reader(self) -> IQuotesReader:
        """Get `ChQuotesReader`."""
        clickhouse_settings = SettingsProvider.get_instance().get_settings().clickhouse
        assert clickhouse_settings  # noqa: S101
        return ChQuotesReader(clickhouse_settings.dsn)

    def get_writer(self) -> IQuotesWriter:
        """Get `ChQuotesWriter`."""
        clickhouse_settings = SettingsProvider.get_instance().get_settings().clickhouse
        assert clickhouse_settings  # noqa: S101
        return ChQuotesWriter(clickhouse_settings.dsn)
