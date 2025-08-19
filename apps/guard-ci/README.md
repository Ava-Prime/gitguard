# GitGuard CI

The **guard-ci** service provides CI/CD integration adapters for GitGuard's org-brain security governance platform, including policy transparency integration and chaos engineering support.

## Scope

This service handles integration with various CI/CD systems to collect and process build artifacts:

- **Coverage analysis**: Parse test coverage reports and calculate deltas
- **Performance metrics**: Extract performance benchmarks and regression detection
- **SBOM (Software Bill of Materials)**: Process dependency changes and vulnerability scanning
- **Build artifacts**: Collect and analyze build outputs, logs, and metadata
- **Quality gates**: Enforce quality thresholds based on CI metrics
- **Policy transparency**: Integrate policy source attribution with CI workflows
- **Chaos engineering**: Support chaos drill execution and result collection
- **SLO monitoring**: Track CI/CD pipeline SLOs and performance metrics

## CI System Adapters

### GitHub Actions Adapter
- Reads workflow artifacts via GitHub API
- Parses action outputs and job summaries
- Integrates with GitHub Checks API

### Jenkins Adapter
- Connects to Jenkins REST API
- Retrieves build artifacts and test results
- Processes pipeline stage outcomes

### GitLab CI Adapter
- Integrates with GitLab CI/CD API
- Collects job artifacts and pipeline data
- Supports GitLab merge request integration

### Generic Webhook Adapter
- Accepts standardized CI payload formats
- Supports custom CI systems via webhooks
- Configurable payload transformation

## Artifact Processors

### Coverage Processor
- **Input formats**: JaCoCo XML, Cobertura XML, LCOV, Istanbul JSON
- **Output**: Coverage percentage, line/branch coverage deltas
- **Features**: Historical trend analysis, threshold enforcement

### Performance Processor
- **Input formats**: JMeter XML, Lighthouse JSON, custom benchmark formats
- **Output**: Performance metrics, regression detection
- **Features**: Baseline comparison, performance budgets

### SBOM Processor
- **Input formats**: SPDX, CycloneDX, Syft JSON
- **Output**: Dependency changes, vulnerability reports
- **Features**: License compliance, security scanning integration

### Build Metadata Processor
- **Input**: Build logs, artifact manifests, deployment info
- **Output**: Build quality metrics, deployment readiness
- **Features**: Build time analysis, artifact validation

## API Endpoints

### Webhook Receivers
- `POST /ci/github/webhook` - GitHub Actions integration
- `POST /ci/jenkins/webhook` - Jenkins build notifications
- `POST /ci/gitlab/webhook` - GitLab CI pipeline events
- `POST /ci/generic/webhook` - Generic CI system integration

### Artifact Upload
- `POST /ci/artifacts/coverage` - Upload coverage reports
- `POST /ci/artifacts/performance` - Upload performance data
- `POST /ci/artifacts/sbom` - Upload SBOM files
- `POST /ci/artifacts/build` - Upload build metadata

### Data Retrieval
- `GET /ci/metrics/{pr_number}` - Get aggregated CI metrics for PR
- `GET /ci/coverage/delta/{pr_number}` - Get coverage delta analysis
- `GET /ci/performance/regression/{pr_number}` - Get performance regression data
- `GET /ci/policy/transparency/{pr_number}` - Get policy transparency metrics
- `GET /ci/chaos/drills/{pr_number}` - Get chaos engineering drill results
- `GET /ci/slo/metrics/{pr_number}` - Get SLO compliance metrics

## Configuration

### CI System Credentials
```yaml
ci_systems:
  github:
    token: ${GITHUB_TOKEN}
    webhook_secret: ${GITHUB_WEBHOOK_SECRET}
  jenkins:
    url: ${JENKINS_URL}
    username: ${JENKINS_USER}
    token: ${JENKINS_TOKEN}
  gitlab:
    url: ${GITLAB_URL}
    token: ${GITLAB_TOKEN}
```

### Quality Thresholds
```yaml
thresholds:
  coverage:
    minimum: 80.0
    delta_threshold: -2.0
  performance:
    regression_threshold: 10.0
    timeout_limit: 30000
  policy_transparency:
    minimum_coverage: 90.0
    source_attribution_required: true
  chaos_engineering:
    drill_success_rate: 95.0
    recovery_time_limit: 300
  slo_monitoring:
    availability_target: 99.9
    response_time_p99: 500
```

## Development Status

✅ **Active**: This service is actively developed with org-brain integration. Implementation status:

1. ✅ **Phase 1**: GitHub Actions adapter with coverage processing
2. ✅ **Phase 2**: Performance metrics and SBOM processing
3. ✅ **Phase 3**: Policy transparency CI integration
4. 🚧 **Phase 4**: Chaos engineering CI support (in progress)
5. 🚧 **Phase 5**: SLO monitoring and alerting (in progress)
6. 📋 **Phase 6**: Additional CI system adapters (planned)

## Architecture Considerations

- **Async processing**: Use background tasks for artifact processing
- **Storage**: Artifact storage strategy (S3, local filesystem, database)
- **Caching**: Cache processed results for performance
- **Retry logic**: Handle transient CI system failures
- **Rate limiting**: Respect CI system API limits

## Integration Examples

### GitHub Actions Workflow
```yaml
- name: Upload Coverage to GitGuard
  run: |
    curl -X POST $GITGUARD_CI_URL/ci/artifacts/coverage \
      -H "Authorization: Bearer $GITGUARD_TOKEN" \
      -F "file=@coverage.xml" \
      -F "pr_number=${{ github.event.number }}"

- name: Upload Policy Transparency Data
  run: |
    curl -X POST $GITGUARD_CI_URL/ci/artifacts/policy \
      -H "Authorization: Bearer $GITGUARD_TOKEN" \
      -F "policy_sources=@policy-sources.json" \
      -F "pr_number=${{ github.event.number }}"

- name: Run Chaos Engineering Drill
  run: |
    curl -X POST $GITGUARD_CI_URL/ci/chaos/drill \
      -H "Authorization: Bearer $GITGUARD_TOKEN" \
      -d '{"drill_type": "network_partition", "pr_number": "${{ github.event.number }}"}'
```

### Jenkins Pipeline
```groovy
post {
  always {
    script {
      sh "curl -X POST $GITGUARD_CI_URL/ci/jenkins/webhook -d @build-metadata.json"
    }
  }
}
```
