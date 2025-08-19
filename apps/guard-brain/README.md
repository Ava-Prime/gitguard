# GitGuard Org-Brain

The **guard-brain** service provides intelligent organizational analysis, policy transparency, and relationship mapping capabilities for GitGuard's security governance platform.

## Scope

This service handles:

- **Policy Transparency**: Automated source attribution and policy traceability
- **Mermaid Graph Generation**: Visual relationship mapping and organizational structure
- **Owners Index Management**: Dynamic ownership tracking and responsibility mapping
- **Graph API**: RESTful API for organizational relationship queries
- **Chaos Engineering**: Resilience testing and failure simulation
- **SLO Monitoring**: Service level objective tracking and alerting

## Architecture

### Worker Interfaces

The guard-brain service implements worker interfaces for distributed processing:

#### Policy Transparency Workers
- `PolicySourceWorker`: Tracks policy origins and source references
- `TransparencyIndexWorker`: Maintains policy transparency metrics
- `SourceAttributionWorker`: Links policies to their authoritative sources

#### Graph Generation Workers
- `MermaidGraphWorker`: Generates Mermaid diagrams for organizational relationships
- `OwnershipGraphWorker`: Creates ownership and responsibility visualizations
- `RelationshipMapWorker`: Maps complex organizational dependencies

#### Graph API Workers
- `GraphQueryWorker`: Handles Graph API endpoint requests
- `RelationshipWorker`: Processes organizational relationship queries
- `OwnerIndexWorker`: Manages dynamic owners index updates

### Temporal Integration

If using Temporal for workflow orchestration:

- Workers register with Temporal task queues
- Workflows coordinate multi-step analysis processes
- Activities handle individual analysis tasks
- Retry policies ensure reliable processing

### Graph API Endpoints

The service exposes FastAPI endpoints for organizational queries:

- `/graph/health` - Service health check
- `/graph/owners` - Owners index and responsibility mapping
- `/graph/policies` - Policy transparency and source attribution
- `/graph/relationships` - Organizational relationship queries
- `/graph/mermaid` - Mermaid graph generation
- `/graph/chaos/drills` - Chaos engineering drill results
- `/graph/slo/metrics` - SLO monitoring and metrics

## Configuration

- `POLICY_TRANSPARENCY_ENABLED`: Enable policy source attribution
- `MERMAID_GRAPHS_ENABLED`: Enable Mermaid graph generation
- `GRAPH_API_ENABLED`: Enable Graph API endpoints
- `CHAOS_ENGINEERING_ENABLED`: Enable chaos engineering features
- `SLO_MONITORING_ENABLED`: Enable SLO monitoring and alerting
- `OWNERS_INDEX_PATH`: Path to owners index configuration
- `POLICY_SOURCES_PATH`: Path to policy source definitions
- `TEMPORAL_NAMESPACE`: Temporal namespace (if using Temporal)

## Development Status

✅ **Active**: This service is actively developed with the following features:

1. ✅ Policy transparency with source attribution
2. ✅ Mermaid graph generation for organizational visualization
3. ✅ Dynamic owners index management
4. ✅ Graph API for relationship queries
5. 🚧 Chaos engineering framework (in progress)
6. 🚧 SLO monitoring and alerting (in progress)

## Features

### Policy Transparency
- Automatic source reference attribution
- Policy traceability and lineage tracking
- Transparency metrics and coverage reporting

### Mermaid Graphs
- Organizational relationship visualization
- Dynamic graph generation from data
- Integration with PR documentation

### Owners Index
- Real-time ownership tracking
- Responsibility mapping and updates
- Integration with organizational changes

### Graph API
- RESTful endpoints for organizational queries
- Real-time relationship data access
- Integration with external tools and dashboards

## Monitoring

- Policy transparency coverage metrics
- Mermaid graph generation performance
- Graph API response times and availability
- Owners index update frequency and accuracy
- Chaos engineering drill success rates
- SLO compliance and breach alerting
