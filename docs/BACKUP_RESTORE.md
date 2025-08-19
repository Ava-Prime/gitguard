# GitGuard Org-Brain Backup & Restore

> **"Backups you can restore blindfolded"** - A comprehensive guide to GitGuard's org-brain backup and disaster recovery system.

## Overview

GitGuard implements a robust backup and restore system designed for production reliability. The system ensures you can rebuild the entire org-brain portal, including policy transparency, Mermaid graphs, owners index, and Graph API data, from database dumps and stream snapshots without GitHub connectivity.

### Key Features

- **🗄️ PostgreSQL Daily Backups** - Automated daily dumps with 7-day retention
- **🌊 JetStream Pre-deployment Snapshots** - Event stream backups before deployments
- **🎭 Weekly Restore Rehearsals** - Automated validation in staging environment
- **📊 Backup Monitoring** - Status tracking and alerting
- **🧹 Automated Cleanup** - Retention policy enforcement
- **🧠 Org-Brain Data** - Policy transparency, Mermaid graphs, and owners index
- **🔗 Graph API State** - Relationship data and API endpoint configurations
- **🔥 Chaos Engineering** - Drill results and resilience metrics

## Quick Start

```bash
# Create complete backup set
make backup-all

# Check backup status
make backup-status

# Run restore rehearsal (staging only)
ENVIRONMENT=staging STAGING_DATABASE_URL="postgresql://..." make restore-rehearsal
```

## Backup Components

### 1. PostgreSQL Backups

**Schedule:** Daily
**Retention:** 7 days
**Format:** Custom format (`.dump`)
**Location:** `/backups/pg_codex_YYYY-MM-DD.dump`

```bash
# Manual backup
make backup-postgres

# Direct script usage
DATABASE_URL="postgresql://..." ./scripts/backup_postgres.sh
```

**Features:**
- Compressed custom format for faster restore
- Atomic backup creation
- Size and integrity validation
- Automatic cleanup of old backups
- Detailed logging and error handling
- Policy transparency data preservation
- Mermaid graph metadata backup
- Owners index relationship data
- Graph API configuration state

### 2. JetStream Snapshots

**Schedule:** Pre-deployment
**Retention:** 14 days
**Format:** Directory snapshot
**Location:** `/backups/js_gh_YYYY-MM-DD/`

```bash
# Manual snapshot
make backup-jetstream

# Direct script usage
./scripts/backup_jetstream.sh GH
```

**Features:**
- Complete stream state capture
- Message count and size validation
- Snapshot integrity verification
- Support for multiple streams
- Restore command hints

### 3. Restore Rehearsal

**Schedule:** Weekly (staging)
**Purpose:** Validate backup viability
**Environment:** Staging only

```bash
# Weekly rehearsal
ENVIRONMENT=staging STAGING_DATABASE_URL="postgresql://..." make restore-rehearsal

# Test specific backup date
./scripts/restore_rehearsal.sh 2024-01-15
```

**Validation Steps:**
1. ✅ Pre-flight environment checks
2. ✅ Database restore from backup
3. ✅ JetStream snapshot restore
4. ✅ Org-brain portal functionality without GitHub
5. ✅ Policy transparency rendering
6. ✅ Mermaid graph generation
7. ✅ Owners index accuracy
8. ✅ Graph API endpoint availability
9. ✅ Service connectivity tests
10. ✅ Cleanup and reporting

## Environment Setup

### Required Environment Variables

```bash
# Production backups
export DATABASE_URL="postgresql://user:pass@host:5432/gitguard"

# Staging rehearsals
export ENVIRONMENT="staging"
export STAGING_DATABASE_URL="postgresql://user:pass@staging:5432/gitguard_staging"

# Optional: Custom backup directory
export BACKUP_DIR="/custom/backup/path"
```

### Directory Structure

```
/backups/
├── pg_codex_2024-01-15.dump          # PostgreSQL backups
├── pg_codex_2024-01-16.dump
├── js_gh_2024-01-15/                  # JetStream snapshots
│   ├── stream.json
│   └── msgs/
├── js_gh_2024-01-16/
├── backup.log                         # PostgreSQL backup log
├── jetstream_backup.log               # JetStream backup log
└── restore_rehearsal_*.report         # Rehearsal reports
```

### Permissions

