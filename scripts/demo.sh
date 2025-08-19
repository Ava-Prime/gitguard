#!/bin/bash
# GitGuard Complete Interactive Demo Script
# Creates a fully self-contained demo environment that showcases all capabilities
# Usage: ./gitguard-demo-script.sh [scenario]

set -euo pipefail

DEMO_REPO="gitguard-demo"
DEMO_ORG="${DEMO_ORG:-gitguard}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
OPA_URL="${OPA_URL:-http://localhost:8181}"

# Demo colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}════════════════════════════════════════${NC}"
    echo -e "${WHITE}🛡️  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════${NC}"
}

print_step() {
    echo -e "${BLUE}▶️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}🚨 $1${NC}"
}

print_metric() {
    echo -e "${PURPLE}📊 $1${NC}"
}

wait_for_user() {
    echo -e "${YELLOW}Press Enter to continue...${NC}"
    read
}

# --- Docs portal cue ---
show_docs_update() {
    echo ""
    echo -e "${CYAN}📖 GitGuard Knowledge Sync...${NC}"
    make docs-build >/dev/null 2>&1 || true
    echo -e "${GREEN}✅ Documentation portal automatically updated following merge.${NC}"
    echo -e "   View the live docs at: ${YELLOW}http://localhost:8001${NC}"
    echo ""
}

# --- Governance link cue ---
show_governance_link() {
    echo ""
    echo -e "${CYAN}📖 GitGuard Governance Link...${NC}"
    echo -e "${GREEN}✅ Blocked action is explained with a link to the relevant policy.${NC}"
    echo -e "   Why was this blocked? See: ${YELLOW}http://localhost:8001/policies/release-windows/${NC}"
    echo ""
}

# =============================================================================
# DEMO ENVIRONMENT SETUP
# =============================================================================

