---
layout: page
title: API Reference
description: Complete API documentation for GitGuard - REST endpoints, webhooks, and integration guides
permalink: /api/
---

# API Reference

GitGuard provides a comprehensive REST API for policy evaluation, configuration management, and system integration. All endpoints return JSON and follow RESTful conventions.

## Base URL

```
https://api.gitguard.dev/v1
# or for self-hosted:
http://localhost:8000/api/v1
```

## Authentication

GitGuard supports multiple authentication methods:

### API Keys
```bash
curl -H "Authorization: Bearer your-api-key" \
     https://api.gitguard.dev/v1/policies
```

### GitHub App Token
```bash
curl -H "Authorization: token github-app-token" \
     https://api.gitguard.dev/v1/evaluate
```

### Webhook Signatures
```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Core Endpoints

### Policy Evaluation

#### `POST /evaluate`

Evaluate policies against input data (typically a GitHub webhook payload).

**Request:**
```json
{
  "input": {
    "pull_request": {
      "number": 123,
      "title": "Add new authentication feature",
      "base": {"ref": "main"},
      "head": {"ref": "feature/auth"},
      "additions": 150,
      "deletions": 25,
      "changed_files": [
        {"filename": "src/auth.py", "status": "added"},
        {"filename": "tests/test_auth.py", "status": "added"}
      ],
      "requested_reviewers": [
        {"login": "reviewer1"}
      ]
    },
    "repository": {
      "name": "my-app",
      "full_name": "org/my-app"
    }
  },
  "policies": ["require_tests", "require_review"],
  "context": {
    "environment": "production",
    "risk_tolerance": "low"
  }
}
```

**Response:**
```json
{
  "decision": {
    "allowed": true,
    "auto_merge": false,
    "risk_score": 25,
    "confidence": 0.95
  },
  "policy_results": [
    {
      "policy": "require_tests",
      "result": true,
      "reason": "Test files found for new features",
      "evidence": ["tests/test_auth.py"]
    },
    {
      "policy": "require_review",
      "result": true,
      "reason": "Reviewer assigned",
      "evidence": ["reviewer1"]
    }
  ],
  "recommendations": [
    "Consider adding integration tests",
    "Verify security review for authentication changes"
  ],
  "metadata": {
    "evaluation_time_ms": 45,
    "policy_version": "1.2.0",
    "timestamp": "2024-01-20T14:30:00Z"
  }
}
```

#### `POST /evaluate/batch`

Evaluate multiple inputs in a single request.

**Request:**
```json
{
  "evaluations": [
    {
      "id": "pr-123",
      "input": {/* PR data */},
      "policies": ["require_tests"]
    },
    {
      "id": "pr-124",
      "input": {/* PR data */},
      "policies": ["require_review"]
    }
  ]
}
```

### Policy Management

#### `GET /policies`

List all available policies.

**Response:**
```json
{
  "policies": [
    {
      "name": "require_tests",
      "description": "Require test files for new features",
      "version": "1.0.0",
      "category": "quality",
      "severity": "error",
      "enabled": true,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-20T14:00:00Z"
    }
  ],
  "total": 15,
  "categories": ["security", "quality", "compliance"]
}
```

#### `GET /policies/{name}`

Get detailed information about a specific policy.

**Response:**
```json
{
  "name": "require_tests",
  "description": "Require test files for new features",
  "version": "1.0.0",
  "category": "quality",
  "severity": "error",
  "enabled": true,
  "rego_code": "package gitguard.policies.tests\n\nrequire_tests {...}",
  "test_cases": [
    {
      "name": "feature_with_tests",
      "input": {/* test input */},
      "expected": true
    }
  ],
  "documentation": {
    "rationale": "Ensures code quality by requiring tests",
    "examples": [/* usage examples */]
  }
}
```

#### `POST /policies`

Create or update a policy.

**Request:**
```json
{
  "name": "custom_policy",
  "description": "Custom organization policy",
  "category": "compliance",
  "severity": "warning",
  "rego_code": "package gitguard.policies.custom\n\n# Policy logic here",
  "test_cases": [
    {
      "name": "test_case_1",
      "input": {/* test data */},
      "expected": true
    }
  ]
}
```

#### `DELETE /policies/{name}`

Delete a policy.

### Configuration

#### `GET /config`

Get current system configuration.

**Response:**
```json
{
  "version": "0.1.0",
  "environment": "production",
  "features": {
    "auto_merge": true,
    "risk_scoring": true,
    "org_brain": true
  },
  "limits": {
    "max_policies_per_evaluation": 50,
    "max_file_size_mb": 10,
    "rate_limit_per_minute": 1000
  },
  "integrations": {
    "github": {
      "app_id": "123456",
      "webhook_url": "https://api.gitguard.dev/webhooks/github"
    }
  }
}
```

#### `PUT /config`

Update system configuration.

### Analytics & Reporting

#### `GET /analytics/decisions`

Get policy decision analytics.

**Query Parameters:**
- `start_date`: ISO 8601 date
- `end_date`: ISO 8601 date
- `repository`: Filter by repository
- `policy`: Filter by policy name

**Response:**
```json
{
  "summary": {
    "total_evaluations": 1250,
    "allowed": 1100,
    "blocked": 150,
    "auto_merged": 450,
    "average_risk_score": 32.5
  },
  "trends": {
    "daily_evaluations": [
      {"date": "2024-01-20", "count": 85},
      {"date": "2024-01-19", "count": 92}
    ]
  },
  "top_policies": [
    {"name": "require_tests", "triggered": 245},
    {"name": "require_review", "triggered": 189}
  ]
}
```

#### `GET /analytics/repositories`

Get repository-level analytics.

#### `GET /analytics/policies/{name}/performance`

Get performance metrics for a specific policy.

### Org-Brain Intelligence

#### `GET /graph/relationships`

Get relationship graph data.

**Response:**
```json
{
  "nodes": [
    {
      "id": "file:src/auth.py",
      "type": "file",
      "properties": {
        "path": "src/auth.py",
        "language": "python",
        "size": 1250
      }
    },
    {
      "id": "user:jane.smith",
      "type": "contributor",
      "properties": {
        "login": "jane.smith",
        "expertise": ["authentication", "security"]
      }
    }
  ],
  "edges": [
    {
      "source": "user:jane.smith",
      "target": "file:src/auth.py",
      "type": "owns",
      "weight": 0.85,
      "properties": {
        "commits": 15,
        "last_modified": "2024-01-18T10:30:00Z"
      }
    }
  ]
}
```

#### `GET /graph/owners/{path}`

Get ownership information for a file or directory.

#### `POST /graph/query`

Execute a graph query using Cypher-like syntax.

## Webhooks

### GitHub Webhook Handler

#### `POST /webhooks/github`

Handles GitHub webhook events automatically.

**Supported Events:**
- `pull_request` (opened, synchronize, reopened, closed)
- `pull_request_review` (submitted, dismissed)
- `push` (to protected branches)
- `check_run` (completed)
- `status` (updated)

**Automatic Actions:**
- Policy evaluation on PR events
- Status check updates
- Auto-merge for approved PRs
- Risk score calculation
- Comment generation with results

### Custom Webhook Registration

#### `POST /webhooks`

Register a custom webhook endpoint.

**Request:**
```json
{
  "url": "https://your-app.com/gitguard-webhook",
  "events": ["policy.evaluated", "decision.made"],
  "secret": "your-webhook-secret",
  "active": true
}
```

## SDKs & Libraries

### Python SDK

```python
from gitguard import GitGuardClient