```bash
# Create backup directory with proper permissions
sudo mkdir -p /backups
sudo chown -R gitguard:gitguard /backups
sudo chmod 750 /backups

# Make scripts executable
chmod +x scripts/backup_*.sh scripts/restore_rehearsal.sh
```

## Operational Procedures

### Daily Operations

```bash
# 1. Create daily backups (automated via cron)
0 2 * * * cd /opt/gitguard && make backup-postgres
0 3 * * * cd /opt/gitguard && make backup-jetstream

# 2. Check backup status
make backup-status

# 3. Monitor backup logs
tail -f /backups/backup.log
```

### Pre-deployment Checklist

```bash
# 1. Create pre-deployment snapshot
make backup-jetstream

# 2. Verify backup integrity
make backup-status

# 3. Test restore capability (staging)
ENVIRONMENT=staging make restore-rehearsal

# 4. Proceed with deployment
```

### Weekly Maintenance

```bash
# 1. Run restore rehearsal (automated)
0 4 * * 1 cd /opt/gitguard && ENVIRONMENT=staging make restore-rehearsal

# 2. Review rehearsal reports
ls -la /backups/restore_rehearsal_*.report

# 3. Clean up old backups (automated)
make backup-cleanup
```

## Disaster Recovery

### Complete System Restore

1. **Prepare Environment**
   ```bash
   # Set up fresh GitGuard installation
   git clone https://github.com/your-org/gitguard.git
   cd gitguard
   make setup
   ```

2. **Restore Database**
   ```bash
   # Create database
   createdb gitguard_restored

   # Restore from backup
   pg_restore -d "postgresql://user:pass@host:5432/gitguard_restored" \
     /backups/pg_codex_YYYY-MM-DD.dump
   ```

3. **Restore JetStream**
   ```bash
   # Start NATS server
   make up

   # Restore stream
   nats stream restore GH /backups/js_gh_YYYY-MM-DD
   ```

4. **Validate System**
   ```bash
   # Update environment variables
   export DATABASE_URL="postgresql://user:pass@host:5432/gitguard_restored"

   # Start services
   make up

   # Verify org-brain functionality
   make health

   # Test Graph API endpoints
   curl -f http://localhost:8002/graph/health

   # Verify policy transparency
   curl -f http://localhost:8000/prs/1.html | grep -q "source-ref"

   # Test Mermaid graph generation
   curl -f http://localhost:8000/prs/1.html | grep -q "mermaid"

   # Validate owners index
   curl -f http://localhost:8000/owners.html
   ```

### Partial Recovery Scenarios

#### Database Only
```bash
# Restore database to specific point in time
pg_restore -d "$DATABASE_URL" /backups/pg_codex_2024-01-15.dump

# Verify schema
make codex.schema
```

#### JetStream Only
```bash
# Restore specific stream
nats stream restore GH_BACKUP /backups/js_gh_2024-01-15

# Verify stream
nats stream info GH_BACKUP
```

## Monitoring & Alerting

### Backup Health Checks

```bash
# Check recent backups
find /backups -name "pg_codex_*.dump" -mtime -1 | wc -l  # Should be >= 1
find /backups -name "js_gh_*" -type d -mtime -1 | wc -l   # Should be >= 1

# Check backup sizes (detect corruption)
ls -lh /backups/pg_codex_*.dump | awk '$5 < "1M" {print "WARNING: Small backup " $9}'

# Validate org-brain data integrity
pg_dump -t policy_transparency -t mermaid_graphs -t owners_index --data-only "$DATABASE_URL" | wc -l

# Check Graph API configuration backup
grep -q "GRAPH_API_ENABLED" /backups/config_backup_*.env || echo "WARNING: Graph API config missing"
```

### Prometheus Metrics

```yaml
# Add to prometheus.yml
- name: backup_health
  rules:
    - alert: BackupMissing
      expr: time() - backup_last_success_timestamp > 86400
      labels:
        severity: critical
      annotations:
        summary: "GitGuard backup missing for > 24h"

    - alert: RestoreRehearsalFailed
      expr: restore_rehearsal_success != 1
      labels:
        severity: warning
      annotations:
        summary: "Weekly restore rehearsal failed"
```

## Troubleshooting

### Common Issues

#### "DATABASE_URL not set"
```bash
# Solution: Set environment variable
export DATABASE_URL="postgresql://user:pass@host:5432/gitguard"

# Or use .env file
echo "DATABASE_URL=postgresql://..." >> .env
```

