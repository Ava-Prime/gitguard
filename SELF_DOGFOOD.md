# 🐕 GitGuard Self-Dogfooding Guide

> **TL;DR**: Use GitGuard to monitor GitGuard itself. Start with `make self-dogfood` for local setup, or deploy to cloud platforms with one-click blueprints.

## Why Self-Dogfood?

Self-dogfooding GitGuard on the GitGuard repository provides:
- **Real-world validation** of policies and decision-making
- **Authentic signals** for tuning and optimization
- **Confidence building** before deploying to production repositories
- **Demonstration value** for stakeholders and new users

---

# 🏠 A) Local Self-Hosting (Fastest Path)

## Prerequisites

- **Docker** (+ Docker Compose)
- **GitHub CLI** (`gh`)
- **jq** (optional, for JSON parsing)
- **ngrok** or **cloudflared** (for webhook tunneling)

## 1. Quick Start with Makefile

```bash
# Clone and navigate to GitGuard
git clone https://github.com/Ava-Prime/gitguard.git
cd gitguard

# 🚀 One-command setup
make self-dogfood
```

This will:
- ✅ Check prerequisites (Docker, GitHub CLI)
- 🔧 Generate `.env.dogfood` with sensible defaults
- 🚀 Launch all services (Temporal, API, Grafana, PostgreSQL)
- 📋 Display clear next steps for GitHub App setup

## 2. Manual Setup (Alternative)

### Step 1: Launch the Stack

```bash
# Bring up services using the temporal compose file
docker-compose -f docker-compose.temporal.yml up -d

# Verify services are running
docker-compose -f docker-compose.temporal.yml ps
```

### Step 2: Create GitHub App from Manifest

