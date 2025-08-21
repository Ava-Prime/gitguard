# Getting Started with GitGuard

Welcome to GitGuard! This guide will help you get up and running with intelligent PR governance in minutes.

## What is GitGuard?

GitGuard is an autonomous repository steward that:

- **🤖 Automates PR decisions** - Merges safe changes, blocks risky ones
- **📋 Enforces governance policies** - Release windows, security reviews, dependency management
- **📚 Generates living documentation** - Real-time PR digests with policy transparency
- **🕸️ Maps relationships** - Visual Mermaid graphs showing code and governance connections
- **👥 Tracks ownership** - Dynamic owners index based on recent activity
- **📊 Provides visibility** - Dashboards with SLO monitoring and chaos engineering validation
- **🔗 Enables integration** - Graph API for cross-origin portal access

## Quick Demo (2 minutes)

```bash
# One-command setup
make setup && make up && make demo-quick
```

This will:
1. Start all GitGuard services locally
2. Run a 2-minute demo showing low-risk and security scenarios
3. Open documentation portal and dashboards

### Access Points

- **📚 Documentation Portal**: http://localhost:8001
- **🕸️ Graph API**: http://localhost:8002
- **📊 Grafana Dashboards**: http://localhost:3000 (admin/gitguard)
- **🔌 API Interface**: http://localhost:8000
- **📈 Prometheus Metrics**: http://localhost:9090

## Understanding GitGuard Workflow

### The Three-Step Process

Every PR goes through GitGuard's three-step evaluation:

#### 1. 🎯 Risk Assessment

GitGuard analyzes multiple factors to compute a risk score:

- **Code Complexity**: Lines changed, cyclomatic complexity
- **Test Coverage**: Coverage delta, test quality
- **Security Impact**: Dependency changes, sensitive file modifications
- **Historical Patterns**: Past failure rates, revert frequency

#### 2. 🚪 Policy Gate

OPA (Open Policy Agent) enforces governance rules:

- **Release Windows**: Block deployments during high-risk periods
- **Infrastructure Reviews**: Require owner approval for infra changes
- **Dependency Security**: Ensure SBOM scans pass for dependency updates
- **Risk Thresholds**: Auto-merge low-risk, require review for high-risk

#### 3. 📖 Org-Brain Intelligence

Codex ("org-brain") generates comprehensive organizational intelligence:

- **PR Digests**: What changed, why it matters, impact assessment
- **Policy Transparency**: Decision explanations with source code references
- **Mermaid Graphs**: Visual relationship maps showing connections
- **Owners Index**: Dynamic ownership tracking based on recent activity
- **Knowledge Graph**: PostgreSQL-backed relationship mapping
- **Graph API**: Real-time access to relationship data

## Demo Scenarios

GitGuard includes three demo flows to showcase different use cases:

### `make demo-quick` (2 minutes)
**Target Audience**: Developers
**Scenarios**: Low-risk auto-merge + Security policy enforcement

### `make demo-investor` (5 minutes)
**Target Audience**: Leadership, Investors
**Scenarios**: Low-risk + Release window + Dashboard metrics

### `make demo-customer` (10 minutes)
**Target Audience**: Enterprise customers
**Scenarios**: Comprehensive governance demo with all policies

## Key Features Walkthrough

### Auto-Merge for Safe Changes

```bash
# Demo a low-risk change
./scripts/demo.sh low-risk
```

**What you'll see**:
- PR created with simple documentation update
- Risk score calculated (low)
- Policy evaluation (passes all checks)
- Automatic merge approval
- Documentation updated in real-time

### Policy Enforcement

```bash
# Demo security policy blocking
./scripts/demo.sh security
```

**What you'll see**:
- PR with dependency changes
- Security scan triggered
- Policy blocks merge due to missing SBOM
- Clear explanation with remediation steps
- Human-readable policy documentation

### Release Window Protection

```bash
# Demo release window restrictions
./scripts/demo.sh release-window
```

**What you'll see**:
- PR attempted during blocked time window
- Policy prevents merge with clear explanation
- Alternative scheduling suggestions
- Override process for emergencies

## Understanding the Dashboard

### Grafana Dashboards (http://localhost:3000)

#### System Overview Dashboard
- **Merge Rate**: PRs merged vs blocked over time
- **Block Reasons**: Why PRs are being blocked (policy breakdown)
- **Revert Rate**: Quality indicator - how often merges are reverted
- **Risk Distribution**: Histogram of risk scores
- **Freshness SLOs**: Documentation drift and P99 monitoring

