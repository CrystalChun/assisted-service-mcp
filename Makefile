IMAGE_NAME ?= quay.io/carbonin/assisted-service-mcp
TAG ?= latest

.PHONY: build
build:
	podman build -t $(IMAGE_NAME):$(TAG) .

.PHONY: push
push:
	podman push $(IMAGE_NAME):$(TAG)

.PHONY: run
run:
	podman run --rm -p 127.0.0.1:8000:8000 $(IMAGE_NAME):$(TAG)

.PHONY: run-local
run-local:
	uv run server.py

.PHONY: test test-coverage test-verbose install-test-deps
test:
	uv run --group test pytest

test-coverage:
	uv run --group test pytest --cov=service_client --cov=server --cov-report=html --cov-report=term-missing

test-verbose:
	uv run --group test pytest -v

install-test-deps:
	uv sync --group test

.PHONY: black pylint pyright docstyle ruff check-types verify format
black:
	uv run black --check .

pylint:
	uv run pylint .

pyright:
	uv run pyright .

docstyle:
	uv run pydocstyle -v .

ruff:
	uv run ruff check .

check-types:
	uv run mypy --explicit-package-bases --disallow-untyped-calls --disallow-untyped-defs --disallow-incomplete-defs --ignore-missing-imports --disable-error-code attr-defined .

verify: black pylint pyright docstyle ruff check-types test

format:
	uv run black .
	uv run ruff check . --fix
