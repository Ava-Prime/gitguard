package repo.guard

import rego.v1

# Default deny
default allow := false

# Input structure:
# {
#   "action": "merge_pr",
#   "pr": {
#     "number": 123,
#     "checks_passed": true,
#     "risk_score": 0.25,
#     "labels": ["risk:low", "area:api"],
#     "changed_paths": ["src/api.py", "tests/test_api.py"],
#     "coverage_delta": -0.1,
#     "perf_delta": 2.5,
#     "size_category": "M"
#   },
#   "repo": {
#     "name": "example-repo",
#     "owner": "example-org",
#     "perf_budget": 5
#   },
#   "actor": "gitguard[bot]"
# }

# Auto-merge allowed for low-risk PRs
allow if {
    input.action == "merge_pr"
    input.pr.checks_passed == true
    input.pr.risk_score <= 0.30
    not high_risk_area
    not exceeds_budgets
    automerge_approved
}

# High-risk areas that need human review
high_risk_area if {
    some path in input.pr.changed_paths
    startswith(path, "infra/")
    input.pr.risk_score > 0.20
}

high_risk_area if {
    some path in input.pr.changed_paths
    startswith(path, "security/")
}

# Budget violations with development phase considerations
exceeds_budgets if {
    input.pr.coverage_delta < coverage_delta_threshold
    not development_phase_exception
}

exceeds_budgets if input.pr.perf_delta > input.repo.perf_budget

# Dynamic coverage delta threshold based on development phase
coverage_delta_threshold := -0.5 if {
    input.pr.development_phase == "initial_dev"
}

coverage_delta_threshold := -0.2 if {
    input.pr.development_phase == "feature_dev"
}

coverage_delta_threshold := -0.1 if {
    input.pr.development_phase == "pre_production"
}

coverage_delta_threshold := -0.05 if {
    input.pr.development_phase == "production"
}

# Default threshold for backward compatibility
coverage_delta_threshold := -0.2

# Development phase exceptions for coverage requirements
development_phase_exception if {
    input.pr.development_phase in {"initial_dev", "feature_dev"}
    has_incomplete_test_markers
}

development_phase_exception if {
    input.pr.development_phase == "initial_dev"
    has_missing_opa_fixtures
}

development_phase_exception if {
    input.pr.development_phase in {"initial_dev", "feature_dev"}
    experimental_code_changes
}

# Check for incomplete test implementation markers
has_incomplete_test_markers if {
    some path in input.pr.changed_paths
    contains(path, "test_")
    input.pr.file_analysis[path].incomplete_markers > 0
}

# Check for missing OPA test fixtures
has_missing_opa_fixtures if {
    some path in input.pr.changed_paths
    endswith(path, ".rego")
    not endswith(path, "_test.rego")
    test_file := sprintf("%s_test.rego", [trim_suffix(path, ".rego")])
    not test_file in input.pr.changed_paths
    not file_exists(test_file)
}

# Check for experimental code changes
experimental_code_changes if {
    some path in input.pr.changed_paths
    path_indicates_experimental(path)
}

path_indicates_experimental(path) if {
    contains(path, "/experimental/")
}

path_indicates_experimental(path) if {
    contains(path, "/prototype/")
}

path_indicates_experimental(path) if {
    contains(path, "/draft/")
}

path_indicates_experimental(path) if {
    contains(path, "_experimental")
}

path_indicates_experimental(path) if {
    contains(path, "_draft")
}

# Helper function to check file existence (would be provided by CI)
file_exists(path) if {
    path in input.pr.existing_files
}

# Auto-merge approval signals with development phase considerations
automerge_approved if "automerge:allowed" in input.pr.labels

automerge_approved if {
    input.pr.size_category in {"XS", "S"}
    not requires_manual_review
}

automerge_approved if docs_only_change

automerge_approved if {
    input.pr.development_phase == "initial_dev"
    prototype_change_only
    "prototype:auto-merge" in input.pr.labels
}

# Require manual review for certain development phase transitions
requires_manual_review if {
    input.pr.development_phase == "pre_production"
    phase_transition_detected
}

requires_manual_review if {
    input.pr.development_phase == "production"
    has_coverage_regression
}

# Detect phase transitions (experimental → production paths)
phase_transition_detected if {
    some path in input.pr.changed_paths
    path_indicates_experimental(path)
    some prod_path in input.pr.changed_paths
    startswith(prod_path, "apps/guard-")
}

