# GitGuard Developer Guide

This guide provides detailed instructions for setting up and developing GitGuard locally.

## Quick Start

```bash
# One-command setup
make setup && make up

# Verify everything is running
make health

# Run a quick demo
make demo-quick
```

## Prerequisites

### Required Software

- **Docker & Docker Compose**: For containerized services
- **Python 3.11+**: For local development
- **Node.js 18+**: For documentation builds
- **Make**: For build automation (or use direct commands on Windows)

### Optional Tools

- **Git**: Version control
- **VS Code**: Recommended IDE with Python extension
- **Postman/Insomnia**: API testing

## Environment Setup

### 1. Initial Setup

```bash
# Clone repository
git clone https://github.com/your-org/gitguard.git
cd gitguard

# Setup development environment
make setup
```

This command will:
- Create Python virtual environment
- Install dependencies
- Setup pre-commit hooks
- Initialize configuration files

### 2. Start Services

```bash
# Start all services in background
make up

# Or start with logs visible
make up-logs
```

### 3. Verify Installation

```bash
# Check service health
make health

# Expected output:
# ✓ guard-api: healthy
# ✓ guard-codex: healthy
# ✓ prometheus: healthy
# ✓ grafana: healthy
```

## Local Development Ports

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8000 | - |
| **Docs Portal** | http://localhost:8001 | - |
| **Graph API** | http://localhost:8002 | - |
| **Grafana** | http://localhost:3000 | admin/gitguard |
| **Prometheus** | http://localhost:9090 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Graph API Docs** | http://localhost:8002/docs | - |

## Development Workflow

### Code Changes

```bash
# Make your changes
vim apps/guard-api/main.py

# Run tests
pytest -q

# Format and lint
make format
make lint

# Restart affected services
make restart-api
```

### Hot Reloading

Services are configured for hot reloading during development:

- **API**: FastAPI auto-reloads on file changes
- **Docs**: MkDocs serves with live reload
- **Frontend**: Auto-refresh on changes

### Testing

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests
pytest tests/policies/      # Policy tests

# Run with coverage
make test-coverage

# Fast tests only (skip slow integration tests)
pytest -q -m "not slow"
```

## Smoke Tests

Quick verification that core functionality works:

```bash
# Run smoke tests
make smoke-test
```

Smoke tests verify:
- API endpoints respond correctly
- Graph API serves relationship data
- Documentation builds successfully with Mermaid graphs
- Policy engine evaluates basic rules with transparency
- Owners index updates dynamically
- Metrics are being collected
- Chaos engineering drills pass

## Adding New Features

### 1. Adding a New Policy

```bash
# 1. Define policy in Rego
vim policies/guard_rules.rego

# Add new rule:
# high_risk_files := {
#     "Dockerfile",
#     "docker-compose.yml",
#     ".github/workflows"
# }

# 2. Create documentation
vim docs_src/policies/high-risk-files.md

# 3. Add tests
vim tests/policies/test_high_risk_files.py

# 4. Test the policy
make test-policies

# 5. Update demo scenarios
vim scripts/demo.sh
```

### 2. Adding a Documentation Page

```bash
# 1. Create markdown file
vim docs_src/new-feature.md

# 2. Update navigation (if needed)
vim mkdocs.yml

# 3. Build and test
make docs-build
make docs-serve

# 4. Verify at http://localhost:8001
```

### 3. Adding API Endpoints

```bash
# 1. Add endpoint to FastAPI app
vim apps/guard-api/routers/new_feature.py

# 2. Add tests
vim tests/integration/test_new_feature.py

# 3. Update OpenAPI docs
# (Auto-generated from FastAPI)

# 4. Test endpoint
curl http://localhost:8000/api/v1/new-feature
```

### 4. Working with Org-Brain Features

```bash
# 1. Add policy transparency
vim apps/guard-codex/policy_explain.py

# 2. Update Mermaid graph generation
vim apps/guard-codex/activities.py

# 3. Modify owners index logic
vim apps/guard-codex/owners_emit.py

# 4. Test Graph API
curl http://localhost:8002/graph/pr/123

# 5. Validate knowledge graph updates
make test-graph
```

## Configuration

### Environment Variables

Create `.env` file for local development:

```bash
# Copy example configuration
cp config/gitguard.settings.example.yaml config/gitguard.settings.yaml

