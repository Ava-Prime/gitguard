.PHONY: help setup up down restart logs clean test test-fast lint format build bootstrap sync-labels demo demo-setup demo-low-risk demo-medium-risk demo-high-risk demo-security demo-release-window demo-dashboard demo-video demo-risk-low demo-risk-medium demo-risk-high demo-risk-security demo-quick demo-investor demo-customer demo-customer-plus-knowledge health metrics debug backup-config update-deps docker-clean docs docs-serve docs-init docs-serve-bg graph

# Color definitions for better UX
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
MAGENTA := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[0;37m
NC := \033[0m # No Color

# Configuration
COMPOSE_FILE := ops/compose.yml
DEMO_SCRIPT := scripts/demo.sh

# Default target
help: ## Show this help message with categories
	@echo -e "$(CYAN)GitGuard - Autonomous Repository Steward$(NC)"
	@echo -e "$(BLUE)═══════════════════════════════════════$(NC)"
	@echo ""
	@echo -e "$(GREEN)📦 DEVELOPMENT:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## Development:' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## Development: "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)⚙️  OPERATIONS:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## Operations:' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## Operations: "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(MAGENTA)🎬 DEMOS:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## Demo:' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## Demo: "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(BLUE)💡 EXAMPLES:$(NC)"
	@echo -e "  $(CYAN)make demo-quick$(NC)      # 2-minute demo"
	@echo -e "  $(CYAN)make demo-investor$(NC)   # 5-minute investor pitch"
	@echo -e "  $(CYAN)make demo-customer$(NC)   # 10-minute technical demo"
	@echo ""

# =============================================================================
# DEVELOPMENT
# =============================================================================

setup: ## Development: Install dependencies and setup development environment
	@echo -e "$(CYAN)📦 Setting up GitGuard development environment...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo -e "$(GREEN)✅ Development environment ready$(NC)"

test: ## Development: Run all tests with coverage
	@echo -e "$(CYAN)🧪 Running GitGuard tests...$(NC)"
	pytest tests/ -v --cov=apps --cov-report=html --cov-report=term
	@echo -e "$(GREEN)✅ Tests completed. Coverage report: htmlcov/index.html$(NC)"

test-fast: ## Development: Run tests without coverage (faster)
	@echo -e "$(CYAN)⚡ Running fast tests...$(NC)"
	pytest tests/ -v -x

test-initial-dev: ## Development: Run tests with initial development phase coverage (60%)
	@echo -e "$(CYAN)🚀 Running tests for initial development phase...$(NC)"
	pytest tests/ -v --cov=apps --cov-report=html --cov-report=term \
		--cov-fail-under=60 \
		-m 'not (incomplete_fixtures or requires_full_implementation)'
	@echo -e "$(GREEN)✅ Initial dev tests completed (60% threshold)$(NC)"

test-feature-dev: ## Development: Run tests with feature development phase coverage (70%)
	@echo -e "$(CYAN)🔧 Running tests for feature development phase...$(NC)"
	pytest tests/ -v --cov=apps --cov-report=html --cov-report=term \
		--cov-fail-under=70 \
		-m 'not incomplete_fixtures'
	@echo -e "$(GREEN)✅ Feature dev tests completed (70% threshold)$(NC)"

test-pre-production: ## Development: Run tests with pre-production phase coverage (80%)
	@echo -e "$(CYAN)🎯 Running tests for pre-production phase...$(NC)"
	pytest tests/ -v --cov=apps --cov-report=html --cov-report=term \
		--cov-fail-under=80 --strict-markers --strict-config
	@echo -e "$(GREEN)✅ Pre-production tests completed (80% threshold)$(NC)"

test-production: ## Development: Run tests with production phase coverage (85%)
	@echo -e "$(CYAN)🏭 Running tests for production phase...$(NC)"
	pytest tests/ -v --cov=apps --cov-report=html --cov-report=term \
		--cov-fail-under=85 --strict-markers --strict-config
	@echo -e "$(GREEN)✅ Production tests completed (85% threshold)$(NC)"

test-coverage-delta: ## Development: Validate coverage delta between branches
	@echo -e "$(CYAN)📊 Validating coverage delta...$(NC)"
	@if [ -z "$(BASE_REF)" ]; then \
		echo -e "$(RED)❌ BASE_REF not set. Usage: make test-coverage-delta BASE_REF=main$(NC)"; \
		exit 1; \
	fi
	python scripts/validate_coverage_delta.py \
		--threshold=-2.0 \
		--base-ref=$(BASE_REF) \
		--head-ref=HEAD
	@echo -e "$(GREEN)✅ Coverage delta validation completed$(NC)"

test-detect-phase: ## Development: Detect development phase for current changes
	@echo -e "$(CYAN)🔍 Detecting development phase...$(NC)"
	@CHANGED_FILES=$$(git diff --name-only HEAD~1 HEAD | tr '\n' ','); \
	python scripts/coverage_gate_detector.py --changed-files="$$CHANGED_FILES"
	@echo -e "$(GREEN)✅ Phase detection completed$(NC)"

test.e2e: ## Development: Run end-to-end codex PR tests
	@echo -e "$(CYAN)🔄 Running end-to-end codex PR tests...$(NC)"
	pytest -q tests/e2e_codex_pr.py

test.chaos: ## Development: Run chaos engineering drills
	@echo -e "$(CYAN)🌪️  Running chaos engineering drills...$(NC)"
	pytest -q tests/chaos_drills.py -v

chaos.slow-publish: ## Development: One-command staging drill (alerts + retries)
	@echo -e "$(CYAN)🚨 Starting chaos drill: Slow publish with alert testing...$(NC)"
	@echo -e "$(YELLOW)This will trigger CodexBuildStall alert and test JetStream redelivery$(NC)"
	# Force a retry by making publish_portal fail once & slow after
	FAULT_ONCE_DELIVERY_ID=ALERT-TEST PUBLISH_SLOW_MS=90000 \
	docker compose exec guard-codex bash -lc 'python - <<PY\nprint("armed")\nPY'; \
	python - <<'PY'\nimport os, json, asyncio\nfrom nats.aio.client import Client as NATS\nasync def go():\n nc=NATS(); await nc.connect(servers=[os.getenv('NATS_URL','nats://localhost:4222')]); js=nc.jetstream();\n evt={'event':'pull_request','delivery_id':'ALERT-TEST','pull_request':{'number':901,'head':{'sha':'HEAD'}},'repository':{'full_name':'org/repo'}}\n await js.publish('gh.pull_request.opened', json.dumps(evt).encode()); await nc.drain()\nasyncio.run(go())\nPY
	@echo -e "$(GREEN)✅ Chaos drill initiated. Watch for:$(NC)"
	@echo -e "$(CYAN)  • CodexBuildStall alert fire, then auto-resolve$(NC)"
	@echo -e "$(CYAN)  • JetStream redelivery logged, workflow succeeds$(NC)"

lint: ## Development: Run comprehensive linting checks
	@echo -e "$(CYAN)🔍 Running linting checks...$(NC)"
	flake8 apps/ --max-line-length=88 --extend-ignore=E203,W503
	black --check apps/
	mypy apps/ --ignore-missing-imports
	bandit -r apps/ -f json -o security-report.json || true
	@echo -e "$(GREEN)✅ Linting completed$(NC)"

format: ## Development: Format code with black and isort
	@echo -e "$(CYAN)✨ Formatting code...$(NC)"
	black apps/
	isort apps/ --profile black
	@echo -e "$(GREEN)✅ Code formatted$(NC)"

build: ## Development: Build all Docker images
	@echo -e "$(CYAN)🏗️  Building GitGuard Docker images...$(NC)"
	docker compose -f $(COMPOSE_FILE) build
	@echo -e "$(GREEN)✅ Images built successfully$(NC)"

# =============================================================================
# OPERATIONS
# =============================================================================

up: ## Operations: Start all GitGuard services
	@echo -e "$(CYAN)🚀 Starting GitGuard services...$(NC)"
	docker compose -f $(COMPOSE_FILE) up -d
	@docker compose -f $(COMPOSE_FILE) up -d --build codex
	@echo -e "$(GREEN)✅ GitGuard is running!$(NC)"
	@echo -e "$(BLUE)🌐 API: http://localhost:8000$(NC)"
	@echo -e "$(BLUE)📊 Grafana: http://localhost:3000 (admin/admin)$(NC)"
	@echo -e "$(BLUE)🔍 Temporal UI: http://localhost:8233$(NC)"

down: ## Operations: Stop all GitGuard services
	@echo -e "$(CYAN)🛑 Stopping GitGuard services...$(NC)"
	docker compose -f $(COMPOSE_FILE) down
	@echo -e "$(GREEN)✅ Services stopped$(NC)"

restart: ## Operations: Restart GitGuard services
	@echo -e "$(CYAN)🔄 Restarting GitGuard services...$(NC)"
	docker compose -f $(COMPOSE_FILE) restart
	@echo -e "$(GREEN)✅ Services restarted$(NC)"

logs: ## Operations: Show live service logs
	@echo -e "$(CYAN)📋 GitGuard service logs (Ctrl+C to exit):$(NC)"
	docker compose -f $(COMPOSE_FILE) logs -f

clean: ## Operations: Clean up containers, volumes, and images
	@echo -e "$(CYAN)🧹 Cleaning up GitGuard resources...$(NC)"
	docker compose -f $(COMPOSE_FILE) down -v
	docker system prune -f
	@echo -e "$(GREEN)✅ Cleanup completed$(NC)"

bootstrap: ## Operations: Bootstrap a repository with GitGuard
	@echo -e "$(CYAN)🎯 Bootstrapping repository...$(NC)"
	@chmod +x scripts/bootstrap.sh
	@./scripts/bootstrap.sh
	@echo -e "$(GREEN)✅ Repository bootstrapped$(NC)"

sync-labels: ## Operations: Sync GitHub labels with GitGuard configuration
	@echo -e "$(CYAN)🏷️  Syncing GitHub labels...$(NC)"
	python scripts/sync_labels.py
	@echo -e "$(GREEN)✅ Labels synchronized$(NC)"

prometheus-reload: ## Operations: Reload Prometheus configuration and verify alerts
	@echo -e "$(CYAN)📊 Reloading Prometheus configuration...$(NC)"
	@if command -v pwsh >/dev/null 2>&1; then \
		pwsh -File scripts/reload_prometheus.ps1; \
	else \
		chmod +x scripts/reload_prometheus.sh && ./scripts/reload_prometheus.sh; \
	fi
	@echo -e "$(GREEN)✅ Prometheus configuration reloaded$(NC)"

validate-github: ## Validate GitHub workflow configuration
	@if command -v pwsh >/dev/null 2>&1; then \
		pwsh -File scripts/validate_github.ps1; \
	else \
		if [ -f ".github/workflows/codex-docs.yml" ]; then \
			echo -e "$(GREEN)✅ codex-docs.yml workflow found$(NC)"; \
			if grep -q "pull_request:" .github/workflows/codex-docs.yml; then \
				echo -e "$(GREEN)✅ PR trigger configured$(NC)"; \
			else \
				echo -e "$(RED)❌ PR trigger missing$(NC)"; \
			fi; \
			if grep -q "thollander/actions-comment-pull-request" .github/workflows/codex-docs.yml; then \
				echo -e "$(GREEN)✅ PR comment action configured$(NC)"; \
			else \
				echo -e "$(RED)❌ PR comment action missing$(NC)"; \
			fi; \
			if grep -q "CODEX_BASE_URL" .github/workflows/codex-docs.yml; then \
				echo -e "$(GREEN)✅ CODEX_BASE_URL variable referenced$(NC)"; \
				echo -e "$(YELLOW)⚠️  Remember to set CODEX_BASE_URL in repository variables$(NC)"; \
			else \
				echo -e "$(RED)❌ CODEX_BASE_URL variable missing$(NC)"; \
			fi; \
		else \
			echo -e "$(RED)❌ codex-docs.yml workflow not found$(NC)"; \
		fi; \
		echo -e "$(BLUE)📖 See docs/GITHUB_INTEGRATION.md for setup instructions$(NC)"; \
	fi

test-secrets: ## Test secrets redaction functionality
	@echo -e "$(CYAN)🔐 Testing secrets hygiene...$(NC)"
	@if command -v python >/dev/null 2>&1; then \
		python test_secrets_redaction.py; \
	else \
		echo -e "$(RED)❌ Python not found$(NC)"; \
		echo -e "$(BLUE)📖 See docs/SECRETS_HYGIENE.md for setup instructions$(NC)"; \
	fi

# =============================================================================
# BACKUP & RESTORE
# =============================================================================

backup-postgres: ## Operations: Create PostgreSQL backup with 7-day retention
	@echo -e "$(CYAN)💾 Creating PostgreSQL backup...$(NC)"
	@if [ -z "$$DATABASE_URL" ]; then \
		echo -e "$(RED)❌ DATABASE_URL environment variable not set$(NC)"; \
		echo -e "$(BLUE)💡 Set DATABASE_URL and try again$(NC)"; \
		exit 1; \
	fi
	@chmod +x scripts/backup_postgres.sh
	@./scripts/backup_postgres.sh
	@echo -e "$(GREEN)✅ PostgreSQL backup completed$(NC)"

backup-jetstream: ## Operations: Create JetStream snapshot for pre-deployment
	@echo -e "$(CYAN)🌊 Creating JetStream snapshot...$(NC)"
	@chmod +x scripts/backup_jetstream.sh
	@./scripts/backup_jetstream.sh GH
	@echo -e "$(GREEN)✅ JetStream snapshot completed$(NC)"

backup-all: ## Operations: Create both PostgreSQL and JetStream backups
	@echo -e "$(CYAN)📦 Creating complete backup set...$(NC)"
	@$(MAKE) backup-postgres
	@$(MAKE) backup-jetstream
	@echo -e "$(GREEN)🎉 Complete backup set created$(NC)"

restore-rehearsal: ## Operations: Run weekly restore rehearsal in staging
	@echo -e "$(CYAN)🎭 Running restore rehearsal...$(NC)"
	@if [ "$$ENVIRONMENT" != "staging" ]; then \
		echo -e "$(YELLOW)⚠️  Warning: Not running in staging environment$(NC)"; \
		echo -e "$(BLUE)💡 Set ENVIRONMENT=staging for proper rehearsal$(NC)"; \
	fi
	@if [ -z "$$STAGING_DATABASE_URL" ]; then \
		echo -e "$(RED)❌ STAGING_DATABASE_URL environment variable not set$(NC)"; \
		echo -e "$(BLUE)💡 Set STAGING_DATABASE_URL and try again$(NC)"; \
		exit 1; \
	fi
	@chmod +x scripts/restore_rehearsal.sh
	@./scripts/restore_rehearsal.sh
	@echo -e "$(GREEN)✅ Restore rehearsal completed$(NC)"

backup-status: ## Operations: Show backup status and available backups
	@echo -e "$(CYAN)📊 Backup Status$(NC)"
	@echo -e "$(BLUE)═══════════════$(NC)"
	@echo -e "$(YELLOW)PostgreSQL Backups:$(NC)"
	@ls -lh /backups/pg_codex_*.dump 2>/dev/null | awk '{print "  📁 " $$9 " (" $$5 ", " $$6 " " $$7 ")"}' || echo -e "$(RED)  ❌ No PostgreSQL backups found$(NC)"
	@echo -e "$(YELLOW)JetStream Snapshots:$(NC)"
	@ls -ld /backups/js_gh_* 2>/dev/null | awk '{print "  🌊 " $$9 " (" $$6 " " $$7 " " $$8 ")"}' || echo -e "$(RED)  ❌ No JetStream snapshots found$(NC)"
	@echo -e "$(YELLOW)Backup Directory:$(NC)"
	@du -sh /backups 2>/dev/null | awk '{print "  💾 Total size: " $$1}' || echo -e "$(RED)  ❌ Backup directory not accessible$(NC)"

backup-cleanup: ## Operations: Clean up old backups (PostgreSQL >7 days, JetStream >14 days)
	@echo -e "$(CYAN)🧹 Cleaning up old backups...$(NC)"
	@echo -e "$(YELLOW)Cleaning PostgreSQL backups older than 7 days...$(NC)"
	@find /backups -name 'pg_codex_*.dump' -mtime +7 -delete 2>/dev/null || true
	@echo -e "$(YELLOW)Cleaning JetStream snapshots older than 14 days...$(NC)"
	@find /backups -name 'js_gh_*' -type d -mtime +14 -exec rm -rf {} + 2>/dev/null || true
	@echo -e "$(GREEN)✅ Backup cleanup completed$(NC)"

# =============================================================================
# DEMO SCENARIOS
# =============================================================================

demo: ## Demo: Run interactive GitGuard demo
	@echo -e "$(CYAN)🎬 Starting GitGuard interactive demo...$(NC)"
	@chmod +x $(DEMO_SCRIPT)
	@$(DEMO_SCRIPT)

demo-setup: ## Demo: Setup demo environment
	@echo -e "$(CYAN)🎯 Setting up demo environment...$(NC)"
	@chmod +x $(DEMO_SCRIPT)
	@$(DEMO_SCRIPT) setup

demo-low-risk: ## Demo: Low-risk PR (auto-merge)
	@echo -e "$(CYAN)📝 Demo: Low-risk PR scenario$(NC)"
	@chmod +x $(DEMO_SCRIPT)
	@$(DEMO_SCRIPT) low-risk

demo-medium-risk: ## Demo: Medium-risk PR (manual review)
	@echo -e "$(CYAN)⚠️  Demo: Medium-risk PR scenario$(NC)"
	@chmod +x $(DEMO_SCRIPT)
	@$(DEMO_SCRIPT) medium-risk

demo-high-risk: ## Demo: High-risk PR (blocked)
	@echo -e "$(CYAN)🚨 Demo: High-risk PR scenario$(NC)"
	@chmod +x $(DEMO_SCRIPT)
	@$(DEMO_SCRIPT) high-risk

demo-security: ## Demo: Security policy violation
	@echo -e "$(CYAN)🔒 Demo: Security violation scenario$(NC)"
	@chmod +x $(DEMO_SCRIPT)
	@$(DEMO_SCRIPT) security

demo-release-window: ## Demo: Release window policy enforcement
	@echo -e "$(CYAN)🕐 Demo: Release window enforcement$(NC)"
	@chmod +x $(DEMO_SCRIPT)
	@$(DEMO_SCRIPT) release-window

demo-dashboard: ## Demo: Show GitGuard metrics dashboard
	@echo -e "$(CYAN)📊 Demo: GitGuard dashboard$(NC)"
	@chmod +x $(DEMO_SCRIPT)
	@$(DEMO_SCRIPT) dashboard

demo-video: ## Demo: Generate 60-second demo video script
	@echo -e "$(CYAN)🎬 Demo: Video narration script$(NC)"
	@chmod +x $(DEMO_SCRIPT)
	@$(DEMO_SCRIPT) video

# =============================================================================
# RISK TESTING SHORTCUTS
# =============================================================================

demo-risk-low: ## Demo: Test low-risk PR scoring
	@echo -e "$(CYAN)📊 Low-Risk PR Analysis:$(NC)"
	@echo '{"lines_changed": 8, "files_touched": 1, "coverage_delta": 0, "perf_delta": 0, "new_tests": false}' > /tmp/ci.json
	@echo '{"type": "docs", "security_flags": false, "perf_budget": 5, "rubric_failures": [0, 0, 0, 0, 0]}' > /tmp/review.json
	@cat /tmp/ci.json /tmp/review.json | python scripts/risk_score.py
	@rm -f /tmp/ci.json /tmp/review.json

demo-risk-medium: ## Demo: Test medium-risk PR scoring  
	@echo -e "$(CYAN)📊 Medium-Risk PR Analysis:$(NC)"
	@echo '{"lines_changed": 120, "files_touched": 4, "coverage_delta": 1.5, "perf_delta": 2, "new_tests": true}' > /tmp/ci.json
	@echo '{"type": "feat", "security_flags": false, "perf_budget": 5, "rubric_failures": [0, 1, 0, 0, 0]}' > /tmp/review.json
	@cat /tmp/ci.json /tmp/review.json | python scripts/risk_score.py
	@rm -f /tmp/ci.json /tmp/review.json

demo-risk-high: ## Demo: Test high-risk PR scoring
	@echo -e "$(CYAN)📊 High-Risk PR Analysis:$(NC)"
	@echo '{"lines_changed": 300, "files_touched": 8, "coverage_delta": -2.0, "perf_delta": 12, "new_tests": false}' > /tmp/ci.json
	@echo '{"type": "feat", "security_flags": true, "perf_budget": 5, "rubric_failures": [1, 1, 0, 1, 0]}' > /tmp/review.json
	@cat /tmp/ci.json /tmp/review.json | python scripts/risk_score.py
	@rm -f /tmp/ci.json /tmp/review.json

demo-risk-security: ## Demo: Test security violation scoring
	@echo -e "$(CYAN)📊 Security Violation Analysis:$(NC)"
	@echo '{"lines_changed": 85, "files_touched": 2, "coverage_delta": 0, "perf_delta": 0, "new_tests": false}' > /tmp/ci.json
	@echo '{"type": "fix", "security_flags": true, "perf_budget": 5, "rubric_failures": [1, 1, 1, 1, 1]}' > /tmp/review.json
	@cat /tmp/ci.json /tmp/review.json | python scripts/risk_score.py
	@rm -f /tmp/ci.json /tmp/review.json

# =============================================================================
# QUICK DEMO SEQUENCES
# =============================================================================

demo-quick: ## Demo: 2 min. Auto-merge then block
	@$(MAKE) demo-low-risk
	@$(MAKE) demo-security

demo-investor: ## Demo: 5 min. Flow + metrics
	@$(MAKE) demo-low-risk
	@sleep 1
	@$(MAKE) demo-release-window
	@sleep 1
	@$(MAKE) demo-dashboard

demo-customer: ## Demo: 10 min. Governance deep dive
	@$(MAKE) demo-setup
	@$(MAKE) demo-low-risk
	@$(MAKE) demo-security
	@$(MAKE) demo-release-window

demo-customer-plus-knowledge: ## Demo: 15-min customer demo with knowledge deep-dive
	@echo -e "$(CYAN)🔧 Technical Customer Demo with Knowledge Portal...$(NC)"
	@$(MAKE) demo-setup
	@$(MAKE) docs-init
	@$(MAKE) docs-serve-bg
	@echo -e "$(YELLOW)Press Enter to demo a low-risk merge and auto-doc update...$(NC)"; read
	@$(MAKE) demo-low-risk
	@echo -e "$(YELLOW)Press Enter to demo a security violation and its governance doc...$(NC)"; read
	@$(MAKE) demo-security
	@echo -e "$(YELLOW)Press Enter to demo the knowledge graph for the blocked PR...$(NC)"; read
	@$(MAKE) graph
	@echo ""
	@echo -e "$(GREEN)🎯 Knowledge-Infused Demo Complete!$(NC)"

# =============================================================================
# MONITORING & TROUBLESHOOTING
# =============================================================================

health: ## Operations: Check GitGuard service health
	@echo -e "$(CYAN)🏥 GitGuard Health Check:$(NC)"
	@echo -n "API (8000): "
	@curl -s http://localhost:8000/health >/dev/null 2>&1 && echo -e "$(GREEN)✅ OK$(NC)" || echo -e "$(RED)❌ DOWN$(NC)"
	@echo -n "Temporal (8233): "
	@curl -s http://localhost:8233 >/dev/null 2>&1 && echo -e "$(GREEN)✅ OK$(NC)" || echo -e "$(RED)❌ DOWN$(NC)"
	@echo -n "OPA (8181): "
	@curl -s http://localhost:8181/health >/dev/null 2>&1 && echo -e "$(GREEN)✅ OK$(NC)" || echo -e "$(RED)❌ DOWN$(NC)"
	@echo -n "Grafana (3000): "
	@curl -s http://localhost:3000 >/dev/null 2>&1 && echo -e "$(GREEN)✅ OK$(NC)" || echo -e "$(RED)❌ DOWN$(NC)"
	@echo -n "Prometheus (9090): "
	@curl -s http://localhost:9090 >/dev/null 2>&1 && echo -e "$(GREEN)✅ OK$(NC)" || echo -e "$(RED)❌ DOWN$(NC)"

metrics: ## Operations: Show GitGuard metrics summary
	@echo -e "$(CYAN)📊 GitGuard Metrics:$(NC)"
	@curl -s http://localhost:8080/metrics | grep -E "(gitguard_|http_requests_total)" | head -10 || echo -e "$(YELLOW)Metrics not available (is API running?)$(NC)"

debug: ## Operations: Show debug information
	@echo -e "$(CYAN)🐛 Debug Information:$(NC)"
	@echo "Docker Compose Status:"
	@docker compose -f $(COMPOSE_FILE) ps
	@echo ""
	@echo "Recent Logs (last 20 lines):"
	@docker compose -f $(COMPOSE_FILE) logs --tail=20

# =============================================================================
# UTILITIES & MAINTENANCE  
# =============================================================================

backup-config: ## Operations: Backup GitGuard configuration
	@echo -e "$(CYAN)💾 Backing up configuration...$(NC)"
	@tar -czf "gitguard-config-backup-$(date +%Y%m%d-%H%M%S).tar.gz" config/ policies/
	@echo -e "$(GREEN)✅ Configuration backed up$(NC)"

update-deps: ## Development: Update Python dependencies
	@echo -e "$(CYAN)📦 Updating dependencies...$(NC)"
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip freeze > requirements.lock
	@echo -e "$(GREEN)✅ Dependencies updated$(NC)"

docker-clean: ## Operations: Clean up Docker resources
	@echo -e "$(CYAN)🧹 Cleaning Docker resources...$(NC)"
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f
	docker volume prune -f
	@echo -e "$(GREEN)✅ Docker cleanup completed$(NC)"

# =============================================================================
# DOCUMENTATION GENERATION
# =============================================================================

docs: ## Development: Generate documentation
	@echo -e "$(CYAN)📖 Generating documentation...$(NC)"
	@if command -v mkdocs >/dev/null 2>&1; then \
		mkdocs build; \
		echo -e "$(GREEN)✅ Documentation generated in site/$(NC)"; \
	else \
		echo -e "$(YELLOW)⚠️  MkDocs not installed. Install with: pip install mkdocs$(NC)"; \
	fi

docs-serve: ## Development: Serve documentation locally
	@echo -e "$(CYAN)📖 Serving documentation...$(NC)"
	@if command -v mkdocs >/dev/null 2>&1; then \
		mkdocs serve; \
	else \
		echo -e "$(YELLOW)⚠️  MkDocs not installed. Install with: pip install mkdocs$(NC)"; \
	fi

# =============================================================================
# KNOWLEDGE & DOCS INTEGRATION
# =============================================================================

docs-init: ## Development: Initialize the docs portal structure
	@echo -e "$(CYAN)📖 Initializing documentation portal...$(NC)"
	@mkdir -p docs_src/policies
	@echo '# GitGuard Governance Policies' > docs_src/index.md
	@echo 'This portal contains living documentation for all GitGuard policies.' >> docs_src/index.md
	@echo '## Release Windows' > docs_src/policies/release-windows.md
	@echo '**Policy ID:** POL-001' >> docs_src/policies/release-windows.md
	@echo '**Description:** To protect production stability, deployments are blocked outside of standard business hours.' >> docs_src/policies/release-windows.md
	@echo '**Window:** Monday 08:00 to Friday 16:00 (Africa/Johannesburg)' >> docs_src/policies/release-windows.md
	@echo '**Enforcement:** Automated via OPA policy `repo.guard.blocks_merge`.' >> docs_src/policies/release-windows.md
	@echo -e "$(GREEN)✅ Docs portal initialized in docs_src/$(NC)"

docs-serve-bg: ## Development: Serve docs in the background for demos
	@echo -e "$(CYAN)📖 Serving documentation at http://localhost:8001 (background)...$(NC)"
	@if ! pgrep -f "mkdocs serve" > /dev/null; then \
		mkdocs serve -a localhost:8001 > /tmp/mkdocs.log 2>&1 & \
		echo $$! > /tmp/mkdocs.pid; \
		echo -e "$(GREEN)✅ Docs server started.$(NC)"; \
	else \
		echo -e "$(YELLOW)⚠️  Docs server already running.$(NC)"; \
	fi

graph: ## Demo: Generate and display the knowledge graph
	@echo -e "$(CYAN)🧠 Generating knowledge graph visualization...$(NC)"
	@echo 'graph TD;' > /tmp/graph.mmd
	@echo '  subgraph "Repository: your-org/your-repo"' >> /tmp/graph.mmd
	@echo '    PR123[PR #123: "fix: resolve login bug"]' >> /tmp/graph.mmd
	@echo '    User[User: Phoenix]' >> /tmp/graph.mmd
	@echo '    PolicyRW(Policy: Release Window)' >> /tmp/graph.mmd
	@echo '    Decision{Decision: BLOCKED}' >> /tmp/graph.mmd
	@echo '  end' >> /tmp/graph.mmd
	@echo '  User -- "Authored" --> PR123' >> /tmp/graph.mmd
	@echo '  PR123 -- "Violated" --> PolicyRW' >> /tmp/graph.mmd
	@echo '  PolicyRW -- "Led to" --> Decision' >> /tmp/graph.mmd
	@echo -e "$(GREEN)✅ Mermaid graph generated. Paste into a viewer to see the relationship.$(NC)"
	@cat /tmp/graph.mmd

# =============================================================================
# CODEX MANAGEMENT
# =============================================================================

codex.up: ## Operations: Start the guard-codex service
	@echo -e "$(CYAN)🚀 Starting guard-codex service...$(NC)"
	docker compose up -d guard-codex
	@echo -e "$(GREEN)✅ Guard-codex service started$(NC)"

codex.schema: ## Operations: Initialize codex database schema
	@echo -e "$(CYAN)🗄️  Initializing codex database schema...$(NC)"
	docker compose exec guard-codex bash -lc "python - <<'PY'\nfrom activities import _ensure_schema; _ensure_schema(); print('codex schema ready')\nPY"
	@echo -e "$(GREEN)✅ Codex schema initialized$(NC)"

codex.mock-pr: ## Demo: Send a mock PR event to test codex portal updates
	@echo -e "$(CYAN)📝 Sending mock PR event to NATS...$(NC)"
	python - <<'PY'\nimport json, asyncio, os\nfrom nats.aio.client import Client as NATS\nasync def go():\n  nc=NATS(); await nc.connect(os.getenv('NATS_URL','nats://localhost:4222'))\n  evt={'event':'pull_request','repository':{'full_name':os.getenv('GITHUB_OWNER','org')+'/'+os.getenv('GITHUB_REPO','repo')},'pull_request':{'number':123,'title':'Demo PR','head':{'sha':'HEAD'},'user':{'login':'phoenix'},'labels':[]},'changed_files':['apps/guard-codex/activities.py'],'risk':{'score':3.2},'checks':{'all_passed':True},'coverage_delta':0.5,'perf_delta':-1.2,'release_window_state':'open','policies':['repo.guard.automerge'],'adrs':[]}\n  await nc.publish('gh.pull_request.opened', json.dumps(evt).encode()); await nc.drain()\nasyncio.run(go())\nPY
	@echo -e "$(GREEN)✅ Mock PR event sent - check the codex portal for updates$(NC)"

nats.setup: ## Operations: Setup NATS JetStream with durable streams and consumers
	@echo -e "$(CYAN)🌊 Setting up NATS JetStream streams and consumers...$(NC)"
	@echo -e "$(YELLOW)Creating GH stream for GitHub events...$(NC)"
	docker compose exec nats nats stream add GH --subjects "gh.*.*" --retention limits --storage file --max-msgs=-1 --max-bytes=-1 --replicas 1 --defaults
	@echo -e "$(YELLOW)Creating CODEX consumer for durable event processing...$(NC)"
	docker compose exec nats nats consumer add GH CODEX --filter "gh.*.*" --deliver all --ack explicit --replay instant --max-deliver 5 --backoff 1s,5s,20s,60s --defaults
	@echo -e "$(GREEN)✅ NATS JetStream configured with durable streams$(NC)"

nats.status: ## Operations: Show NATS JetStream status and consumer info
	@echo -e "$(CYAN)📊 NATS JetStream Status$(NC)"
	@echo -e "$(YELLOW)Streams:$(NC)"
	docker compose exec nats nats stream ls
	@echo -e "$(YELLOW)Consumers:$(NC)"
	docker compose exec nats nats consumer ls GH
	@echo -e "$(YELLOW)Stream Info:$(NC)"
	docker compose exec nats nats stream info GH

nats.reset: ## Operations: Reset NATS JetStream (delete streams and consumers)
	@echo -e "$(CYAN)🔄 Resetting NATS JetStream...$(NC)"
	@echo -e "$(YELLOW)Deleting CODEX consumer...$(NC)"
	-docker compose exec nats nats consumer rm GH CODEX --force
	@echo -e "$(YELLOW)Deleting GH stream...$(NC)"
	-docker compose exec nats nats stream rm GH --force
	@echo -e "$(GREEN)✅ NATS JetStream reset complete$(NC)"

scheduler.setup: ## Operations: Setup periodic maintenance scheduler for database cleanup
	@echo -e "$(CYAN)⏰ Setting up maintenance scheduler...$(NC)"
	docker compose exec guard-codex python scheduler.py
	@echo -e "$(GREEN)✅ Maintenance scheduler configured$(NC)"
