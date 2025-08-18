SHELL := /usr/bin/env bash
APP ?= app.main:app
PY := .venv/bin/python
PIP := .venv/bin/pip
POLICY_DIR ?= policies

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

dev: fmt lint type test pre-commit
	@echo "✅ Development workflow complete"

pre-commit: ## Run pre-commit hooks on all files
	@echo "🔍 Running pre-commit hooks..."
	pre-commit run --all-files

policy-test: ## Run OPA policy tests
	@command -v opa >/dev/null || (echo "Install opa (e.g. via mise: mise use opa@latest)" && exit 1)
	@opa test $(POLICY_DIR) -v

cov: ## Run tests with coverage report
	$(PY) -m pytest --cov=app --cov-report=term-missing

check: fmt lint type test policy-test ## Run all quality checks including policy tests

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache **/__pycache__
