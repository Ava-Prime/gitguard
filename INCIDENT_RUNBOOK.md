# GitGuard Incident Response Runbook

This runbook provides step-by-step procedures for responding to GitGuard incidents, from detection through resolution and post-incident review.

## 🚨 Incident Classification

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| **P0 - Critical** | Complete service outage | 15 minutes | GitGuard completely down, all PRs blocked |
| **P1 - High** | Major functionality impacted | 1 hour | Policy evaluation failures, webhook timeouts |
| **P2 - Medium** | Partial functionality affected | 4 hours | Slow response times, intermittent errors |
| **P3 - Low** | Minor issues, workarounds available | 24 hours | UI glitches, non-critical feature bugs |

### Incident Types

- **🔥 Service Outage**: GitGuard is completely unavailable
- **⚡ Performance Degradation**: Slow response times or timeouts
- **🔒 Security Incident**: Potential security breach or vulnerability
- **📊 Data Issues**: Policy evaluation errors or incorrect results
- **🔗 Integration Failure**: GitHub webhook or API issues
- **🐛 Application Error**: Bugs causing functional problems

## 🎯 Immediate Response (First 15 Minutes)

### 1. Incident Detection

**Automated Alerts:**
```bash
# Check health endpoints
curl -f http://localhost:8080/health || echo "GitGuard health check failed"
curl -f http://localhost:7233/api/v1/namespaces || echo "Temporal health check failed"

# Check service status
docker-compose ps
make status
```

**Manual Detection:**
- User reports via GitHub issues
- Failed PR checks
- Webhook delivery failures in GitHub
- Monitoring alerts

### 2. Initial Assessment

**Gather Basic Information:**
```bash
# Service status
docker-compose ps
docker stats --no-stream

# Recent logs (last 50 lines)
docker-compose logs --tail=50 gitguard
docker-compose logs --tail=50 temporal

# System resources
df -h
free -h
```

**Quick Triage Questions:**
- Is GitGuard responding to health checks?
- Are webhooks being received?
- Are policies evaluating correctly?
- When did the issue start?
- What changed recently?

### 3. Immediate Mitigation

**For Service Outages:**
```bash
# Restart services
docker-compose restart gitguard

# Full stack restart if needed
docker-compose down
docker-compose up -d

# Check if services recover
make status
```

**For Performance Issues:**
```bash
# Check resource usage
docker stats

# Scale if using Docker Swarm/Kubernetes
# docker service scale gitguard=3

# Clear any stuck workflows
# (Temporal UI: http://localhost:8088)
```

## 🔍 Detailed Investigation

### Log Analysis

**GitGuard Application Logs:**
```bash
# Error patterns
docker-compose logs gitguard | grep -i "error\|exception\|panic"

# Webhook processing
docker-compose logs gitguard | grep "webhook"

# Policy evaluation
docker-compose logs gitguard | grep "policy"

# Performance metrics
docker-compose logs gitguard | grep "duration\|latency"
```

**Temporal Workflow Logs:**
```bash
# Workflow failures
docker-compose logs temporal | grep -i "failed\|error"

# Activity timeouts
docker-compose logs temporal | grep "timeout"

# Task queue issues
docker-compose logs temporal | grep "task_queue"
```

**System-Level Diagnostics:**
```bash
# Disk space
df -h
du -sh /var/lib/docker

# Memory usage
free -h
ps aux --sort=-%mem | head -10

# Network connectivity
ping github.com
curl -I https://api.github.com

# DNS resolution
nslookup github.com
```

### Configuration Validation

```bash
# Environment variables
env | grep -E '^(GITHUB_|GITGUARD_)' | wc -l

# Docker Compose configuration
docker-compose config --quiet || echo "Configuration error"

# Policy syntax validation
make dryrun

# GitHub App connectivity
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     https://api.github.com/app
```

### Database/Storage Issues

