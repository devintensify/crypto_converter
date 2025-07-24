"""Converter API app.

Is a demo version without rate limiting and performance/load tests.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from crypto_converter.api.handler import ConversionHandler
from crypto_converter.api.log import setup_logger
from crypto_converter.api.middleware import RoundtripReporterMiddleware
from crypto_converter.api.router import convert_router, system_router
from crypto_converter.external import get_quotes_io_factory
from crypto_converter.settings import SettingsProvider


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Control app actions on start and on stop."""
    setup_logger()
    settings = SettingsProvider.get_instance().get_settings()
    quotes_reader = get_quotes_io_factory(settings.database_type).get_reader()
    conversion_handler = ConversionHandler(quotes_reader)
    app.state.conversion_handler = conversion_handler
    await conversion_handler.open()
    yield
    await conversion_handler.close()


app = FastAPI(lifespan=lifespan)
app.include_router(convert_router)
app.include_router(system_router)

app.add_middleware(RoundtripReporterMiddleware)