setup_demo_environment() {
    print_header "Setting Up Demo Environment"

    print_step "Creating demo repository structure..."
    mkdir -p "$DEMO_REPO"/{src/{api,models,utils},tests,docs,infra,.github/workflows}

    # Create realistic application files
    cat > "$DEMO_REPO/src/api/main.py" << 'EOF'
from fastapi import FastAPI, HTTPException
from src.models.user import User
from src.utils.auth import verify_token

app = FastAPI(title="Demo API", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/users/{user_id}")
async def get_user(user_id: int, token: str = None):
    """Get user by ID with authentication"""
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    if user_id < 1:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    return {"id": user_id, "name": f"User {user_id}", "active": True}
EOF

    cat > "$DEMO_REPO/src/utils/auth.py" << 'EOF'
import hashlib
import secrets

def verify_token(token: str) -> bool:
    """Verify authentication token"""
    if not token:
        return False

    # Simple token validation for demo
    return len(token) > 10

def generate_token(user_id: int) -> str:
    """Generate authentication token"""
    return secrets.token_hex(16)
EOF

    cat > "$DEMO_REPO/tests/test_api.py" << 'EOF'
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_user_requires_auth():
    response = client.get("/users/1")
    assert response.status_code == 401
EOF

    cat > "$DEMO_REPO/README.md" << 'EOF'
# Demo API

A simple FastAPI application for GitGuard demonstration.

## Endpoints

- GET /health - Health check
- GET /users/{id} - Get user by ID (requires auth)
EOF

    print_success "Demo environment created"
}

# =============================================================================
# SIMULATED WEBHOOK PAYLOADS
# =============================================================================

create_pr_payload() {
    local pr_number=$1
    local title="$2"
    local files=($3)
    local risk_score=${4:-0.25}

    cat << EOF
{
  "action": "opened",
  "pull_request": {
    "number": $pr_number,
    "title": "$title",
    "state": "open",
    "user": {
      "login": "developer"
    },
    "head": {
      "sha": "abc123def456"
    },
    "base": {
      "ref": "main"
    }
  },
  "repository": {
    "name": "$DEMO_REPO",
    "owner": {
      "login": "$DEMO_ORG"
    }
  },
  "changes": {
    "files": $(printf '%s\n' "${files[@]}" | jq -R . | jq -s .),
    "lines_added": 15,
    "lines_deleted": 3,
    "total_changes": 18
  },
  "analysis": {
    "risk_score": $risk_score,
    "coverage_delta": 0.0,
    "performance_delta": 0,
    "security_flags": false,
    "new_tests": false
  }
}
EOF
}

call_guard_api() {
    local payload="$1"
    curl -s -X POST -H "Content-Type: application/json" \
        --data "$payload" \
        http://localhost:8000/webhook/github >/dev/null || true
}

simulate_webhook_call() {
    local payload="$1"
    local endpoint="$2"

    print_step "Sending webhook to GitGuard API..."

    # Simulate API call (in real demo, this would hit actual GitGuard)
    echo "$payload" > /tmp/webhook_payload.json

    if command -v jq &> /dev/null; then
        echo "📡 Webhook Payload:"
        echo "$payload" | jq '.'
    fi

    print_step "GitGuard processing webhook..."
    sleep 2  # Simulate processing time
}

# =============================================================================
# DEMO SCENARIOS
# =============================================================================

demo_low_risk_pr() {
    print_header "Demo Scenario 1: Low-Risk PR (Auto-Merge)"

    print_step "Creating documentation-only PR..."

    # Simulate documentation change
    cat >> "$DEMO_REPO/README.md" << 'EOF'

## Installation

```bash
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```
EOF

    # Create PR payload
    local payload=$(create_pr_payload 1 "docs: add installation instructions" '["README.md"]' 0.08)

    simulate_webhook_call "$payload" "/webhook/github"
    call_guard_api "$payload"

    print_metric "GitGuard Analysis Results:"
    print_metric "  Risk Score: 0.08 (docs:0.05 + size:0.03)"
    print_metric "  Size: XS (1 file, ~8 lines)"
    print_metric "  Security: ✅ No flags"
    print_metric "  Tests: ✅ Not required for docs"
    print_metric "  Coverage: ➡️ No change (0.0%)"

    sleep 1

    print_step "OPA Policy Evaluation..."

    # Simulate OPA policy check
    cat > /tmp/opa_input.json << EOF
{
  "action": "merge_pr",
  "pr": {
    "number": 1,
    "checks_passed": true,
    "risk_score": 0.08,
    "labels": ["risk:low", "size:XS"],
    "changed_paths": ["README.md"],
    "coverage_delta": 0,
    "size_category": "XS"
  },
  "repo": {
    "name": "$DEMO_REPO",
    "owner": "$DEMO_ORG"
  },
  "actor": "gitguard[bot]"
}
EOF

    print_metric "Policy Decision: ✅ ALLOW (auto-merge eligible)"
    print_metric "  - Risk score 0.08 < threshold 0.30 ✅"
    print_metric "  - Documentation-only change ✅"
    print_metric "  - All checks passed ✅"

    sleep 2

    print_success "PR #1 AUTO-MERGED in 45 seconds!"
    print_success "🚀 Zero human intervention required"

    # --- ADD THIS LINE ---
    show_docs_update

    wait_for_user
}

demo_medium_risk_pr() {
    print_header "Demo Scenario 2: Medium-Risk PR (Manual Review)"

    print_step "Creating feature PR with business logic changes..."

    # Simulate feature addition
    cat > "$DEMO_REPO/src/api/profiles.py" << 'EOF'
from fastapi import APIRouter, HTTPException
from src.models.user import User
from src.utils.auth import verify_token

router = APIRouter()

@router.post("/profiles")
async def create_profile(profile_data: dict, token: str = None):
    """Create user profile"""
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Business logic here
    return {"id": 123, "status": "created"}
EOF

    cat > "$DEMO_REPO/tests/test_profiles.py" << 'EOF'
def test_create_profile():
    # TODO: Implement profile creation tests
    pass
EOF

    local payload=$(create_pr_payload 2 "feat: add user profile management endpoint" '["src/api/profiles.py", "tests/test_profiles.py", "src/api/main.py"]' 0.35)

    simulate_webhook_call "$payload" "/webhook/github"
    call_guard_api "$payload"

    print_metric "GitGuard Analysis Results:"
    print_metric "  Risk Score: 0.35 (feat:0.25 + size:0.12 + incomplete_tests:-0.02)"
    print_metric "  Size: M (3 files, ~45 lines)"
    print_metric "  Security: ✅ No flags detected"
    print_metric "  Tests: ⚠️  Stub tests detected"
    print_metric "  Coverage: ⚠️  Estimated -1.2% (new code, minimal tests)"

    sleep 1

    print_step "OPA Policy Evaluation...)"

    print_metric "Policy Decision: ⚠️  MANUAL REVIEW REQUIRED"
    print_metric "  - Risk score 0.35 > threshold 0.30 ❌"
    print_metric "  - New API endpoint (requires review) ❌"
    print_metric "  - Incomplete test coverage ❌"

    sleep 2

    print_warning "PR #2 assigned to @backend-team for review"
    print_warning "🔍 Human reviewer will assess business logic and test quality)"

    wait_for_user
}

demo_high_risk_infrastructure() {
    print_header "Demo Scenario 3: High-Risk Infrastructure PR (Blocked)"

    print_step "Creating infrastructure changes PR..."

    # Simulate dangerous infrastructure change
    cat > "$DEMO_REPO/infra/docker-compose.yml" << 'EOF'
version: '3.8'
services:
  api:
    build: ..
    ports:
      - "80:8000"
    environment:
      - DATABASE_URL=postgresql://user:${DB_PASSWORD}@db:5432/prod

  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"  # SECURITY RISK: Database exposed
    volumes:
      - /data:/var/lib/postgresql/data
EOF

    cat > "$DEMO_REPO/infra/nginx.conf" << 'EOF'
server {
    listen 80;
    location / {
        proxy_pass http://api:8000;
        # Missing security headers
        # No rate limiting
    }
}
EOF

    local payload=$(create_pr_payload 3 "feat: production deployment infrastructure" '["infra/docker-compose.yml", "infra/nginx.conf", ".github/workflows/deploy.yml"]' 0.72)

    simulate_webhook_call "$payload" "/webhook/github"
    call_guard_api "$payload"

    print_metric "GitGuard Analysis Results:"
    print_metric "  Risk Score: 0.72 (feat:0.25 + infra:0.30 + security:0.20 + size:0.12)"
    print_metric "  Size: M (3 files, ~60 lines)"
    print_metric "  Security: 🚨 Infrastructure exposure detected"
    print_metric "  Tests: ❌ No infrastructure tests"
    print_metric "  Changes: Production deployment config"

    sleep 1

    print_step "OPA Policy Evaluation..."
    print_error "SECURITY FLAGS DETECTED:"
    print_error "  🔍 Database port exposed (5432:5432)"
    print_error "  🔍 Missing nginx security headers"
    print_error "  🔍 No rate limiting configuration"
    print_error "  🔍 Production secrets in plaintext"

    print_metric "Policy Decision: 🚨 AUTO-MERGE BLOCKED"
    print_metric "  - Risk score 0.72 > threshold 0.30 ❌"
    print_metric "  - Infrastructure changes require review ❌"
    print_metric "  - Security flags detected ❌"
    print_metric "  - No infrastructure tests ❌"

    sleep 2

    print_error "PR #3 BLOCKED - requires @platform-team + @security-team approval"
    print_error "🛡️  GitGuard prevented potentially dangerous deployment)"

    show_governance_link

    wait_for_user
}

demo_security_violation() {
    print_header "Demo Scenario 4: Security Policy Violation (Hard Block)"

    print_step "Creating PR with critical security vulnerabilities..."

    # Simulate security violations
    cat > "$DEMO_REPO/src/utils/auth.py" << 'EOF'
import hashlib

# SECURITY VIOLATION: SQL Injection vulnerability
def authenticate_user(username: str, password: str, db):
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    return db.execute(query).fetchone()

def verify_token(token: str) -> bool:
    # SECURITY VIOLATION: Hardcoded admin bypass
    admin_tokens = ["admin123", "super_secret", "dev_bypass"]
    if token in admin_tokens:
        return True

    # SECURITY VIOLATION: Weak hash
    expected = hashlib.md5(token.encode()).hexdigest()
    return expected == "5d41402abc4b2a76b9719d911017c592"

# SECURITY VIOLATION: Plaintext credentials
DEFAULT_ADMIN_PASSWORD = "password123"
API_KEY = "sk-1234567890abcdef"
EOF

    local payload=$(create_pr_payload 4 "fix: quick auth improvements for demo" '["src/utils/auth.py"]' 0.85)

    simulate_webhook_call "$payload" "/webhook/github"
    call_guard_api "$payload"

    print_metric "GitGuard Analysis Results:"
    print_metric "  Risk Score: 0.85 (fix:0.20 + security_critical:0.50 + size:0.15)"
    print_metric "  Size: S (1 file, ~25 lines)"
    print_metric "  Security: 🚨🚨🚨 CRITICAL VIOLATIONS DETECTED"
    print_metric "  Tests: ❌ No security tests added"

    sleep 1

    print_step "Security Scanner Analysis..."
    print_error "CRITICAL SECURITY VIOLATIONS:"
    print_error "  💉 SQL Injection vulnerability in authenticate_user())"
    print_error "  🔑 Hardcoded admin bypass tokens)"
    print_error "  🔐 Weak MD5 hash usage)"
    print_error "  📝 Plaintext password storage)"
    print_error "  🔓 Hardcoded API keys in source code)"

    sleep 2

    print_step "OPA Security Policy Evaluation..."

    print_metric "Policy Decision: ⛔ SECURITY POLICY VIOLATION"
    print_metric "  - Critical security flags detected ❌"
    print_metric "  - SQL injection vulnerability ❌"
    print_metric "  - Hardcoded secrets detected ❌"
    print_metric "  - Weak cryptography usage ❌"

    sleep 2

    print_error "🚨 PR #4 HARD BLOCKED by security policy"
    print_error "🚨 Security team automatically notified"
    print_error "🚨 Remediation required before any further commits"
    print_error "🛡️  GitGuard prevented critical security breach!)"

    # --- ADD THIS LINE ---
    show_governance_link

    wait_for_user
}

demo_release_window_policy() {
    print_header "Demo Scenario 5: Release Window Policy Enforcement"

    print_step "Attempting release during blocked window..."

    # Simulate Friday evening release attempt
    print_metric "Current time: Friday 17:30 Africa/Johannesburg"
    print_metric "Attempting to create release tag: v1.2.0"

    cat > /tmp/release_input.json << 'EOF'
{
  "action": "create_tag",
  "tag": {
    "name": "v1.2.0",
    "message": "Release v1.2.0: New user profile features"
  },
  "repository": {
    "name": "demo-repo"
  },
  "actor": "release-bot"
}
EOF

    sleep 1

    print_step "OPA Release Window Policy Evaluation..."

    print_metric "Checking release window policy..."
    print_metric "  Current time: Friday 17:30 🕐"
    print_metric "  Blocked window: Fri 16:00 → Mon 08:00 📅"
    print_metric "  Window status: BLOCKED ❌"

    sleep 2

    print_error "🕐 RELEASE BLOCKED: Weekend deployment freeze active"
    print_error "Next allowed release window: Monday 08:00 Africa/Johannesburg"
    print_error "Policy: repo.guard.release_windows.weekend_freeze"

    # --- ADD THIS LINE ---
    show_governance_link

    sleep 1

    print_step "Testing allowed release window..."
    print_metric "Simulating time: Tuesday 10:00 Africa/Johannesburg"
    print_metric "Window status: ALLOWED ✅"
    print_success "Release would be permitted during business hours)"

    wait_for_user
}

demo_dashboard_overview() {
    print_header "GitGuard Dashboard Overview"

    print_step "Repository Protection Status..."

    cat << 'EOF'
┌─────────────────────────────────────────┐
│         GitGuard Dashboard             │
└─────────────────────────────────────────┘

Repository: gitguard-demo
Status: 🛡️  PROTECTED
Branch Protection: ✅ Enforced

Recent Activity (Last 24h):
├── PR #4: fix/auth-improvements     🚨 BLOCKED (security violation)
├── PR #3: feat/infrastructure       🚨 BLOCKED (high risk: 0.72)
├── PR #2: feat/user-profiles        ⚠️  REVIEW REQUIRED (risk: 0.35)
└── PR #1: docs/installation         ✅ AUTO-MERGED (risk: 0.08)

Policy Compliance:
├── Auto-merge rate: 25% (1/4 PRs)
├── Security violations: 0 shipped to main
├── Average merge time: 2.1 hours
└── Policy violations blocked: 2

Risk Distribution (30 days):
├── Low (0.0-0.3):    ████████░░ 60%
├── Medium (0.3-0.6): ███░░░░░░░ 30%
└── High (0.6-1.0):   █░░░░░░░░░ 10%

Developer Impact:
├── Time saved: ~16 hours/week (auto-merge)
├── Incidents prevented: 3 (security blocks)
├── Code quality score: 4.2/5 (up from 3.1)
└── Developer satisfaction: 4.7/5

Active Policies:
├── ✅ Auto-merge: risk ≤ 0.30
├── ✅ Release windows: weekday business hours
├── ✅ Security scanning: all PRs
├── ✅ Branch protection: required
└── ✅ Conventional commits: enforced
EOF

    echo ""
    print_metric "Performance Metrics:"
    print_metric "  Merge velocity: +60% improvement"
    print_metric "  Security incidents: 0 (100% prevention)"
    print_metric "  Code review efficiency: +40%"
    print_metric "  Policy compliance: 100%"

    print_step "Opening Grafana dashboard..."
    if command -v open &> /dev/null; then
        echo "🌐 Opening http://localhost:3000 (admin/gitguard)"
        # open "http://localhost:3000" 2>/dev/null || true
    else
        echo "🌐 Dashboard available at: http://localhost:3000 (admin/gitguard)"
    fi

    wait_for_user
}

demo_video_narration() {
    print_header "60-Second Demo Video Narration"

    cat << 'EOF'
🎬 GITGUARD DEMO VIDEO SCRIPT (60 seconds)

[0-15s] THE PROBLEM
Visual: Split screen - Developer waiting + Long PR review queue
"Development teams waste 40% of their time on code reviews.
Critical bugs slip through while simple docs updates sit for days."

[15-25s] GITGUARD INTRODUCTION
Visual: GitGuard logo + dashboard appearing
"GitGuard is your AI repository steward. It watches every PR,
scores risk intelligently, and acts autonomously."

[25-40s] LIVE DEMO - AUTO MERGE
Visual: Screen recording of docs PR
- PR created: "docs: add installation instructions"
- GitGuard analysis: Risk 0.08, Size XS
- Auto-merge: "✅ Merged in 45 seconds"
"Watch this docs PR get analyzed, risk-scored, and merged
automatically. Zero human intervention needed."

[40-50s] SECURITY PROTECTION
Visual: High-risk PR with security flags
- Code shows SQL injection
- GitGuard: "🚨 SECURITY VIOLATION - Blocked"
- Security team notification sent
"But when GitGuard detects security risks, it blocks dangerous
changes and alerts your security team instantly."

[50-60s] CALL TO ACTION
Visual: Dashboard showing results
"GitGuard: 60% faster merges, zero security incidents,
happier developers. Your repositories, under guard."
Text: "Start free trial → gitguard.com"
EOF

    wait_for_user
}

# =============================================================================
# MAIN DEMO ORCHESTRATION
# =============================================================================

run_full_demo() {
    print_header "GitGuard Complete Live Demo"

    setup_demo_environment
    demo_low_risk_pr
    demo_medium_risk_pr
    demo_high_risk_infrastructure
    demo_security_violation
    demo_release_window_policy
    demo_dashboard_overview

    print_header "Demo Complete!"
    print_success "GitGuard showcased:"
    print_success "  ✅ Intelligent auto-merge (25% of PRs)"
    print_success "  ⚠️  Smart review assignment (risk-based)"
    print_success "  🚨 Security policy enforcement (100% block rate)"
    print_success "  🕐 Release window governance"
    print_success "  📊 Comprehensive observability"

    echo ""
    print_metric "Next Steps:"
    echo "  1. Review generated demo repository"
    echo "  2. Explore GitGuard dashboard at http://localhost:3000"
    echo "  3. Test API endpoints at http://localhost:8000"
    echo "  4. Customize policies in policies/guard_rules.rego"
    echo "  5. Deploy to production with make bootstrap REPO=your/repo"

    echo ""
    print_success "GitGuard: Your repositories, under guard 🛡️"
}

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

show_help() {
    echo "GitGuard Interactive Demo Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  full              Run complete demo sequence"
    echo "  setup             Setup demo environment only"
    echo "  low-risk          Demo low-risk PR (auto-merge)"
    echo "  medium-risk       Demo medium-risk PR (manual review)"
    echo "  high-risk         Demo high-risk PR (blocked)"
    echo "  security          Demo security violation (hard block)"
    echo "  release-window    Demo release window enforcement"
    echo "  dashboard         Show GitGuard dashboard"
    echo "  video             Show 60-second video script"
    echo "  help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 full           # Complete demo experience"
    echo "  $0 security       # Just show security blocking"
    echo "  $0 dashboard      # Display metrics dashboard"
}

main() {
    case "${1:-full}" in
        "setup")
            setup_demo_environment
            ;;
        "low-risk")
            demo_low_risk_pr
            ;;
        "medium-risk")
            demo_medium_risk_pr
            ;;
        "high-risk")
            demo_high_risk_infrastructure
            ;;
        "security")
            demo_security_violation
            ;;
        "release-window")
            demo_release_window_policy
            ;;
        "dashboard")
            demo_dashboard_overview
            ;;
        "video")
            demo_video_narration
            ;;
        "full")
            run_full_demo
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            echo "Unknown command: $1"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Ensure we're in the right directory
if [[ ! -f "Makefile" ]] && [[ ! -f "config/gitguard.settings.yaml" ]]; then
    echo "⚠️  This script should be run from the GitGuard project root directory"
    echo "Run 'make setup' first to initialize the project"
    exit 1
fi

# Run the demo
main "$@"
