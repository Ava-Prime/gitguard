# Reload Prometheus configuration and verify alerts
# PowerShell version for Windows

Write-Host "🔄 Reloading Prometheus configuration..." -ForegroundColor Yellow

try {
    # Reload Prometheus config via API
    Invoke-RestMethod -Uri "http://localhost:9090/-/reload" -Method Post -ErrorAction Stop
    Write-Host "✅ Prometheus configuration reloaded successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to reload Prometheus configuration: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "📊 Checking alert rules..." -ForegroundColor Yellow

# Wait a moment for reload to complete
Start-Sleep -Seconds 2

try {
    # Check if alerts are loaded
    $rules = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/rules" -ErrorAction Stop
    $codexGroup = $rules.data.groups | Where-Object { $_.name -eq "codex" }

    if ($codexGroup) {
        Write-Host "✅ Codex alerts are loaded and active" -ForegroundColor Green
        Write-Host "📋 Found alerts:" -ForegroundColor Cyan
        foreach ($rule in $codexGroup.rules) {
            Write-Host "  - $($rule.name): $($rule.state)" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️  Codex alert group not found" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  Could not verify alert status: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 SLO Targets:" -ForegroundColor Cyan
Write-Host "  - Freshness: 99% PR events → page within 3m" -ForegroundColor White
Write-Host "  - Completeness: 95% PRs have ≥1 touches edge within 2m" -ForegroundColor White
Write-Host ""
Write-Host "📋 Alert Summary:" -ForegroundColor Cyan
Write-Host "  - CodexBuildStall: P95 publish_portal > 60s for 10m (severity: page)" -ForegroundColor White
Write-Host "  - CodexEventErrors: >5 failed events in 5m (severity: page)" -ForegroundColor White
Write-Host "  - JetStreamConsumerLag: CODEX consumer backlog >10m (severity: ticket)" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Prometheus UI: http://localhost:9090" -ForegroundColor Blue
Write-Host "🔗 Grafana UI: http://localhost:3000 (admin/gitguard)" -ForegroundColor Blue
