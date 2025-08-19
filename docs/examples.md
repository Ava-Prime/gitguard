---
layout: default
title: Policy Examples
description: Real-world GitGuard policy examples and implementation patterns
---

# Policy Examples

This page provides practical, real-world examples of GitGuard policies that you can adapt for your organization.

## Quick Examples

### 1. Basic Release Window Policy

**Use Case**: Prevent deployments during weekends and holidays

```rego
package gitguard.examples.basic_release_window

# Allow merges only during business days
allow {
    input.event_type == "pull_request"
    input.action == "closed"
    input.pull_request.merged == true
    is_business_day
}

is_business_day {
    now := time.now_ns()
    weekday := time.weekday(now)[0]
    weekday >= 1  # Monday
    weekday <= 5  # Friday
}

# Deny message for weekend attempts
deny[msg] {
    input.event_type == "pull_request"
    input.action == "closed"
    input.pull_request.merged == true
    not is_business_day
    msg := "Deployments are not allowed on weekends"
}
```

### 2. Risk-Based Approval Policy

**Use Case**: Require more approvals for high-risk changes

```rego
package gitguard.examples.risk_based_approvals

# Calculate risk score based on files changed
risk_score := score {
    critical_files := count([f | f := input.files[_]; is_critical_file(f.filename)])
    total_files := count(input.files)
    lines_changed := sum([f.changes | f := input.files[_]])

    file_risk := (critical_files / total_files) * 40
    size_risk := min([lines_changed / 10, 40])
    author_risk := calculate_author_risk

    score := file_risk + size_risk + author_risk
}

# Determine required approvals based on risk
required_approvals := approvals {
    risk := risk_score
    approvals := 1 if risk < 30
    approvals := 2 if risk >= 30; risk < 70
    approvals := 3 if risk >= 70
}

# Main policy decision
allow {
    count(input.approvals) >= required_approvals
}

# Helper functions
is_critical_file(filename) {
    critical_patterns := [
        "Dockerfile", "docker-compose", "package.json",
        "requirements.txt", ".github/workflows", "terraform"
    ]
    pattern := critical_patterns[_]
    contains(filename, pattern)
}

calculate_author_risk := risk {
    # New contributors have higher risk
    author := input.pull_request.user.login
    contributions := data.contributors[author].contributions
    risk := 20 if contributions < 5
    risk := 10 if contributions >= 5; contributions < 20
    risk := 0 if contributions >= 20
}
```

## Advanced Examples

### 3. Security-Focused Policy

**Use Case**: Enhanced security checks for sensitive files

```rego
package gitguard.examples.security_policy

# Security-sensitive file patterns
security_patterns := [
    "auth", "security", "crypto", "password", "token",
    "secret", "key", "cert", "ssl", "tls"
]

# Detect security-related changes
has_security_changes {
    file := input.files[_]
    pattern := security_patterns[_]
    contains(lower(file.filename), pattern)
}

# Require security team approval for security changes
requires_security_approval {
    has_security_changes
    not has_security_team_approval
}

has_security_team_approval {
    approval := input.approvals[_]
    approval.user.login in data.security_team_members
}

# Check for potential secrets in diff
has_potential_secrets {
    file := input.files[_]
    line := file.patch_lines[_]

    # Simple regex patterns for common secrets
    secret_patterns := [
        "password\s*=\s*['\"][^'\"]+['\"]i",
        "api[_-]?key\s*=\s*['\"][^'\"]+['\"]i",
        "secret\s*=\s*['\"][^'\"]+['\"]i",
        "token\s*=\s*['\"][^'\"]+['\"]i"
    ]

    pattern := secret_patterns[_]
    regex.match(pattern, line.content)
}

# Main security policy
allow {
    not requires_security_approval
    not has_potential_secrets
    passes_security_scan
}

deny[msg] {
    requires_security_approval
    msg := "Security team approval required for security-related changes"
}

deny[msg] {
    has_potential_secrets
    msg := "Potential secrets detected in code changes"
}

passes_security_scan {
    # Integration with external security tools
    scan_result := data.security_scans[input.pull_request.head.sha]
    scan_result.status == "passed"
}
```

