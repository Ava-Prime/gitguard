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

1. **Install GitHub App** (or configure webhook)
2. **Configure Repository Settings**:
   ```yaml
   github:
     repository: "your-org/your-repo"
     webhook_secret: "your-secret"
   ```
3. **Set Branch Protection Rules**:
   - Require GitGuard status checks
   - Enable auto-merge for approved PRs

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