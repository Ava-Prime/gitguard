---
layout: default
title: Troubleshooting Guide
description: Common issues, debugging techniques, and solutions for GitGuard
---

# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with GitGuard policies, integrations, and deployments.

## Quick Diagnostics

### Health Check

First, verify that GitGuard is running correctly:

```bash
# Check GitGuard service status
curl -f http://localhost:8080/health

# Expected response:
{
  "status": "healthy",
  "version": "0.1.0",
  "components": {
    "opa": "ready",
    "temporal": "connected",
    "github": "authenticated",
    "org_brain": "synced"
  }
}
```

### Policy Validation

```bash
# Validate policy syntax
opa fmt policies/

# Test policy compilation
opa test policies/ --verbose

# Check for policy conflicts
gitguard validate-policies --config config/production.yml
```

## Common Issues

### 1. Policy Not Triggering

**Symptoms:**
- GitHub webhooks received but no policy evaluation
- Expected policy decisions not appearing
- Status checks not updating

**Diagnosis:**

```bash
# Check webhook delivery
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo/hooks/12345/deliveries

# Verify policy package structure
opa eval -d policies/ "data"

# Test policy with sample input
opa eval -d policies/ -i test-input.json "data.gitguard.policies.allow"
```

**Solutions:**

1. **Verify Webhook Configuration:**
   ```yaml
   # Ensure webhook URL is correct
   webhook_url: "https://your-domain.com/webhook"
   events:
     - pull_request
     - pull_request_review
     - push
   ```

2. **Check Policy Package Names:**
   ```rego
   # Correct package structure
   package gitguard.policies  # Not gitguard_policies or gitguard/policies
   ```

3. **Validate Input Structure:**
   ```json
   {
     "event_type": "pull_request",
     "action": "opened",
     "pull_request": {
       "number": 123,
       "title": "Fix bug"
     }
   }
   ```

### 2. Performance Issues

**Symptoms:**
- Slow policy evaluation (>5 seconds)
- Webhook timeouts
- High CPU/memory usage

**Diagnosis:**

```bash
# Profile policy performance
opa test policies/ --profile

# Monitor resource usage
docker stats gitguard

# Check evaluation metrics
curl http://localhost:8080/metrics | grep policy_evaluation
```

**Solutions:**

1. **Optimize Policy Queries:**
   ```rego
   # Inefficient - iterates all files multiple times
   has_critical_files {
     file := input.files[_]
     is_critical(file.path)
   }

   # Efficient - single iteration with comprehension
   critical_files := [f | f := input.files[_]; is_critical(f.path)]
   has_critical_files {
     count(critical_files) > 0
   }
   ```

2. **Use Data Indexing:**
   ```rego
   # Create indexed lookups
   critical_file_index := {path: true | path := data.critical_files[_]}

   is_critical(path) {
     critical_file_index[path]
   }
   ```

3. **Implement Caching:**
   ```yaml
   # config/performance.yml
   cache:
     policy_results:
       ttl: 300s
       max_size: 1000

     org_brain_data:
       ttl: 3600s
       max_size: 10000
   ```

### 3. Authentication Errors

**Symptoms:**
- "403 Forbidden" errors
- "Invalid GitHub App installation"
- "Token expired" messages

**Diagnosis:**

```bash
# Test GitHub App authentication
curl -H "Authorization: Bearer $GITHUB_APP_TOKEN" \
  https://api.github.com/app

# Check installation permissions
curl -H "Authorization: token $INSTALLATION_TOKEN" \
  https://api.github.com/installation/repositories

# Verify webhook secret
echo -n "payload" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET"
```

**Solutions:**

1. **Regenerate GitHub App Credentials:**
   ```bash
   # Update private key
   export GITHUB_APP_PRIVATE_KEY="$(cat new-private-key.pem)"

   # Verify app ID
   export GITHUB_APP_ID="123456"
   ```

2. **Check Installation Permissions:**
   - Repository permissions: Contents (read), Pull requests (write)
   - Organization permissions: Members (read)
   - Events: Pull request, Push, Pull request review

3. **Update Webhook Secret:**
   ```bash
   # Generate new secret
   openssl rand -hex 32

   # Update in GitHub and GitGuard config
   export GITHUB_WEBHOOK_SECRET="new-secret"
   ```

### 4. Org-Brain Sync Issues

**Symptoms:**
- Outdated team information
- Missing code ownership data
- Incorrect expertise mapping

**Diagnosis:**

```bash
# Check Org-Brain sync status
curl http://localhost:8080/org-brain/status

# Verify data freshness
curl http://localhost:8080/org-brain/teams | jq '.last_updated'

# Test relationship queries
curl "http://localhost:8080/org-brain/relationships?repo=myrepo"
```

**Solutions:**

1. **Force Sync:**
   ```bash
   # Trigger manual sync
   curl -X POST http://localhost:8080/org-brain/sync

   # Check sync logs
   docker logs gitguard | grep "org-brain"
   ```

2. **Update Sync Configuration:**
   ```yaml
   # config/org-brain.yml
   sync:
     interval: "1h"
     sources:
       - github_teams
       - github_collaborators
       - codeowners_files

     github:
       rate_limit_buffer: 100
       batch_size: 50
   ```

3. **Verify Data Sources:**
   ```bash
   # Check CODEOWNERS file
   cat .github/CODEOWNERS

   # Verify team memberships
   gh api orgs/myorg/teams
   ```

### 5. Temporal Workflow Failures

**Symptoms:**
- Workflows stuck in "Running" state
- "Workflow not found" errors
- Timeout exceptions

