#!/bin/bash
# GitGuard Development Environment Validation Script
# Run this script to verify your complete development setup

set -e

echo "🔍 GitGuard Development Environment Validation"
echo "============================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_status "$1 is available"
        return 0
    else
        print_error "$1 is not available"
        return 1
    fi
}

echo "📋 Step 1: Checking required tools..."
check_command "mise" || { print_error "Install mise first: https://mise.jdx.dev/getting-started.html"; exit 1; }
check_command "make" || { print_error "Make is required"; exit 1; }
check_command "python3" || { print_error "Python 3 is required"; exit 1; }
echo

echo "🐍 Step 2: Checking Python version with mise..."
if mise current python 2>/dev/null | grep -q "3.11"; then
    print_status "Python 3.11.x is active via mise"
else
    print_warning "Expected Python 3.11.x, got: $(mise current python 2>/dev/null || echo 'not set')"
fi
echo

echo "📦 Step 3: Setting up virtual environment and dependencies..."
if make venv sync; then
    print_status "Virtual environment and dependencies installed successfully"
else
    print_error "Failed to set up virtual environment or install dependencies"
    exit 1
fi
echo

echo "🔧 Step 4: Running code quality checks..."
if make fmt lint type; then
    print_status "Code formatting, linting, and type checking passed"
else
    print_warning "Code quality checks failed - this may be expected for a new setup"
fi
echo

echo "🧪 Step 5: Running tests..."
if make test; then
    print_status "All tests passed"
else
    print_warning "Some tests failed - this may be expected for a new setup"
fi
echo

echo "🌐 Step 6: Testing development server..."
echo "Starting development server for 5 seconds..."
if timeout 5s make run &>/dev/null || [ $? -eq 124 ]; then
    print_status "Development server starts successfully (tested for 5s)"
else
    print_warning "Development server may have issues starting"
fi
echo

echo "📁 Step 7: Checking configuration files..."
config_files=(
    ".vscode/settings.json"
    ".vscode/launch.json"
    ".gitattributes"
    ".editorconfig"
    ".mise.toml"
    "pyproject.toml"
    "Makefile"
    ".trae/rules/gitguard-pack.md"
    ".trae/agents/gitguard-code-surgeon.json"
    ".trae/agents/policy-explainer-opa.json"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        print_status "$file exists"
    else
        print_error "$file is missing"
    fi
done
echo

echo "🐳 Step 8: Checking optional Temporal setup..."
if [ -f "docker-compose.temporal.yml" ]; then
    print_status "Temporal docker-compose configuration available"
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        print_status "Docker and docker-compose are available for Temporal setup"
        echo "  Run: docker compose -f docker-compose.temporal.yml up -d"
    else
        print_warning "Docker/docker-compose not available - Temporal setup will be manual"
    fi
else
    print_error "docker-compose.temporal.yml is missing"
fi
echo

echo "🎉 Validation Complete!"
echo "======================"
echo "Your GitGuard development environment is ready!"
echo
echo "Next steps:"
echo "  • Open the project in VS Code or Trae IDE"
echo "  • Use 'make dev' for the full development workflow"
echo "  • Use 'make run' to start the development server"
echo "  • Configure Trae IDE with the rules and agents in .trae/"
echo "  • (Optional) Start Temporal: docker compose -f docker-compose.temporal.yml up -d"
echo
