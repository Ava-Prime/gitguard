# GitGuard Prometheus Alerts & SLO Monitoring

This document describes the Prometheus alerting setup for GitGuard's services, including the org-brain (Codex), Graph API, chaos engineering validation, and Service Level Objectives (SLOs).

## 🎯 Service Level Objectives (SLOs)

GitGuard services maintain the following SLOs:

- **Documentation Freshness**: P99 of PR events reach the portal page within 180 seconds
- **Graph API Performance**: P95 response time < 500ms for relationship queries
- **Policy Transparency**: 100% of decisions include source code references
- **Chaos Resilience**: 95% of chaos drills pass validation criteria
- **System Availability**: 99.9% uptime for core services

## 📊 Alert Rules

### CodexBuildStall

**Severity**: `page` (immediate attention required)

**Condition**: 95th percentile of `publish_portal` activity duration exceeds 60 seconds for more than 10 minutes.

```promql
histogram_quantile(0.95, sum(rate(codex_activity_seconds_bucket{name="publish_portal"}[10m])) by (le)) > 60
```

**Impact**: Portal updates are slow, affecting PR analysis freshness SLO.

**Runbook**: See `RUNBOOK.md#portal-not-updating`

### CodexEventErrors

**Severity**: `page` (immediate attention required)

**Condition**: More than 5 codex events fail within 5 minutes.

```promql
increase(codex_events_total{result!="ok"}[5m]) > 5
```

**Impact**: Event processing failures may indicate workflow issues, database connectivity problems, or service degradation.

**Runbook**: See `RUNBOOK.md#stuck-workflow`

### JetStreamConsumerLag

**Severity**: `ticket` (investigate during business hours)

**Condition**: CODEX JetStream consumer has pending messages for more than 10 minutes.

```promql
max(nats_jetstream_consumer_num_pending{consumer="CODEX"}) > 0
```

**Impact**: Consumer falling behind may affect both freshness and completeness SLOs.

**Runbook**: See `RUNBOOK.md#jetstream-lag`

### CodexFreshnessSLOBreached

**Severity**: `page` (immediate attention required)

**Condition**: P99 documentation freshness exceeds 180 seconds.

```promql
histogram_quantile(0.99, sum(rate(DOC_FRESH_bucket[10m])) by (le)) > 180
```

**Impact**: Documentation drift affects developer experience and policy transparency.

**Runbook**: See `RUNBOOK.md#freshness-slo-breach`

### GraphAPIPerformanceDegraded

**Severity**: `ticket` (investigate during business hours)

**Condition**: P95 Graph API response time exceeds 500ms for 5 minutes.

```promql
histogram_quantile(0.95, sum(rate(graph_api_response_time_bucket[5m])) by (le)) > 0.5
```

**Impact**: Slow Graph API affects portal performance and user experience.

**Runbook**: See `RUNBOOK.md#graph-api-performance`

### ChaosEngineeringFailure

**Severity**: `ticket` (investigate during business hours)

**Condition**: Chaos drill success rate drops below 95% over 24 hours.

```promql
(sum(rate(chaos_drill_success_total[24h])) / sum(rate(chaos_drill_total[24h]))) < 0.95
```

**Impact**: System resilience degradation may indicate infrastructure issues.

**Runbook**: See `RUNBOOK.md#chaos-drill-failures`

## 🚀 Quick Start

### 1. Deploy Alerts

```bash
# Start GitGuard with monitoring stack
make up

# Reload Prometheus configuration
make prometheus-reload
```

### 2. Verify Alerts

Check that alerts are loaded:

```bash
# Via API
curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name == "codex")'

# Via UI
open http://localhost:9090/alerts
```

### 3. Test Alerts

Simulate alert conditions:

```bash
# Run chaos engineering drills
make test.chaos

# Monitor alert states
watch 'curl -s http://localhost:9090/api/v1/alerts | jq ".data[] | select(.labels.alertname | startswith(\"Codex\"))"'
```

## 📈 Metrics Reference

### Core Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `codex_activity_seconds_bucket` | Histogram | Activity duration by name (e.g., publish_portal) |
| `codex_events_total` | Counter | Total events processed by result (ok/error) |
| `nats_jetstream_consumer_num_pending` | Gauge | Pending messages in JetStream consumer |
| `DOC_FRESH_bucket` | Histogram | Documentation generation latency for SLO monitoring |
| `graph_api_response_time_bucket` | Histogram | Graph API response times by endpoint |
| `chaos_drill_total` | Counter | Total chaos engineering drills executed |
| `chaos_drill_success_total` | Counter | Successful chaos engineering drills |
| `policy_transparency_decisions_total` | Counter | Policy decisions with source code references |
| `mermaid_graph_generation_seconds` | Histogram | Time to generate Mermaid graphs |
| `owners_index_update_seconds` | Histogram | Time to update dynamic owners index |

