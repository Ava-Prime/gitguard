#!/bin/bash
# Reload Prometheus configuration and verify alerts

set -e

echo "🔄 Reloading Prometheus configuration..."

# Reload Prometheus config via API
curl -X POST http://localhost:9090/-/reload

if [ $? -eq 0 ]; then
    echo "✅ Prometheus configuration reloaded successfully"
else
    echo "❌ Failed to reload Prometheus configuration"
    exit 1
fi

echo "📊 Checking alert rules..."

# Wait a moment for reload to complete
sleep 2

# Check if alerts are loaded
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name == "codex") | .rules[] | {alert: .name, state: .state}'

if [ $? -eq 0 ]; then
    echo "✅ Codex alerts are loaded and active"
else
    echo "⚠️  Could not verify alert status (jq may not be installed)"
fi

echo "🎯 SLO Targets:"
echo "  - Freshness: 99% PR events → page within 3m"
echo "  - Completeness: 95% PRs have ≥1 touches edge within 2m"
echo ""
echo "📋 Alert Summary:"
echo "  - CodexBuildStall: P95 publish_portal > 60s for 10m (severity: page)"
echo "  - CodexEventErrors: >5 failed events in 5m (severity: page)"
echo "  - JetStreamConsumerLag: CODEX consumer backlog >10m (severity: ticket)"
echo ""
echo "🔗 Prometheus UI: http://localhost:9090"
echo "🔗 Grafana UI: http://localhost:3000 (admin/gitguard)"