**Diagnosis:**

```bash
# Check Temporal server connection
tctl cluster health

# List running workflows
tctl workflow list --query "WorkflowType='GitGuardPolicyWorkflow'"

# Get workflow details
tctl workflow show -w $WORKFLOW_ID
```

**Solutions:**

1. **Restart Stuck Workflows:**
   ```bash
   # Terminate stuck workflow
   tctl workflow terminate -w $WORKFLOW_ID -r "Manual restart"

   # Start new workflow
   tctl workflow start --type GitGuardPolicyWorkflow --input '{"pr_number": 123}'
   ```

2. **Update Workflow Configuration:**
   ```yaml
   # config/temporal.yml
   workflows:
     policy_evaluation:
       timeout: "10m"
       retry_policy:
         max_attempts: 3
         backoff_coefficient: 2.0
   ```

3. **Check Worker Health:**
   ```bash
   # Verify workers are running
   docker ps | grep temporal-worker

   # Check worker logs
   docker logs temporal-worker
   ```

## Debugging Techniques

### 1. Enable Debug Logging

```yaml
# config/logging.yml
logging:
  level: debug
  components:
    policy_engine: debug
    webhook_handler: debug
    org_brain: info
    temporal: debug

  output:
    console: true
    file: "/var/log/gitguard/debug.log"
```

### 2. Policy Debug Mode

```rego
package gitguard.policies

# Add debug information to policy decisions
allow {
    # Your policy logic here
    input.debug == true
    trace(sprintf("Policy evaluation for PR %d", [input.pull_request.number]))
}

# Include debug data in response
debug_info := {
    "risk_score": risk_score,
    "required_approvals": required_approvals,
    "current_approvals": count(input.approvals),
    "evaluation_time": time.now_ns()
}
```

### 3. Test with Sample Data

```bash
# Create test input file
cat > test-input.json << EOF
{
  "event_type": "pull_request",
  "action": "opened",
  "pull_request": {
    "number": 123,
    "title": "Test PR",
    "user": {"login": "testuser"}
  },
  "files": [
    {"filename": "src/main.py", "changes": 10}
  ],
  "approvals": []
}
EOF

# Test policy evaluation
opa eval -d policies/ -i test-input.json "data.gitguard.policies"
```

### 4. Monitor Policy Metrics

```bash
# Policy evaluation metrics
curl http://localhost:8080/metrics | grep -E "(policy_evaluation|webhook_processing)"

# Example metrics:
# policy_evaluation_duration_seconds{policy="release_window"} 0.045
# policy_evaluation_total{policy="risk_assessment",result="allow"} 142
# webhook_processing_errors_total{source="github"} 3
```

## Error Reference

### Policy Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `rego_parse_error` | Invalid Rego syntax | Run `opa fmt` and fix syntax |
| `undefined_function` | Unknown function call | Check OPA built-in functions |
| `type_error` | Type mismatch | Verify data types in policy |
| `recursion_limit` | Infinite recursion | Review recursive rules |

### Integration Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `webhook_signature_invalid` | Wrong webhook secret | Update `GITHUB_WEBHOOK_SECRET` |
| `github_api_rate_limit` | Too many API calls | Implement rate limiting |
| `temporal_connection_failed` | Temporal server down | Check Temporal server status |
| `org_brain_sync_timeout` | Large organization data | Increase sync timeout |

### Configuration Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `config_file_not_found` | Missing config file | Create config file |
| `invalid_yaml_syntax` | Malformed YAML | Validate YAML syntax |
| `missing_required_field` | Required config missing | Add required configuration |
| `environment_variable_unset` | Missing env var | Set environment variable |

## Performance Optimization

### 1. Policy Optimization

```rego
# Before: Inefficient nested loops
has_security_approval {
    file := input.files[_]
    contains(file.path, "security")
    approval := input.approvals[_]
    approval.user.login in data.security_team
}

# After: Optimized with early exit
has_security_approval {
    security_files := [f | f := input.files[_]; contains(f.path, "security")]
    count(security_files) > 0
    security_approvers := {a.user.login | a := input.approvals[_]; a.user.login in data.security_team}
    count(security_approvers) > 0
}
```

### 2. Caching Strategy

```yaml
# config/cache.yml
cache:
  layers:
    - name: "policy_results"
      ttl: "5m"
      key_pattern: "policy:{repo}:{pr}:{sha}"

    - name: "org_brain_data"
      ttl: "1h"
      key_pattern: "orgbrain:{org}:{type}"

    - name: "github_api"
      ttl: "10m"
      key_pattern: "github:{endpoint}:{params_hash}"
```

### 3. Resource Limits

```yaml
# docker-compose.yml
services:
  gitguard:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Getting Help

### 1. Community Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/your-org/gitguard/issues)
- **Discord**: [Join our community chat](https://discord.gg/gitguard)
- **Documentation**: [Browse comprehensive guides](https://gitguard.dev/docs)

### 2. Professional Support

- **Enterprise Support**: Contact support@gitguard.dev
- **Consulting Services**: Available for custom implementations
- **Training**: Policy development workshops

### 3. Diagnostic Information

When reporting issues, include:

```bash
# System information
gitguard version
docker version
kubectl version  # if using Kubernetes

# Configuration (sanitized)
gitguard config show --sanitize

# Recent logs
gitguard logs --since 1h --level error

# Policy validation
opa test policies/ --verbose
```

---

*Still having issues? [Open a support ticket](https://github.com/your-org/gitguard/issues/new?template=bug_report.md) with the diagnostic information above.*
