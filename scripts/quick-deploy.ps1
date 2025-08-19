# GitGuard Quick Deploy Script for Windows
# Enables instant deployment and demo experience for external users

param(
    [string]$Version = "latest",
    [string]$Method = "docker-compose",
    [int]$Port = 8080,
    [int]$GrafanaPort = 3000,
    [switch]$Cleanup,
    [switch]$NoDemo,
    [switch]$Help
)

# Configuration
$GitGuardVersion = if ($env:GITGUARD_VERSION) { $env:GITGUARD_VERSION } else { $Version }
$DeployMethod = if ($env:DEPLOY_METHOD) { $env:DEPLOY_METHOD } else { $Method }
$DemoMode = if ($env:DEMO_MODE) { $env:DEMO_MODE } else { if ($NoDemo) { "false" } else { "true" } }
$GitGuardPort = if ($env:PORT) { $env:PORT } else { $Port }
$GrafanaPortValue = if ($env:GRAFANA_PORT) { $env:GRAFANA_PORT } else { $GrafanaPort }

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    Magenta = "Magenta"
    Cyan = "Cyan"
}

function Write-Banner {
    Write-Host @"
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
"@ -ForegroundColor Magenta
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] WARNING: $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Test-Dependencies {
    Write-Log "Checking dependencies..."

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is required but not installed. Please install Docker Desktop first."
    }

    if ($DeployMethod -eq "docker-compose") {
        if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
            # Try docker compose (newer syntax)
            try {
                docker compose version | Out-Null
                $script:ComposeCmd = "docker compose"
            }
            catch {
                Write-Error "Docker Compose is required but not installed."
            }
        }
        else {
            $script:ComposeCmd = "docker-compose"
        }
    }

    Write-Log "✅ Dependencies check passed"
}

function New-DemoConfig {
    Write-Log "Generating demo configuration..."

    # Generate random passwords
    $postgresPassword = "demo_password_" + (-join ((1..8) | ForEach-Object { [char]((97..122) + (48..57) | Get-Random) }))
    $redisPassword = "demo_redis_" + (-join ((1..8) | ForEach-Object { [char]((97..122) + (48..57) | Get-Random) }))
    $grafanaPassword = "demo_grafana_" + (-join ((1..8) | ForEach-Object { [char]((97..122) + (48..57) | Get-Random) }))
    $encryptionKey = -join ((1..64) | ForEach-Object { [char]((97..102) + (48..57) | Get-Random) })
    $jwtSecret = -join ((1..64) | ForEach-Object { [char]((97..102) + (48..57) | Get-Random) })

    $envContent = @"
# GitGuard Demo Configuration
ENVIRONMENT=demo
LOG_LEVEL=info
DEBUG=true
METRICS_ENABLED=true

# Ports
GITGUARD_PORT=$GitGuardPort
GRAFANA_PORT=$GrafanaPortValue
PROMETHEUS_PORT=9090
REDIS_PORT=6379
POSTGRES_PORT=5432

# Database
POSTGRES_DB=gitguard_demo
POSTGRES_USER=gitguard
POSTGRES_PASSWORD=$postgresPassword

# Redis
REDIS_PASSWORD=$redisPassword

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
GRAFANA_ADMIN_PASSWORD=$grafanaPassword
PROMETHEUS_RETENTION=7d

# Security (Demo only - use proper secrets in production)
ENCRYPTION_KEY=$encryptionKey
JWT_SECRET=$jwtSecret
"@

    $envContent | Out-File -FilePath ".env.demo" -Encoding UTF8

    Write-Log "✅ Demo configuration generated"
}

function New-DockerCompose {
    Write-Log "Generating Docker Compose configuration..."

    $composeContent = @'
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
'@

    $composeContent | Out-File -FilePath "docker-compose.demo.yml" -Encoding UTF8

    Write-Log "✅ Docker Compose configuration generated"
}

function New-DemoData {
    Write-Log "Generating demo data..."

    if (-not (Test-Path "scripts")) {
        New-Item -ItemType Directory -Path "scripts" | Out-Null
    }

    $demoDataContent = @'
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
'@

    $demoDataContent | Out-File -FilePath "scripts\demo-data.sql" -Encoding UTF8

    Write-Log "✅ Demo data generated"
}

function Start-Services {
    Write-Log "Starting GitGuard services..."

    # Start services
    Invoke-Expression "$ComposeCmd -f docker-compose.demo.yml up -d"

    Write-Log "⏳ Waiting for services to be ready..."

    # Wait for services to be healthy
    $maxAttempts = 60
    $attempt = 1

    while ($attempt -le $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$GitGuardPort/health" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Log "✅ GitGuard API is ready!"
                break
            }
        }
        catch {
            # Service not ready yet
        }

        if ($attempt -eq $maxAttempts) {
            Write-Error "Services failed to start within expected time"
        }

        Write-Host "." -NoNewline
        Start-Sleep -Seconds 5
        $attempt++
    }

    Write-Host ""
}

