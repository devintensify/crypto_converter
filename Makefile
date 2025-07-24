PROJECT_NAME = ./crypto_converter/
TESTS_FOLDER = ./tests/
PYTHON = python3.13
UV = uv
VENV = .venv

help:
	@echo "Use one of the following commands:"
	@echo "  make setup    - Create virtual env and install dependencies"
	@echo "  make lint     - Run Ruff linter"
	@echo "  make format   - Run isort and Ruff formatter"
	@echo "  make prod     - Run complex code checking: format, lint, unit tests. Is highly recommended to use before pushing commits."
	@echo "  make test     - Run unit tests"
	@echo "  make test-cov - Run unit tests with code coverage report"

setup:
	$(UV) venv
	$(UV) pip install --group dev

lint:
	$(UV) run ruff check $(PROJECT_NAME) $(TESTS_FOLDER)

format:
	$(UV) run isort $(PROJECT_NAME) $(TESTS_FOLDER)
	$(UV) run ruff format $(PROJECT_NAME) $(TESTS_FOLDER)

format-check-only:
	$(UV) run isort --check-only $(PROJECT_NAME) $(TESTS_FOLDER)
	$(UV) run ruff format --check $(PROJECT_NAME) $(TESTS_FOLDER)

test:
	$(UV) run pytest $(TESTS_FOLDER)

test-cov:
	$(UV) run pytest --cov=$(PROJECT_NAME) --cov-report=html

prod: format lint test-cov
