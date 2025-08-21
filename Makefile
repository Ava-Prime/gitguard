SHELL := /usr/bin/env bash
APP ?= app.main:app
PY := .venv/bin/python
PIP := .venv/bin/pip
POLICY_DIR ?= policies

.PHONY: help venv sync fmt lint type test run dev clean self-dogfood dogfood-status dogfood-stop

help:
	@echo "venv         - create .venv and upgrade pip"
	@echo "sync         - install deps from requirements*.txt or pyproject (uv if available)"
	@echo "fmt          - black + ruff --fix"
	@echo "lint         - ruff check"
	@echo "type         - mypy"
	@echo "test         - pytest"
	@echo "run          - uvicorn $(APP) --reload"
	@echo "dev          - fmt, lint, type, test"
	@echo "clean        - remove caches"
	@echo "self-dogfood - 🐕 Setup GitGuard to monitor itself (local development)"
	@echo "dogfood-status - Check status of self-dogfooding setup"
	@echo "dogfood-stop - Stop self-dogfooding services"

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

self-dogfood: ## 🐕 Setup GitGuard to monitor itself (local development)
	@echo "🐕 Setting up GitGuard self-dogfooding..."
	@echo "📋 Prerequisites check:"
	@command -v docker >/dev/null || (echo "❌ Docker not found. Install Docker Desktop" && exit 1)
	@command -v docker-compose >/dev/null || docker compose version >/dev/null || (echo "❌ Docker Compose not found" && exit 1)
	@command -v gh >/dev/null || (echo "⚠️  GitHub CLI not found. Install 'gh' for easier setup" && exit 1)
	@echo "✅ Prerequisites satisfied"
	@echo ""
	@echo "🔧 Creating .env.dogfood file..."
	@echo "# GitGuard Self-Dogfooding Configuration" > .env.dogfood
	@echo "# Generated on $$(date)" >> .env.dogfood
	@echo "" >> .env.dogfood
	@echo "# GitHub App Configuration (REQUIRED - set these after creating your GitHub App)" >> .env.dogfood
	@echo "GITHUB_APP_ID=" >> .env.dogfood
	@echo "GITHUB_APP_PRIVATE_KEY=" >> .env.dogfood
	@echo "GITHUB_WEBHOOK_SECRET=" >> .env.dogfood
	@echo "" >> .env.dogfood
	@echo "# GitGuard Configuration" >> .env.dogfood
	@echo "GITGUARD_MODE=report-only" >> .env.dogfood
	@echo "GITGUARD_LOG_LEVEL=info" >> .env.dogfood
	@echo "GITGUARD_WEBHOOK_PATH=/webhook/github" >> .env.dogfood
	@echo "" >> .env.dogfood
	@echo "# Database Configuration" >> .env.dogfood
	@echo "POSTGRES_DB=gitguard" >> .env.dogfood
	@echo "POSTGRES_USER=gitguard" >> .env.dogfood
	@echo "POSTGRES_PASSWORD=gitguard-dev-$$(date +%s)" >> .env.dogfood
	@echo "" >> .env.dogfood
	@echo "# Temporal Configuration" >> .env.dogfood
	@echo "TEMPORAL_HOST=localhost:7233" >> .env.dogfood
	@echo "TEMPORAL_NAMESPACE=gitguard" >> .env.dogfood
	@echo ""
	@echo "🚀 Starting GitGuard services..."
	@docker-compose -f docker-compose.temporal.yml --env-file .env.dogfood up -d
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo ""
	@echo "🎉 GitGuard is now running in self-dogfood mode!"
	@echo ""
	@echo "📋 NEXT STEPS:"
	@echo "1. Create a GitHub App:"
	@echo "   • Go to: https://github.com/settings/apps/new"
	@echo "   • Click 'Create from manifest' and paste contents of app.json"
	@echo "   • After creation, click 'Install App' and select Ava-Prime/gitguard"
	@echo ""
	@echo "2. Configure your GitHub App secrets in .env.dogfood:"
	@echo "   • GITHUB_APP_ID=<your-app-id>"
	@echo "   • GITHUB_APP_PRIVATE_KEY=<paste-your-private-key>"
	@echo "   • GITHUB_WEBHOOK_SECRET=<choose-a-random-string>"
	@echo ""
	@echo "3. Expose your local server to GitHub:"
	@echo "   • Install ngrok: https://ngrok.com/download"
	@echo "   • Run: ngrok http 8080"
	@echo "   • Set webhook URL to: https://<your-ngrok-url>/webhook/github"
	@echo ""
	@echo "4. Test the setup:"
	@echo "   • make dogfood-status  # Check service health"
	@echo "   • Open http://localhost:8080  # GitGuard UI"
	@echo "   • Open http://localhost:3000  # Grafana dashboards"
	@echo ""
	@echo "5. Create a test PR to trigger GitGuard:"
	@echo "   • git checkout -b test/dogfood-check"
	@echo "   • echo 'self-dogfood test' >> DOGFOOD.md"
	@echo "   • git add . && git commit -m 'test: trigger GitGuard'"
	@echo "   • git push -u origin HEAD && gh pr create --fill"
	@echo ""
	@echo "🔗 Useful URLs:"
	@echo "   GitGuard UI:      http://localhost:8080"
	@echo "   Grafana:          http://localhost:3000 (admin/admin)"
	@echo "   Policy API:       http://localhost:8080/api/v1/policies/evaluate"
	@echo "   Health Check:     http://localhost:8080/health"

dogfood-status: ## Check status of self-dogfooding services
	@echo "🔍 GitGuard Self-Dogfood Status:"
	@echo ""
	@echo "📊 Docker Services:"
	@docker-compose -f docker-compose.temporal.yml ps 2>/dev/null || echo "❌ Services not running. Run 'make self-dogfood' first."
	@echo ""
	@echo "🌐 Service Health Checks:"
	@echo -n "GitGuard API:     "
	@curl -s http://localhost:8080/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not responding"
	@echo -n "Grafana:          "
	@curl -s http://localhost:3000/api/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not responding"
	@echo -n "Temporal:         "
	@curl -s http://localhost:8233/api/v1/namespaces >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not responding"
	@echo ""
	@echo "📋 Configuration:"
	@[ -f .env.dogfood ] && echo "✅ .env.dogfood exists" || echo "❌ .env.dogfood missing"
	@[ -f app.json ] && echo "✅ GitHub App manifest ready" || echo "❌ app.json missing"
	@echo ""
	@echo "🔗 Quick Links:"
	@echo "   GitGuard UI:      http://localhost:8080"
	@echo "   Grafana:          http://localhost:3000"
	@echo "   Policy Evaluation: curl http://localhost:8080/api/v1/policies/evaluate"

dogfood-stop: ## Stop self-dogfooding services
	@echo "🛑 Stopping GitGuard self-dogfood services..."
	@docker-compose -f docker-compose.temporal.yml down
	@echo "✅ Services stopped. Data preserved in Docker volumes."
	@echo "💡 To restart: make self-dogfood"
	@echo "💡 To clean up completely: docker-compose -f docker-compose.temporal.yml down -v"
