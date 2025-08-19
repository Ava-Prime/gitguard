---
layout: page
title: Getting Started
description: Complete setup guide for GitGuard - from installation to your first policy
permalink: /getting-started/
---

# Getting Started with GitGuard

Get GitGuard up and running in your organization in just a few minutes. This guide will walk you through installation, configuration, and deploying your first policies.

## Quick Installation

### Option 1: One-Click GitHub App (Recommended)

The fastest way to get started is with our GitHub App:

1. **Install the GitHub App**
   ```
   Visit: https://github.com/apps/gitguard-policy-engine
   Click "Install" and select your repositories
   ```

2. **Configure Webhooks**
   The app automatically configures these webhook events:
   - `pull_request`
   - `pull_request_review`
   - `push`
   - `check_run`
   - `status`

3. **Set Environment Variables**
   ```bash
   # In your repository settings > Secrets
   GITGUARD_API_URL=https://api.gitguard.dev
   GITGUARD_WEBHOOK_SECRET=your-webhook-secret
   ```

### Option 2: Self-Hosted Deployment

For full control, deploy GitGuard in your own infrastructure:

```bash
# Clone the repository
git clone https://github.com/your-org/gitguard.git
cd gitguard

# Copy example configuration
cp config/example.env .env
cp config/policies/examples/* config/policies/

# Start with Docker Compose
docker-compose up -d

# Verify installation
curl http://localhost:8000/health
```

## Configuration

### Environment Variables

Create a `.env` file with these essential settings:

```bash
# Core Configuration
GITGUARD_PORT=8000
GITGUARD_LOG_LEVEL=info
GITGUARD_ENVIRONMENT=production

# GitHub Integration
GITHUB_APP_ID=your-app-id
GITHUB_APP_PRIVATE_KEY_PATH=/path/to/private-key.pem
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Policy Engine
OPA_BUNDLE_URL=file:///app/config/policies
OPA_DECISION_LOG_ENABLED=true

# Database (Optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/gitguard

# Redis (Optional)
REDIS_URL=redis://localhost:6379
```

### Policy Configuration

GitGuard uses [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) with Rego policies:

```rego
# config/policies/basic_checks.rego
package gitguard.policies

# Require PR reviews for main branch
require_review {
    input.pull_request.base.ref == "main"
    input.pull_request.requested_reviewers
    count(input.pull_request.requested_reviewers) > 0
}

# Block large PRs
block_large_pr {
    input.pull_request.additions > 500
    input.pull_request.deletions > 200
}

# Allow auto-merge for small, reviewed changes
allow_auto_merge {
    require_review
    not block_large_pr
    input.pull_request.additions < 100
}
```

## Your First Policy

Let's create a simple policy that requires tests for new features:

1. **Create the policy file**
   ```bash
   # config/policies/require_tests.rego
   ```

2. **Define the policy**
   ```rego
   package gitguard.policies.tests

   # Require tests for new features
   require_tests {
       # Check if this is a feature branch
       startswith(input.pull_request.head.ref, "feature/")

       # Ensure test files are included
       some file in input.pull_request.changed_files
       contains(file.filename, "test")
   }

   # Policy decision
   decision := {
       "allowed": require_tests,
       "reason": "Feature branches must include test files",
       "severity": "error"
   }
   ```

3. **Test the policy**
   ```bash
   # Use the built-in policy tester
   curl -X POST http://localhost:8000/api/v1/policies/test \
     -H "Content-Type: application/json" \
     -d '{
       "policy": "require_tests",
       "input": {
         "pull_request": {
           "head": {"ref": "feature/new-login"},
           "changed_files": [
             {"filename": "src/auth.py"},
             {"filename": "tests/test_auth.py"}
           ]
         }
       }
     }'
   ```

## Integration Examples

### GitHub Actions Workflow

```yaml
# .github/workflows/gitguard.yml
name: GitGuard Policy Check

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  policy-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: GitGuard Policy Evaluation
        uses: gitguard/action@v1
        with:
          api-url: ${{ secrets.GITGUARD_API_URL }}
          token: ${{ secrets.GITGUARD_TOKEN }}
          policy-bundle: './config/policies'

      - name: Comment Results
        uses: actions/github-script@v6
        with:
          script: |
            const { data: result } = await github.rest.checks.listForRef({
              owner: context.repo.owner,
              repo: context.repo.repo,
              ref: context.sha
            });

            // Post policy results as PR comment
            await github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## GitGuard Policy Results\n\n${result.summary}`
            });
```

### Webhook Handler

```python
# Custom webhook handler
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.json

    if payload['action'] in ['opened', 'synchronize']:
        # Forward to GitGuard for evaluation
        response = requests.post(
            'http://localhost:8000/api/v1/evaluate',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        result = response.json()

        # Update PR status
        if result['decision']['allowed']:
            set_status('success', 'Policies passed')
        else:
            set_status('failure', result['decision']['reason'])

    return jsonify({'status': 'processed'})

def set_status(state, description):
    # Update GitHub commit status
    pass
```

## Verification

Verify your GitGuard installation:

### 1. Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "0.1.0"}
```

### 2. Policy Validation
```bash
curl http://localhost:8000/api/v1/policies
# Expected: List of loaded policies
```

### 3. Test Evaluation
```bash
curl -X POST http://localhost:8000/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
# Expected: Policy evaluation results
```

### 4. GitHub Integration
Create a test PR and verify:
- ✅ Webhook delivery in GitHub settings
- ✅ Policy evaluation in GitGuard logs
- ✅ Status check on the PR
- ✅ Comment with policy results

## Next Steps

### Explore Advanced Features
- **[Policy Development Guide](/policies)** - Write sophisticated policies
- **[API Reference](/api)** - Integrate with your tools
- **[Architecture Overview](/architecture)** - Understand the system
- **[MCP Integration](/mcp)** - Claude Desktop integration

### Join the Community
- **GitHub**: [Issues & Discussions](https://github.com/your-org/gitguard)
- **Discord**: [Community Server](https://discord.gg/gitguard)
- **Documentation**: [docs.gitguard.dev](https://docs.gitguard.dev)

### Production Checklist

- [ ] Configure monitoring and alerting
- [ ] Set up backup and disaster recovery
- [ ] Review security settings
- [ ] Train your team on policy development
- [ ] Establish policy governance process
- [ ] Configure integration with existing tools

---

## Troubleshooting

### Common Issues

**GitGuard not receiving webhooks**
- Verify webhook URL is accessible
- Check webhook secret configuration
- Review GitHub App permissions

**Policies not loading**
- Validate Rego syntax with `opa fmt`
- Check file permissions and paths
- Review OPA bundle configuration

**Performance issues**
- Enable Redis for caching
- Configure database connection pooling
- Review policy complexity

### Getting Help

If you encounter issues:
1. Check the [troubleshooting guide](/troubleshooting)
2. Search [existing issues](https://github.com/your-org/gitguard/issues)
3. Join our [Discord community](https://discord.gg/gitguard)
4. Create a [new issue](https://github.com/your-org/gitguard/issues/new)

---

*Ready to dive deeper? Explore our [comprehensive examples](/examples) or learn about [advanced policy patterns](/policies/advanced).*
