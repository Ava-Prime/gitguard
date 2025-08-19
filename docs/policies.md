---
layout: default
title: Policy Documentation
description: Comprehensive guide to GitGuard policies, OPA/Rego rules, and policy configuration
---

# Policy Documentation

GitGuard uses Open Policy Agent (OPA) and Rego to define flexible, powerful policies for repository governance. This guide covers policy creation, configuration, and best practices.

## Quick Start

### Basic Policy Structure

```rego
package gitguard.policies

# Policy metadata
metadata := {
    "name": "release-window-policy",
    "description": "Enforces release window restrictions",
    "version": "1.0.0"
}

# Main policy decision
allow {
    input.event_type == "pull_request"
    is_within_release_window
    has_required_approvals
}

# Helper rules
is_within_release_window {
    # Implementation details
}

has_required_approvals {
    # Implementation details
}
```

## Core Policy Types

### 1. Release Window Policies

Control when changes can be merged based on time windows, holidays, and business rules.

```rego
package gitguard.policies.release_window

# Allow merges during business hours (9 AM - 5 PM UTC)
allow_business_hours {
    now := time.now_ns()
    hour := time.weekday(now)[1]
    hour >= 9
    hour <= 17
}

# Block merges on weekends
deny_weekends {
    now := time.now_ns()
    weekday := time.weekday(now)[0]
    weekday_name := ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][weekday]
    weekday_name in ["Saturday", "Sunday"]
}

# Holiday restrictions
deny_holidays {
    now := time.now_ns()
    date := time.date(now)
    date in data.holidays
}
```

### 2. Risk Assessment Policies

Evaluate PR risk based on multiple factors and assign risk scores.

```rego
package gitguard.policies.risk_assessment

# Calculate overall risk score (0-100)
risk_score := score {
    file_risk := calculate_file_risk
    author_risk := calculate_author_risk
    change_risk := calculate_change_risk

    score := (file_risk + author_risk + change_risk) / 3
}

# File-based risk calculation
calculate_file_risk := risk {
    critical_files := count([f | f := input.files[_]; is_critical_file(f)])
    total_files := count(input.files)

    risk := (critical_files / total_files) * 100
}

# Critical file detection
is_critical_file(file) {
    critical_patterns := [
        "Dockerfile",
        "docker-compose.yml",
        "package.json",
        "requirements.txt",
        ".github/workflows/"
    ]

    pattern := critical_patterns[_]
    contains(file.path, pattern)
}
```

### 3. Approval Policies

Define approval requirements based on change type, risk level, and organizational structure.

```rego
package gitguard.policies.approvals

# Required approvals based on risk level
required_approvals := count {
    risk := data.risk_assessment.risk_score

    count := 1 if risk < 30
    count := 2 if risk >= 30; risk < 70
    count := 3 if risk >= 70
}

# Team-based approval requirements
requires_team_approval {
    affected_teams := get_affected_teams
    count(affected_teams) > 1
}

get_affected_teams := teams {
    teams := {team |
        file := input.files[_]
        team := data.codeowners[file.path]
    }
}
```

## Advanced Policy Features

### Org-Brain Integration

Leverage organizational intelligence for smarter policy decisions.

```rego
package gitguard.policies.org_brain

# Dynamic owner detection
get_dynamic_owners := owners {
    # Query Org-Brain for relationship mapping
    relationships := data.org_brain.relationships[input.repository]

    owners := {owner |
        rel := relationships[_]
        rel.type == "owns"
        owner := rel.target
    }
}

# Expertise-based routing
get_expert_reviewers := experts {
    files := input.files
    technologies := extract_technologies(files)

    experts := {expert |
        tech := technologies[_]
        expert := data.org_brain.experts[tech][_]
    }
}
```

### Temporal Workflows

Integrate with Temporal for complex, stateful policy workflows.

