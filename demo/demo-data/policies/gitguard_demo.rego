# GitGuard Demo Policies
# This file contains sample OPA policies for demonstrating GitGuard's capabilities

package gitguard.demo

import rego.v1

# Default deny for all actions
default allow := false

# Secret Detection Policy
secret_detection := {
    "enabled": true,
    "patterns": [
        "(?i)(api[_-]?key|apikey)\\s*[=:]\\s*['\"][a-zA-Z0-9]{20,}['\"]?",
        "(?i)(password|passwd|pwd)\\s*[=:]\\s*['\"][^'\"\\s]{8,}['\"]?",
        "(?i)(secret|token)\\s*[=:]\\s*['\"][a-zA-Z0-9]{16,}['\"]?",
        "(?i)(aws[_-]?access[_-]?key[_-]?id)\\s*[=:]\\s*['\"]?AKIA[0-9A-Z]{16}['\"]?",
        "(?i)(aws[_-]?secret[_-]?access[_-]?key)\\s*[=:]\\s*['\"][a-zA-Z0-9/+=]{40}['\"]?"
    ],
    "entropy_threshold": 4.5,
    "min_length": 12
}

# Vulnerability Scanning Policy
vulnerability_policy := {
    "enabled": true,
    "severity_thresholds": {
        "critical": "block",
        "high": "block",
        "medium": "warn",
        "low": "info"
    },
    "max_age_days": 30,
    "exclude_dev_dependencies": false
}

# License Compliance Policy
license_policy := {
    "enabled": true,
    "allowed_licenses": [
        "MIT",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "ISC",
        "Unlicense"
    ],
    "forbidden_licenses": [
        "GPL-2.0",
        "GPL-3.0",
        "AGPL-3.0",
        "LGPL-2.1",
        "LGPL-3.0"
    ],
    "require_license_file": true
}

# Code Quality Policy
code_quality_policy := {
    "enabled": true,
    "min_test_coverage": 80,
    "max_cyclomatic_complexity": 10,
    "max_function_length": 50,
    "max_file_length": 500,
    "require_docstrings": true
}

# Pull Request Policy
pr_policy := {
    "enabled": true,
    "require_reviews": 2,
    "require_security_review": true,
    "block_force_push": true,
    "require_up_to_date_branch": true,
    "require_status_checks": [
        "ci/tests",
        "security/scan",
        "quality/lint"
    ]
}

# Branch Protection Policy
branch_protection := {
    "enabled": true,
    "protected_branches": ["main", "master", "develop", "release/*"],
    "require_pull_request": true,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "restrict_pushes": true
}

# File Pattern Restrictions
file_restrictions := {
    "enabled": true,
    "forbidden_patterns": [
        "*.pem",
        "*.key",
        "*.p12",
        "*.pfx",
        "id_rsa*",
        ".env*",
        "*.backup",
        "*.dump"
    ],
    "max_file_size_mb": 100,
    "binary_file_extensions": [
        ".exe", ".dll", ".so", ".dylib",
        ".jar", ".war", ".ear",
        ".zip", ".tar", ".gz", ".rar"
    ]
}

# Demo-specific rules
allow if {
    input.action == "read"
    input.resource.type == "demo"
}

allow if {
    input.action == "scan"
    input.user.role in ["developer", "security_admin", "admin"]
}

allow if {
    input.action == "merge"
    input.pull_request.approved_by_security == true
    count(input.pull_request.violations) == 0
}

# Secret detection rule
secret_violation if {
    some pattern in secret_detection.patterns
    regex.match(pattern, input.file.content)
}

# Vulnerability assessment rule
vulnerability_violation if {
    some vuln in input.vulnerabilities
    vuln.severity in ["critical", "high"]
    vulnerability_policy.severity_thresholds[vuln.severity] == "block"
}

# License compliance rule
license_violation if {
    some license in input.dependencies[_].licenses
    license in license_policy.forbidden_licenses
}

# Code quality rule
quality_violation if {
    input.metrics.test_coverage < code_quality_policy.min_test_coverage
}

quality_violation if {
    input.metrics.cyclomatic_complexity > code_quality_policy.max_cyclomatic_complexity
}

# Branch protection rule
branch_protection_violation if {
    input.branch in branch_protection.protected_branches
    input.action == "push"
    not input.pull_request
}

# File restriction rule
file_restriction_violation if {
    some pattern in file_restrictions.forbidden_patterns
    glob.match(pattern, [], input.file.path)
}

# Aggregate policy decision
policy_decision := {
    "allow": allow,
    "violations": violations,
    "warnings": warnings,
    "metadata": {
        "policy_version": "demo-1.0",
        "evaluated_at": time.now_ns(),
        "rules_applied": applied_rules
    }
}

violations := [
    {"type": "secret", "message": "Secret detected in code"} |
    secret_violation
] ++ [
    {"type": "vulnerability", "message": "Critical vulnerability found"} |
    vulnerability_violation
] ++ [
    {"type": "license", "message": "Forbidden license detected"} |
    license_violation
] ++ [
    {"type": "branch_protection", "message": "Branch protection violated"} |
    branch_protection_violation
] ++ [
    {"type": "file_restriction", "message": "Forbidden file pattern"} |
    file_restriction_violation
]

warnings := [
    {"type": "quality", "message": "Code quality threshold not met"} |
    quality_violation
]

applied_rules := [
    "secret_detection",
    "vulnerability_policy",
    "license_policy",
    "code_quality_policy",
    "branch_protection",
    "file_restrictions"
]