#### Policy Effectiveness Dashboard
- **Policy Triggers**: Which policies are most active
- **Policy Transparency**: Decision explanation quality metrics
- **Override Frequency**: How often policies are overridden
- **Time to Merge**: Average time from PR creation to merge
- **Developer Satisfaction**: Metrics on developer experience

#### Chaos Engineering Dashboard
- **Drill Results**: Chaos experiment success rates
- **System Resilience**: Recovery time metrics
- **Failure Scenarios**: Types of chaos tests performed
- **Reliability Trends**: System stability over time

### Documentation Portal (http://localhost:8001)

#### Live PR Digests
- Real-time updates as PRs are processed
- Human-readable summaries with policy transparency
- Mermaid graphs showing relationship maps
- Impact assessments and risk explanations
- Links to related documentation and policies

#### Policy Documentation
- Clear explanations with source code references
- Decision transparency with Rego snippets
- Examples of when policies trigger
- Remediation steps for common issues
- Contact information for policy owners

#### Owners Index
- Dynamic ownership based on recent activity
- File-level ownership tracking
- Activity heatmaps and contribution patterns
- Contact information for code owners

#### Graph API Integration
- Real-time relationship data access
- CORS-enabled for portal integration
- Visual graph exploration capabilities
- Dynamic relationship updates

## Org-Brain Intelligence API (60-Second Verification)

GitGuard's "Org-Brain" provides real-time organizational intelligence through a REST API. Here's how to verify it's working in under a minute:

### Quick API Test

```bash
# 1. Check API health (5 seconds)
curl http://localhost:8002/health
# Expected: {"status": "healthy", "services": ["postgresql", "nats", "temporal"]}

# 2. Get ownership index (15 seconds)
curl http://localhost:8002/api/v1/ownership/index | jq
# Expected: Dynamic ownership mapping based on recent commits

# 3. Query file ownership (10 seconds)
curl "http://localhost:8002/api/v1/ownership/files?path=apps/guard-api/main.py" | jq
# Expected: Owner details with activity metrics

# 4. Get relationship graph (15 seconds)
curl http://localhost:8002/api/v1/graph/relationships | jq
# Expected: Node/edge data for Mermaid visualization

# 5. Search knowledge graph (15 seconds)
curl "http://localhost:8002/api/v1/knowledge/search?q=policy" | jq
# Expected: Policy-related entities and relationships
```

### Sample Response - Ownership Index

```json
{
  "owners": {
    "apps/guard-api/": {
      "primary": "alice@company.com",
      "secondary": ["bob@company.com"],
      "activity_score": 0.85,
      "last_commit": "2024-01-15T10:30:00Z",
      "expertise_areas": ["webhooks", "temporal", "nats"]
    },
    "policies/": {
      "primary": "security-team@company.com",
      "secondary": ["alice@company.com"],
      "activity_score": 0.92,
      "last_commit": "2024-01-14T16:45:00Z",
      "expertise_areas": ["opa", "governance", "compliance"]
    }
  },
  "metadata": {
    "generated_at": "2024-01-15T12:00:00Z",
    "total_files": 247,
    "coverage_percentage": 94.2
  }
}
```

### Sample Response - Relationship Graph

```json
{
  "nodes": [
    {
      "id": "guard-api",
      "type": "service",
      "label": "Guard API",
      "properties": {
        "language": "python",
        "framework": "fastapi",
        "owner": "alice@company.com"
      }
    },
    {
      "id": "opa-policies",
      "type": "policy_set",
      "label": "OPA Policies",
      "properties": {
        "policy_count": 12,
        "owner": "security-team@company.com"
      }
    }
  ],
  "edges": [
    {
      "from": "guard-api",
      "to": "opa-policies",
      "type": "evaluates",
      "properties": {
        "frequency": "per_pr",
        "last_evaluation": "2024-01-15T11:45:00Z"
      }
    }
  ]
}
```

### Integration Examples

**Portal Integration (JavaScript)**:
```javascript
// Fetch ownership for current file
const ownership = await fetch(`http://localhost:8002/api/v1/ownership/files?path=${filePath}`);
const data = await ownership.json();
console.log(`File owner: ${data.primary}`);
```

**CLI Integration (Python)**:
```python
import requests

# Get expertise areas for a user
response = requests.get("http://localhost:8002/api/v1/ownership/users/alice@company.com")
user_data = response.json()
print(f"Expertise: {', '.join(user_data['expertise_areas'])}")
```

**Dashboard Widget (curl + jq)**:
```bash
# Generate ownership summary for dashboard
curl -s http://localhost:8002/api/v1/ownership/summary | \
  jq -r '.top_contributors[] | "\(.email): \(.contribution_percentage)%"'