```bash
# Temporal database connectivity
docker-compose exec temporal temporal --address temporal:7233 \
  namespace list

# PostgreSQL health (if using)
docker-compose exec postgres pg_isready

# Storage volumes
docker volume ls
docker system df
```

## 🛠️ Common Incident Scenarios

### Scenario 1: Complete Service Outage

**Symptoms:**
- GitGuard health check fails
- No webhook processing
- All PR checks fail

**Investigation Steps:**
```bash
# 1. Check container status
docker-compose ps

# 2. Review startup logs
docker-compose logs gitguard | tail -100

# 3. Check dependencies
docker-compose logs temporal
docker-compose logs postgres

# 4. Verify configuration
docker-compose config
```

**Resolution:**
```bash
# 1. Restart services
docker-compose restart

# 2. If restart fails, rebuild
docker-compose down
docker-compose pull
docker-compose up -d

# 3. Verify recovery
make status
curl http://localhost:8080/health
```

### Scenario 2: Webhook Processing Failures

**Symptoms:**
- GitHub shows webhook delivery failures
- PRs not being processed
- Webhook endpoint timeouts

**Investigation:**
```bash
# 1. Check webhook logs
docker-compose logs gitguard | grep "webhook"

# 2. Test webhook endpoint
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -d '{"zen": "test"}'

# 3. Verify GitHub connectivity
curl -I https://api.github.com

# 4. Check webhook secret
echo $GITHUB_WEBHOOK_SECRET | wc -c
```

**Resolution:**
```bash
# 1. Restart GitGuard
docker-compose restart gitguard

# 2. Update webhook URL in GitHub App
# (if using ngrok/cloudflared)

# 3. Redeliver failed webhooks from GitHub
# (GitHub App settings > Advanced > Recent Deliveries)
```

### Scenario 3: Policy Evaluation Errors

**Symptoms:**
- PR checks fail with policy errors
- Inconsistent policy results
- Policy timeout errors

**Investigation:**
```bash
# 1. Test policy syntax
make dryrun

# 2. Check policy logs
docker-compose logs gitguard | grep "policy"

# 3. Test policy evaluation
curl -X POST http://localhost:8080/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{"policy": "package main\nallow = true", "input": {}}'

# 4. Check Temporal workflows
# Visit http://localhost:8088
```

**Resolution:**
```bash
# 1. Fix policy syntax errors
# Edit policies in policies/ directory

# 2. Restart to reload policies
docker-compose restart gitguard

# 3. Retry failed evaluations
# Re-run PR checks or trigger webhook
```

### Scenario 4: Performance Degradation

**Symptoms:**
- Slow webhook processing
- Policy evaluation timeouts
- High resource usage

**Investigation:**
```bash
# 1. Check resource usage
docker stats --no-stream
top -p $(pgrep -f gitguard)

# 2. Analyze slow queries/operations
docker-compose logs gitguard | grep "duration"

# 3. Check for resource limits
docker-compose config | grep -A5 -B5 "limits"

# 4. Monitor over time
watch -n 5 'docker stats --no-stream'
```

**Resolution:**
```bash
# 1. Increase resource limits
# Edit docker-compose.yml

# 2. Optimize policies
# Review and simplify complex policies

# 3. Scale horizontally (if supported)
# docker-compose up --scale gitguard=2

# 4. Clear old data
docker system prune -f
```

## 📋 Incident Communication

### Internal Communication

**Incident Declaration:**
```markdown
🚨 **INCIDENT DECLARED** - P[0-3]

**Summary:** Brief description of the issue
**Impact:** Who/what is affected
**Started:** Timestamp
**Responder:** @username
**Status:** Investigating/Mitigating/Resolved

**Next Update:** In 30 minutes
```

**Status Updates:**
```markdown
📊 **INCIDENT UPDATE** - P[0-3] - [Timestamp]

**Current Status:** What's happening now
**Actions Taken:** What we've done
**Next Steps:** What we're doing next
**ETA:** Expected resolution time
```

