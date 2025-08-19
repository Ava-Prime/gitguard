#!/bin/bash
# JetStream snapshot script for pre-deployment backups
# Usage: ./backup_jetstream.sh [stream_name]

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
DATE=$(date +%F)
STREAM_NAME="${1:-GH}"  # Default to GH stream if not specified
SNAPSHOT_PATH="${BACKUP_DIR}/js_${STREAM_NAME,,}_${DATE}"  # Convert to lowercase
LOG_FILE="${BACKUP_DIR}/jetstream_backup.log"

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
    echo -e "${RED}❌ JetStream backup failed: $1${NC}"
    exit 1
}

# Check if nats CLI is available
if ! command -v nats &> /dev/null; then
    error_exit "nats CLI is not installed or not in PATH"
fi

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR" || error_exit "Failed to create backup directory: $BACKUP_DIR"
    log "Created backup directory: $BACKUP_DIR"
fi

# Check if snapshot already exists for today
if [ -d "$SNAPSHOT_PATH" ]; then
    echo -e "${YELLOW}⚠️  Snapshot already exists for today: $SNAPSHOT_PATH${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Snapshot cancelled by user"
        exit 0
    fi
    rm -rf "$SNAPSHOT_PATH"
fi

log "Starting JetStream snapshot for stream: $STREAM_NAME"
echo -e "${YELLOW}🔄 Creating JetStream snapshot...${NC}"
echo -e "${BLUE}📊 Stream: $STREAM_NAME${NC}"
echo -e "${BLUE}📁 Destination: $SNAPSHOT_PATH${NC}"

# Check if stream exists
if ! nats stream info "$STREAM_NAME" &>/dev/null; then
    error_exit "Stream '$STREAM_NAME' does not exist or is not accessible"
fi

# Get stream info before backup
STREAM_INFO=$(nats stream info "$STREAM_NAME" --json 2>/dev/null || echo '{}')
MESSAGE_COUNT=$(echo "$STREAM_INFO" | jq -r '.state.messages // "unknown"' 2>/dev/null || echo "unknown")
STREAM_SIZE=$(echo "$STREAM_INFO" | jq -r '.state.bytes // "unknown"' 2>/dev/null || echo "unknown")

log "Stream info - Messages: $MESSAGE_COUNT, Size: $STREAM_SIZE bytes"
echo -e "${BLUE}📈 Messages: $MESSAGE_COUNT${NC}"
echo -e "${BLUE}💾 Size: $STREAM_SIZE bytes${NC}"

# Create the snapshot
if nats stream snapshot "$STREAM_NAME" "$SNAPSHOT_PATH"; then
    # Calculate snapshot size
    if [ -d "$SNAPSHOT_PATH" ]; then
        SNAPSHOT_SIZE=$(du -sh "$SNAPSHOT_PATH" 2>/dev/null | cut -f1 || echo "unknown")
    else
        SNAPSHOT_SIZE="unknown"
    fi

    log "Snapshot completed successfully: $SNAPSHOT_PATH ($SNAPSHOT_SIZE)"
    echo -e "${GREEN}✅ Snapshot created: $SNAPSHOT_PATH ($SNAPSHOT_SIZE)${NC}"
else
    error_exit "nats stream snapshot failed"
fi

# Verify snapshot integrity
echo -e "${YELLOW}🔍 Verifying snapshot integrity...${NC}"
if [ -d "$SNAPSHOT_PATH" ] && [ "$(ls -A "$SNAPSHOT_PATH" 2>/dev/null)" ]; then
    SNAPSHOT_FILES=$(find "$SNAPSHOT_PATH" -type f | wc -l)
    log "Snapshot verification passed: $SNAPSHOT_FILES files found"
    echo -e "${GREEN}✅ Snapshot verified: $SNAPSHOT_FILES files${NC}"
else
    error_exit "Snapshot verification failed: directory is empty or missing"
fi

# Clean up old snapshots (keep 14 days for JetStream)
log "Cleaning up old JetStream snapshots (keeping 14 days)..."
echo -e "${YELLOW}🧹 Cleaning up old snapshots...${NC}"

OLD_SNAPSHOTS=$(find "$BACKUP_DIR" -name "js_${STREAM_NAME,,}_*" -type d -mtime +14 2>/dev/null || true)
if [ -n "$OLD_SNAPSHOTS" ]; then
    echo "$OLD_SNAPSHOTS" | while read -r old_snapshot; do
        if [ -d "$old_snapshot" ]; then
            rm -rf "$old_snapshot"
            log "Deleted old snapshot: $old_snapshot"
            echo -e "${GREEN}🗑️  Deleted: $(basename "$old_snapshot")${NC}"
        fi
    done
else
    log "No old snapshots to clean up"
    echo -e "${GREEN}✅ No old snapshots to clean up${NC}"
fi

# Show backup summary
echo -e "\n${GREEN}📊 JetStream Snapshot Summary:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌊 Stream: $STREAM_NAME"
echo "📁 Snapshot path: $SNAPSHOT_PATH"
echo "📏 Size: $SNAPSHOT_SIZE"
echo "📅 Date: $DATE"
echo "📈 Messages: $MESSAGE_COUNT"
echo "💾 Stream size: $STREAM_SIZE bytes"
echo "📂 Directory: $BACKUP_DIR"

# List current snapshots for this stream
echo -e "\n${YELLOW}📋 Current snapshots for $STREAM_NAME:${NC}"
ls -ld "$BACKUP_DIR"/js_${STREAM_NAME,,}_* 2>/dev/null | awk '{print "  " $9 " (" $6 " " $7 " " $8 ")"}' || echo "  No snapshots found"

log "JetStream snapshot process completed successfully"
echo -e "\n${GREEN}🎉 JetStream snapshot completed successfully!${NC}"

# Show restore command hint
echo -e "\n${BLUE}💡 To restore this snapshot:${NC}"
echo -e "${BLUE}   nats stream restore $STREAM_NAME $SNAPSHOT_PATH${NC}"
