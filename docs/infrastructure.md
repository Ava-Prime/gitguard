# Infrastructure Configuration

This page documents GitGuard's Docker Compose infrastructure configuration, including the NATS→Temporal bridge and container orchestration setup.

## Architecture Overview

GitGuard uses a microservices architecture with the following core components:

- **NATS JetStream**: Message queue with persistent storage
- **Temporal**: Workflow engine for orchestrating long-running processes
- **PostgreSQL**: Database for workflow state and codex data
- **Redis**: Cache and rate limiting
- **OPA**: Policy engine for security rules
- **Guard Services**: API, Codex worker, and trigger components

## Docker Compose Configuration

The main infrastructure is defined in [`ops/compose.yml`](../ops/compose.yml):

### Message Queue (NATS)

```yaml
nats:
  image: nats:2.10
  ports:
    - "4222:4222"      # NATS protocol
    - "8222:8222"      # HTTP monitoring
  command: ["--http_port", "8222", "--jetstream", "--store_dir", "/data"]
  volumes:
    - nats_data:/data
```

**Key Features:**
- JetStream enabled for persistent messaging
- HTTP monitoring on port 8222
- Persistent storage for message durability

### Workflow Engine (Temporal)

```yaml
temporal:
  image: temporalio/auto-setup:1.24
  environment:
    - DB=postgresql
    - POSTGRES_USER=temporal
    - POSTGRES_PASSWORD=temporal
    - POSTGRES_SEEDS=postgres
  ports:
    - "7233:7233"      # gRPC API
    - "8233:8233"      # Web UI
  depends_on:
    - postgres
```

**Key Features:**
- Auto-setup with PostgreSQL backend
- Web UI for workflow monitoring
- gRPC API for workflow execution

### NATS→Temporal Bridge (Codex Trigger)

```yaml
codex-trigger:
  build:
    context: ..
    dockerfile: apps/guard-codex/Dockerfile.trigger
  environment:
    - TEMPORAL_HOST=temporal:7233
    - TEMPORAL_NAMESPACE=default
    - NATS_URL=nats://nats:4222
  depends_on:
    - temporal
    - nats
  restart: unless-stopped
```

**Critical Component**: This sidecar service bridges NATS messages to Temporal workflows:

- **Function**: Listens to NATS JetStream events and triggers corresponding Temporal workflows
- **Reliability**: `restart: unless-stopped` ensures high availability
- **Integration**: Direct connection to both NATS (4222) and Temporal (7233)
- **Namespace**: Uses default Temporal namespace for workflow execution

### GitGuard Codex Worker

```yaml
guard-codex:
  build:
    context: ..
    dockerfile: apps/guard-codex/Dockerfile
  environment:
    - DATABASE_URL=${DATABASE_URL}
    - TEMPORAL_HOST=temporal:7233
    - TEMPORAL_NAMESPACE=default
    - NATS_URL=nats://nats:4222
    - REPO_ROOT=/workspace/repo
    - CODEX_DOCS_DIR=/workspace/repo/docs
    - CODEX_PORTAL_SITE_DIR=/workspace/repo/site
  volumes:
    - ../:/workspace/repo
  depends_on:
    - temporal
    - nats
    - postgres
```

**Key Features:**
- Documentation generation and knowledge management
- Direct repository access via volume mount
- Integration with both NATS and Temporal
- Database connectivity for persistent storage

### GitGuard API Server

```yaml
guard-api:
  build:
    context: ../apps/guard-api
    dockerfile: Dockerfile
  environment:
    - NATS_URL=nats://nats:4222
    - REDIS_URL=redis://redis:6379
    - TEMPORAL_ADDRESS=temporal:7233
    - OPA_URL=http://opa:8181/v1/data/repo/guard
    - CODEX_URL=http://guard-codex:8010
  ports:
    - "8000:8000"      # API
    - "8080:8080"      # Metrics
```

**Integration Points:**
- NATS for event publishing
- Temporal for workflow management
- OPA for policy evaluation
- Redis for caching and rate limiting

## Health Checks and Monitoring

### Service Health Validation

To verify the NATS→Temporal bridge is functioning:

```bash
# Check NATS JetStream status
curl http://localhost:8222/jsz

# Check Temporal Web UI
open http://localhost:8233

# Verify codex-trigger container is running
docker compose -f ops/compose.yml ps codex-trigger

# Check NATS consumer status
nats consumer info GH CODEX
```

### Monitoring Stack

```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ../ops/prometheus.yml:/etc/prometheus/prometheus.yml:ro

grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=gitguard
```

**Monitoring Endpoints:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/gitguard)
- NATS Monitoring: http://localhost:8222
- Temporal UI: http://localhost:8233

## Deployment Variants

GitGuard supports multiple deployment configurations:

### Staging Environment

- **File**: [`ops/compose.staging.yml`](../ops/compose.staging.yml)
- **Purpose**: Build-only mode with debug logging
- **Database**: Separate staging database (port 5433)
- **NATS**: Staging-specific instance (port 4223)

### Canary Deployment

- **File**: [`ops/compose.canary.yml`](../ops/compose.canary.yml)
- **Purpose**: 10% traffic rollout with enhanced monitoring
- **Features**: Repository selection, performance tracking
- **Safety**: Rollback capabilities and error rate thresholds

## Verification Commands

### Infrastructure Status

```bash
# Start all services
make up

# Check service health
make health

# View service logs
docker compose -f ops/compose.yml logs -f codex-trigger

# Monitor NATS→Temporal bridge
watch "nats consumer info GH CODEX | grep 'Num Pending'"
```

### Container Validation

```bash
# Verify codex-trigger sidecar
docker compose -f ops/compose.yml exec codex-trigger ps aux

# Check NATS connectivity
docker compose -f ops/compose.yml exec codex-trigger nats server check

# Validate Temporal connection
docker compose -f ops/compose.yml exec codex-trigger temporal workflow list
```

## Troubleshooting

### Common Issues

1. **NATS→Temporal Bridge Not Working**
   - Check codex-trigger container logs
   - Verify NATS and Temporal connectivity
   - Ensure JetStream is enabled

2. **Workflow Execution Failures**
   - Check Temporal Web UI for workflow status
   - Verify database connectivity
   - Review worker logs for errors

3. **Message Queue Backlog**
   - Monitor NATS consumer lag
   - Scale codex workers if needed
   - Check for processing bottlenecks

### Debug Commands

```bash
# Full system debug
make debug

# NATS-specific debugging
nats stream info GH
nats consumer info GH CODEX

# Temporal workflow debugging
temporal workflow list --namespace default
temporal workflow describe --workflow-id <id>
```

## Security Considerations

- All inter-service communication uses internal Docker networks
- External ports are limited to necessary endpoints
- Secrets are managed via environment variables
- Policy evaluation is isolated in OPA containers

For detailed security policies, see [SECURITY.md](../SECURITY.md).