### Labels

- `name`: Activity name (publish_portal, analyze_pr, etc.)
- `result`: Event processing result (ok, error, timeout)
- `consumer`: JetStream consumer name (CODEX)
- `endpoint`: Graph API endpoint path (/graph/pr/{id}, /graph/owners, etc.)
- `drill_type`: Chaos engineering drill type (slow-publish, db-disconnect, etc.)
- `policy_name`: Policy rule name for transparency tracking
- `has_source_ref`: Whether policy decision includes source code reference

## 🔧 Configuration

### Prometheus Configuration

Alerts are defined in [`ops/prometheus/alerts_codex.yml`](../ops/prometheus/alerts_codex.yml) and loaded via:

```yaml
# ops/prometheus.yml
rule_files:
  - "prometheus/alerts_codex.yml"
```

### Docker Compose Integration

The monitoring stack is configured in [`ops/compose.yml`](../ops/compose.yml):

```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ../ops/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - ../ops/prometheus:/etc/prometheus/prometheus:ro
  command:
    - '--web.enable-lifecycle'  # Enables config reload via API
    - '--web.enable-admin-api'  # Enables admin operations
```

## 🛠️ Operations

### Reload Configuration

```bash
# Using Makefile (recommended)
make prometheus-reload

# Manual reload
curl -X POST http://localhost:9090/-/reload
```

### Check Alert Status

```bash
# All alerts
curl http://localhost:9090/api/v1/alerts

# Codex alerts only
curl -s http://localhost:9090/api/v1/alerts | jq '.data[] | select(.labels.alertname | startswith("Codex"))'

# Alert rules
curl http://localhost:9090/api/v1/rules
```

### Silence Alerts

```bash
# Silence CodexBuildStall for 1 hour
curl -X POST http://localhost:9090/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [{"name": "alertname", "value": "CodexBuildStall"}],
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "endsAt": "'$(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "comment": "Maintenance window",
    "createdBy": "ops-team"
  }'
```

## 📱 Integration

### Grafana Dashboards

Alerts integrate with Grafana dashboards at `http://localhost:3000`:

- **GitGuard Overview**: Service health and SLO tracking
- **Codex Performance**: Detailed org-brain metrics and trends
- **Graph API Metrics**: Response times and endpoint performance
- **Freshness SLOs**: Documentation drift and P99 monitoring
- **Chaos Engineering**: Drill results and system resilience
- **Policy Transparency**: Decision quality and source reference tracking
- **Alert Status**: Current alert states and history

### External Alerting

Configure Prometheus Alertmanager for:

- **Slack notifications**: `#gitguard-alerts` channel
- **PagerDuty integration**: For `severity: page` alerts
- **Email notifications**: For `severity: ticket` alerts

## 🔍 Troubleshooting

### Common Issues

**Alerts not loading**:
```bash
# Check Prometheus logs
docker compose -f ops/compose.yml logs prometheus

# Validate YAML syntax
yamllint ops/prometheus/alerts_codex.yml
```

**Metrics not available**:
```bash
# Check codex service metrics endpoint
curl http://localhost:8090/metrics

# Verify Prometheus targets
open http://localhost:9090/targets
```

**False positives**:
- Review alert thresholds in `alerts_codex.yml`
- Check metric collection intervals
- Validate query expressions in Prometheus UI

### Debug Queries

```promql
# Check publish_portal latency distribution
histogram_quantile(0.95, sum(rate(codex_activity_seconds_bucket{name="publish_portal"}[5m])) by (le))

# Documentation freshness P99
histogram_quantile(0.99, sum(rate(DOC_FRESH_bucket[10m])) by (le))

# Graph API performance by endpoint
histogram_quantile(0.95, sum(rate(graph_api_response_time_bucket[5m])) by (le, endpoint))

# Chaos drill success rate
(sum(rate(chaos_drill_success_total[1h])) / sum(rate(chaos_drill_total[1h]))) * 100

# Policy transparency coverage
(sum(rate(policy_transparency_decisions_total{has_source_ref="true"}[5m])) / sum(rate(policy_transparency_decisions_total[5m]))) * 100

# Event error rate
rate(codex_events_total{result!="ok"}[5m])

# JetStream consumer lag trend
nats_jetstream_consumer_num_pending{consumer="CODEX"}

# Mermaid graph generation performance
histogram_quantile(0.95, sum(rate(mermaid_graph_generation_seconds_bucket[5m])) by (le))

# Owners index update latency
histogram_quantile(0.95, sum(rate(owners_index_update_seconds_bucket[5m])) by (le))
```

## 📚 References

- [Prometheus Alerting Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [GitGuard Architecture](../ARCHITECTURE.md)
- [Chaos Engineering Guide](../tests/CHAOS_ENGINEERING.md)
- [Operational Runbooks](../RUNBOOK.md)