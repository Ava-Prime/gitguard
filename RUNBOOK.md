# GitGuard Operations Runbook

This runbook provides operational procedures for common issues and maintenance tasks in the GitGuard system, including the org-brain (Codex), Graph API, and chaos engineering features.

## 🚨 Common Issues & Solutions

### Docs Drift: Owners Index Out of Sync

**Problem**: The `owners.md` file falls behind actual repository ownership data.

**Solution**:
```bash
# Regenerate owners index from database
python -c "from owners_emit import emit_owners_index; import os; emit_owners_index(os.getenv('DATABASE_URL'),'docs')"

# Rebuild documentation
mkdocs build
```

**Prevention**: The owners index is automatically updated as part of the render cycle, but manual regeneration may be needed after bulk ownership changes.

### Policy Confusion: Engineers Need Rule Clarity

**Problem**: Engineers are confused about why their PR was flagged or approved.

**Solution**: Direct engineers to the **"Policy Evaluation"** section on their PR page. This section contains:
- Exact rule snippet that made the decision
- Input data used for evaluation
- Clear explanation of the policy logic

**Location**: `https://your-codex-domain/prs/{pr-number}/#policy-evaluation`

### JetStream Stuck: Message Processing Lag

**Problem**: NATS JetStream consumer has processing lag.

**Diagnosis**:
```bash
# Check consumer info
nats consumer info GH CODEX
```

**Solution**: If lag > 0 for >10 minutes:

1. **Scale Worker Replicas**:
   ```bash
   # Increase replicas in docker-compose
   docker compose up --scale guard-codex=3 -d
   ```

2. **Increase Concurrent Activities**:
   ```bash
   # Update environment variable
   export MAX_CONCURRENT_ACTIVITIES=10
   docker compose restart guard-codex
   ```

3. **Monitor Recovery**:
   ```bash
   # Watch lag decrease
   watch "nats consumer info GH CODEX | grep 'Num Pending'"
   ```

### Graph API Issues: CORS or Performance Problems

**Problem**: Graph API (port 8002) not responding or CORS errors.

**Diagnosis**:
```bash
# Check Graph API health
curl http://localhost:8002/health

# Test CORS headers
curl -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Headers: X-Requested-With" -X OPTIONS http://localhost:8002/graph/pr/123
```

**Solution**:
1. **Restart Graph API**:
   ```bash
   docker compose restart graph-api
   ```

2. **Check PostgreSQL Connection**:
   ```bash
   # Verify database connectivity
   docker compose exec postgres psql -U gitguard -d codex -c "SELECT COUNT(*) FROM knowledge_graph;"
   ```

3. **Monitor Performance**:
   ```bash
   # Check response times
   curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8002/graph/pr/123
   ```

## 📋 "Done-Done" Validation Checklist

Use this checklist to verify all core features are working correctly:

### ✅ Policy Source & Inputs Render on PR Pages

**What to Check**: PR pages display policy evaluation details

**Validation**:
1. Navigate to any PR page: `/prs/{pr-number}/`
2. Locate "Policy Evaluation" section
3. Verify it shows:
   - Rule source code snippet
   - Input data used for evaluation
   - Decision explanation

**Implementation**: `policy_explain.py` module integrated into `activities.py`

### ✅ Mermaid Graph Appears on PR Pages (≤20 nodes)

**What to Check**: PR pages show visual graph of file relationships

**Validation**:
1. Navigate to any PR page: `/prs/{pr-number}/`
2. Locate "File Relationships" section
3. Verify Mermaid graph displays:
   - PR node in center
   - Connected file nodes
   - Relationship edges (touches, depends, etc.)
   - Node count ≤ 20 for readability

**Implementation**: `_mermaid()` function in `activities.py`

### ✅ Owners Index Updates as Part of Render Cycle

**What to Check**: Owners index stays current with repository changes

**Validation**:
1. Check `/owners/` page exists and loads
2. Verify recent ownership changes are reflected
3. Confirm automatic updates during PR processing

**Implementation**: `owners_emit.py` module integrated into render cycle

### ✅ Freshness P99 Alert in Prometheus

**What to Check**: Prometheus monitors documentation freshness SLO

**Validation**:
1. Open Prometheus UI: `http://localhost:9090`
2. Search for `DOC_FRESH` metric
3. Verify `CodexFreshnessSLOBreached` alert rule exists
4. Check alert fires when P99 latency > 180s