1. **Navigate to GitHub**: [Settings → Developer settings → GitHub Apps → New GitHub App](https://github.com/settings/apps/new)
2. **Import from manifest**: Click "Create from manifest" and paste contents of `app.json`
3. **Install the App**: After creation, click "Install App" and select `Ava-Prime/gitguard`

You'll receive:
- **App ID** (e.g., `123456`)
- **Private Key** (download the `.pem` file)
- **Webhook Secret** (you choose this)

### Step 3: Configure Environment

Create or update `.env.dogfood`:

```bash
# GitHub App Configuration
export GITHUB_APP_ID=123456
export GITHUB_APP_PRIVATE_KEY="$(cat /path/to/your-private-key.pem)"
export GITHUB_WEBHOOK_SECRET="your-chosen-secret-string"

# GitGuard Configuration
export GITGUARD_MODE=report-only  # Start safe!
export GITGUARD_LOG_LEVEL=info
export GITGUARD_WEBHOOK_PATH=/webhook/github

# Database Configuration
export POSTGRES_DB=gitguard
export POSTGRES_USER=gitguard
export POSTGRES_PASSWORD=gitguard-dev-$(date +%s)

# Temporal Configuration
export TEMPORAL_HOST=localhost:7233
export TEMPORAL_NAMESPACE=gitguard
```

### Step 4: Expose Local Server to GitHub

```bash
# Option A: ngrok (recommended)
ngrok http 8080
# Note the HTTPS URL: https://abc123.ngrok.io

# Option B: Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8080
```

**Update GitHub App Webhook URL** to: `https://<your-tunnel-url>/webhook/github`

### Step 5: Restart with Configuration

```bash
# Restart services with new environment
docker-compose -f docker-compose.temporal.yml --env-file .env.dogfood down
docker-compose -f docker-compose.temporal.yml --env-file .env.dogfood up -d
```

## 3. Verification & Testing

### Health Checks

```bash
# Check service status
make dogfood-status

# Manual health checks
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/policies/evaluate | jq '.decision.reasoning'
```

### Access Dashboards

- **GitGuard UI**: http://localhost:8080 (Policy explorer, org-brain insights)
- **Grafana**: http://localhost:3000 (admin/admin - P99 latency, merge rates, policy decisions)
- **Temporal UI**: http://localhost:8233 (Workflow monitoring)

### Create Test PR (Self-Dogfood)

```bash
# Create a test branch and trigger GitGuard
git checkout -b chore/dogfood-check
echo "self-dogfood test $(date)" >> DOGFOOD.md
git add DOGFOOD.md
git commit -m "chore: trigger GitGuard self-dogfood evaluation"
git push -u origin HEAD
gh pr create --fill
```

**Expected Behavior**:
- GitGuard receives webhook from GitHub
- Evaluates PR against policies
- Posts decision and reasoning as PR comment
- Updates Grafana metrics
- Logs decision audit trail

## 4. GitHub App Creation with Manifest

### Using the Included Manifest

GitGuard includes a pre-configured GitHub App manifest in `app.json` that simplifies app creation:

```bash
# 1. Navigate to GitHub App creation page
open "https://github.com/settings/apps/new"

# 2. Click "Create from manifest" and paste the contents of app.json
cat app.json | pbcopy  # macOS
cat app.json | clip   # Windows

# 3. After creation, install the app on your repository
# 4. Download the private key and note the App ID
```

### Manual Configuration (Alternative)

If you prefer manual setup:

1. **App Name**: `GitGuard Self-Dogfood`
2. **Homepage URL**: `https://github.com/Ava-Prime/gitguard`
3. **Webhook URL**: `https://your-tunnel-url/webhook/github`
4. **Webhook Secret**: Generate a secure random string
5. **Permissions**:
   - Repository permissions: Contents (Read), Metadata (Read), Pull requests (Write), Checks (Write), Statuses (Write)
   - Subscribe to events: Pull request, Push, Check suite, Check run, Issue comment, Repository

## 5. Webhook Safety & Security

### Webhook Validation

GitGuard validates all incoming webhooks using HMAC-SHA256:

```bash
# Ensure your webhook secret is secure
export GITHUB_WEBHOOK_SECRET="$(openssl rand -hex 32)"

# Test webhook validation
curl -X POST http://localhost:8080/webhook/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -H "X-Hub-Signature-256: sha256=$(echo -n '{}' | openssl dgst -sha256 -hmac "$GITHUB_WEBHOOK_SECRET" | cut -d' ' -f2)" \
  -d '{}'
```

### Tunnel Security Best Practices

```bash
# For ngrok: Use auth tokens and restrict access
ngrok config add-authtoken YOUR_AUTHTOKEN
ngrok http 8080 --basic-auth="gitguard:$(openssl rand -base64 32)"

# For cloudflared: Use access policies
cloudflared tunnel --url http://localhost:8080 --name gitguard-tunnel
```

### Rate Limiting & Monitoring

```bash
# Monitor webhook delivery in real-time
tail -f logs/gitguard.log | grep "webhook"

# Check webhook delivery status in GitHub
open "https://github.com/settings/apps/YOUR_APP_ID/advanced"
```

## 6. End-to-End Smoke Test

### Automated Smoke Test

Run the comprehensive smoke test:

```bash
# Run the built-in smoke test
make dogfood-smoketest

# Or manually:
./scripts/smoketest.sh
```

### Manual Smoke Test Scenarios

#### Scenario 1: PR Label Policy Test

```bash
# Create a test branch
git checkout -b test/pr-label-policy

# Make a simple change
echo "# Test PR Label Policy" >> TEST_PR_LABELS.md
git add TEST_PR_LABELS.md
git commit -m "test: verify PR label policy enforcement"
git push -u origin HEAD

# Create PR without required labels
gh pr create --title "Test PR without labels" --body "This PR should trigger label policy"

# Expected: GitGuard comments about missing required labels
# Expected: PR status check shows "pending" or "failure"
```

#### Scenario 2: Security Policy Test

```bash
# Create a branch with potential security issues
git checkout -b test/security-policy

# Add a file with a fake API key
echo 'API_KEY="sk-1234567890abcdef"' > config.py
git add config.py
git commit -m "test: add configuration with API key"
git push -u origin HEAD

# Create PR
gh pr create --title "Test security policy" --body "This PR contains a potential secret"

# Expected: GitGuard flags the potential secret
# Expected: PR comment with security policy violation details
```

#### Scenario 3: Dependency Policy Test

```bash
# Create a branch with vulnerable dependencies
git checkout -b test/dependency-policy

# Add a requirements file with known vulnerabilities
echo "requests==2.25.0" > requirements.txt  # Known vulnerability
echo "django==2.0.0" >> requirements.txt     # Outdated version
git add requirements.txt
git commit -m "test: add dependencies with vulnerabilities"
git push -u origin HEAD

# Create PR
gh pr create --title "Test dependency policy" --body "This PR adds vulnerable dependencies"

# Expected: GitGuard identifies vulnerable dependencies
# Expected: PR comment with upgrade recommendations
```

### Verification Checklist

After running smoke tests, verify:

- [ ] **Webhook Delivery**: GitHub shows successful webhook deliveries
- [ ] **Policy Evaluation**: GitGuard logs show policy evaluation for each PR
- [ ] **PR Comments**: GitGuard posts decision comments on test PRs
- [ ] **Status Checks**: GitHub shows GitGuard status checks on PRs
- [ ] **Metrics**: Grafana dashboards show policy decision metrics
- [ ] **Audit Trail**: Decision logs are stored and queryable
- [ ] **Performance**: API responses are under 2 seconds
- [ ] **Error Handling**: Invalid webhooks are rejected gracefully

### Cleanup Test Data

```bash
# Clean up test branches and PRs
gh pr list --state=open --json number,headRefName | jq -r '.[] | select(.headRefName | startswith("test/")) | .number' | xargs -I {} gh pr close {}
git branch | grep "test/" | xargs -I {} git branch -D {}
git push origin --delete $(git branch -r | grep "origin/test/" | sed 's/origin\///')
```

---

# ☁️ B) Cloud Deployment (One-Click Style)

Choose your preferred cloud platform. All deployment files are included in the repository.

## Railway (Recommended)

```bash
# Prerequisites: Railway CLI
npm install -g @railway/cli
railway login

# Deploy using railway.json blueprint
railway up

# Set environment variables in Railway dashboard
railway variables set GITHUB_APP_ID=123456
railway variables set GITHUB_APP_PRIVATE_KEY="$(cat your-key.pem)"
railway variables set GITHUB_WEBHOOK_SECRET="your-secret"
```

**Post-deployment**:
1. Note your Railway app URL (e.g., `https://gitguard-production.up.railway.app`)
2. Update GitHub App webhook to: `https://your-railway-url/webhook/github`
3. Test with a PR

## Fly.io

```bash
# Prerequisites: Fly CLI
curl -L https://fly.io/install.sh | sh
flyctl auth login

# Deploy using fly.toml configuration
flyctl deploy --copy-config --app gitguard-self

# Set secrets
flyctl secrets set GITHUB_APP_ID=123456
flyctl secrets set GITHUB_APP_PRIVATE_KEY="$(cat your-key.pem)"
flyctl secrets set GITHUB_WEBHOOK_SECRET="your-secret"
```

## Render

1. **Create Blueprint**: Go to [Render Dashboard](https://dashboard.render.com) → New + → Blueprint
2. **Connect Repository**: Point to `https://github.com/Ava-Prime/gitguard`
3. **Auto-deploy**: Render reads `render.yaml` and provisions services
4. **Set Environment Variables**: Add the three GitHub App secrets in Render dashboard
5. **Update Webhook**: Set GitHub App webhook to your Render URL

## Vercel/Netlify (Static + Serverless)

```bash
# For documentation and static assets only
# API requires serverless functions or external hosting

# Vercel
vercel --prod

# Netlify
netlify deploy --prod
```

---

# 🎯 C) Deployment Strategy: Do Both

## Phase 1: Self-Dogfood on Production Repo

**Target**: `Ava-Prime/gitguard` (this repository)

**Configuration**:
```yaml
# Start in report-only mode
GITGUARD_MODE: report-only
GITGUARD_AUTO_MERGE: false
GITGUARD_BLOCK_ON_POLICY_VIOLATION: false
```

**Benefits**:
- Real contributor behavior and code patterns
- Authentic policy evaluation scenarios
- Gradual confidence building
- No risk of disrupting development workflow

**Monitoring**:
- Watch Grafana dashboards for policy decision trends
- Review false positive/negative rates
- Collect developer feedback on policy helpfulness

## Phase 2: Create Public Demo Repository

**Target**: `Ava-Prime/gitguard-demo` (new sandbox repo)

**Purpose**:
- Controlled demonstration environment
- Synthetic "naughty" PRs for guaranteed interesting results
- Safe space for policy experimentation
- Marketing and sales demonstrations

**Demo Scenarios**:
```bash
# Create demo repository with synthetic violations
gh repo create Ava-Prime/gitguard-demo --public --clone
cd gitguard-demo

# Seed with problematic code
echo 'api_key = "sk-1234567890abcdef"' > config.py  # Secret detection
echo 'requests==2.25.0' > requirements.txt          # Vulnerable dependency
echo 'GPL-licensed-lib==1.0' >> requirements.txt    # License conflict

# Create "bad" PRs for demo purposes
gh pr create --title "feat: add API integration" --body "Demo PR with secrets"
```

---

# 📋 Configuration Reference

## Environment Variables

### Required (GitHub App)
```bash
GITHUB_APP_ID=123456                    # Your GitHub App ID
GITHUB_APP_PRIVATE_KEY="-----BEGIN..." # Private key content
GITHUB_WEBHOOK_SECRET="random-string"   # Webhook validation secret
```

### GitGuard Behavior
```bash
GITGUARD_MODE=report-only               # report-only | enforce
GITGUARD_AUTO_MERGE=false               # Auto-merge approved PRs
GITGUARD_BLOCK_ON_POLICY_VIOLATION=false # Block violating PRs
GITGUARD_LOG_LEVEL=info                 # debug | info | warn | error
GITGUARD_WEBHOOK_PATH=/webhook/github   # Webhook endpoint path
```

### Database & Infrastructure
```bash
POSTGRES_DB=gitguard
POSTGRES_USER=gitguard
POSTGRES_PASSWORD=secure-password
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=gitguard
REDIS_URL=redis://localhost:6379
```

## Policy Configuration

Create `.gitguard/config.yml` in your repository:

```yaml
# GitGuard Configuration
version: "1.0"

policies:
  # Secret Detection
  secrets:
    enabled: true
    sensitivity: high  # high | medium | low
    block_on_detection: true
    patterns:
      - api_keys
      - database_urls
      - private_keys

  # Dependency Security
  dependencies:
    enabled: true
    vulnerability_threshold: medium  # critical | high | medium | low
    license_compatibility: strict    # strict | permissive
    auto_update_minor: true

  # Code Quality
  code_quality:
    enabled: true
    test_coverage_threshold: 80
    require_tests_for_new_code: true
    max_complexity: 10

  # Code Ownership
  ownership:
    enabled: true
    require_codeowner_approval: true
    min_reviewers: 1
    auto_assign_reviewers: true

# Notification Settings
notifications:
  slack:
    webhook_url: "https://hooks.slack.com/..."
    channels:
      - "#security-alerts"
      - "#dev-notifications"

  email:
    smtp_host: "smtp.gmail.com"
    recipients:
      - "security@company.com"
      - "devops@company.com"
```

---

# 🔧 Operational Commands

## Local Development

```bash
# Start self-dogfooding
make self-dogfood

# Check status
make dogfood-status

# Stop services (preserves data)
make dogfood-stop

# Clean restart
docker-compose -f docker-compose.temporal.yml down -v
make self-dogfood

# View logs
docker-compose -f docker-compose.temporal.yml logs -f gitguard-api
docker-compose -f docker-compose.temporal.yml logs -f temporal
```

## Policy Testing

```bash
# Test policies locally
opa test policies/ -v

# Test specific policy
curl -X POST http://localhost:8080/api/v1/policies/evaluate \
  -H "Content-Type: application/json" \
  -d '{"files": {"test.py": "api_key = \"sk-test\""}}'

# Policy coverage report
opa test policies/ --coverage
```

## Monitoring & Debugging

```bash
# Health checks
curl http://localhost:8080/health
curl http://localhost:8080/metrics  # Prometheus metrics

# Policy evaluation endpoint
curl http://localhost:8080/api/v1/policies/evaluate | jq

# Webhook testing
curl -X POST http://localhost:8080/webhook/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d @test-webhook.json
```

---

# 🎯 Pro Tips for Successful Self-Dogfooding

## Start Conservative

1. **Begin with `report-only` mode** - observe decisions without blocking
2. **Monitor false positive rates** - tune policies based on real usage
3. **Gradual enforcement** - enable blocking for clearly low-risk rules first
4. **Team communication** - announce the rollout and gather feedback

## Policy Tuning

```yaml
# Example: Gradual tightening
week_1:
  mode: report-only
  policies: [secrets, critical_vulnerabilities]

week_2:
  mode: conditional
  policies: [secrets, vulnerabilities, license_conflicts]

week_3:
  mode: enforce
  policies: [all]
  exceptions: [documentation_changes, test_files]
```

## Documentation Integration

1. **Link to policy cookbook** in PR templates:
   ```markdown
   ## Policy Information
   📋 [What to expect from GitGuard](docs/policy-cookbook.md)
   📊 [Live dashboards](http://localhost:3000)
   ```

2. **Pin dashboard links** in repository description
3. **Add policy status badges** to README

## Automation Enhancements

```bash
# Add to .github/workflows/self-dogfood.yml
name: Self-Dogfood Health Check
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Check GitGuard Health
        run: |
          curl -f http://localhost:8080/health || exit 1
          curl -f http://localhost:3000/api/health || exit 1
```

---

# 🚨 Troubleshooting

## Common Issues

### Services Won't Start
```bash
# Check Docker daemon
docker info

# Check port conflicts
lsof -i :8080
lsof -i :3000
lsof -i :7233

# Check logs
docker-compose -f docker-compose.temporal.yml logs
```

### GitHub Webhook Not Received
```bash
# Verify tunnel is active
curl https://your-ngrok-url.ngrok.io/health

# Check GitHub App webhook settings
gh api /app/hook/deliveries

# Test webhook locally
curl -X POST http://localhost:8080/webhook/github \
  -H "X-GitHub-Event: ping" \
  -d '{}'
```

### Policy Evaluation Errors
```bash
# Check OPA syntax
opa fmt policies/
opa test policies/ -v

# Validate policy data
curl http://localhost:8080/api/v1/policies/debug
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor API response times
curl -w "@curl-format.txt" http://localhost:8080/health

# Grafana performance dashboard
open http://localhost:3000/d/gitguard-performance
```

## Getting Help

- 📖 **Documentation**: [docs/](docs/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/Ava-Prime/gitguard/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Ava-Prime/gitguard/discussions)
- 📧 **Security**: [security@gitguard.dev](mailto:security@gitguard.dev)

---

# 🎉 Success Metrics

Track these metrics to measure self-dogfooding success:

## Policy Effectiveness
- **True Positive Rate**: Legitimate security issues caught
- **False Positive Rate**: Safe changes incorrectly flagged
- **Policy Coverage**: Percentage of changes evaluated
- **Response Time**: Time from PR to policy decision

## Developer Experience
- **Adoption Rate**: Teams using GitGuard
- **Feedback Sentiment**: Developer satisfaction scores
- **Time to Resolution**: How quickly policy violations are fixed
- **Learning Curve**: Time for new developers to understand policies

## Security Impact
- **Vulnerabilities Prevented**: Issues caught before merge
- **Compliance Score**: Adherence to security policies
- **Incident Reduction**: Decrease in security-related incidents
- **Audit Readiness**: Completeness of decision audit trails

---

**🚀 Ready to start?** Run `make self-dogfood` and begin your GitGuard journey!

**💡 Questions?** Check the [troubleshooting guide](docs/troubleshooting.md) or [open an issue](https://github.com/Ava-Prime/gitguard/issues/new).
