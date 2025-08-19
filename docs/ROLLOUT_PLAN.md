# GitGuard Org-Brain Zero-Drama Rollout Plan

This document outlines the phased rollout strategy for GitGuard org-brain with feature flags to ensure zero-drama deployment, including policy transparency, Graph API, chaos engineering, and SLO monitoring.

## Overview

The rollout follows a four-phase approach:
1. **Staging Cut**: Deploy with build-only mode (no external publish)
2. **Canary**: Enable publish for 10% of repositories
3. **Full Production**: Complete rollout with all repositories
4. **Advanced Features**: Enable Graph API, chaos engineering, and SLO monitoring

## Feature Flags

All new functionality is controlled by environment variables:

```bash
CODEX_PUBLISH_ENABLED=true          # Core publishing functionality
CODEX_EMBEDDINGS_ENABLED=false      # Semantic search embeddings
CODEX_OWNERS_ENABLED=false          # CODEOWNERS integration
POLICY_TRANSPARENCY_ENABLED=false   # Policy source code references
MERMAID_GRAPHS_ENABLED=false        # Visual relationship diagrams
GRAPH_API_ENABLED=false             # REST API for relationship data
CHAOS_ENGINEERING_ENABLED=false     # Chaos drill validation
SLO_MONITORING_ENABLED=false        # Freshness and performance SLOs
```

## Phase 1: Staging Cut

### Objective
Deploy Codex with `publish_portal` set to build-only mode to validate functionality without external impact.

### Configuration
- Environment: `config/rollout/staging.env`
- Key Settings:
  - `CODEX_PUBLISH_PORTAL=build-only`
  - `CODEX_EMBEDDINGS_ENABLED=false`
  - `CODEX_OWNERS_ENABLED=false`
  - `POLICY_TRANSPARENCY_ENABLED=false`
  - `MERMAID_GRAPHS_ENABLED=false`
  - `GRAPH_API_ENABLED=false`
  - `CHAOS_ENGINEERING_ENABLED=false`
  - `SLO_MONITORING_ENABLED=false`
  - `DOCS_PUBLISH_ENABLED=false`

### Deployment Steps
1. Load staging environment configuration
2. Deploy Codex service with staging config
3. Verify build pipeline functionality
4. Test documentation generation (build-only)
5. Monitor logs and metrics for errors

### Success Criteria
- [ ] Org-brain service starts successfully
- [ ] Documentation builds complete without errors
- [ ] No external publishing occurs
- [ ] All health checks pass
- [ ] Performance metrics within acceptable ranges
- [ ] Policy transparency framework initialized
- [ ] Mermaid graph generation pipeline ready
- [ ] Graph API endpoints accessible (but disabled)
- [ ] Chaos engineering framework initialized
- [ ] SLO monitoring baseline established

### Rollback Plan
- Stop Codex service
- Revert to previous stable version
- Verify system returns to baseline state

## Phase 2: Canary Deployment

### Objective
Enable external publishing for 10% of repositories to validate end-to-end functionality.

### Configuration
- Environment: `config/rollout/canary.env`
- Key Settings:
  - `CODEX_PUBLISH_PORTAL=external`
  - `CODEX_REPO_INCLUDE_LIST=<10% of repos>`
  - `POLICY_TRANSPARENCY_ENABLED=true`
  - `MERMAID_GRAPHS_ENABLED=true`
  - `GRAPH_API_ENABLED=false` (still disabled)
  - `CHAOS_ENGINEERING_ENABLED=false` (still disabled)
  - `SLO_MONITORING_ENABLED=true`
  - `JETSTREAM_MAX_AGE=72h` (unbounded for replay)
  - Enhanced monitoring and alerting

### Repository Selection (10%)
Select repositories based on:
- Low to medium traffic
- Non-critical business impact
- Good test coverage
- Active maintenance

Example canary repositories:
- `gitguard/platform-core`
- `gitguard/api-gateway`
- `gitguard/auth-service`
- `gitguard/notification-service`
- `gitguard/metrics-collector`

### Deployment Steps
1. Load canary environment configuration
2. Update repository include list
3. Deploy Codex with canary config
4. Monitor canary repositories for 24-48 hours
5. Validate documentation publishing
6. Check performance metrics and error rates

### Success Criteria
- [ ] Canary repositories publish successfully
- [ ] Policy transparency shows source code references
- [ ] Mermaid graphs render correctly in PR pages
- [ ] SLO monitoring tracks documentation freshness
- [ ] Error rate < 5%
- [ ] Latency < 5000ms
- [ ] No data corruption or loss
- [ ] JetStream replay functionality works
- [ ] Rollback capability verified
- [ ] Graph API endpoints ready (but disabled)
- [ ] Chaos engineering framework prepared

