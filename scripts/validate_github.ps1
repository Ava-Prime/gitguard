#!/usr/bin/env pwsh
# GitGuard GitHub Workflow Validation Script
# Validates the GitHub workflow configuration for PR comments

Write-Host "🔍 Validating GitHub workflow configuration..." -ForegroundColor Cyan

$workflowPath = ".github/workflows/codex-docs.yml"
$allChecksPass = $true

# Check if workflow file exists
if (Test-Path $workflowPath) {
    Write-Host "✅ codex-docs.yml workflow found" -ForegroundColor Green

    $workflowContent = Get-Content $workflowPath -Raw

    # Check for PR trigger
    if ($workflowContent -match "pull_request:") {
        Write-Host "✅ PR trigger configured" -ForegroundColor Green
    } else {
        Write-Host "❌ PR trigger missing" -ForegroundColor Red
        $allChecksPass = $false
    }

    # Check for PR comment action
    if ($workflowContent -match "thollander/actions-comment-pull-request") {
        Write-Host "✅ PR comment action configured" -ForegroundColor Green
    } else {
        Write-Host "❌ PR comment action missing" -ForegroundColor Red
        $allChecksPass = $false
    }

    # Check for CODEX_BASE_URL variable
    if ($workflowContent -match "CODEX_BASE_URL") {
        Write-Host "✅ CODEX_BASE_URL variable referenced" -ForegroundColor Green
        Write-Host "⚠️  Remember to set CODEX_BASE_URL in repository variables" -ForegroundColor Yellow
    } else {
        Write-Host "❌ CODEX_BASE_URL variable missing" -ForegroundColor Red
        $allChecksPass = $false
    }

    # Check for comment job
    if ($workflowContent -match "comment:") {
        Write-Host "✅ Comment job configured" -ForegroundColor Green
    } else {
        Write-Host "❌ Comment job missing" -ForegroundColor Red
        $allChecksPass = $false
    }

    # Check for proper permissions
    if ($workflowContent -match "pull-requests: write") {
        Write-Host "✅ Pull request write permissions configured" -ForegroundColor Green
    } else {
        Write-Host "❌ Pull request write permissions missing" -ForegroundColor Red
        $allChecksPass = $false
    }

} else {
    Write-Host "❌ codex-docs.yml workflow not found" -ForegroundColor Red
    $allChecksPass = $false
}

Write-Host ""
Write-Host "📖 See docs/GITHUB_INTEGRATION.md for setup instructions" -ForegroundColor Blue

if ($allChecksPass) {
    Write-Host "🎉 All GitHub workflow checks passed!" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Set CODEX_BASE_URL in your repository variables" -ForegroundColor White
    Write-Host "2. Create a PR targeting the 'docs' branch to test" -ForegroundColor White
    Write-Host "3. Verify the comment appears with the correct preview link" -ForegroundColor White
} else {
    Write-Host "❌ Some GitHub workflow checks failed" -ForegroundColor Red
    Write-Host "Please review the errors above and update your workflow configuration" -ForegroundColor Yellow
    exit 1
}