### 4. Org-Brain Intelligence Policy

**Use Case**: Dynamic code ownership and expert routing

```rego
package gitguard.examples.org_brain_policy

# Get dynamic code owners based on Org-Brain analysis
get_code_owners := owners {
    changed_files := {f.filename | f := input.files[_]}

    owners := {owner |
        file := changed_files[_]
        ownership_data := data.org_brain.file_ownership[file]
        owner := ownership_data.primary_owners[_]
    }
}

# Find subject matter experts for the changes
get_experts := experts {
    technologies := extract_technologies

    experts := {expert |
        tech := technologies[_]
        expert_data := data.org_brain.expertise[tech]
        expert := expert_data.experts[_]
        expert_data.confidence > 0.7
    }
}

# Extract technologies from file changes
extract_technologies := techs {
    techs := {tech |
        file := input.files[_]
        extension := get_file_extension(file.filename)
        tech := data.technology_mapping[extension]
    }
}

# Require approval from code owners or experts
allow {
    has_owner_approval or has_expert_approval
}

has_owner_approval {
    owners := get_code_owners
    approval := input.approvals[_]
    approval.user.login in owners
}

has_expert_approval {
    experts := get_experts
    approval := input.approvals[_]
    approval.user.login in experts
}

# Helper function
get_file_extension(filename) := ext {
    parts := split(filename, ".")
    ext := parts[count(parts) - 1]
}
```

### 5. Temporal Workflow Integration

**Use Case**: Complex approval workflows with time-based escalation

```rego
package gitguard.examples.temporal_workflow

# Trigger different workflows based on change characteristics
workflow_decision := decision {
    risk := calculate_risk_score

    decision := "fast_track" if risk < 20
    decision := "standard_review" if risk >= 20; risk < 60
    decision := "enhanced_review" if risk >= 60; risk < 80
    decision := "security_review" if risk >= 80
}

# Fast track for low-risk changes
fast_track_allowed {
    workflow_decision == "fast_track"
    has_basic_approval
    passes_automated_checks
}

# Standard review process
standard_review_allowed {
    workflow_decision == "standard_review"
    count(input.approvals) >= 2
    has_ci_passed
    not blocks_deployment
}

# Enhanced review for high-risk changes
enhanced_review_allowed {
    workflow_decision == "enhanced_review"
    has_senior_approval
    has_architecture_review
    passes_security_scan
}

# Security review for critical changes
security_review_allowed {
    workflow_decision == "security_review"
    has_security_team_approval
    has_penetration_test_approval
    has_compliance_sign_off
}

# Main policy decision
allow {
    fast_track_allowed
} else {
    standard_review_allowed
} else {
    enhanced_review_allowed
} else {
    security_review_allowed
}

# Escalation triggers
escalation_required {
    hours_since_creation > 48
    not has_sufficient_approvals
    workflow_decision in ["enhanced_review", "security_review"]
}

# Helper functions
calculate_risk_score := score {
    # Implementation from previous examples
    score := 50  # Placeholder
}

has_basic_approval {
    count(input.approvals) >= 1
}

has_senior_approval {
    approval := input.approvals[_]
    approval.user.login in data.senior_developers
}

hours_since_creation := hours {
    created := time.parse_rfc3339_ns(input.pull_request.created_at)
    now := time.now_ns()
    hours := (now - created) / 1000000000 / 3600
}
```

## Integration Examples

### 6. GitHub Actions Integration

**Use Case**: Integrate GitGuard policies with GitHub Actions workflows

```yaml
# .github/workflows/gitguard-check.yml
name: GitGuard Policy Check

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  policy-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: GitGuard Policy Evaluation
        uses: gitguard/policy-action@v1
        with:
          policy-bundle: './policies'
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Post Results
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('gitguard-results.json'));

            const body = `## GitGuard Policy Results

            **Decision**: ${results.allow ? '✅ APPROVED' : '❌ BLOCKED'}
            **Risk Score**: ${results.risk_score}/100

            ### Policy Violations
            ${results.violations.map(v => `- ${v}`).join('\n')}

            ### Required Actions
            ${results.required_actions.map(a => `- ${a}`).join('\n')}
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