# Edit configuration
vim config/gitguard.settings.yaml
```

### Key Configuration Options

```yaml
# GitHub Integration
github:
  token: "ghp_your_token_here"
  webhook_secret: "your_webhook_secret"

# Risk Scoring
risk:
  max_score: 100
  thresholds:
    low: 30
    medium: 60
    high: 80

# Policies
policies:
  release_windows:
    enabled: true
    blocked_days: ["friday", "saturday", "sunday"]
```

## Debugging

### Service Logs

```bash
# View all service logs
make logs

# View specific service logs
docker-compose logs -f guard-api
docker-compose logs -f guard-codex

# Follow logs in real-time
make logs-follow
```

### Debug Mode

```bash
# Start services in debug mode
make debug

# This enables:
# - Verbose logging
# - Debug endpoints
# - Hot reloading
# - Source maps
```

### Common Debug Commands

```bash
# Check service status
make status

# Restart specific service
make restart-api
make restart-codex

# Reset database
make db-reset

# Clean and rebuild
make clean && make setup && make up
```

## Performance Testing

### Load Testing

```bash
# Install load testing tools
pip install locust

# Run load tests
make load-test

# View results at http://localhost:8089
```

### Profiling

```bash
# Profile API performance
make profile-api

# Profile policy evaluation
make profile-policies

# Generate performance report
make perf-report
```

## Database Operations

### Local Database

```bash
# Connect to database
make db-connect

# Run migrations
make db-migrate

# Seed test data
make db-seed

# Backup database
make db-backup

# Restore database
make db-restore backup.sql
```

## Monitoring and Metrics

### Grafana Dashboards

- **System Overview**: http://localhost:3000/d/system
- **API Metrics**: http://localhost:3000/d/api
- **Graph API Metrics**: http://localhost:3000/d/graph-api
- **Policy Decisions**: http://localhost:3000/d/policies
- **Freshness SLOs**: http://localhost:3000/d/freshness
- **Chaos Engineering**: http://localhost:3000/d/chaos
- **Error Rates**: http://localhost:3000/d/errors

### Custom Metrics

```python
# Add custom metrics in your code
from prometheus_client import Counter, Histogram

# Define metrics
api_requests = Counter('api_requests_total', 'Total API requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

# Use in code
api_requests.inc()
with request_duration.time():
    # Your code here
    pass
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>
```

#### Docker Issues
```bash
# Clean Docker environment
make docker-clean

# Rebuild containers
make rebuild

# Check Docker resources
docker system df
docker system prune
```

#### Import Errors
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements-dev.txt
```

#### Test Failures
```bash
# Run tests with verbose output
pytest -v --tb=short

# Run specific failing test
pytest tests/test_specific.py::test_function -v

# Debug test with pdb
pytest --pdb tests/test_specific.py::test_function
```

### Getting Help

1. **Check Documentation**: http://localhost:8001
2. **View Service Logs**: `make logs`
3. **Run Health Checks**: `make health`
4. **Check GitHub Issues**: Known issues and solutions
5. **Ask Team**: Use team chat or create GitHub discussion

## Advanced Topics

### Custom Policy Development

See [Policy Development Guide](docs_src/policies/README.md) for detailed instructions on:
- Writing Rego policies with transparency
- Testing policy logic
- Policy performance optimization
- Integration with external data sources
- Adding policy explanations and source references

### Org-Brain Development

See [Org-Brain Guide](docs_src/org-brain/README.md) for:
- Knowledge graph schema design
- Mermaid diagram generation
- Dynamic ownership algorithms
- Policy transparency implementation
- Graph API development

### Chaos Engineering

See [Chaos Engineering Guide](tests/CHAOS_ENGINEERING.md) for:
- Writing chaos experiments
- Validating system resilience
- Monitoring chaos drill results
- Integrating with CI/CD pipelines

### API Extension

See [API Development Guide](docs_src/api/README.md) for:
- Adding new endpoints
- Authentication and authorization
- Rate limiting
- API versioning strategies
- CORS configuration for Graph API

### Deployment

See [Deployment Guide](docs_src/deployment/README.md) for:
- Production deployment
- Environment configuration
- Monitoring setup
- Backup and recovery
- SLO monitoring and alerting