# Check for coverage regression in production code
has_coverage_regression if {
    input.pr.coverage_delta < -0.01
    some path in input.pr.changed_paths
    startswith(path, "apps/guard-")
    not path_indicates_experimental(path)
}

# Prototype-only changes
prototype_change_only if {
    count(input.pr.changed_paths) > 0
    every path in input.pr.changed_paths {
        path_indicates_experimental(path) or
        startswith(path, "docs/") or
        endswith(path, ".md")
    }
}

docs_only_change if {
    count(input.pr.changed_paths) > 0
    every path in input.pr.changed_paths {
        endswith(path, ".md") or
        startswith(path, "docs/") or
        path == "README.md"
    }
}

# Release window restrictions
deny_release if {
    input.action == "create_tag"
    in_blocked_window
}

in_blocked_window if {
    now := time.now_ns()
    tz := "Africa/Johannesburg"
    tod := time.clock(now, tz)
    dow := time.weekday(now, tz)

    # Friday 16:00 - Monday 08:00
    (dow == "Friday" and tod.hour >= 16) or
    (dow == "Saturday") or
    (dow == "Sunday") or
    (dow == "Monday" and tod.hour < 8)
}

# Infrastructure changes require platform team approval
deny[msg] {
    input.action == "merge_pr"
    some path in input.pr.changed_paths
    infra_path_pattern(path)
    not "owner-approved" in input.pr.labels
    not emergency_override_approved
    msg := "Infrastructure change requires @platform-team approval (owner-approved label)"
}

# Policy changes require security team approval
deny[msg] {
    input.action == "merge_pr"
    some path in input.pr.changed_paths
    startswith(path, "policies/")
    not "security-approved" in input.pr.labels
    not emergency_override_approved
    msg := "Policy change requires @security-team approval (security-approved label)"
}

# API changes require backend team security review
deny[msg] {
    input.action == "merge_pr"
    some path in input.pr.changed_paths
    startswith(path, "apps/guard-api/")
    not "api-security-reviewed" in input.pr.labels
    not emergency_override_approved
    msg := "API change requires @backend-team security review (api-security-reviewed label)"
}

# AI/ML changes require AI team security review
deny[msg] {
    input.action == "merge_pr"
    some path in input.pr.changed_paths
    startswith(path, "apps/guard-brain/")
    not "ai-security-reviewed" in input.pr.labels
    not emergency_override_approved
    msg := "AI/ML change requires @ai-team security review (ai-security-reviewed label)"
}

# Documentation changes require docs team approval
deny[msg] {
    input.action == "merge_pr"
    some path in input.pr.changed_paths
    docs_path_pattern(path)
    not "docs-approved" in input.pr.labels
    not emergency_override_approved
    not docs_only_change  # Allow auto-merge for docs-only changes
    msg := "Documentation change requires @docs-team approval (docs-approved label)"
}

# Helper functions for path matching
infra_path_pattern(path) {
    startswith(path, "infra/")
}

infra_path_pattern(path) {
    startswith(path, "ops/")
}

infra_path_pattern(path) {
    startswith(path, ".github/")
}

docs_path_pattern(path) {
    endswith(path, ".md")
}

docs_path_pattern(path) {
    startswith(path, "docs/")
}

# Emergency override with security approval
emergency_override_approved {
    "emergency-override" in input.pr.labels
    "security-approved" in input.pr.labels
}

# Dependency bumps must pin versions & pass SBOM scan
deny[msg] {
    input.action == "merge_pr"
    "dependencies" in input.pr.labels
    not input.pr.checks["sbom_ok"]  # set by CI after Trivy/Grype
    msg := "Dependencies changed without passing SBOM scan"
}

deny[msg] {
    input.action == "merge_pr"
    "dependencies" in input.pr.labels
    some f
    f := input.pr.changed_paths[_]
    endswith(f, "requirements.txt")
    input.pr.diff_unpinned_versions == true
    msg := "Unpinned versions in requirements.txt"
}

# Enhanced lockfile and dependency management policies
deny[msg] {
    input.action == "merge_pr"
    some path in input.pr.changed_paths
    is_lockfile(path)
    not has_corresponding_manifest_change(path)
    not "lockfile-only" in input.pr.labels
    msg := sprintf("Lockfile %s changed without corresponding manifest file update. Add 'lockfile-only' label if intentional.", [path])
}

