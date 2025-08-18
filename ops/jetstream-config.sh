#!/bin/bash
# GitGuard Codex - JetStream Configuration Script
# Manages JetStream retention policies during rollout phases

set -euo pipefail

# Configuration
NATS_URL="${NATS_URL:-nats://localhost:4222}"
STREAM_NAME="${JETSTREAM_STREAM:-codex-production}"
SUBJECT="codex.events.>"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

# Check if nats CLI is available
check_nats_cli() {
    if ! command -v nats &> /dev/null; then
        error "nats CLI not found. Please install it first."
        echo "Install with: go install github.com/nats-io/natscli/nats@latest"
        exit 1
    fi
}

# Check NATS connection
check_connection() {
    log "Checking connection to NATS server: $NATS_URL"
    if ! nats --server="$NATS_URL" server check; then
        error "Cannot connect to NATS server: $NATS_URL"
        exit 1
    fi
    success "Connected to NATS server"
}

# Create stream with unbounded retention (Phase 3a)
create_unbounded_stream() {
    log "Creating JetStream with unbounded retention for 72h replay capability"
    
    nats --server="$NATS_URL" stream add "$STREAM_NAME" \
        --subjects="$SUBJECT" \
        --retention=limits \
        --max-age=72h \
        --max-msgs=-1 \
        --max-bytes=-1 \
        --storage=file \
        --replicas=1 \
        --discard=old \
        --dupe-window=2m \
        --allow-rollup \
        --deny-delete \
        --deny-purge=false
    
    success "Created stream '$STREAM_NAME' with unbounded retention"
}

# Update to sane retention limits (Phase 3b)
update_to_sane_limits() {
    log "Updating JetStream to sane retention limits"
    
    nats --server="$NATS_URL" stream edit "$STREAM_NAME" \
        --max-age=24h \
        --max-msgs=1000000 \
        --max-bytes=10GB
    
    success "Updated stream '$STREAM_NAME' to sane retention limits"
}

# Show stream information
show_stream_info() {
    log "Stream information for '$STREAM_NAME':"
    nats --server="$NATS_URL" stream info "$STREAM_NAME"
}

# Backup stream configuration
backup_stream_config() {
    local backup_file="jetstream-backup-$(date +%Y%m%d-%H%M%S).json"
    log "Backing up stream configuration to: $backup_file"
    
    nats --server="$NATS_URL" stream info "$STREAM_NAME" --json > "$backup_file"
    success "Stream configuration backed up to: $backup_file"
}

# Restore stream from backup
restore_stream_config() {
    local backup_file="$1"
    if [[ ! -f "$backup_file" ]]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log "Restoring stream configuration from: $backup_file"
    # Note: This would require custom logic to parse JSON and recreate stream
    warn "Stream restoration requires manual configuration based on backup file"
}

# Monitor stream metrics
monitor_stream() {
    log "Monitoring stream '$STREAM_NAME' (Press Ctrl+C to stop)"
    
    while true; do
        clear
        echo "=== JetStream Monitor - $(date) ==="
        nats --server="$NATS_URL" stream info "$STREAM_NAME" --json | jq '{
            name: .config.name,
            messages: .state.messages,
            bytes: .state.bytes,
            first_seq: .state.first_seq,
            last_seq: .state.last_seq,
            consumer_count: .state.consumer_count,
            max_age: .config.max_age,
            max_msgs: .config.max_msgs,
            max_bytes: .config.max_bytes
        }'
        echo ""
        echo "Storage usage: $(nats --server="$NATS_URL" stream info "$STREAM_NAME" --json | jq -r '.state.bytes' | numfmt --to=iec)"
        sleep 5
    done
}

# Purge stream (emergency)
purge_stream() {
    warn "This will purge ALL messages from stream '$STREAM_NAME'"
    read -p "Are you sure? Type 'yes' to confirm: " confirm
    
    if [[ "$confirm" == "yes" ]]; then
        nats --server="$NATS_URL" stream purge "$STREAM_NAME" --force
        success "Stream '$STREAM_NAME' purged"
    else
        log "Purge cancelled"
    fi
}

# Delete stream (emergency)
delete_stream() {
    warn "This will DELETE stream '$STREAM_NAME' and ALL its data"
    read -p "Are you sure? Type 'DELETE' to confirm: " confirm
    
    if [[ "$confirm" == "DELETE" ]]; then
        nats --server="$NATS_URL" stream delete "$STREAM_NAME" --force
        success "Stream '$STREAM_NAME' deleted"
    else
        log "Delete cancelled"
    fi
}

# Usage information
usage() {
    echo "GitGuard Codex JetStream Configuration Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  create-unbounded    Create stream with unbounded retention (Phase 3a)"
    echo "  update-sane-limits  Update to sane retention limits (Phase 3b)"
    echo "  info               Show stream information"
    echo "  backup             Backup stream configuration"
    echo "  restore <file>     Restore stream from backup file"
    echo "  monitor            Monitor stream metrics (real-time)"
    echo "  purge              Purge all messages (emergency)"
    echo "  delete             Delete stream (emergency)"
    echo ""
    echo "Environment Variables:"
    echo "  NATS_URL           NATS server URL (default: nats://localhost:4222)"
    echo "  JETSTREAM_STREAM   Stream name (default: codex-production)"
    echo ""
    echo "Examples:"
    echo "  $0 create-unbounded"
    echo "  $0 update-sane-limits"
    echo "  $0 monitor"
    echo "  NATS_URL=nats://prod:4222 $0 info"
}

# Main script logic
main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi
    
    check_nats_cli
    check_connection
    
    case "$1" in
        create-unbounded)
            create_unbounded_stream
            ;;
        update-sane-limits)
            update_to_sane_limits
            ;;
        info)
            show_stream_info
            ;;
        backup)
            backup_stream_config
            ;;
        restore)
            if [[ $# -lt 2 ]]; then
                error "Backup file required for restore command"
                exit 1
            fi
            restore_stream_config "$2"
            ;;
        monitor)
            monitor_stream
            ;;
        purge)
            purge_stream
            ;;
        delete)
            delete_stream
            ;;
        *)
            error "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"