**Implementation**:
- `DOC_FRESH` histogram in `activities.py`
- Alert rule in `ops/prometheus/alerts_codex.yml`

### ✅ Chaos Engineering Drills Validate System Resilience

**What to Check**: Chaos engineering drills validate alert mechanisms and system recovery

**Validation**:
1. **Slow-Publish Drill**: `make chaos.slow-publish`
   - Monitor `CodexBuildStall` alert fires and resolves
   - Verify JetStream redelivery works correctly

2. **Database Chaos**: `make chaos.db-disconnect`
   - Verify Graph API graceful degradation
   - Check PostgreSQL connection recovery

3. **Network Partition**: `make chaos.network-partition`
   - Test service mesh resilience
   - Validate circuit breaker patterns

4. **Memory Pressure**: `make chaos.memory-pressure`
   - Monitor OOM handling
   - Verify graceful service restart

**Implementation**: Chaos targets in `Makefile` and `tests/CHAOS_ENGINEERING.md`

### ✅ Graph API Serves Real-Time Relationship Data

**What to Check**: Graph API provides CORS-enabled access to knowledge graph

**Validation**:
1. Test API endpoints:
   ```bash
   curl http://localhost:8002/graph/pr/123
   curl http://localhost:8002/graph/owners
   curl http://localhost:8002/health
   ```
2. Verify CORS headers for cross-origin requests
3. Check response times < 500ms for graph queries
4. Confirm real-time updates from PostgreSQL

**Implementation**: FastAPI service with PostgreSQL backend

## 🔧 Maintenance Procedures

### Database Backup & Restore

**Backup**:
```bash
# PostgreSQL backup
./scripts/backup_postgres.sh

# JetStream backup
./scripts/backup_jetstream.sh
```

**Restore Rehearsal**:
```bash
# Full restore rehearsal
./scripts/restore_rehearsal.sh
```

### Prometheus Alert Management

**Reload Configuration**:
```bash
# Reload Prometheus config
./scripts/reload_prometheus.sh
```

**Silence Alerts**:
```bash
# Silence CodexBuildStall for 1 hour
curl -X POST http://localhost:9093/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [{"name": "alertname", "value": "CodexBuildStall"}],
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "endsAt": "'$(date -u -d "+1 hour" +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "comment": "Planned maintenance"
  }'
```

### Performance Monitoring

**Key Metrics to Watch**:
- `DOC_FRESH` histogram (documentation generation latency)
- `codex_build_duration_seconds` (overall build time)
- `graph_api_response_time` (Graph API performance)
- `chaos_drill_success_rate` (system resilience)
- JetStream consumer lag
- PostgreSQL connection pool usage
- SLO breach frequency (P99 freshness)

**Grafana Dashboards**:
- Codex Performance Overview
- Graph API Metrics
- Freshness SLOs
- Chaos Engineering Results
- JetStream Message Flow
- Alert Status Summary

## 🎯 System Architecture Summary

You've built an **org-brain that can explain itself**. This is the line between "documentation" and "judgment with receipts".

**Core Capabilities**:
- **Policy Transparency**: Every decision shows its source code and inputs
- **Visual Relationships**: Mermaid graphs reveal file dependencies and governance connections
- **Dynamic Ownership**: Always-current owners index based on recent activity
- **SLO Monitoring**: P99 freshness alerts ensure documentation quality
- **Chaos Engineering**: Automated resilience testing and validation
- **Graph API**: CORS-enabled real-time access to relationship data
- **Cross-Origin Integration**: Portal-ready API for external consumption
- **Knowledge Graph**: PostgreSQL-backed relationship mapping

**Future Extensions Ready**:
- Enhanced D3 visualizations via Graph API
- Real-time collaboration features
- Advanced analytics and ML insights
- Multi-repository governance
- Incident correlation and timeline analysis

## 📞 Escalation Contacts

**System Issues**: Check Prometheus alerts and SLO dashboards first, then escalate to platform team
**Policy Questions**: Direct to "Policy Evaluation" section on PR pages for transparency
**Performance Problems**: Run chaos drills to validate system resilience and recovery
**Graph API Issues**: Check CORS configuration and PostgreSQL connectivity
**Data Issues**: Use backup/restore procedures for recovery
**Chaos Drill Failures**: Review chaos engineering logs and system resilience metrics

---

*This runbook is automatically updated as part of the documentation generation process. Last updated: $(date)*
