# GitGuard Architecture (v2)

## Overview

GitGuard is an autonomous repository steward that combines risk assessment, policy enforcement, automated documentation, and organizational intelligence to ensure safe and compliant code changes. It features self-explaining policies, visual relationship mapping, dynamic ownership tracking, and chaos-resilient operations.

## Core Components

### guard-api
- **Purpose**: Receives GitHub webhooks, normalizes events, forwards to Codex
- **Technology**: FastAPI service
- **Responsibilities**:
  - GitHub webhook processing
  - Event normalization and validation
  - Risk score computation
  - Integration with OPA for policy decisions

### codex ("org-brain")
- **Purpose**: Organizational intelligence engine that writes PR digests, maintains knowledge graphs, and provides transparency
- **Technology**: Python service with MkDocs integration, PostgreSQL knowledge graph
- **Responsibilities**:
  - Generate human-readable PR summaries with policy explanations
  - Update documentation portal in real-time
  - Maintain knowledge graph of code changes and relationships
  - Generate Mermaid diagrams for visual relationship mapping
  - Emit dynamic owners index based on recent activity
  - Provide policy transparency with source code and decision explanations
  - Trigger documentation builds

### OPA (Open Policy Agent)
- **Purpose**: Policy decisions for merge/tag (release windows, infra reviews, deps)
- **Technology**: OPA with Rego policies
- **Responsibilities**:
  - Evaluate merge eligibility based on policies
  - Enforce release window restrictions
  - Require infrastructure owner reviews
  - Validate dependency security (SBOM)

### Temporal/NATS
- **Purpose**: Workflow orchestration and event streaming
- **Technology**: Temporal for workflows, NATS for messaging
- **Responsibilities**:
  - Coordinate multi-step processes
  - Handle async operations
  - Ensure reliable event delivery

### Prometheus/Grafana
- **Purpose**: Observability, metrics, and SLO monitoring
- **Technology**: Prometheus for metrics collection, Grafana for visualization
- **Responsibilities**:
  - Track merge rates and block reasons
  - Monitor system health and freshness P99 SLOs
  - Measure revert rates and quality metrics
  - Provide real-time dashboards
  - Alert on documentation drift and system anomalies
  - Support chaos engineering validation

### Graph API
- **Purpose**: Read-only API for accessing knowledge graph data
- **Technology**: FastAPI with CORS support
- **Responsibilities**:
  - Serve graph data (nodes and edges) for PR visualization
  - Enable cross-origin requests for portal integration
  - Provide real-time access to relationship data
  - Support dynamic graph rendering in documentation

### CI Pipeline
- **Purpose**: Lint, tests, SBOM; sets `checks` signals for OPA input
- **Technology**: GitHub Actions
- **Responsibilities**:
  - Run automated tests
  - Perform security scans
  - Generate SBOM reports
  - Provide quality signals to OPA
  - Support chaos engineering drills

## Data Flow

```
PR Created → CI Pipeline → Risk Computation → OPA Policy Gate → Decision
    ↓              ↓              ↓                ↓            ↓
 Webhook      Test Results   Risk Score      Policy Check   Merge/Block
    ↓              ↓              ↓                ↓            ↓
guard-api    Quality Signals  Risk Factors   Rego Rules   GitHub Status
    ↓                             ↓                ↓            ↓
 Codex (org-brain)         OPA Input        Decision     Documentation
    ↓              ↓              ↓                ↓            ↓
Knowledge Graph    Policy Explain   Mermaid Graph   Owners Index
    ↓              ↓              ↓                ↓            ↓
Graph API      Docs Portal    Visual Relations  Dynamic Ownership
    ↓              ↓              ↓                ↓            ↓
Real-time Data  Self-Explaining  Relationship Map  Activity Tracking
```

### Detailed Flow

1. **PR Event**: Developer creates/updates PR
2. **CI Artifacts**: GitHub Actions run tests, linting, security scans, chaos drills
3. **Risk Compute**: guard-api calculates risk score based on:
   - Code complexity and size
   - Test coverage delta
   - Security scan results
   - Historical patterns
4. **OPA Gate**: Policy engine evaluates:
   - Risk score thresholds
   - Release window restrictions
   - Required approvals (infrastructure changes)
   - Dependency security requirements
5. **Decision**: Merge allowed or blocked with transparent explanation
6. **Codex Intelligence**: org-brain generates:
   - PR digest with policy explanations
   - Mermaid graphs showing relationships
   - Updated owners index based on activity
   - Knowledge graph updates
7. **Documentation**: Real-time portal updates with visual elements
8. **Graph API**: Serves relationship data for dynamic visualizations
9. **Dashboards**: Metrics and SLO monitoring updated in Grafana

## Security Model

- **Principle of Least Privilege**: Each component has minimal required permissions
- **Policy as Code**: All governance rules defined in version-controlled Rego files
- **Policy Transparency**: Decision explanations with source code references
- **Audit Trail**: All decisions logged and traceable with full context
- **Fail-Safe**: System defaults to blocking on errors or missing data
- **Chaos Resilience**: Regular chaos engineering validates system robustness
- **Secrets Hygiene**: Automated detection and redaction of sensitive data

## Scalability Considerations

- **Horizontal Scaling**: All services designed as stateless containers
- **Event-Driven**: Async processing prevents blocking operations
- **Caching**: Risk scores and policy decisions cached for performance
- **Rate Limiting**: GitHub API calls managed to prevent quota exhaustion

## Monitoring and Observability

- **Health Checks**: All services expose `/health` endpoints
- **Metrics**: Prometheus metrics for all critical operations
- **SLO Monitoring**: Freshness P99 alerts for documentation drift
- **Logging**: Structured logging with correlation IDs
- **Alerting**: Grafana alerts for system anomalies and policy violations
- **Chaos Validation**: Automated chaos engineering with monitoring integration

## Development Environment

- **Local Setup**: `make setup && make up`
- **Port Allocation**:
  - API: http://localhost:8000
  - Docs: http://localhost:8001
  - Graph API: http://localhost:8002
  - Grafana: http://localhost:3000
  - Prometheus: http://localhost:9090
- **Testing**: Comprehensive validation including chaos engineering drills

## Key Features

- **Policy Transparency**: Self-explaining decisions with source code references
- **Visual Relationships**: Mermaid diagrams showing code and governance connections
- **Dynamic Ownership**: Real-time owners index based on recent activity
- **Chaos Engineering**: Automated resilience testing and validation
- **SLO Monitoring**: Freshness alerts and documentation drift detection
- **Knowledge Graph**: PostgreSQL-backed relationship mapping
- **Cross-Origin API**: CORS-enabled Graph API for portal integration

## Future Enhancements

- **ML Risk Models**: Machine learning for more accurate risk prediction
- **Advanced Workflows**: Complex approval chains and escalation
- **Integration Ecosystem**: Plugins for Slack, Teams, JIRA
- **Policy Simulation**: Test policy changes before deployment
- **Enhanced Visualizations**: Interactive graph exploration and filtering
