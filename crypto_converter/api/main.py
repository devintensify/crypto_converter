"""Converter API entrypoint."""

import argparse
import asyncio
from contextlib import suppress

from uvicorn import Config, Server

from crypto_converter.api.app import app


async def _main() -> None:
    """Run converter api.

    Import `FastAPI` app instance from `app` module. Parse cli args.

    Run `uvicorn.Server.serve`
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True, help="Host for ASGI to be run on")
    parser.add_argument("--port", required=True, help="Port for ASGI to listen to")
    parser.add_argument("--reload", default=False)
    args, _ = parser.parse_known_args()

    config = Config(app, host=args.host, port=int(args.port), reload=args.reload)
    server = Server(config)

    await server.serve()


def main() -> None:
    """Run Converter API."""
    with suppress(asyncio.CancelledError, KeyboardInterrupt):
        asyncio.run(_main())


if __name__ == "__main__":
    main()
