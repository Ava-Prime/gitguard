# Contributing to GitGuard

Welcome to GitGuard! This guide will help you contribute effectively to the project.

## Development Workflow

### Branching Strategy

- **Base Branch**: Always branch from `main`
- **Branch Naming**: Use the format `<type>/<scope>-<slug>`
  - `feat/api-risk-scoring`
  - `fix/codex-import-error`
  - `chore/deps-update-fastapi`
  - `docs/architecture-diagrams`

### Commit Standards

- **Conventional Commits**: Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification
- **Format**: `<type>[optional scope]: <description>`
- **Examples**:
  ```
  feat(api): add risk score calculation endpoint
  fix(codex): resolve import path for main module
  docs(policies): add infrastructure review policy
  chore(deps): bump fastapi to 0.104.1
  ```

### Merge Policy

- **Squash Merge Only**: All PRs must be squash merged to maintain clean history
- **Linear History**: No merge commits allowed
- **Branch Protection**: All changes must go through PR review process

## Local Development

### Initial Setup

```bash
# Clone and setup
git clone https://github.com/your-org/gitguard.git
cd gitguard
make setup && make up
```

### Development Commands

```bash
# Start all services
make up

# Run tests
pytest -q

# Run linting
make lint

# Format code
make format

# Type checking
make typecheck

# Stop services
make down
```

### Port Allocation

- **API**: http://localhost:8000
- **Docs Portal**: http://localhost:8001
- **Graph API**: http://localhost:8002
- **Grafana**: http://localhost:3000 (admin/gitguard)
- **Prometheus**: http://localhost:9090

## Code Quality Standards

### Python Code Style

- **Formatter**: Black (line length: 88)
- **Linter**: Ruff for fast linting
- **Type Checker**: MyPy for static type analysis
- **Import Sorting**: isort

### Testing Requirements

- **Coverage**: Aim for coverage deltas ≥ -0.2%
- **Test Types**:
  - Unit tests for business logic
  - Integration tests for API endpoints
  - Graph API tests for relationship data
  - Policy transparency tests
  - Chaos engineering validation
  - End-to-end tests for critical workflows

### Code Review Checklist