```

### API Documentation

Full API documentation is available at:
- **Interactive Docs**: http://localhost:8002/docs
- **OpenAPI Spec**: http://localhost:8002/openapi.json
- **Graph Schema**: http://localhost:8002/api/v1/schema

## Customizing GitGuard

### Adding Custom Policies

1. **Define Policy Logic** in `policies/guard_rules.rego`:
```rego
# Example: Block PRs that modify critical files without senior review
critical_files_need_senior_review {
    input.files[_].path == "src/payment/processor.py"
    not input.approvals[_].user.role == "senior"
}
```

2. **Create Documentation** in `docs_src/policies/`:
```markdown
# Critical Files Policy

Changes to payment processing code require senior developer review.

## Rationale
Payment code has direct financial impact...
```

3. **Test the Policy**:
```bash
pytest tests/policies/test_critical_files.py
```

### Configuring Risk Scoring

Edit `config/gitguard.settings.yaml`:

```yaml
risk:
  weights:
    complexity: 0.3      # Code complexity factor
    coverage: 0.2        # Test coverage impact
    security: 0.4        # Security scan results
    history: 0.1         # Historical patterns
  thresholds:
    auto_merge: 30       # Auto-merge below this score
    require_review: 70   # Require review above this score
```

### Integrating with Your Repository

#### GitHub App Installation (Recommended)

GitGuard operates as a GitHub App for secure, least-privilege access to your repositories.

##### Required OAuth Scopes

The GitGuard GitHub App requires the following permissions:

**Repository Permissions:**
- `contents: read` - Read repository files and commits
- `metadata: read` - Access repository metadata
- `pull_requests: write` - Create comments, update PR status
- `checks: write` - Create and update check runs
- `statuses: write` - Update commit status
- `issues: write` - Create and update issues for policy violations
- `actions: read` - Access workflow run information
- `security_events: read` - Access security alerts and scanning results

**Organization Permissions:**
- `members: read` - Read organization membership for ownership tracking
- `administration: read` - Access organization settings for compliance

##### Required Webhook Events

GitGuard subscribes to these webhook events:

**Essential Events:**
- `pull_request` - PR creation, updates, and state changes
- `pull_request_review` - Review submissions and state changes
- `push` - Branch updates and new commits
- `check_run` - CI/CD pipeline status updates
- `status` - Commit status updates from other tools

**Enhanced Intelligence Events:**
- `issues` - Issue creation and updates for policy tracking
- `release` - Release creation for deployment coordination
- `workflow_run` - GitHub Actions workflow completion
- `security_advisory` - Security vulnerability notifications
- `dependabot_alert` - Dependency security alerts

##### One-Click Installation

**Option 1: GitHub App Manifest (Recommended)**

1. **Create the GitHub App**:
   ```bash
   # Use the provided manifest for instant setup
   curl -X POST \
     -H "Accept: application/vnd.github.v3+json" \
     -H "Authorization: token YOUR_PERSONAL_ACCESS_TOKEN" \
     https://api.github.com/app-manifests/MANIFEST_CODE/conversions
   ```

2. **Install via Web Interface**:
   - Visit: `https://github.com/apps/gitguard-YOUR-ORG`
   - Click "Install"
   - Select repositories or install organization-wide
   - Authorize the required permissions

**Option 2: Manual GitHub App Creation**

1. **Navigate to GitHub Settings**:
   - Go to `https://github.com/settings/apps` (personal) or
   - `https://github.com/organizations/YOUR-ORG/settings/apps` (organization)

2. **Create New GitHub App**:
   - **App Name**: `GitGuard-YOUR-ORG`
   - **Homepage URL**: `https://your-org.github.io/gitguard`
   - **Webhook URL**: `https://your-gitguard-instance.com/webhooks/github`
   - **Webhook Secret**: Generate a secure random string

3. **Configure Permissions**: Use the OAuth scopes listed above

4. **Subscribe to Events**: Enable all webhook events listed above

##### Installation Manifest

For automated setup, use this GitHub App manifest:

```json
{
  "name": "GitGuard",
  "url": "https://github.com/gitguard/gitguard",
  "hook_attributes": {
    "url": "https://your-gitguard-instance.com/webhooks/github",
    "active": true
  },
  "redirect_url": "https://your-gitguard-instance.com/auth/github/callback",
  "callback_urls": [
    "https://your-gitguard-instance.com/auth/github/callback"
  ],
  "public": false,
  "default_permissions": {
    "contents": "read",
    "metadata": "read",
    "pull_requests": "write",
    "checks": "write",
    "statuses": "write",
    "issues": "write",
    "actions": "read",
    "security_events": "read",
    "members": "read",
    "administration": "read"
  },
  "default_events": [
    "pull_request",
    "pull_request_review",
    "push",
    "check_run",
    "status",
    "issues",
    "release",
    "workflow_run",
    "security_advisory",
    "dependabot_alert"
  ]
}
```

##### Post-Installation Configuration

1. **Configure Repository Settings**:
   ```yaml
   github:
     app_id: "123456"  # From GitHub App settings
     installation_id: "789012"  # From installation
     private_key_path: "/path/to/gitguard.private-key.pem"
     webhook_secret: "your-webhook-secret"
     repository: "your-org/your-repo"
   ```

2. **Set Branch Protection Rules**:
   - Require GitGuard status checks: `gitguard/policy-check`
   - Require GitGuard reviews: `gitguard/risk-assessment`
   - Enable auto-merge for approved PRs
   - Dismiss stale reviews when new commits are pushed

3. **Verify Installation**:
   ```bash
   # Test webhook delivery
   make test-webhook

   # Verify GitHub App permissions
   make verify-github-app

   # Check policy evaluation
   make test-policies
   ```

#### Alternative: Webhook-Only Setup

For organizations that prefer webhook-only integration:

1. **Create Repository Webhook**:
   - URL: `https://your-gitguard-instance.com/webhooks/github`
   - Content Type: `application/json`
   - Secret: Use the same webhook secret as configured
   - Events: Select the same events as listed above

2. **Generate Personal Access Token**:
   - Scopes: `repo`, `read:org`, `read:user`
   - Store securely in GitGuard configuration

**Note**: GitHub App installation is strongly recommended for production use due to enhanced security, granular permissions, and better audit trails.

## Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check Docker is running
docker --version

# Check port availability
lsof -i :8000,8001,8002,3000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Reset environment
make clean && make setup && make up
```

#### Demo Not Working
```bash
# Verify all services are healthy
make health

# Check service logs
make logs

# Restart specific service
make restart-api
```

#### Policy Not Triggering
```bash
# Test policy logic
opa test policies/

# Check policy syntax
opa fmt policies/guard_rules.rego

# View policy evaluation logs
docker-compose logs guard-api | grep policy
```

### Getting Help

- **📖 Documentation**: Complete guides at http://localhost:8001
- **🐛 Issues**: Report bugs on GitHub Issues
- **💬 Discussions**: Ask questions in GitHub Discussions
- **📧 Support**: Contact support@gitguard.dev

## Next Steps

### For Developers
1. **Explore the API**: http://localhost:8000/docs
2. **Graph API**: http://localhost:8002 for relationship data
3. **Read Architecture Guide**: [ARCHITECTURE.md](ARCHITECTURE.md)
4. **Contribute**: [CONTRIBUTING.md](CONTRIBUTING.md)
5. **Development Setup**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
6. **Chaos Engineering**: [tests/CHAOS_ENGINEERING.md](tests/CHAOS_ENGINEERING.md)

### For Teams
1. **Customize Policies**: Add rules with transparency features
2. **Configure Integrations**: Connect to Slack, JIRA, etc.
3. **Set Up Monitoring**: Configure SLO alerts and chaos drills
4. **Train Team**: Share demo scenarios and policy explanations
5. **Explore Relationships**: Use Mermaid graphs for code understanding
6. **Track Ownership**: Leverage dynamic owners index

### For Organizations
1. **Enterprise Setup**: Multi-repository configuration
2. **SSO Integration**: Connect to your identity provider
3. **Compliance Reporting**: Generate audit trails and reports
4. **Custom Dashboards**: Build organization-specific metrics

## Success Metrics

After implementing GitGuard, you should see:

- **📈 Faster Merge Times**: Automated decisions reduce review bottlenecks
- **📉 Reduced Incidents**: Policy enforcement prevents risky changes
- **📚 Better Documentation**: Automated PR digests with policy transparency
- **🕸️ Enhanced Understanding**: Mermaid graphs reveal code relationships
- **👥 Clear Ownership**: Dynamic tracking improves accountability
- **😊 Developer Satisfaction**: Transparent policies and fast feedback
- **🔍 Increased Visibility**: SLO monitoring and chaos validation
- **🛡️ System Resilience**: Chaos engineering validates robustness

Welcome to intelligent repository governance with GitGuard! 🛡️