### External Communication

**For P0/P1 Incidents:**
- Update GitHub repository status
- Post in relevant Slack/Discord channels
- Consider status page updates

**Template:**
```markdown
⚠️ **Service Alert**

We're currently experiencing issues with GitGuard that may affect PR processing.

**Impact:** [Description]
**Status:** Investigating
**Updates:** We'll provide updates every 30 minutes

For urgent issues, please contact: [emergency contact]
```

## 🔄 Recovery Procedures

### Service Recovery Verification

```bash
# 1. Health checks
curl -f http://localhost:8080/health
curl -f http://localhost:7233/api/v1/namespaces

# 2. End-to-end test
make smoketest

# 3. Create test PR
# Use synthetic dogfood workflow
gh workflow run synthetic-dogfood.yml

# 4. Monitor for 15 minutes
watch -n 30 'make status'
```

### Data Integrity Checks

```bash
# 1. Check recent policy evaluations
docker-compose logs gitguard | grep "evaluation" | tail -10

# 2. Verify webhook processing
docker-compose logs gitguard | grep "webhook" | tail -10

# 3. Check Temporal workflow state
# Visit http://localhost:8088 and review recent workflows

# 4. Test policy evaluation
curl -X POST http://localhost:8080/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{"policy": "package main\nallow = true", "input": {}}'
```

## 📊 Post-Incident Review

### Incident Timeline

```markdown
## Incident Timeline

- **[Time]** - Incident detected
- **[Time]** - Initial response started
- **[Time]** - Root cause identified
- **[Time]** - Mitigation applied
- **[Time]** - Service restored
- **[Time]** - Incident closed

**Total Duration:** X hours Y minutes
**MTTR:** X minutes
```

### Root Cause Analysis

1. **What happened?** Detailed description
2. **Why did it happen?** Root cause analysis
3. **How was it detected?** Detection method
4. **How was it resolved?** Resolution steps
5. **What was the impact?** User/business impact

### Action Items

```markdown
## Action Items

- [ ] **Prevention:** [Action to prevent recurrence] - @owner - [due date]
- [ ] **Detection:** [Improve monitoring/alerting] - @owner - [due date]
- [ ] **Response:** [Improve response procedures] - @owner - [due date]
- [ ] **Documentation:** [Update runbooks/docs] - @owner - [due date]
```

### Metrics to Track

- **MTTR (Mean Time To Recovery):** Time from detection to resolution
- **MTTD (Mean Time To Detection):** Time from incident start to detection
- **Incident Frequency:** Number of incidents per month
- **Severity Distribution:** P0/P1/P2/P3 incident counts

## 🛡️ Prevention Strategies

### Monitoring & Alerting

```bash
# Health check monitoring
*/5 * * * * curl -f http://localhost:8080/health || alert

# Resource monitoring
*/1 * * * * docker stats --no-stream | awk 'NR>1{if($3>80) print "High CPU: "$1" "$3}'

# Log monitoring
*/1 * * * * docker-compose logs --since=1m gitguard | grep -i error && alert
```

### Automated Recovery

```bash
# Auto-restart on failure
# Add to docker-compose.yml:
# restart: unless-stopped

# Health check with auto-restart
# healthcheck:
#   test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
#   interval: 30s
#   timeout: 10s
#   retries: 3
#   start_period: 40s
```

### Capacity Planning

- Monitor resource trends
- Plan for peak usage periods
- Set up horizontal scaling
- Regular performance testing

## 📞 Emergency Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| Primary On-Call | @primary | Immediate |
| Secondary On-Call | @secondary | +15 minutes |
| Engineering Manager | @manager | +30 minutes |
| Security Team | security@gitguard.dev | For security incidents |

---

**Remember:** Stay calm, follow the procedures, communicate clearly, and learn from every incident to improve our resilience.

**Emergency Hotline:** For P0 incidents, call [emergency number] or page @oncall