#### "pg_dump: command not found"
```bash
# Install PostgreSQL client tools
# Ubuntu/Debian
sudo apt-get install postgresql-client

# RHEL/CentOS
sudo yum install postgresql

# macOS
brew install postgresql
```

#### "nats: command not found"
```bash
# Install NATS CLI
# Using Go
go install github.com/nats-io/natscli/nats@latest

# Using curl
curl -sf https://binaries.nats.dev/nats-io/natscli/nats@latest | sh
```

#### "Permission denied: /backups"
```bash
# Fix permissions
sudo mkdir -p /backups
sudo chown -R $(whoami):$(whoami) /backups
sudo chmod 755 /backups
```

#### "Backup file too small"
```bash
# Check database connectivity
psql "$DATABASE_URL" -c "SELECT version();"

# Check org-brain table sizes
psql "$DATABASE_URL" -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE tablename IN ('policy_transparency','mermaid_graphs','owners_index');"

# Verify org-brain data in backup
pg_restore --list /backups/pg_codex_latest.dump | grep -E "(policy_transparency|mermaid_graphs|owners_index)"

# Check disk space
df -h /backups

# Review backup logs
tail -n 50 /backups/backup.log
```

#### "Restore rehearsal timeout"
```bash
# Increase timeout in script
export TEST_TIMEOUT=600  # 10 minutes

# Check staging resources
docker stats

# Review rehearsal logs
tail -f /backups/restore_rehearsal.log
```

#### "Portal Page Not Found"
```bash
# Check database connection
psql "$DATABASE_URL" -c "\dt"

# Verify required tables exist
psql "$DATABASE_URL" -c "SELECT count(*) FROM prs;"
psql "$DATABASE_URL" -c "SELECT count(*) FROM policy_transparency;"
psql "$DATABASE_URL" -c "SELECT count(*) FROM owners_index;"

# Check Graph API health
curl -f http://localhost:8002/graph/health

# Verify org-brain features
curl -s http://localhost:8000/prs/1.html | grep -q "source-ref" || echo "Policy transparency missing"
curl -s http://localhost:8000/prs/1.html | grep -q "mermaid" || echo "Mermaid graphs missing"

# Restart services in correct order
make down && make up
```

### Log Analysis

```bash
# Recent backup activity
grep "$(date +%Y-%m-%d)" /backups/backup.log

# Error patterns
grep -i "error\|failed\|timeout" /backups/*.log

# Backup sizes over time
ls -lt /backups/pg_codex_*.dump | head -10
```

### Recovery Validation

```bash
# Test database restore
pg_restore --list /backups/pg_codex_latest.dump | head -20

# Test JetStream snapshot
nats stream info GH_TEST --json | jq '.state.messages'

# Test org-brain portal connectivity
curl -f http://localhost:8000/health || echo "Portal not responding"

# Validate Graph API
curl -f http://localhost:8002/graph/health || echo "Graph API not responding"
curl -f http://localhost:8002/graph/owners | jq '.owners | length'

# Test policy transparency
curl -s http://localhost:8000/prs/1.html | grep -c "source-ref" || echo "Policy transparency missing"

# Test Mermaid graphs
curl -s http://localhost:8000/prs/1.html | grep -c "mermaid" || echo "Mermaid graphs missing"

# Validate owners index
curl -f http://localhost:8000/owners.html | grep -c "owner-entry" || echo "Owners index missing"

# Test chaos engineering data
curl -f http://localhost:8002/graph/chaos/drills | jq '.drills | length'
```

## Automation

### Cron Jobs

```bash
# Add to crontab (crontab -e)
# Daily PostgreSQL backup at 2 AM
0 2 * * * cd /opt/gitguard && make backup-postgres >> /var/log/gitguard-backup.log 2>&1

# Weekly restore rehearsal on Mondays at 4 AM
0 4 * * 1 cd /opt/gitguard && ENVIRONMENT=staging make restore-rehearsal >> /var/log/gitguard-rehearsal.log 2>&1

# Monthly cleanup on first Sunday at 5 AM
0 5 1-7 * 0 cd /opt/gitguard && make backup-cleanup >> /var/log/gitguard-cleanup.log 2>&1
```

### Systemd Timers

