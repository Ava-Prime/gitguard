#!/bin/bash
# Setup backup directory structure and permissions
# Usage: ./setup_backup_infrastructure.sh [backup_dir]

set -euo pipefail

# Configuration
BACKUP_DIR="${1:-/backups}"
BACKUP_USER="${BACKUP_USER:-gitguard}"
BACKUP_GROUP="${BACKUP_GROUP:-gitguard}"
LOG_FILE="/tmp/backup_setup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    echo -e "${RED}❌ Setup failed: $1${NC}"
    exit 1
}

# Success function
success() {
    log "SUCCESS: $1"
    echo -e "${GREEN}✅ $1${NC}"
}

# Info function
info() {
    log "INFO: $1"
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Warning function
warn() {
    log "WARNING: $1"
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if running as root or with sudo
check_privileges() {
    if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
        error_exit "This script requires root privileges or passwordless sudo access"
    fi
    success "Privilege check passed"
}

# Create backup user and group if they don't exist
setup_user_group() {
    info "Setting up backup user and group..."
    
    # Create group if it doesn't exist
    if ! getent group "$BACKUP_GROUP" >/dev/null 2>&1; then
        if [ "$EUID" -eq 0 ]; then
            groupadd "$BACKUP_GROUP"
        else
            sudo groupadd "$BACKUP_GROUP"
        fi
        success "Created group: $BACKUP_GROUP"
    else
        info "Group already exists: $BACKUP_GROUP"
    fi
    
    # Create user if it doesn't exist
    if ! id "$BACKUP_USER" >/dev/null 2>&1; then
        if [ "$EUID" -eq 0 ]; then
            useradd -r -g "$BACKUP_GROUP" -s /bin/bash -d "$BACKUP_DIR" "$BACKUP_USER"
        else
            sudo useradd -r -g "$BACKUP_GROUP" -s /bin/bash -d "$BACKUP_DIR" "$BACKUP_USER"
        fi
        success "Created user: $BACKUP_USER"
    else
        info "User already exists: $BACKUP_USER"
    fi
}

# Create backup directory structure
setup_directories() {
    info "Setting up backup directory structure..."
    
    # Create main backup directory
    if [ "$EUID" -eq 0 ]; then
        mkdir -p "$BACKUP_DIR"
    else
        sudo mkdir -p "$BACKUP_DIR"
    fi
    success "Created backup directory: $BACKUP_DIR"
    
    # Create subdirectories for organization
    local subdirs=(
        "postgres"
        "jetstream"
        "reports"
        "logs"
        "temp"
        "archive"
    )
    
    for subdir in "${subdirs[@]}"; do
        local full_path="$BACKUP_DIR/$subdir"
        if [ "$EUID" -eq 0 ]; then
            mkdir -p "$full_path"
        else
            sudo mkdir -p "$full_path"
        fi
        info "Created subdirectory: $full_path"
    done
    
    success "Directory structure created"
}

# Set proper permissions
set_permissions() {
    info "Setting backup directory permissions..."
    
    # Set ownership
    if [ "$EUID" -eq 0 ]; then
        chown -R "$BACKUP_USER:$BACKUP_GROUP" "$BACKUP_DIR"
    else
        sudo chown -R "$BACKUP_USER:$BACKUP_GROUP" "$BACKUP_DIR"
    fi
    success "Set ownership to $BACKUP_USER:$BACKUP_GROUP"
    
    # Set permissions
    # Main directory: rwx for owner, rx for group, no access for others
    if [ "$EUID" -eq 0 ]; then
        chmod 750 "$BACKUP_DIR"
        # Subdirectories: same permissions
        find "$BACKUP_DIR" -type d -exec chmod 750 {} \;
        # Files: rw for owner, r for group, no access for others
        find "$BACKUP_DIR" -type f -exec chmod 640 {} \;
    else
        sudo chmod 750 "$BACKUP_DIR"
        sudo find "$BACKUP_DIR" -type d -exec chmod 750 {} \;
        sudo find "$BACKUP_DIR" -type f -exec chmod 640 {} \;
    fi
    success "Set directory permissions (750) and file permissions (640)"
}

# Create backup configuration file
create_config() {
    info "Creating backup configuration..."
    
    local config_file="$BACKUP_DIR/backup.conf"
    
    cat > "/tmp/backup.conf" << EOF
# GitGuard Backup Configuration
# Generated on $(date)

# Backup Directory
BACKUP_DIR="$BACKUP_DIR"

# User and Group
BACKUP_USER="$BACKUP_USER"
BACKUP_GROUP="$BACKUP_GROUP"

# Retention Policies (days)
POSTGRES_RETENTION=7
JETSTREAM_RETENTION=14
REPORT_RETENTION=30
LOG_RETENTION=90

# Backup Schedule
# PostgreSQL: Daily at 2 AM
# JetStream: Pre-deployment
# Rehearsal: Weekly on Monday at 4 AM

# Monitoring
BACKUP_ALERT_EMAIL="ops@yourcompany.com"
BACKUP_SLACK_WEBHOOK="https://hooks.slack.com/..."

# Compression
POSTGRES_COMPRESSION=9
JETSTREAM_COMPRESSION=true

# Encryption (optional)
# GPG_KEY_ID="your-gpg-key-id"
# ENCRYPT_BACKUPS=false
EOF

    if [ "$EUID" -eq 0 ]; then
        mv "/tmp/backup.conf" "$config_file"
        chown "$BACKUP_USER:$BACKUP_GROUP" "$config_file"
        chmod 640 "$config_file"
    else
        sudo mv "/tmp/backup.conf" "$config_file"
        sudo chown "$BACKUP_USER:$BACKUP_GROUP" "$config_file"
        sudo chmod 640 "$config_file"
    fi
    
    success "Created configuration file: $config_file"
}

# Create logrotate configuration
setup_logrotate() {
    info "Setting up log rotation..."
    
    local logrotate_file="/etc/logrotate.d/gitguard-backup"
    
    cat > "/tmp/gitguard-backup-logrotate" << EOF
$BACKUP_DIR/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 640 $BACKUP_USER $BACKUP_GROUP
    postrotate
        # Send HUP signal to any processes that need to reopen log files
        /bin/kill -HUP \$(cat /var/run/gitguard-backup.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF

    if [ "$EUID" -eq 0 ]; then
        mv "/tmp/gitguard-backup-logrotate" "$logrotate_file"
        chmod 644 "$logrotate_file"
    else
        sudo mv "/tmp/gitguard-backup-logrotate" "$logrotate_file"
        sudo chmod 644 "$logrotate_file"
    fi
    
    success "Created logrotate configuration: $logrotate_file"
}

# Create systemd service files
setup_systemd() {
    info "Setting up systemd services..."
    
    # Backup service
    cat > "/tmp/gitguard-backup.service" << EOF
[Unit]
Description=GitGuard Backup Service
After=postgresql.service nats.service
Requires=postgresql.service

[Service]
Type=oneshot
User=$BACKUP_USER
Group=$BACKUP_GROUP
WorkingDirectory=$(pwd)
EnvironmentFile=-/opt/gitguard/.env
ExecStart=/usr/bin/make backup-all
StandardOutput=append:$BACKUP_DIR/logs/backup.log
StandardError=append:$BACKUP_DIR/logs/backup.log

[Install]
WantedBy=multi-user.target
EOF

    # Backup timer
    cat > "/tmp/gitguard-backup.timer" << EOF
[Unit]
Description=GitGuard Daily Backup Timer
Requires=gitguard-backup.service

[Timer]
OnCalendar=daily
RandomizedDelaySec=1800
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Rehearsal service
    cat > "/tmp/gitguard-rehearsal.service" << EOF
[Unit]
Description=GitGuard Restore Rehearsal Service
After=postgresql.service nats.service
Requires=postgresql.service

[Service]
Type=oneshot
User=$BACKUP_USER
Group=$BACKUP_GROUP
WorkingDirectory=$(pwd)
Environment=ENVIRONMENT=staging
EnvironmentFile=-/opt/gitguard/.env
ExecStart=/usr/bin/make restore-rehearsal
StandardOutput=append:$BACKUP_DIR/logs/rehearsal.log
StandardError=append:$BACKUP_DIR/logs/rehearsal.log

[Install]
WantedBy=multi-user.target
EOF

    # Rehearsal timer
    cat > "/tmp/gitguard-rehearsal.timer" << EOF
[Unit]
Description=GitGuard Weekly Restore Rehearsal Timer
Requires=gitguard-rehearsal.service

[Timer]
OnCalendar=Mon *-*-* 04:00:00
RandomizedDelaySec=1800
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Install service files
    local services=(
        "gitguard-backup.service"
        "gitguard-backup.timer"
        "gitguard-rehearsal.service"
        "gitguard-rehearsal.timer"
    )
    
    for service in "${services[@]}"; do
        if [ "$EUID" -eq 0 ]; then
            mv "/tmp/$service" "/etc/systemd/system/$service"
            chmod 644 "/etc/systemd/system/$service"
        else
            sudo mv "/tmp/$service" "/etc/systemd/system/$service"
            sudo chmod 644 "/etc/systemd/system/$service"
        fi
        info "Created systemd service: $service"
    done
    
    # Reload systemd
    if [ "$EUID" -eq 0 ]; then
        systemctl daemon-reload
    else
        sudo systemctl daemon-reload
    fi
    
    success "Systemd services created and reloaded"
}

# Validate setup
validate_setup() {
    info "Validating backup infrastructure setup..."
    
    # Check directory exists and has correct permissions
    if [ ! -d "$BACKUP_DIR" ]; then
        error_exit "Backup directory does not exist: $BACKUP_DIR"
    fi
    
    # Check ownership
    local owner
    owner=$(stat -c '%U:%G' "$BACKUP_DIR")
    if [ "$owner" != "$BACKUP_USER:$BACKUP_GROUP" ]; then
        error_exit "Incorrect ownership: expected $BACKUP_USER:$BACKUP_GROUP, got $owner"
    fi
    
    # Check permissions
    local perms
    perms=$(stat -c '%a' "$BACKUP_DIR")
    if [ "$perms" != "750" ]; then
        error_exit "Incorrect permissions: expected 750, got $perms"
    fi
    
    # Check subdirectories
    local subdirs=("postgres" "jetstream" "reports" "logs" "temp" "archive")
    for subdir in "${subdirs[@]}"; do
        if [ ! -d "$BACKUP_DIR/$subdir" ]; then
            error_exit "Missing subdirectory: $BACKUP_DIR/$subdir"
        fi
    done
    
    # Check configuration file
    if [ ! -f "$BACKUP_DIR/backup.conf" ]; then
        error_exit "Missing configuration file: $BACKUP_DIR/backup.conf"
    fi
    
    # Test write access
    local test_file="$BACKUP_DIR/test_write_$$"
    if ! sudo -u "$BACKUP_USER" touch "$test_file" 2>/dev/null; then
        error_exit "Backup user cannot write to backup directory"
    fi
    rm -f "$test_file"
    
    success "Backup infrastructure validation passed"
}

# Generate setup report
generate_report() {
    local report_file="$BACKUP_DIR/reports/setup_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
# GitGuard Backup Infrastructure Setup Report

**Date:** $(date)
**User:** $(whoami)
**Host:** $(hostname)

## Configuration

- **Backup Directory:** $BACKUP_DIR
- **Backup User:** $BACKUP_USER
- **Backup Group:** $BACKUP_GROUP
- **Directory Permissions:** 750
- **File Permissions:** 640

## Directory Structure

$(tree "$BACKUP_DIR" 2>/dev/null || find "$BACKUP_DIR" -type d | sed 's/^/  /')

## Disk Usage

$(df -h "$BACKUP_DIR")

## Services Created

- gitguard-backup.service (daily backups)
- gitguard-backup.timer
- gitguard-rehearsal.service (weekly rehearsals)
- gitguard-rehearsal.timer

## Next Steps

1. Configure environment variables in /opt/gitguard/.env
2. Enable and start systemd timers:
   - sudo systemctl enable --now gitguard-backup.timer
   - sudo systemctl enable --now gitguard-rehearsal.timer
3. Test backup functionality:
   - make backup-postgres
   - make backup-jetstream
4. Review and customize backup.conf
5. Set up monitoring and alerting

## Validation Results

✅ Directory structure created
✅ Permissions set correctly
✅ User and group configured
✅ Configuration files created
✅ Systemd services installed
✅ Write access verified

EOF

    if [ "$EUID" -eq 0 ]; then
        chown "$BACKUP_USER:$BACKUP_GROUP" "$report_file"
        chmod 640 "$report_file"
    else
        sudo chown "$BACKUP_USER:$BACKUP_GROUP" "$report_file"
        sudo chmod 640 "$report_file"
    fi
    
    info "Setup report generated: $report_file"
}

# Main execution
main() {
    echo -e "${BLUE}🏗️  GitGuard Backup Infrastructure Setup${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}📁 Backup Directory: $BACKUP_DIR${NC}"
    echo -e "${BLUE}👤 Backup User: $BACKUP_USER${NC}"
    echo -e "${BLUE}👥 Backup Group: $BACKUP_GROUP${NC}"
    echo ""
    
    log "Starting backup infrastructure setup"
    
    # Execute setup steps
    check_privileges
    setup_user_group
    setup_directories
    set_permissions
    create_config
    setup_logrotate
    setup_systemd
    validate_setup
    generate_report
    
    echo -e "\n${GREEN}🎉 Backup Infrastructure Setup Completed!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Directory structure: CREATED${NC}"
    echo -e "${GREEN}✅ Permissions: CONFIGURED${NC}"
    echo -e "${GREEN}✅ User/Group: SETUP${NC}"
    echo -e "${GREEN}✅ Configuration: GENERATED${NC}"
    echo -e "${GREEN}✅ Systemd services: INSTALLED${NC}"
    echo -e "${GREEN}✅ Validation: PASSED${NC}"
    
    echo -e "\n${YELLOW}📋 Next Steps:${NC}"
    echo -e "${YELLOW}1. Enable backup timers:${NC}"
    echo -e "   sudo systemctl enable --now gitguard-backup.timer"
    echo -e "   sudo systemctl enable --now gitguard-rehearsal.timer"
    echo -e "${YELLOW}2. Configure environment variables in .env${NC}"
    echo -e "${YELLOW}3. Test backup functionality: make backup-all${NC}"
    echo -e "${YELLOW}4. Review configuration: $BACKUP_DIR/backup.conf${NC}"
    
    echo -e "\n${BLUE}📊 Setup completed in $SECONDS seconds${NC}"
    echo -e "${BLUE}📋 Report: $BACKUP_DIR/reports/setup_report_$(date +%Y%m%d_*)${NC}"
    
    log "Backup infrastructure setup completed successfully in ${SECONDS}s"
}

# Run main function
main "$@"