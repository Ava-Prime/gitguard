#!/bin/bash
# GitGuard Bootstrap Script

set -euo pipefail

REPO=${1:-}
if [[ -z "$REPO" ]]; then
    echo "Usage: $0 <org/repo>"
    exit 1
fi

echo "🛡️  Bootstrapping GitGuard for $REPO"

# Install GitHub CLI if not present
if ! command -v gh &> /dev/null; then
    echo "Please install GitHub CLI: https://cli.github.com/"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "Please authenticate with GitHub CLI: gh auth login"
    exit 1
fi

echo "📋 Setting up branch protection..."
gh api -X PUT "repos/$REPO/branches/main/protection" \
  -H "Accept: application/vnd.github+json" \
  -f required_status_checks.strict=true \
  -f required_status_checks.contexts[]="GitGuard CI" \
  -f enforce_admins=true \
  -f required_pull_request_reviews.required_approving_review_count=1 \
  -f required_linear_history=true \
  -f allow_force_pushes=false \
  -f allow_deletions=false

echo "🔐 Requiring signed commits..."
gh api -X PUT "repos/$REPO/branches/main/protection/required_signatures" || true

echo "🏷️  Setting up labels..."
python scripts/sync_labels.py "$REPO"

echo "✅ GitGuard bootstrap complete for $REPO"
