SHELL := /usr/bin/env bash
APP ?= app.main:app
PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help venv sync fmt lint type test run dev clean

help:
	@echo "venv     - create .venv and upgrade pip"
	@echo "sync     - install deps from requirements*.txt or pyproject (uv if available)"
	@echo "fmt      - black + ruff --fix"
	@echo "lint     - ruff check"
	@echo "type     - mypy"
	@echo "test     - pytest"
	@echo "run      - uvicorn $(APP) --reload"
	@echo "dev      - fmt, lint, type, test"
	@echo "clean    - remove caches"

venv:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip wheel

sync:
	@if command -v uv >/dev/null; then \
	  uv pip install -r requirements.txt || true; \
	  uv pip install -r requirements-dev.txt || true; \
	else \
	  [ -f requirements.txt ] && $(PIP) install -r requirements.txt || true; \
	  [ -f requirements-dev.txt ] && $(PIP) install -r requirements-dev.txt || true; \
	fi

fmt:
	$(PY) -m black .
	$(PY) -m ruff check --fix .

lint:
	$(PY) -m ruff check .

type:
	$(PY) -m mypy .

test:
	$(PY) -m pytest -q

run:
	$(PY) -m uvicorn $(APP) --reload --host 0.0.0.0 --port 8000

dev: fmt lint type test

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache **/__pycache__
