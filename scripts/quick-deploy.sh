#!/bin/bash

# GitGuard Quick Deploy Script
# Enables instant deployment and demo experience for external users

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
GITGUARD_VERSION="${GITGUARD_VERSION:-latest}"
DEPLOY_METHOD="${DEPLOY_METHOD:-docker-compose}"
DEMO_MODE="${DEMO_MODE:-true}"
PORT="${PORT:-8080}"
GRAFANA_PORT="${GRAFANA_PORT:-3000}"

# Functions
print_banner() {
    echo -e "${PURPLE}"
    cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ██████╗ ██╗████████╗ ██████╗ ██╗   ██╗ █████╗ ██████╗  ║
    ║  ██╔════╝ ██║╚══██╔══╝██╔════╝ ██║   ██║██╔══██╗██╔══██╗ ║
    ║  ██║  ███╗██║   ██║   ██║  ███╗██║   ██║███████║██████╔╝ ║
    ║  ██║   ██║██║   ██║   ██║   ██║██║   ██║██╔══██║██╔══██╗ ║
    ║  ╚██████╔╝██║   ██║   ╚██████╔╝╚██████╔╝██║  ██║██║  ██║ ║
    ║   ╚═════╝ ╚═╝   ╚═╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ║
    ║                                                           ║
    ║           The Autonomous Repository Steward               ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

check_dependencies() {
    log "Checking dependencies..."

    if ! command -v docker &> /dev/null; then
        error "Docker is required but not installed. Please install Docker first."
    fi

    if [[ "$DEPLOY_METHOD" == "docker-compose" ]] && ! command -v docker-compose &> /dev/null; then
        if ! docker compose version &> /dev/null; then
            error "Docker Compose is required but not installed."
        fi
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi

    log "✅ Dependencies check passed"
}

generate_demo_config() {
    log "Generating demo configuration..."

    # Create demo environment file
    cat > .env.demo << EOF
# GitGuard Demo Configuration
ENVIRONMENT=demo
LOG_LEVEL=info
DEBUG=true
METRICS_ENABLED=true

# Ports
GITGUARD_PORT=$PORT
GRAFANA_PORT=$GRAFANA_PORT
PROMETHEUS_PORT=9090
REDIS_PORT=6379
POSTGRES_PORT=5432

# Database
POSTGRES_DB=gitguard_demo
POSTGRES_USER=gitguard
POSTGRES_PASSWORD=demo_password_$(openssl rand -hex 8)

# Redis
REDIS_PASSWORD=demo_redis_$(openssl rand -hex 8)

# Demo Data
DEMO_MODE=true
GENERATE_SAMPLE_DATA=true
SAMPLE_REPOS=5
SAMPLE_POLICIES=10

# GitHub (Demo mode - optional)
# GITHUB_APP_ID=your_app_id
# GITHUB_APP_PRIVATE_KEY=your_private_key
# GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Temporal
TEMPORAL_HOST=temporal:7233
TEMPORAL_NAMESPACE=gitguard-demo

# OPA
OPA_ENDPOINT=http://opa:8181

# Monitoring
GRAFANA_ADMIN_PASSWORD=demo_grafana_$(openssl rand -hex 8)
PROMETHEUS_RETENTION=7d

# Security (Demo only - use proper secrets in production)
ENCRYption_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
EOF

    log "✅ Demo configuration generated"
}

generate_docker_compose() {
    log "Generating Docker Compose configuration..."

    cat > docker-compose.demo.yml << 'EOF'
version: '3.8'

services:
  # GitGuard API
  gitguard-api:
    image: ghcr.io/codessa-platform/gitguard:${GITGUARD_VERSION:-latest}
    container_name: gitguard-api
    ports:
      - "${GITGUARD_PORT:-8080}:8080"
    environment:
      - ENVIRONMENT=demo
      - DATABASE_URL=postgresql://gitguard:${POSTGRES_PASSWORD}@postgres:5432/gitguard_demo
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - TEMPORAL_HOST=temporal:7233
      - OPA_ENDPOINT=http://opa:8181
      - DEMO_MODE=true
    depends_on:
      - postgres
      - redis
      - temporal
      - opa
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - gitguard-network

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: gitguard-postgres
    environment:
      - POSTGRES_DB=gitguard_demo
      - POSTGRES_USER=gitguard
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/demo-data.sql:/docker-entrypoint-initdb.d/demo-data.sql
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gitguard -d gitguard_demo"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - gitguard-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: gitguard-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    restart: unless-stopped
    networks:
      - gitguard-network

  # Temporal Server
  temporal:
    image: temporalio/auto-setup:latest
    container_name: gitguard-temporal
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=gitguard
      - POSTGRES_PWD=${POSTGRES_PASSWORD}
      - POSTGRES_SEEDS=postgres
      - DYNAMIC_CONFIG_FILE_PATH=config/dynamicconfig/development-sql.yaml
    ports:
      - "7233:7233"
      - "8233:8233"
    depends_on:
      - postgres
    volumes:
      - temporal_data:/etc/temporal
    restart: unless-stopped
    networks:
      - gitguard-network

  # Open Policy Agent
  opa:
    image: openpolicyagent/opa:latest-envoy
    container_name: gitguard-opa
    command:
      - "run"
      - "--server"
      - "--addr=0.0.0.0:8181"
      - "--diagnostic-addr=0.0.0.0:8282"
      - "--set=plugins.envoy_ext_authz_grpc.addr=:9191"
      - "--set=plugins.envoy_ext_authz_grpc.query=data.envoy.authz.allow"
      - "--set=decision_logs.console=true"
      - "/policies"
    ports:
      - "8181:8181"
      - "8282:8282"
    volumes:
      - ./policies:/policies
    restart: unless-stopped
    networks:
      - gitguard-network

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: gitguard-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=${PROMETHEUS_RETENTION:-7d}'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    volumes:
      - ./ops/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped
    networks:
      - gitguard-network

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: gitguard-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-worldmap-panel
    ports:
      - "${GRAFANA_PORT:-3000}:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./ops/monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./ops/monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - gitguard-network

  # Temporal Web UI
  temporal-web:
    image: temporalio/web:latest
    container_name: gitguard-temporal-web
    environment:
      - TEMPORAL_GRPC_ENDPOINT=temporal:7233
      - TEMPORAL_PERMIT_WRITE_API=true
    ports:
      - "8088:8088"
    depends_on:
      - temporal
    restart: unless-stopped
    networks:
      - gitguard-network

volumes:
  postgres_data:
  redis_data:
  temporal_data:
  prometheus_data:
  grafana_data:

networks:
  gitguard-network:
    driver: bridge
EOF

    log "✅ Docker Compose configuration generated"
}

generate_demo_data() {
    log "Generating demo data..."

    mkdir -p scripts
    cat > scripts/demo-data.sql << 'EOF'
-- GitGuard Demo Data
-- This script creates sample data for demonstration purposes

-- Create demo repositories
INSERT INTO repositories (id, name, full_name, owner, description, private, created_at, updated_at) VALUES
('repo-1', 'demo-webapp', 'demo-org/demo-webapp', 'demo-org', 'A sample web application for GitGuard demo', false, NOW(), NOW()),
('repo-2', 'api-service', 'demo-org/api-service', 'demo-org', 'REST API service with GitGuard policies', false, NOW(), NOW()),
('repo-3', 'mobile-app', 'demo-org/mobile-app', 'demo-org', 'Mobile application repository', true, NOW(), NOW()),
('repo-4', 'infrastructure', 'demo-org/infrastructure', 'demo-org', 'Infrastructure as Code repository', true, NOW(), NOW()),
('repo-5', 'documentation', 'demo-org/documentation', 'demo-org', 'Project documentation and guides', false, NOW(), NOW());

-- Create demo policies
INSERT INTO policies (id, name, description, type, enabled, created_at, updated_at) VALUES
('policy-1', 'Release Window Policy', 'Restricts deployments to business hours', 'release_window', true, NOW(), NOW()),
('policy-2', 'Security Review Policy', 'Requires security review for sensitive changes', 'approval', true, NOW(), NOW()),
('policy-3', 'Breaking Change Policy', 'Prevents breaking changes without approval', 'risk_assessment', true, NOW(), NOW()),
('policy-4', 'Dependency Update Policy', 'Automates dependency updates with safety checks', 'automation', true, NOW(), NOW()),
('policy-5', 'Compliance Policy', 'Ensures regulatory compliance for releases', 'compliance', true, NOW(), NOW());

-- Create demo policy evaluations
INSERT INTO policy_evaluations (id, repository_id, policy_id, pull_request_number, result, reason, created_at) VALUES
('eval-1', 'repo-1', 'policy-1', 123, 'approved', 'Within business hours (09:00-17:00 UTC)', NOW() - INTERVAL '1 hour'),
('eval-2', 'repo-2', 'policy-2', 124, 'pending', 'Awaiting security team review', NOW() - INTERVAL '30 minutes'),
('eval-3', 'repo-3', 'policy-3', 125, 'rejected', 'Breaking API changes detected', NOW() - INTERVAL '15 minutes'),
('eval-4', 'repo-4', 'policy-4', 126, 'approved', 'Dependency updates are safe', NOW() - INTERVAL '5 minutes'),
('eval-5', 'repo-5', 'policy-5', 127, 'approved', 'Compliance checks passed', NOW());

-- Create demo metrics
INSERT INTO metrics (id, name, value, labels, timestamp) VALUES
('metric-1', 'gitguard_policy_evaluations_total', 150, '{"status":"approved"}', NOW()),
('metric-2', 'gitguard_policy_evaluations_total', 25, '{"status":"rejected"}', NOW()),
('metric-3', 'gitguard_policy_evaluations_total', 10, '{"status":"pending"}', NOW()),
('metric-4', 'gitguard_deployment_success_rate', 0.94, '{"environment":"production"}', NOW()),
('metric-5', 'gitguard_average_review_time_seconds', 1800, '{"policy_type":"security"}', NOW());
EOF

    log "✅ Demo data generated"
}

start_services() {
    log "Starting GitGuard services..."

    # Load environment variables
    set -a
    source .env.demo
    set +a

    # Start services
    $COMPOSE_CMD -f docker-compose.demo.yml up -d

    log "⏳ Waiting for services to be ready..."

    # Wait for services to be healthy
    local max_attempts=60
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:$PORT/health &> /dev/null; then
            log "✅ GitGuard API is ready!"
            break
        fi

        if [ $attempt -eq $max_attempts ]; then
            error "Services failed to start within expected time"
        fi

        echo -n "."
        sleep 5
        ((attempt++))
    done

    echo
}

show_access_info() {
    log "GitGuard Demo is ready! 🚀"

    echo -e "${CYAN}"
    cat << EOF

╔══════════════════════════════════════════════════════════════╗
║                     🎯 ACCESS INFORMATION                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📊 GitGuard Dashboard:  http://localhost:$PORT                ║
║  📈 Grafana Monitoring:  http://localhost:$GRAFANA_PORT                ║
║  🔍 Prometheus Metrics:  http://localhost:9090              ║
║  ⏰ Temporal Web UI:     http://localhost:8088              ║
║  🛡️  OPA Policy Server:   http://localhost:8181              ║
║                                                              ║
║  📚 API Documentation:   http://localhost:$PORT/docs          ║
║  🔍 Health Check:        http://localhost:$PORT/health        ║
║  📊 Metrics Endpoint:    http://localhost:$PORT/metrics       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

EOF
    echo -e "${NC}"

    # Show credentials
    echo -e "${YELLOW}📋 Demo Credentials:${NC}"
    echo -e "  Grafana Admin: admin / $(grep GRAFANA_ADMIN_PASSWORD .env.demo | cut -d'=' -f2)"
    echo -e "  PostgreSQL: gitguard / $(grep POSTGRES_PASSWORD .env.demo | cut -d'=' -f2)"
    echo

    # Show quick commands
    echo -e "${BLUE}🚀 Quick Commands:${NC}"
    echo -e "  View logs:           $COMPOSE_CMD -f docker-compose.demo.yml logs -f"
    echo -e "  Stop services:       $COMPOSE_CMD -f docker-compose.demo.yml down"
    echo -e "  Restart services:    $COMPOSE_CMD -f docker-compose.demo.yml restart"
    echo -e "  Clean up:            $COMPOSE_CMD -f docker-compose.demo.yml down -v"
    echo

    # Show demo scenarios
    echo -e "${GREEN}🎭 Demo Scenarios:${NC}"
    echo -e "  1. Visit the dashboard to see policy evaluations"
    echo -e "  2. Check Grafana for real-time monitoring"
    echo -e "  3. Explore the API documentation"
    echo -e "  4. View Temporal workflows in action"
    echo -e "  5. Test policy decisions with sample data"
    echo
}

cleanup() {
    log "Cleaning up previous demo installation..."

    if [ -f "docker-compose.demo.yml" ]; then
        $COMPOSE_CMD -f docker-compose.demo.yml down -v 2>/dev/null || true
    fi

    # Remove demo files
    rm -f .env.demo docker-compose.demo.yml
    rm -rf scripts/demo-data.sql

    log "✅ Cleanup completed"
}

show_help() {
    cat << EOF
GitGuard Quick Deploy Script

Usage: $0 [OPTIONS]

Options:
  -h, --help              Show this help message
  -v, --version VERSION   Specify GitGuard version (default: latest)
  -p, --port PORT         Specify GitGuard port (default: 8080)
  -g, --grafana-port PORT Specify Grafana port (default: 3000)
  -m, --method METHOD     Deployment method (docker-compose, kubernetes)
  -c, --cleanup           Clean up existing demo installation
  --no-demo               Disable demo mode

Environment Variables:
  GITGUARD_VERSION        GitGuard version to deploy
  DEPLOY_METHOD           Deployment method
  DEMO_MODE               Enable/disable demo mode
  PORT                    GitGuard API port
  GRAFANA_PORT            Grafana dashboard port

Examples:
  $0                      # Deploy with defaults
  $0 -v v0.1.0           # Deploy specific version
  $0 -p 9000 -g 4000     # Custom ports
  $0 --cleanup           # Clean up demo

EOF
}

# Main execution
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                GITGUARD_VERSION="$2"
                shift 2
                ;;
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            -g|--grafana-port)
                GRAFANA_PORT="$2"
                shift 2
                ;;
            -m|--method)
                DEPLOY_METHOD="$2"
                shift 2
                ;;
            -c|--cleanup)
                cleanup
                exit 0
                ;;
            --no-demo)
                DEMO_MODE="false"
                shift
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done

    print_banner

    log "Starting GitGuard Quick Deploy..."
    log "Version: $GITGUARD_VERSION"
    log "Method: $DEPLOY_METHOD"
    log "Demo Mode: $DEMO_MODE"
    log "Port: $PORT"

    check_dependencies
    generate_demo_config
    generate_docker_compose

    if [[ "$DEMO_MODE" == "true" ]]; then
        generate_demo_data
    fi

    start_services
    show_access_info

    log "🎉 GitGuard demo deployment completed successfully!"
    log "Visit http://localhost:$PORT to get started"
}

# Handle script interruption
trap 'error "Script interrupted"' INT TERM

# Run main function
main "$@"