### Monitoring
- Error rate threshold: 5%
- Latency threshold: 5000ms
- Alert on any failures
- 24/7 monitoring during canary period

### Rollback Plan
1. Disable publishing for canary repositories
2. Replay JetStream messages if needed
3. Revert to staging configuration
4. Investigate and fix issues

## Phase 3: Full Production

### Objective
Complete rollout to all repositories with full functionality enabled.

### Configuration
- Environment: `config/rollout/production.env`
- Key Settings:
  - `CODEX_PUBLISH_ENABLED=true`
  - `CODEX_REPO_INCLUDE_LIST=` (empty = all repos)
  - `POLICY_TRANSPARENCY_ENABLED=true`
  - `MERMAID_GRAPHS_ENABLED=true`
  - `SLO_MONITORING_ENABLED=true`
  - `GRAPH_API_ENABLED=false` (enable in Phase 4)
  - `CHAOS_ENGINEERING_ENABLED=false` (enable in Phase 4)
  - `JETSTREAM_MAX_AGE=72h` (initial), then sane limits
  - Production monitoring and alerting

### Deployment Steps

#### Phase 3a: Initial Full Rollout
1. Load production environment configuration
2. Remove repository filtering (enable all repos)
3. Deploy with unbounded JetStream retention (72h)
4. Monitor system performance closely
5. Validate all repositories are processing

#### Phase 3b: Optimize Retention (After 72h)
1. Update JetStream configuration:
   ```bash
   JETSTREAM_MAX_AGE=24h
   JETSTREAM_MAX_MSGS=1000000
   JETSTREAM_MAX_BYTES=10GB
   ```
2. Apply configuration changes
3. Monitor storage usage and performance

### Success Criteria
- [ ] All repositories publish successfully
- [ ] Policy transparency coverage > 90%
- [ ] Mermaid graphs generated for all PRs
- [ ] SLO monitoring shows P99 < 10s
- [ ] Error rate < 1%
- [ ] Latency < 3000ms
- [ ] System performance stable
- [ ] Storage usage within limits
- [ ] No customer impact
- [ ] Documentation freshness SLOs met

### Monitoring
- Error rate threshold: 1%
- Latency threshold: 3000ms
- Storage usage monitoring
- Performance dashboards
- Customer feedback monitoring

## JetStream Retention Strategy

### Initial Phase (0-72h)
- **Retention**: Unbounded
- **Purpose**: Allow full replay capability during rollout
- **Settings**:
  ```bash
  JETSTREAM_MAX_AGE=72h
  JETSTREAM_MAX_MSGS=-1
  JETSTREAM_MAX_BYTES=-1
  ```

### Steady State (After 72h)
- **Retention**: Sane limits
- **Purpose**: Optimize storage and performance
- **Settings**:
  ```bash
  JETSTREAM_MAX_AGE=24h
  JETSTREAM_MAX_MSGS=1000000
  JETSTREAM_MAX_BYTES=10GB
  ```

## Rollback Procedures

### Emergency Rollback
1. **Immediate**: Set `CODEX_PUBLISH_ENABLED=false`
2. **Service**: Stop Codex service
3. **Replay**: Use JetStream replay if data recovery needed
4. **Revert**: Deploy previous stable version
5. **Verify**: Confirm system stability

### Partial Rollback
1. **Reduce Scope**: Update `CODEX_REPO_INCLUDE_LIST` to exclude problematic repos
2. **Monitor**: Watch for improvement
3. **Investigate**: Debug issues with excluded repositories
4. **Gradual Re-enable**: Add repositories back incrementally

## Phase 4: Advanced Features

### Objective
Enable Graph API, chaos engineering, and advanced monitoring features after core functionality is stable.

### Configuration
- Environment: `config/rollout/advanced.env`
- Key Settings:
  - `GRAPH_API_ENABLED=true`
  - `CHAOS_ENGINEERING_ENABLED=true`
  - All previous features remain enabled
  - Graph API port 8002 exposed
  - Chaos drill scheduling enabled

### Deployment Steps
1. Enable Graph API with CORS configuration
2. Start chaos engineering drill scheduler
3. Validate Graph API endpoints
4. Run initial chaos drills
5. Monitor system resilience

