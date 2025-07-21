FROM python:3.13.5-slim

WORKDIR /app

RUN pip install --upgrade pip uv

COPY pyproject.toml .
COPY uv.lock .

RUN uv sync

COPY ./crypto_converter .
COPY ./logs .
