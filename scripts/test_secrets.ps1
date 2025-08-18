#!/usr/bin/env pwsh
# Test secrets redaction functionality

Write-Host "🔐 Testing secrets hygiene..." -ForegroundColor Cyan

# Check if Python is available
if (Get-Command python -ErrorAction SilentlyContinue) {
    try {
        # Run the secrets redaction test
        python test_secrets_redaction.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Secrets hygiene tests completed successfully" -ForegroundColor Green
        } else {
            Write-Host "❌ Secrets hygiene tests failed" -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "❌ Error running secrets tests: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Python not found" -ForegroundColor Red
    Write-Host "📖 See docs/SECRETS_HYGIENE.md for setup instructions" -ForegroundColor Blue
    exit 1
}

Write-Host ""
Write-Host "📖 For more information, see docs/SECRETS_HYGIENE.md" -ForegroundColor Blue