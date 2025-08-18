# Infrastructure Owner Review Policy

**Policy ID:** POL-002  
**Status:** Active  
**Last Updated:** 2024-12-19

## Overview

This policy ensures that all infrastructure changes receive proper oversight from designated repository owners before being merged. This includes infrastructure for org-brain features like Graph API, policy transparency services, Mermaid graph generation, and SLO monitoring systems.

## Policy Statement

Any pull request that modifies files within the `infra/` directory or org-brain infrastructure components must be explicitly approved by a repository owner before it can be merged.

## Rationale

Infrastructure changes can have significant impact on:
- System availability and reliability
- Security posture
- Operational costs
- Compliance requirements
- Graph API performance and scalability
- Policy transparency service reliability
- SLO monitoring accuracy
- Chaos engineering test integrity

By requiring owner review, we ensure that:
1. Changes are aligned with architectural standards
2. Security implications are properly assessed
3. Operational impact is understood
4. Knowledge is shared across the team
5. Org-brain feature dependencies are maintained
6. Graph database performance is preserved
7. Policy evaluation infrastructure remains stable

## Implementation

### Automatic Detection
GitGuard automatically detects when a PR modifies files under `infra/` and applies this policy.

### Approval Process
1. **Developer** creates PR with infrastructure changes
2. **GitGuard** automatically adds `needs-owner-review` label
3. **Repository Owner** reviews the changes
4. **Repository Owner** adds `owner-approved` label when satisfied
5. **GitGuard** allows merge to proceed

### Affected Paths

#### Core Infrastructure
- `infra/terraform/`
- `infra/kubernetes/`
- `infra/docker/`
- `infra/scripts/`
- Any file or directory under `infra/`

#### Org-Brain Infrastructure
- `apps/guard-brain/infra/` - Graph API infrastructure
- `apps/guard-brain/k8s/` - Kubernetes manifests for Graph API
- `apps/guard-brain/docker/` - Graph API container configurations
- `infra/graph-db/` - Neo4j and graph database infrastructure
- `infra/policy-engine/` - OPA and policy evaluation infrastructure
- `infra/mermaid-service/` - Mermaid graph generation service
- `infra/slo-monitoring/` - SLO monitoring and alerting infrastructure
- `infra/chaos-engineering/` - Chaos testing infrastructure

#### Configuration Files
- `*.yaml` files in org-brain service directories
- `docker-compose.yml` files for org-brain services
- Helm charts for Graph API and policy services
- Prometheus and Grafana configurations for SLO monitoring

## Enforcement

**OPA Policy:** `repo.guard.deny[msg]` (infra changes rule)  
**Trigger:** Pull request merge attempt  
**Action:** Block merge until `owner-approved` label is present

## Exceptions

No automatic exceptions are granted. All infrastructure changes require owner approval.

## Org-Brain Specific Considerations

### Graph API Infrastructure
- **Database Changes**: Neo4j configuration and schema modifications
- **API Gateway**: GraphQL endpoint and routing configurations
- **Caching Layer**: Redis or similar caching infrastructure
- **Load Balancing**: API load balancer and scaling configurations

### Policy Transparency Infrastructure
- **OPA Deployment**: Open Policy Agent runtime configurations
- **Policy Storage**: Policy source code storage and versioning
- **Evaluation Engine**: Policy evaluation service infrastructure
- **Transparency API**: Policy source code serving infrastructure

### SLO Monitoring Infrastructure
- **Metrics Collection**: Prometheus and metrics aggregation
- **Dashboards**: Grafana and visualization infrastructure
- **Alerting**: Alert manager and notification infrastructure
- **Data Retention**: Metrics storage and retention policies

### Chaos Engineering Infrastructure
- **Test Environment**: Isolated chaos testing infrastructure
- **Safety Controls**: Emergency stop and rollback mechanisms
- **Monitoring**: Chaos test result collection and analysis
- **Scheduling**: Automated chaos test execution infrastructure

## Related Policies

- [Release Windows](release-windows.md) - Timing restrictions for deployments
- [Dependency Management](deps-sbom.md) - Security scanning for dependencies
- [Security Posture](../security.md) - Infrastructure security requirements

## Contact

For questions about this policy, contact the Platform Engineering team or repository owners.