deny[msg] {
    input.action == "merge_pr"
    some path in input.pr.changed_paths
    is_manifest_file(path)
    corresponding_lockfile := get_corresponding_lockfile(path)
    corresponding_lockfile != ""
    not corresponding_lockfile in input.pr.changed_paths
    not "manifest-only" in input.pr.labels
    msg := sprintf("Manifest file %s changed without updating lockfile %s. Add 'manifest-only' label if intentional.", [path, corresponding_lockfile])
}

deny[msg] {
    input.action == "merge_pr"
    some path in input.pr.changed_paths
    is_lockfile(path)
    input.pr.file_analysis[path].security_vulnerabilities > 0
    not "security-reviewed" in input.pr.labels
    msg := sprintf("Lockfile %s contains security vulnerabilities. Requires security team review.", [path])
}

# DCO (Developer Certificate of Origin) policy for main branch
deny[msg] {
    input.action == "merge_pr"
    input.pr.target_branch == "main"
    some commit in input.pr.commits
    not has_dco_signoff(commit)
    not "dco-exempt" in input.pr.labels
    msg := sprintf("Commit %s missing DCO sign-off (Signed-off-by line). All main branch commits must include DCO.", [commit.sha[:8]])
}

deny[msg] {
    input.action == "merge_pr"
    input.pr.target_branch == "main"
    some commit in input.pr.commits
    not is_commit_signed(commit)
    not "unsigned-commit-approved" in input.pr.labels
    not emergency_override_approved
    msg := sprintf("Commit %s is not cryptographically signed. Main branch requires signed commits.", [commit.sha[:8]])
}

# Helper functions for lockfile detection
is_lockfile(path) {
    lockfile_patterns := [
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "Pipfile.lock",
        "poetry.lock",
        "Gemfile.lock",
        "composer.lock",
        "go.sum",
        "Cargo.lock"
    ]
    some pattern in lockfile_patterns
    endswith(path, pattern)
}

is_manifest_file(path) {
    manifest_patterns := [
        "package.json",
        "Pipfile",
        "pyproject.toml",
        "requirements.txt",
        "Gemfile",
        "composer.json",
        "go.mod",
        "Cargo.toml"
    ]
    some pattern in manifest_patterns
    endswith(path, pattern)
}

get_corresponding_lockfile(manifest_path) := lockfile {
    endswith(manifest_path, "package.json")
    lockfile := replace(manifest_path, "package.json", "package-lock.json")
} else := lockfile {
    endswith(manifest_path, "package.json")
    lockfile := replace(manifest_path, "package.json", "yarn.lock")
} else := lockfile {
    endswith(manifest_path, "Pipfile")
    lockfile := replace(manifest_path, "Pipfile", "Pipfile.lock")
} else := lockfile {
    endswith(manifest_path, "pyproject.toml")
    lockfile := replace(manifest_path, "pyproject.toml", "poetry.lock")
} else := lockfile {
    endswith(manifest_path, "requirements.txt")
    lockfile := replace(manifest_path, "requirements.txt", "requirements.lock")
} else := lockfile {
    endswith(manifest_path, "Gemfile")
    lockfile := replace(manifest_path, "Gemfile", "Gemfile.lock")
} else := lockfile {
    endswith(manifest_path, "composer.json")
    lockfile := replace(manifest_path, "composer.json", "composer.lock")
} else := lockfile {
    endswith(manifest_path, "go.mod")
    lockfile := replace(manifest_path, "go.mod", "go.sum")
} else := lockfile {
    endswith(manifest_path, "Cargo.toml")
    lockfile := replace(manifest_path, "Cargo.toml", "Cargo.lock")
} else := ""

has_corresponding_manifest_change(lockfile_path) {
    some manifest_path in input.pr.changed_paths
    is_manifest_file(manifest_path)
    get_corresponding_lockfile(manifest_path) == lockfile_path
}

# DCO validation helpers
has_dco_signoff(commit) {
    contains(commit.message, "Signed-off-by:")
    regex.match(`Signed-off-by: .+ <.+@.+>`, commit.message)
}

is_commit_signed(commit) {
    commit.verification.verified == true
} else {
    commit.gpg_signature.verified == true
} else {
    "signed" in commit.labels
}
