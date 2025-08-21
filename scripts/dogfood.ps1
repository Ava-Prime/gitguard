<#
.SYNOPSIS
Cross-platform friendly wrappers for self-dogfooding GitGuard on Windows.

.DESCRIPTION
This PowerShell script provides Windows-compatible equivalents to the Makefile targets
for setting up and managing GitGuard's self-dogfooding environment.

.PARAMETER cmd
The command to execute. Valid options:
- self-dogfood: Start the dogfooding stack
- status: Check service status and health
- stop: Stop all services and clean up
- dryrun: Toggle dry-run mode (on|off)
- killswitch: Manage bypass label (on|off)
- smoketest: Run basic connectivity tests
- replay-latest: Replay the latest workflow

.PARAMETER arg
Optional argument for commands that require it (e.g., 'on' or 'off' for dryrun/killswitch)

.EXAMPLE
.\scripts\dogfood.ps1 self-dogfood
Starts the GitGuard dogfooding environment

.EXAMPLE
.\scripts\dogfood.ps1 dryrun on
Enables dry-run mode

.EXAMPLE
.\scripts\dogfood.ps1 smoketest
Runs health checks on the running services
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('self-dogfood','status','stop','dryrun','killswitch','smoketest','replay-latest')]
    $cmd,
    [string]$arg
)

$ErrorActionPreference = "Stop"
$compose = "docker compose"
$envFile = ".env.dogfood"
$composeFile = "docker-compose.temporal.yml"

function Require($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "❌ $name is required. Please install it and retry."
    }
}

function Prereq {
    Write-Host "📋 Prerequisites check:"
    Require "docker"
    if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
        Write-Error "❌ Docker not found. Install Docker Desktop"
    }

    # Check if Docker is running
    try {
        docker ps | Out-Null
    } catch {
        Write-Error "❌ Docker is not running. Please start Docker Desktop"
    }

    Require "curl"
    Write-Host "✅ Prerequisites satisfied"
}