#### Technical Requirements
- [ ] Tests pass locally (`pytest -q`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make typecheck`)
- [ ] Coverage maintained or improved
- [ ] Graph API tests pass if applicable
- [ ] Policy transparency validated
- [ ] Chaos engineering tests pass
- [ ] Documentation updated if needed
- [ ] Mermaid diagrams render correctly
- [ ] Conventional commit format used

#### Approval Gate Requirements
Based on changed files, ensure appropriate team approval:

- [ ] **Infrastructure Changes** (`/infra/**`, `/ops/**`, `/.github/**`)
  - Requires: @platform-team approval
  - Label: `owner-approved`
  - Security focus: Deployment, CI/CD, supply chain

- [ ] **Policy Changes** (`/policies/**`)
  - Requires: @security-team + @platform-team approval
  - Label: `security-approved`
  - Security focus: Access control, compliance, OPA policies

- [ ] **API Changes** (`/apps/guard-api/**`)
  - Requires: @backend-team approval
  - Label: `api-security-reviewed`
  - Security focus: Endpoints, validation, data handling

- [ ] **AI/ML Changes** (`/apps/guard-brain/**`)
  - Requires: @ai-team approval
  - Label: `ai-security-reviewed`
  - Security focus: Model security, graph API, policy engine

- [ ] **Documentation Changes** (`**/*.md`, `/docs/**`)
  - Requires: @docs-team approval
  - Label: `docs-approved`
  - Focus: Accuracy, clarity, completeness

## Approval Workflow

### Understanding CODEOWNERS Integration

GitGuard automatically enforces approval requirements based on the files changed in your PR. The system maps file paths to required approvers using our CODEOWNERS configuration:

```
# Current CODEOWNERS mapping
* @platform-team                    # Default fallback
/infra/** @platform-team @security-team
/ops/** @platform-team
/.github/** @platform-team
/apps/guard-api/** @backend-team
/apps/guard-brain/** @ai-team
/workflows/** @platform-team @backend-team
/policies/** @security-team @platform-team
**/*.md @docs-team
/docs/** @docs-team
```

### Approval Process Flow

1. **Create PR**: Developer creates pull request
2. **Auto-Detection**: GitGuard analyzes changed files
3. **Label Assignment**: System adds required approval labels
4. **Team Review**: Appropriate teams review changes
5. **Label Addition**: Reviewers add approval labels when satisfied
6. **Gate Enforcement**: OPA policies block merge until all labels present
7. **Merge Allowed**: PR can be merged once all gates pass

### Required Labels by Area

| File Pattern | Required Teams | Required Labels | OPA Policy |
|--------------|----------------|-----------------|------------|
| `/infra/**` | @platform-team @security-team | `owner-approved` | `infra_approval_required` |
| `/policies/**` | @security-team @platform-team | `security-approved` | `policy_approval_required` |
| `/apps/guard-api/**` | @backend-team | `api-security-reviewed` | `api_approval_required` |
| `/apps/guard-brain/**` | @ai-team | `ai-security-reviewed` | `ai_approval_required` |
| `**/*.md` | @docs-team | `docs-approved` | `docs_approval_required` |
| `/ops/**` | @platform-team | `owner-approved` | `ops_approval_required` |
| `/.github/**` | @platform-team | `owner-approved` | `github_approval_required` |

### Emergency Override Process

For critical security fixes or production incidents:

1. **Emergency Label**: Add `emergency-override` label
2. **Justification**: Include detailed justification in PR description
3. **Post-Incident Review**: Schedule follow-up review within 24 hours
4. **Audit Trail**: All emergency overrides are logged and audited

**Note**: Emergency overrides still require at least one security team approval.

## Policy Development

### Adding New Policies

1. **Define Policy**: Add Rego rules to `policies/guard_rules.rego`
2. **Document Policy**: Create documentation page under `docs_src/policies/`
3. **Test Policy**: Add test cases in `tests/policies/`
4. **Update Examples**: Include policy in demo scenarios
5. **Security Review**: Ensure @security-team approval for policy changes

### Policy Documentation Requirements

Every policy change requires a corresponding documentation page with:

- **Overview**: What the policy does
- **Rationale**: Why it's needed
- **Implementation**: How it works with transparency
- **Examples**: When it triggers with decision explanations
- **Exceptions**: How to override if needed
- **Source References**: Links to Rego code snippets
- **Input Data**: What data the policy evaluates

## Org-Brain Development

### Knowledge Graph Features

1. **Policy Transparency**: Enhance `policy_explain.py` for better decision explanations
2. **Mermaid Graphs**: Update `activities.py` for visual relationship mapping
3. **Owners Index**: Modify `owners_emit.py` for dynamic ownership tracking
4. **Graph API**: Extend `api_graph.py` for new relationship endpoints

### Org-Brain Testing

```bash
# Test policy transparency
pytest tests/org_brain/test_policy_explain.py

# Test Mermaid generation
pytest tests/org_brain/test_mermaid.py

# Test Graph API
curl http://localhost:8002/graph/pr/123

# Validate owners index
make test-owners
```

### Graph API Development

- **CORS Configuration**: Ensure cross-origin support for portal integration
- **Performance**: Optimize PostgreSQL queries for large graphs
- **Caching**: Implement appropriate caching strategies
- **Error Handling**: Provide meaningful error responses

## Documentation

### Documentation Structure

```
docs_src/
├── index.md              # Main landing page
├── policies/             # Policy documentation
│   ├── release-windows.md
│   ├── infra-owners.md
│   └── deps-sbom.md
└── prs/                  # Auto-generated PR digests
```

### Building Documentation

```bash
# Build docs locally
make docs-build

# Serve docs with live reload
make docs-serve

# View at http://localhost:8001
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_risk_score.py

# With coverage
pytest --cov=gitguard

# Fast mode (skip slow tests)
pytest -q -m "not slow"
```

### Test Categories

- **Unit Tests**: `tests/unit/`
- **Integration Tests**: `tests/integration/`
- **Graph API Tests**: `tests/graph/`
- **Policy Tests**: `tests/policies/`
- **Chaos Engineering**: `tests/chaos/`
- **Org-Brain Tests**: `tests/org_brain/`
- **End-to-End Tests**: `tests/e2e/`

## Debugging

### Local Debugging

```bash
# View service logs
make logs

# Debug specific service
docker-compose logs -f guard-api

# Health check all services
make health

# Reset local environment
make clean && make setup && make up
```

### Common Issues

1. **Port Conflicts**: Check if ports 8000, 8001, 3000 are available
2. **Docker Issues**: Try `make clean` and restart Docker
3. **Import Errors**: Ensure virtual environment is activated
4. **Test Failures**: Check if services are running with `make health`

## Release Process

### Version Bumping

- Follow [Semantic Versioning](https://semver.org/)
- Update version in `pyproject.toml`
- Create release notes in `CHANGELOG.md`

### Deployment

- Deployments are automated via GitHub Actions
- Staging deployment on merge to `main`
- Production deployment on tagged releases

## Getting Help

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Check the docs at http://localhost:8001 when running locally
- **Code Review**: Tag maintainers for review assistance

## Security

### Reporting Security Issues

- **Private Disclosure**: Email security@gitguard.dev
- **No Public Issues**: Don't create public GitHub issues for security vulnerabilities
- **Response Time**: We aim to respond within 24 hours

### Security Best Practices

- Never commit secrets or API keys
- Use environment variables for configuration
- Follow principle of least privilege
- Keep dependencies updated

## License

By contributing to GitGuard, you agree that your contributions will be licensed under the same license as the project.
