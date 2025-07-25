"""Quote consumer entrypoint."""

import asyncio
import signal
from typing import Any

from crypto_converter.external.session_pool import ClientSessionPool
from crypto_converter.quote_consumer.consumer import QuoteConsumer
from crypto_converter.quote_consumer.gateway import get_gateway
from crypto_converter.quote_consumer.log import get_logger, setup_logger
from crypto_converter.settings import SettingsProvider

logger = get_logger()


async def _main() -> None:
    """Run quote consumer.

    Create and start `IGateway`. Create and run `QuoteConsumer`.

    Release all resources on shutdown.
    """

    def _sigint_sigterm_handler(signal: int, _: Any) -> None:
        logger.info("Got signal=%s. Shutdown..", signal)
        raise asyncio.CancelledError

    signal.signal(signal.SIGINT, _sigint_sigterm_handler)
    signal.signal(signal.SIGTERM, _sigint_sigterm_handler)

    settings = SettingsProvider.get_instance().get_settings()
    gateway = get_gateway(settings.exchange_name)
    logger.info("Working with gateway: `%s`", gateway)
    await gateway.start()

    quote_consumer = QuoteConsumer(gateway=gateway.as_publisher())
    graceful_shutdown = True
    try:
        await quote_consumer.run()
    except asyncio.CancelledError:
        pass
    except BaseException as exc:
        graceful_shutdown = False
        logger.exception(
            "Quote consumer shutting down due to unexpected error..",
            *exc.args,
            stack_info=True,
        )
        raise
    finally:
        if graceful_shutdown:
            logger.info("Quote consumer shutting down gracefully..")
        await gateway.stop()
        await ClientSessionPool.shutdown()
        logger.info("Quote consumer finished.")


def main() -> None:
    """Run quote consumer."""
    setup_logger()
    asyncio.run(_main())


if __name__ == "__main__":
    main()