function Show-AccessInfo {
    Write-Log "GitGuard Demo is ready! 🚀"

    Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                     🎯 ACCESS INFORMATION                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📊 GitGuard Dashboard:  http://localhost:$GitGuardPort                ║
║  📈 Grafana Monitoring:  http://localhost:$GrafanaPortValue                ║
║  🔍 Prometheus Metrics:  http://localhost:9090              ║
║  ⏰ Temporal Web UI:     http://localhost:8088              ║
║  🛡️  OPA Policy Server:   http://localhost:8181              ║
║                                                              ║
║  📚 API Documentation:   http://localhost:$GitGuardPort/docs          ║
║  🔍 Health Check:        http://localhost:$GitGuardPort/health        ║
║  📊 Metrics Endpoint:    http://localhost:$GitGuardPort/metrics       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

    # Show credentials
    $envContent = Get-Content ".env.demo" -Raw
    $grafanaPassword = ($envContent | Select-String "GRAFANA_ADMIN_PASSWORD=(.+)").Matches[0].Groups[1].Value
    $postgresPassword = ($envContent | Select-String "POSTGRES_PASSWORD=(.+)").Matches[0].Groups[1].Value

    Write-Host "📋 Demo Credentials:" -ForegroundColor Yellow
    Write-Host "  Grafana Admin: admin / $grafanaPassword"
    Write-Host "  PostgreSQL: gitguard / $postgresPassword"
    Write-Host ""

    # Show quick commands
    Write-Host "🚀 Quick Commands:" -ForegroundColor Blue
    Write-Host "  View logs:           $ComposeCmd -f docker-compose.demo.yml logs -f"
    Write-Host "  Stop services:       $ComposeCmd -f docker-compose.demo.yml down"
    Write-Host "  Restart services:    $ComposeCmd -f docker-compose.demo.yml restart"
    Write-Host "  Clean up:            $ComposeCmd -f docker-compose.demo.yml down -v"
    Write-Host ""

    # Show demo scenarios
    Write-Host "🎭 Demo Scenarios:" -ForegroundColor Green
    Write-Host "  1. Visit the dashboard to see policy evaluations"
    Write-Host "  2. Check Grafana for real-time monitoring"
    Write-Host "  3. Explore the API documentation"
    Write-Host "  4. View Temporal workflows in action"
    Write-Host "  5. Test policy decisions with sample data"
    Write-Host ""
}

function Remove-Demo {
    Write-Log "Cleaning up previous demo installation..."

    if (Test-Path "docker-compose.demo.yml") {
        try {
            Invoke-Expression "$ComposeCmd -f docker-compose.demo.yml down -v" 2>$null
        }
        catch {
            # Ignore errors during cleanup
        }
    }

    # Remove demo files
    if (Test-Path ".env.demo") { Remove-Item ".env.demo" -Force }
    if (Test-Path "docker-compose.demo.yml") { Remove-Item "docker-compose.demo.yml" -Force }
    if (Test-Path "scripts\demo-data.sql") { Remove-Item "scripts\demo-data.sql" -Force }

    Write-Log "✅ Cleanup completed"
}

function Show-Help {
    Write-Host @"
GitGuard Quick Deploy Script for Windows

Usage: .\quick-deploy.ps1 [OPTIONS]

Options:
  -Help                   Show this help message
  -Version VERSION        Specify GitGuard version (default: latest)
  -Port PORT              Specify GitGuard port (default: 8080)
  -GrafanaPort PORT       Specify Grafana port (default: 3000)
  -Method METHOD          Deployment method (docker-compose, kubernetes)
  -Cleanup                Clean up existing demo installation
  -NoDemo                 Disable demo mode

Environment Variables:
  GITGUARD_VERSION        GitGuard version to deploy
  DEPLOY_METHOD           Deployment method
  DEMO_MODE               Enable/disable demo mode
  PORT                    GitGuard API port
  GRAFANA_PORT            Grafana dashboard port

Examples:
  .\quick-deploy.ps1                      # Deploy with defaults
  .\quick-deploy.ps1 -Version v0.1.0     # Deploy specific version
  .\quick-deploy.ps1 -Port 9000 -GrafanaPort 4000  # Custom ports
  .\quick-deploy.ps1 -Cleanup             # Clean up demo

"@
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

if ($Cleanup) {
    Remove-Demo
    exit 0
}

Write-Banner

Write-Log "Starting GitGuard Quick Deploy..."
Write-Log "Version: $GitGuardVersion"
Write-Log "Method: $DeployMethod"
Write-Log "Demo Mode: $DemoMode"
Write-Log "Port: $GitGuardPort"

Test-Dependencies
New-DemoConfig
New-DockerCompose

if ($DemoMode -eq "true") {
    New-DemoData
}

Start-Services
Show-AccessInfo

Write-Log "🎉 GitGuard demo deployment completed successfully!"
Write-Log "Visit http://localhost:$GitGuardPort to get started"
