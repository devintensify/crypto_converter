# Crypto Converter

**Crypto Converter** is a Python-based service consisting of two components:

- **Currency Conversion API** – provides HTTP JSON API for converting cryptocurrency amounts for selected timestamp.
- **Quote Consumer** – continuously fetches real-time cryptocurrencies tickers prices from crypto exchange and stores them for conversion.

---

## Project Structure

This repository includes two services that run as **separate processes**, but share the same Docker image and codebase:

1. **Currency Conversion API**
   - Asynchronous HTTP API server for currency conversion.
   - Exposes endpoint `/convert`.

2. **Quote Consumer**
   - Connects to exchange via public API.
   - Stores quotes every 30 seconds.
   - Keeps only the last 7 days of data.

---

## Getting Started

### Prerequisites

To run this project in container, one needs to have the following installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

To run this project components locally, one needs to have the following installed:

- [Python 3.13](https://www.python.org/downloads/)
- [uv (Python package manager)](https://docs.astral.sh/uv/)

### Run the whole project in container

```bash
docker compose up
```

This will launch both services:
- the API (on `localhost:8000` by default);
- the quote consumer.

### Setting up environment for local development

```bash
# create virtual env
uv venv .venv --python=python3.13
source .venv/bin/activate

# install dependencies
uv sync --locked

# install pre-commit hooks
pre-commit install
```

This project also has a `Makefile`. Please run the following command in project directory to take a look at useful commands which are introduced to help one to perform code checks.

```bash
make help
```

### Manually run components
You can also run components individually using following commands:

```bash
uv run python -m crypto_converter.api.main --host localhost --port 8000
uv run python -m crypto_converter.quote_consumer.main
# note that the last one requires active quotes storage to be run.
```

---

## Configuration

The project is fully configurable using environment variables (see `.env.example`). Below variables are listed:

| Variable | Default | Description | Valid values |
|----------|---------|-------------|--------------|
| `exchange_name` || Name of the crypto exchange to get quotes from | `bybit`      |
| `database_type` || Type of database to be used as quotes storage  | `clickhouse` |
| `clickhouse__dsn` | `None` | ClickHouse DSN. Required if `database_type` is `clickhouse` | `URL-string` or `None` |
| `transport__connections` | `{"wss": 1}` | Config for creating connections with different protocols and quantity to connect to exchange | `{"wss": 1}` only
| `transport__local_queue_max_size` | `10000` | Low-level setting for `ProxyTransport` stability | `uint >= 10000`
| `quote_consumer__flush_interval` | `30` | Interval in seconds for writing quotes to storage | `uint <= 0.5 * quote_reader__outdated_interval` |
| `quote_consumer__delete_interval` | `7` | Interval in days after which data is dropped from storage | `uint` |
| `quote_consumer__logs_path` || Path to put quote consumer log files to | existing `Path` |
| `quote_reader__logs_path` || Path to put converter api log files to | existing `Path` |
| `quote_reader__outdated_interval` | `60` | Interval in seconds after which ticker record becomes outdated | `uint`

> Currently supported exchanges:
> - `bybit` (via public WebSocket connection)
> _(one can implement connections to other quotes sources)_

> Storage backend:
> - `clickhouse` (via `aiohttp` session wrapped into `aiochclient`).
> _(one can implement i/o to other quotes storages)_

> API Framework:
> - Uses `FastAPI` with full async support and Swagger UI.

---

## Documentation
- Swagger UI: http://localhost:8000/docs (is able after api service started)
- Diagram on Miro: https://miro.com/app/board/uXjVJdWfJRM=/

One can also take a look at interfaces declared in `abstract` modules in code-base to get brief descriptions of interface methods.