```rego
package gitguard.policies.temporal

# Trigger workflow for high-risk changes
trigger_review_workflow {
    risk_score > 80
    not has_security_review
}

# Escalation policies
escalate_to_security_team {
    security_files_changed
    not security_team_approved
    hours_since_creation > 24
}

security_files_changed {
    file := input.files[_]
    security_patterns := [
        "auth", "security", "crypto", "password", "token"
    ]
    pattern := security_patterns[_]
    contains(lower(file.path), pattern)
}
```

## Policy Configuration

### Environment-Specific Policies

```yaml
# config/policies.yml
production:
  policies:
    - name: "strict-release-window"
      enabled: true
      config:
        business_hours_only: true
        weekend_block: true
        holiday_block: true

    - name: "high-security-approval"
      enabled: true
      config:
        min_approvals: 3
        security_team_required: true

staging:
  policies:
    - name: "relaxed-release-window"
      enabled: true
      config:
        business_hours_only: false
        weekend_block: false

    - name: "standard-approval"
      enabled: true
      config:
        min_approvals: 1
```

### Policy Testing

```rego
package gitguard.policies.release_window_test

import data.gitguard.policies.release_window

# Test business hours policy
test_allow_business_hours {
    # Mock input for Tuesday 2 PM UTC
    mock_input := {
        "timestamp": "2024-01-16T14:00:00Z"
    }

    release_window.allow_business_hours with input as mock_input
}

test_deny_weekend {
    # Mock input for Saturday
    mock_input := {
        "timestamp": "2024-01-13T14:00:00Z"
    }

    release_window.deny_weekends with input as mock_input
}
```

## Policy Examples

### Complete Release Policy

```rego
package gitguard.examples.complete_release

# Main policy decision
allow {
    is_pull_request
    within_release_window
    has_sufficient_approvals
    passes_risk_threshold
    no_security_violations
}

# Helper rules
is_pull_request {
    input.event_type == "pull_request"
    input.action in ["opened", "synchronize", "reopened"]
}

within_release_window {
    not is_weekend
    not is_holiday
    is_business_hours
}

has_sufficient_approvals {
    required := calculate_required_approvals
    actual := count(input.approvals)
    actual >= required
}

passes_risk_threshold {
    risk := calculate_risk_score
    threshold := data.config.risk_threshold
    risk <= threshold
}

no_security_violations {
    not has_security_issues
    not modifies_security_files without security_approval
}
```

## Best Practices

### 1. Policy Organization

- **Modular Design**: Break policies into focused, reusable modules
- **Clear Naming**: Use descriptive package and rule names
- **Documentation**: Include metadata and comments

### 2. Performance Optimization

- **Efficient Queries**: Minimize data traversal
- **Caching**: Use data references for expensive computations
- **Indexing**: Structure data for fast lookups

### 3. Testing Strategy

- **Unit Tests**: Test individual rules in isolation
- **Integration Tests**: Test complete policy workflows
- **Regression Tests**: Prevent policy regressions

### 4. Monitoring and Observability

- **Policy Metrics**: Track policy execution and decisions
- **Audit Logs**: Maintain decision audit trails
- **Performance Monitoring**: Monitor policy evaluation time

## Troubleshooting

### Common Issues

1. **Policy Not Triggering**
   - Check policy package name
   - Verify input data structure
   - Review policy conditions

2. **Performance Issues**
   - Profile policy execution
   - Optimize data queries
   - Consider policy caching

3. **Unexpected Decisions**
   - Enable debug logging
   - Test with sample data
   - Review policy logic

### Debug Tools

```bash
# Test policy with sample input
opa eval -d policies/ -i input.json "data.gitguard.policies.allow"

# Profile policy performance
opa test policies/ --profile

# Validate policy syntax
opa fmt policies/
```

## Next Steps

- [API Reference](api.md) - Integrate policies via API
- [Examples](examples/) - Browse policy examples
- [Architecture](architecture.md) - Understand policy execution
- [Troubleshooting](troubleshooting.md) - Resolve common issues