### Success Criteria
- [ ] Graph API responds on port 8002
- [ ] CORS headers configured correctly
- [ ] Chaos drills execute successfully
- [ ] System recovers from chaos scenarios
- [ ] API response times < 500ms
- [ ] Chaos drill success rate > 95%

## Feature Flag Activation Timeline

### Phase 1: Staging (Core Only)
```bash
CODEX_PUBLISH_ENABLED=true
POLICY_TRANSPARENCY_ENABLED=false
MERMAID_GRAPHS_ENABLED=false
GRAPH_API_ENABLED=false
CHAOS_ENGINEERING_ENABLED=false
SLO_MONITORING_ENABLED=false
```

### Phase 2: Canary (Policy + Graphs + SLOs)
```bash
CODEX_PUBLISH_ENABLED=true
POLICY_TRANSPARENCY_ENABLED=true
MERMAID_GRAPHS_ENABLED=true
GRAPH_API_ENABLED=false
CHAOS_ENGINEERING_ENABLED=false
SLO_MONITORING_ENABLED=true
```

### Phase 3: Production (All Visual Features)
```bash
CODEX_PUBLISH_ENABLED=true
POLICY_TRANSPARENCY_ENABLED=true
MERMAID_GRAPHS_ENABLED=true
GRAPH_API_ENABLED=false
CHAOS_ENGINEERING_ENABLED=false
SLO_MONITORING_ENABLED=true
```

### Phase 4: Advanced (API + Chaos)
```bash
CODEX_PUBLISH_ENABLED=true
POLICY_TRANSPARENCY_ENABLED=true
MERMAID_GRAPHS_ENABLED=true
GRAPH_API_ENABLED=true
CHAOS_ENGINEERING_ENABLED=true
SLO_MONITORING_ENABLED=true
```

### Future Phases: Additional Features

#### Phase 5: Enable Embeddings (Future)
```bash
CODEX_EMBEDDINGS_ENABLED=true
```
- Requires model router setup
- Additional database storage
- Performance impact assessment

#### Phase 6: Enable Owners (Future)
```bash
CODEX_OWNERS_ENABLED=true
```
- Requires CODEOWNERS file validation
- Additional graph relationships
- Documentation updates

## Monitoring and Alerting

### Key Metrics
- **Error Rate**: < 1% (production), < 5% (canary)
- **Latency**: < 3000ms (production), < 5000ms (canary)
- **Throughput**: Repositories processed per hour
- **Storage**: JetStream and database usage
- **Memory/CPU**: Service resource utilization
- **Policy Transparency**: Coverage percentage of decisions with source references
- **Mermaid Generation**: Graph rendering success rate and latency
- **Graph API**: Response times and endpoint availability
- **Chaos Drills**: Success rate and system recovery time
- **SLO Compliance**: Documentation freshness P99 latency

### Alert Conditions
- Error rate exceeds threshold
- Latency exceeds threshold
- Service health check failures
- Database connection issues
- JetStream connectivity problems
- Policy transparency coverage drops below 85%
- Mermaid graph generation failures
- Graph API response time > 1000ms
- Chaos drill failures
- SLO breach (P99 > 10s)

### Dashboards
- Real-time system health
- Repository processing status
- Performance trends
- Error analysis
- Resource utilization
- Policy transparency metrics
- Mermaid graph generation status
- Graph API performance
- Chaos engineering results
- SLO monitoring and freshness tracking

## Communication Plan

### Stakeholders
- Engineering teams
- DevOps/SRE
- Product management
- Customer support

### Communication Channels
- Slack: `#gitguard-rollout`
- Email: Engineering distribution list
- Status page: External customer communication

### Rollout Schedule
- **Week 1**: Phase 1 (Staging - Core functionality)
- **Week 2**: Phase 2 (Canary - Policy transparency + Mermaid + SLOs)
- **Week 3**: Phase 3a (Full rollout - All visual features)
- **Week 4**: Phase 3b (Optimize retention)
- **Week 5**: Phase 4 (Advanced - Graph API + Chaos engineering)
- **Week 6**: Monitoring and optimization

## Post-Rollout

### Validation
- [ ] All repositories processing correctly
- [ ] Performance within SLA
- [ ] No customer complaints
- [ ] Monitoring dashboards green
- [ ] Documentation up to date

### Optimization
- Review performance metrics
- Optimize resource allocation
- Fine-tune JetStream settings
- Plan future feature enablement

### Documentation Updates
- Update operational runbooks
- Document lessons learned
- Update monitoring procedures
- Plan next feature rollout