### 7. Webhook Handler Example

**Use Case**: Process GitHub webhooks with GitGuard policies

```python
# webhook_handler.py
from flask import Flask, request, jsonify
import json
from gitguard import PolicyEngine

app = Flask(__name__)
engine = PolicyEngine(policy_dir='./policies')

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.json

    # Extract relevant data for policy evaluation
    policy_input = {
        'event_type': payload.get('action'),
        'pull_request': payload.get('pull_request', {}),
        'repository': payload.get('repository', {}),
        'files': get_changed_files(payload),
        'approvals': get_approvals(payload)
    }

    # Evaluate policies
    result = engine.evaluate(policy_input)

    # Take action based on policy decision
    if result['allow']:
        # Auto-merge if conditions are met
        if should_auto_merge(result):
            merge_pull_request(payload['pull_request'])
    else:
        # Block merge and add comment
        add_policy_comment(payload['pull_request'], result)

    return jsonify(result)

def get_changed_files(payload):
    # Implementation to fetch changed files
    pass

def get_approvals(payload):
    # Implementation to fetch approvals
    pass

def should_auto_merge(result):
    return result.get('auto_merge', False)

def merge_pull_request(pr):
    # Implementation to merge PR
    pass

def add_policy_comment(pr, result):
    # Implementation to add comment
    pass
```

## Testing Examples

### 8. Policy Unit Tests

```rego
package gitguard.examples.basic_release_window_test

import data.gitguard.examples.basic_release_window

# Test business day detection
test_monday_is_business_day {
    # Mock Monday timestamp
    mock_time := 1642464000000000000  # Monday, Jan 17, 2022

    basic_release_window.is_business_day with time.now_ns as mock_time
}

test_saturday_is_not_business_day {
    # Mock Saturday timestamp
    mock_time := 1642291200000000000  # Saturday, Jan 15, 2022

    not basic_release_window.is_business_day with time.now_ns as mock_time
}

# Test complete policy
test_allow_business_day_merge {
    mock_input := {
        "event_type": "pull_request",
        "action": "closed",
        "pull_request": {"merged": true}
    }

    mock_time := 1642464000000000000  # Monday

    basic_release_window.allow with input as mock_input with time.now_ns as mock_time
}

test_deny_weekend_merge {
    mock_input := {
        "event_type": "pull_request",
        "action": "closed",
        "pull_request": {"merged": true}
    }

    mock_time := 1642291200000000000  # Saturday

    count(basic_release_window.deny) > 0 with input as mock_input with time.now_ns as mock_time
}
```

## Configuration Examples

### 9. Environment-Specific Configuration

```yaml
# config/production.yml
policies:
  release_window:
    enabled: true
    business_hours_only: true
    timezone: "UTC"
    holidays:
      - "2024-01-01"  # New Year
      - "2024-07-04"  # Independence Day
      - "2024-12-25"  # Christmas

  risk_assessment:
    enabled: true
    thresholds:
      low: 30
      medium: 60
      high: 80

  security:
    enabled: true
    require_security_approval: true
    secret_scanning: true

teams:
  security_team:
    - "security-lead"
    - "security-engineer-1"
    - "security-engineer-2"

  senior_developers:
    - "tech-lead"
    - "senior-dev-1"
    - "architect"

integrations:
  github:
    auto_merge: true
    status_checks: true

  slack:
    notifications: true
    channel: "#deployments"
```

## Next Steps

- **[Policy Documentation](policies.md)** - Learn policy syntax and features
- **[API Reference](api.md)** - Integrate with GitGuard APIs
- **[Getting Started](getting-started.md)** - Set up your first policy
- **[Troubleshooting](troubleshooting.md)** - Debug policy issues

---

*Need help with a specific use case? [Open an issue](https://github.com/your-org/gitguard/issues) or [join our community](https://discord.gg/gitguard).*