```ini
# /etc/systemd/system/gitguard-backup.timer
[Unit]
Description=GitGuard Daily Backup
Requires=gitguard-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/gitguard-backup.service
[Unit]
Description=GitGuard Backup Service

[Service]
Type=oneshot
User=gitguard
WorkingDirectory=/opt/gitguard
ExecStart=/usr/bin/make backup-all
EnvironmentFile=/opt/gitguard/.env
```

### CI/CD Integration

```yaml
# .github/workflows/backup-validation.yml
name: Backup Validation
on:
  schedule:
    - cron: '0 6 * * 1'  # Weekly on Monday

jobs:
  validate-backups:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate Backup Integrity
        run: |
          make backup-status
          ./scripts/validate_backups.sh
```

## Security Considerations

### Backup Encryption

```bash
# Encrypt backups at rest (includes org-brain data)
gpg --cipher-algo AES256 --compress-algo 1 --symmetric \
    --output /backups/pg_codex_$(date +%F).dump.gpg \
    /backups/pg_codex_$(date +%F).dump

# Encrypt Graph API configuration
gpg --symmetric --output /backups/graph_api_config_$(date +%F).env.gpg \
    /backups/graph_api_config_$(date +%F).env

# Decrypt for restore
gpg --decrypt /backups/pg_codex_2024-01-15.dump.gpg > restore.dump
gpg --decrypt /backups/graph_api_config_2024-01-15.env.gpg > graph_config.env
```

### Access Control

```bash
# Restrict backup directory access
chmod 700 /backups
chown -R gitguard:gitguard /backups

# Use dedicated backup user
useradd -r -s /bin/false gitguard-backup
chown -R gitguard-backup:gitguard-backup /backups

# Secure Graph API configurations
chmod 600 /backups/graph_api_config_*.env

# Protect org-brain data backups
chmod 600 /backups/pg_codex_*.dump
```

### Network Security

```bash
# Use SSL for database connections
export DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"

# Restrict NATS access
export NATS_URL="nats://user:pass@localhost:4222"

# Secure Graph API endpoints
export GRAPH_API_TLS_CERT="/etc/ssl/certs/graph-api.crt"
export GRAPH_API_TLS_KEY="/etc/ssl/private/graph-api.key"

# Protect policy transparency data in transit
export ORG_BRAIN_SSL_MODE="require"
```

## Performance Optimization

### Backup Performance

```bash
# Use parallel jobs for large databases
pg_dump -Fc -j 4 -d "$DATABASE_URL" > backup.dump

# Compress backups
pg_dump -Fc -Z 9 -d "$DATABASE_URL" > backup.dump

# Use faster storage for backups
mount -t tmpfs -o size=2G tmpfs /tmp/backup
```

### Restore Performance

```bash
# Use parallel restore
pg_restore -j 4 -d "$DATABASE_URL" backup.dump

# Disable fsync during restore
echo "fsync = off" >> postgresql.conf
# Remember to re-enable after restore
```

## Best Practices

### ✅ Do's

- **Test restores regularly** - Weekly rehearsals catch issues early
- **Monitor backup sizes** - Sudden changes indicate problems
- **Keep multiple backup locations** - Local + remote storage
- **Document recovery procedures** - Team knowledge sharing
- **Automate everything** - Reduce human error
- **Encrypt sensitive backups** - Protect data at rest
- **Version control scripts** - Track backup procedure changes

### ❌ Don'ts

- **Don't skip rehearsals** - Untested backups are useless
- **Don't ignore backup failures** - Silent failures are dangerous
- **Don't store backups on same disk** - Single point of failure
- **Don't hardcode credentials** - Use environment variables
- **Don't backup to production** - Use dedicated backup storage
- **Don't ignore retention policies** - Disk space management
- **Don't forget about dependencies** - Backup related services

## Support

### Getting Help

- **Documentation**: Check this guide first
- **Logs**: Review `/backups/*.log` files
- **Status**: Run `make backup-status`
- **Health**: Run `make health`
- **Community**: GitGuard Slack #backup-restore

### Reporting Issues

When reporting backup issues, include:

1. **Environment details** (OS, PostgreSQL version, NATS version)
2. **Error messages** (from logs)
3. **Backup status** (`make backup-status` output)
4. **Recent changes** (configuration, environment)
5. **Reproduction steps** (if applicable)

---

**Remember**: The best backup is the one you've successfully restored. Test early, test often! 🎭
