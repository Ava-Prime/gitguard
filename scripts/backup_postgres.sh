#!/bin/bash
# PostgreSQL backup script with daily dumps and 7-day retention
# Usage: ./backup_postgres.sh

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
DATE=$(date +%F)
BACKUP_FILE="${BACKUP_DIR}/pg_codex_${DATE}.dump"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    echo -e "${RED}❌ Backup failed: $1${NC}"
    exit 1
}

# Check if DATABASE_URL is set
if [ -z "${DATABASE_URL:-}" ]; then
    error_exit "DATABASE_URL environment variable is not set"
fi

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR" || error_exit "Failed to create backup directory: $BACKUP_DIR"
    log "Created backup directory: $BACKUP_DIR"
fi

# Check if backup already exists for today
if [ -f "$BACKUP_FILE" ]; then
    echo -e "${YELLOW}⚠️  Backup already exists for today: $BACKUP_FILE${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Backup cancelled by user"
        exit 0
    fi
    rm -f "$BACKUP_FILE"
fi

log "Starting PostgreSQL backup..."
echo -e "${YELLOW}🔄 Creating PostgreSQL backup...${NC}"

# Create the backup
if pg_dump -Fc -d "$DATABASE_URL" > "$BACKUP_FILE"; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup completed successfully: $BACKUP_FILE ($BACKUP_SIZE)"
    echo -e "${GREEN}✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)${NC}"
else
    error_exit "pg_dump failed"
fi

# Clean up old backups (keep 7 days)
log "Cleaning up old backups (keeping 7 days)..."
echo -e "${YELLOW}🧹 Cleaning up old backups...${NC}"

OLD_BACKUPS=$(find "$BACKUP_DIR" -name 'pg_codex_*.dump' -mtime +7 2>/dev/null || true)
if [ -n "$OLD_BACKUPS" ]; then
    echo "$OLD_BACKUPS" | while read -r old_backup; do
        if [ -f "$old_backup" ]; then
            rm -f "$old_backup"
            log "Deleted old backup: $old_backup"
            echo -e "${GREEN}🗑️  Deleted: $(basename "$old_backup")${NC}"
        fi
    done
else
    log "No old backups to clean up"
    echo -e "${GREEN}✅ No old backups to clean up${NC}"
fi

# Show backup summary
echo -e "\n${GREEN}📊 Backup Summary:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 Backup file: $BACKUP_FILE"
echo "📏 Size: $BACKUP_SIZE"
echo "📅 Date: $DATE"
echo "📂 Directory: $BACKUP_DIR"

# List current backups
echo -e "\n${YELLOW}📋 Current backups:${NC}"
ls -lh "$BACKUP_DIR"/pg_codex_*.dump 2>/dev/null | awk '{print "  " $9 " (" $5 ", " $6 " " $7 ")"}' || echo "  No backups found"

log "Backup process completed successfully"
echo -e "\n${GREEN}🎉 PostgreSQL backup completed successfully!${NC}"