function GenEnv {
    if (-not (Test-Path $envFile)) {
        Write-Host "🔧 Creating $envFile file..."
        $timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        $secret = -join ((48..57)+(97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

        @"
# GitGuard Self-Dogfooding Configuration
# Generated on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

# GitHub App Configuration (REQUIRED - set these after creating your GitHub App)
GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY=
GITHUB_WEBHOOK_SECRET=$secret

# GitGuard Configuration
GITGUARD_MODE=report-only
GITGUARD_LOG_LEVEL=info
GITGUARD_WEBHOOK_PATH=/webhook/github
GITGUARD_DRY_RUN=true

# Database Configuration
POSTGRES_DB=gitguard
POSTGRES_USER=gitguard
POSTGRES_PASSWORD=gitguard-dev-$timestamp

# Temporal Configuration
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=gitguard

# Repository Configuration
GITHUB_REPO=Ava-Prime/gitguard
"@ | Out-File -Encoding UTF8 $envFile
        Write-Host "✅ Created $envFile"
    }
}

function ShowNextSteps {
    Write-Host ""
    Write-Host "🎉 GitGuard is now running in self-dogfood mode!"
    Write-Host ""
    Write-Host "📋 NEXT STEPS:"
    Write-Host "1. Create a GitHub App:"
    Write-Host "   • Go to: https://github.com/settings/apps/new"
    Write-Host "   • Click 'Create from manifest' and paste contents of app.json"
    Write-Host "   • After creation, click 'Install App' and select Ava-Prime/gitguard"
    Write-Host ""
    Write-Host "2. Configure your GitHub App secrets in $envFile:"
    Write-Host "   • GITHUB_APP_ID=<your-app-id>"
    Write-Host "   • GITHUB_APP_PRIVATE_KEY=<paste-your-private-key>"
    Write-Host "   • GITHUB_WEBHOOK_SECRET=<choose-a-random-string>"
    Write-Host ""
    Write-Host "3. Expose your local server to GitHub:"
    Write-Host "   • Install ngrok: https://ngrok.com/download"
    Write-Host "   • Run: ngrok http 8080"
    Write-Host "   • Set webhook URL to: https://<your-ngrok-url>/webhook/github"
    Write-Host ""
    Write-Host "4. Test the setup:"
    Write-Host "   • .\scripts\dogfood.ps1 status  # Check service health"
    Write-Host "   • Open http://localhost:8080  # GitGuard UI"
    Write-Host "   • Open http://localhost:8233  # Temporal Web UI"
    Write-Host ""
    Write-Host "🔗 Useful URLs:"
    Write-Host "   GitGuard API:     http://localhost:8080"
    Write-Host "   Temporal Web UI:  http://localhost:8233"
    Write-Host "   Health Check:     http://localhost:8080/health"
}

switch ($cmd) {
    'self-dogfood' {
        Write-Host "🐕 Setting up GitGuard self-dogfooding..."
        Prereq
        GenEnv
        Write-Host ""
        Write-Host "🚀 Starting GitGuard services..."
        & $compose -f $composeFile --env-file $envFile up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "⏳ Waiting for services to be ready..."
            Start-Sleep -Seconds 10
            ShowNextSteps
        } else {
            Write-Error "Failed to start services. Check Docker Desktop is running."
        }
    }

    'status' {
        Write-Host "🔍 GitGuard Self-Dogfood Status:"
        Write-Host ""
        Write-Host "📊 Docker Services:"
        try {
            & $compose -f $composeFile ps
        } catch {
            Write-Host "❌ Services not running. Run '.\scripts\dogfood.ps1 self-dogfood' first."
        }
        Write-Host ""
        Write-Host "🌐 Service Health Checks:"
        Write-Host -NoNewline "GitGuard API:     "
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Healthy" -ForegroundColor Green
            } else {
                Write-Host "❌ Unhealthy (Status: $($response.StatusCode))" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Not responding" -ForegroundColor Red
        }

        Write-Host -NoNewline "Temporal Web UI:  "
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8233" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Available" -ForegroundColor Green
            } else {
                Write-Host "❌ Unavailable (Status: $($response.StatusCode))" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Not responding" -ForegroundColor Red
        }
    }

    'stop' {
        Write-Host "🛑 Stopping GitGuard self-dogfood services..."
        & $compose -f $composeFile --env-file $envFile down -v
        Write-Host "✅ Services stopped and volumes cleaned"
    }

    'dryrun' {
        if (-not $arg -or ($arg -ne "on" -and $arg -ne "off")) {
            Write-Error "Usage: .\scripts\dogfood.ps1 dryrun [on|off]"
        }

        if (-not (Test-Path $envFile)) {
            Write-Error "$envFile not found. Run 'self-dogfood' first."
        }

        $dryRunValue = if ($arg -eq "on") { "true" } else { "false" }
        (Get-Content $envFile) -replace '^GITGUARD_DRY_RUN=.*', "GITGUARD_DRY_RUN=$dryRunValue" | Set-Content $envFile

        Write-Host "🔄 Restarting services with GITGUARD_DRY_RUN=$dryRunValue"
        & $compose -f $composeFile --env-file $envFile up -d
        Write-Host "✅ Dry-run mode set to $arg"
    }

    'killswitch' {
        if (-not $arg -or ($arg -ne "on" -and $arg -ne "off")) {
            Write-Error "Usage: .\scripts\dogfood.ps1 killswitch [on|off]"
        }

        if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
            Write-Host "⚠️  GitHub CLI not found. Install 'gh' for label management."
            Write-Host "   Download from: https://cli.github.com/"
            return
        }

        $repo = $env:GITHUB_REPO
        if (-not $repo -and (Test-Path $envFile)) {
            $repoLine = Select-String -Path $envFile -Pattern '^GITHUB_REPO=' -ErrorAction SilentlyContinue
            if ($repoLine) {
                $repo = $repoLine.Line.Split('=')[1]
            }
        }

        if (-not $repo) {
            Write-Error "Set GITHUB_REPO in $envFile or environment variable"
        }

        if ($arg -eq "on") {
            try {
                gh label create gitguard-bypass -R $repo -c FF0000 -d "Bypass GitGuard enforcement" -f 2>$null
                Write-Host "🔴 Killswitch label enabled for $repo"
            } catch {
                Write-Host "⚠️  Label may already exist or insufficient permissions"
            }
        } else {
            try {
                gh label delete gitguard-bypass -R $repo -y 2>$null
                Write-Host "✅ Killswitch label removed from $repo"
            } catch {
                Write-Host "⚠️  Label may not exist or insufficient permissions"
            }
        }
    }

    'smoketest' {
        Write-Host "🧪 Running GitGuard smoketest..."
        Prereq
        $base = "http://localhost:8080"

        Write-Host ""
        Write-Host "# Health Check"
        try {
            $health = Invoke-RestMethod -Uri "$base/health" -TimeoutSec 5
            Write-Host ($health | ConvertTo-Json -Depth 3)
        } catch {
            Write-Host "❌ Health check failed: $($_.Exception.Message)"
        }

        Write-Host ""
        Write-Host "# Ready Check"
        try {
            $ready = Invoke-RestMethod -Uri "$base/ready" -TimeoutSec 5
            Write-Host ($ready | ConvertTo-Json -Depth 3)
        } catch {
            Write-Host "❌ Ready check failed: $($_.Exception.Message)"
        }

        Write-Host ""
        Write-Host "# Metrics Sample"
        try {
            $metrics = Invoke-WebRequest -Uri "$base/metrics" -TimeoutSec 5 -UseBasicParsing
            $lines = $metrics.Content -split "`n" | Select-Object -First 10
            $lines | ForEach-Object { Write-Host $_ }
            Write-Host "... (truncated)"
        } catch {
            Write-Host "❌ Metrics check failed: $($_.Exception.Message)"
        }
    }

    'replay-latest' {
        Write-Host "🔄 Replaying latest workflow..."
        if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
            Write-Error "GitHub CLI required for workflow replay"
        }

        try {
            $latestRun = gh run list --limit 1 --json databaseId --jq '.[0].databaseId'
            if ($latestRun) {
                gh run rerun $latestRun
                Write-Host "✅ Replaying workflow run $latestRun"
            } else {
                Write-Host "❌ No workflow runs found"
            }
        } catch {
            Write-Error "Failed to replay workflow: $($_.Exception.Message)"
        }
    }

    default {
        Write-Error "Unknown command: $cmd"
    }
}