client = GitGuardClient(
    api_url="https://api.gitguard.dev",
    api_key="your-api-key"
)

# Evaluate policies
result = client.evaluate({
    "pull_request": pr_data,
    "repository": repo_data
})

if result.decision.allowed:
    print(f"PR approved with risk score: {result.decision.risk_score}")
else:
    print(f"PR blocked: {result.decision.reason}")

# Manage policies
policies = client.policies.list()
new_policy = client.policies.create(
    name="custom_check",
    rego_code="package custom\n\nallow { true }"
)
```

### JavaScript SDK

```javascript
import { GitGuardClient } from '@gitguard/sdk';

const client = new GitGuardClient({
  apiUrl: 'https://api.gitguard.dev',
  apiKey: 'your-api-key'
});

// Evaluate policies
const result = await client.evaluate({
  pull_request: prData,
  repository: repoData
});

console.log('Decision:', result.decision);
console.log('Policy Results:', result.policy_results);

// Stream real-time events
client.events.on('policy.evaluated', (event) => {
  console.log('Policy evaluated:', event.data);
});
```

### Go SDK

```go
package main

import (
    "github.com/gitguard/go-sdk"
)

func main() {
    client := gitguard.NewClient("https://api.gitguard.dev", "your-api-key")

    result, err := client.Evaluate(gitguard.EvaluationRequest{
        Input: map[string]interface{}{
            "pull_request": prData,
        },
        Policies: []string{"require_tests"},
    })

    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Decision: %+v\n", result.Decision)
}
```

## Rate Limits

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| Policy Evaluation | 1000 requests | 1 minute |
| Policy Management | 100 requests | 1 minute |
| Analytics | 500 requests | 1 minute |
| Webhooks | 10,000 requests | 1 minute |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642694400
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "POLICY_EVALUATION_FAILED",
    "message": "Policy evaluation failed due to invalid input",
    "details": {
      "policy": "require_tests",
      "line": 15,
      "column": 8
    },
    "request_id": "req_1234567890",
    "timestamp": "2024-01-20T14:30:00Z"
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request body |
| `UNAUTHORIZED` | 401 | Invalid or missing authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `POLICY_ERROR` | 422 | Policy compilation or execution error |
| `INTERNAL_ERROR` | 500 | Internal server error |

## Testing

### Policy Testing Endpoint

#### `POST /policies/test`

Test a policy without saving it.

```json
{
  "rego_code": "package test\n\nallow { input.test == true }",
  "test_cases": [
    {
      "input": {"test": true},
      "expected": true
    },
    {
      "input": {"test": false},
      "expected": false
    }
  ]
}
```

### Mock Data Generator

#### `GET /testing/mock-data/{type}`

Generate mock data for testing.

**Types:** `pull_request`, `push`, `review`, `check_run`

---

## Interactive API Explorer

<div class="api-explorer">
  <h3>🚀 Try the API</h3>
  <p>Explore our interactive API documentation:</p>
  <a href="https://api.gitguard.dev/docs" class="btn btn-primary">Open API Explorer</a>
  <a href="https://api.gitguard.dev/redoc" class="btn btn-secondary">View ReDoc</a>
</div>

---

*Need help? Check our [examples](/examples) or join the [community discussion](https://github.com/your-org/gitguard/discussions).*
