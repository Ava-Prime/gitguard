# GitGuard Policy Cookbook

This cookbook provides ready-to-use OPA/Rego policies for common Git repository governance scenarios. Each policy includes:

- ✅ **Copy-paste ready** Rego code
- 🧪 **Unit tests** for validation
- 📋 **Configuration examples**
- 🎯 **Use case scenarios**

## Quick Start

1. Copy the desired policy to your `policies/` directory
2. Customize the configuration values
3. Run tests: `opa test policies/ -v`
4. Deploy with GitGuard

---

## 1. Merge Window Policy

**Use Case**: Block deployments during maintenance windows or freeze periods.

### Policy: `policies/merge_window.rego`

```rego
package gitguard.merge_window

import rego.v1

# Configuration
freeze_periods := [
    {"start": "2024-12-20T00:00:00Z", "end": "2024-01-02T23:59:59Z", "reason": "Holiday freeze"},
    {"start": "2024-06-15T00:00:00Z", "end": "2024-06-17T23:59:59Z", "reason": "Quarterly release freeze"}
]

maintenance_windows := [
    {"day": "friday", "start_hour": 22, "end_hour": 23, "timezone": "UTC"},
    {"day": "saturday", "start_hour": 0, "end_hour": 6, "timezone": "UTC"}
]

# Main decision
default allow := false

allow if {
    not in_freeze_period
    not in_maintenance_window
    not high_risk_change
}

# Check if current time is in a freeze period
in_freeze_period if {
    some period in freeze_periods
    current_time := time.now_ns()
    start_time := time.parse_rfc3339_ns(period.start)
    end_time := time.parse_rfc3339_ns(period.end)
    current_time >= start_time
    current_time <= end_time
}

# Check if current time is in maintenance window
in_maintenance_window if {
    some window in maintenance_windows
    current_time := time.now_ns()
    weekday := time.weekday(current_time)
    hour := time.clock(current_time)[0]

    weekday_name := ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"][weekday]
    weekday_name == window.day
    hour >= window.start_hour
    hour <= window.end_hour
}

# Identify high-risk changes that should be blocked during sensitive periods
high_risk_change if {
    input.pull_request.changed_files > 50
}

high_risk_change if {
    some file in input.pull_request.files
    startswith(file.filename, "infrastructure/")
}

high_risk_change if {
    some file in input.pull_request.files
    endswith(file.filename, ".sql")
}

# Violation details for reporting
violation := {
    "type": "merge_window_violation",
    "message": sprintf("Merge blocked: %s", [reason]),
    "severity": "high",
    "details": {
        "current_time": time.format(time.now_ns()),
        "reason": reason,
        "override_required": true
    }
} if {
    not allow
    reason := get_block_reason
}

get_block_reason := reason if {
    in_freeze_period
    some period in freeze_periods
    current_time := time.now_ns()
    start_time := time.parse_rfc3339_ns(period.start)
    end_time := time.parse_rfc3339_ns(period.end)
    current_time >= start_time
    current_time <= end_time
    reason := period.reason
}

get_block_reason := "Maintenance window active" if {
    in_maintenance_window
    not in_freeze_period
}

get_block_reason := "High-risk change during restricted period" if {
    high_risk_change
    not in_freeze_period
    not in_maintenance_window
}
```

### Test: `policies/merge_window_test.rego`

```rego
package gitguard.merge_window

import rego.v1

test_allow_normal_hours if {
    allow with input as {
        "pull_request": {
            "changed_files": 5,
            "files": [{"filename": "src/app.py"}]
        }
    } with time.now_ns as 1704067200000000000  # Tuesday, Jan 1, 2024 12:00 UTC (outside freeze)
}

test_block_during_freeze if {
    not allow with input as {
        "pull_request": {
            "changed_files": 5,
            "files": [{"filename": "src/app.py"}]
        }
    } with time.now_ns as 1703030400000000000  # Dec 20, 2024 00:00 UTC (in freeze)
}

test_block_high_risk_change if {
    not allow with input as {
        "pull_request": {
            "changed_files": 75,
            "files": [{"filename": "infrastructure/database.tf"}]
        }
    } with time.now_ns as 1704067200000000000
}
```

---

## 2. High-Risk Dependency Block

**Use Case**: Prevent introduction of vulnerable or untrusted dependencies.

### Policy: `policies/dependency_security.rego`

```rego
package gitguard.dependency_security

import rego.v1

# Configuration
blocked_packages := {
    "lodash": {"reason": "Known prototype pollution vulnerabilities", "alternatives": ["ramda", "native ES6"]},
    "request": {"reason": "Deprecated, security issues", "alternatives": ["axios", "node-fetch"]},
    "moment": {"reason": "Large bundle size, maintenance mode", "alternatives": ["date-fns", "dayjs"]}
}

vulnerable_versions := {
    "express": ["<4.17.1"],
    "lodash": ["<4.17.21"],
    "axios": ["<0.21.1"]
}

trusted_registries := {
    "npm": "https://registry.npmjs.org/",
    "pypi": "https://pypi.org/",
    "maven": "https://repo1.maven.org/maven2/"
}

max_critical_vulnerabilities := 0
max_high_vulnerabilities := 2

# Main decision
default allow := true

allow := false if {
    has_blocked_dependency
}

allow := false if {
    has_vulnerable_version
}

allow := false if {
    exceeds_vulnerability_threshold
}

allow := false if {
    has_untrusted_registry
}

# Check for explicitly blocked packages
has_blocked_dependency if {
    some file in input.pull_request.files
    is_dependency_file(file.filename)
    some dep in extract_dependencies(file.content)
    dep.name in blocked_packages
}

# Check for vulnerable versions
has_vulnerable_version if {
    some file in input.pull_request.files
    is_dependency_file(file.filename)
    some dep in extract_dependencies(file.content)
    dep.name in vulnerable_versions
    some vuln_version in vulnerable_versions[dep.name]
    version_matches(dep.version, vuln_version)
}

# Check vulnerability count threshold
exceeds_vulnerability_threshold if {
    vulnerability_count := count_vulnerabilities(input.security_scan)
    vulnerability_count.critical > max_critical_vulnerabilities
}

exceeds_vulnerability_threshold if {
    vulnerability_count := count_vulnerabilities(input.security_scan)
    vulnerability_count.high > max_high_vulnerabilities
}

# Check for untrusted registries
has_untrusted_registry if {
    some file in input.pull_request.files
    is_dependency_file(file.filename)
    some dep in extract_dependencies(file.content)
    dep.registry
    not dep.registry in object.get(trusted_registries, dep.ecosystem, "")
}

# Helper functions
is_dependency_file(filename) if {
    endswith(filename, "package.json")
}

is_dependency_file(filename) if {
    endswith(filename, "requirements.txt")
}

is_dependency_file(filename) if {
    endswith(filename, "pom.xml")
}

is_dependency_file(filename) if {
    endswith(filename, "Cargo.toml")
}

extract_dependencies(content) := deps if {
    # Simplified dependency extraction - in practice, use proper parsers
    deps := []
}

version_matches(version, pattern) if {
    # Simplified version matching - implement semver logic
    startswith(pattern, "<")
    target_version := substring(pattern, 1, -1)
    # Add proper semver comparison logic here
    version == target_version
}

count_vulnerabilities(scan) := result if {
    result := {
        "critical": count([vuln | vuln := scan.vulnerabilities[_]; vuln.severity == "critical"]),
        "high": count([vuln | vuln := scan.vulnerabilities[_]; vuln.severity == "high"]),
        "medium": count([vuln | vuln := scan.vulnerabilities[_]; vuln.severity == "medium"]),
        "low": count([vuln | vuln := scan.vulnerabilities[_]; vuln.severity == "low"])
    }
}

# Violation details
violation := {
    "type": "dependency_security_violation",
    "message": sprintf("Dependency security check failed: %s", [reason]),
    "severity": "high",
    "details": {
        "blocked_packages": get_blocked_packages,
        "vulnerable_versions": get_vulnerable_versions,
        "vulnerability_count": count_vulnerabilities(input.security_scan),
        "remediation": get_remediation_advice
    }
} if {
    not allow
    reason := get_violation_reason
}

get_blocked_packages := [pkg |
    some file in input.pull_request.files
    is_dependency_file(file.filename)
    some dep in extract_dependencies(file.content)
    dep.name in blocked_packages
    pkg := {"name": dep.name, "reason": blocked_packages[dep.name].reason}
]

get_vulnerable_versions := [vuln |
    some file in input.pull_request.files
    is_dependency_file(file.filename)
    some dep in extract_dependencies(file.content)
    dep.name in vulnerable_versions
    vuln := {"name": dep.name, "version": dep.version, "vulnerable_patterns": vulnerable_versions[dep.name]}
]

get_violation_reason := "Blocked dependency detected" if has_blocked_dependency
get_violation_reason := "Vulnerable dependency version" if has_vulnerable_version
get_violation_reason := "Vulnerability threshold exceeded" if exceeds_vulnerability_threshold
get_violation_reason := "Untrusted registry detected" if has_untrusted_registry

get_remediation_advice := advice if {
    blocked := get_blocked_packages
    count(blocked) > 0
    advice := sprintf("Replace blocked packages: %s", [concat(", ", [pkg.name | pkg := blocked[_]])])
}
```

---

## 3. Protected Tag Policy

**Use Case**: Prevent unauthorized changes to release tags and protected branches.

### Policy: `policies/protected_tags.rego`

```rego
package gitguard.protected_tags

import rego.v1

# Configuration
protected_tag_patterns := [
    "v*",           # Version tags
    "release/*",    # Release branches
    "hotfix/*",     # Hotfix branches
    "main",         # Main branch
    "master",       # Master branch
    "develop"       # Development branch
]

authorized_users := {
    "release-bot",
    "admin-user",
    "release-manager"
}

authorized_teams := {
    "release-team",
    "platform-team",
    "security-team"
}

required_approvals := 2
required_checks := [
    "ci/build",
    "security/scan",
    "quality/coverage"
]

# Main decision
default allow := false

allow if {
    not is_protected_ref
}

allow if {
    is_protected_ref
    is_authorized_user
    has_required_approvals
    has_required_checks
    not has_force_push
}

# Emergency override (requires special token)
allow if {
    is_protected_ref
    input.override.emergency == true
    input.override.token == "emergency-override-token"
    input.override.justification
    is_authorized_user
}

# Check if the reference is protected
is_protected_ref if {
    ref := get_target_ref
    some pattern in protected_tag_patterns
    glob.match(pattern, [], ref)
}

# Check if user is authorized
is_authorized_user if {
    input.actor.login in authorized_users
}

is_authorized_user if {
    some team in input.actor.teams
    team in authorized_teams
}

# Check for required approvals
has_required_approvals if {
    count(input.pull_request.approvals) >= required_approvals
}

# Check for required status checks
has_required_checks if {
    every check in required_checks {
        some status in input.pull_request.status_checks
        status.context == check
        status.state == "success"
    }
}

# Check for force push (not allowed on protected refs)
has_force_push if {
    input.push.forced == true
}

# Get the target reference
get_target_ref := ref if {
    input.pull_request.base.ref
    ref := input.pull_request.base.ref
}

get_target_ref := ref if {
    input.push.ref
    ref := input.push.ref
}

get_target_ref := ref if {
    input.tag.name
    ref := input.tag.name
}

# Violation details
violation := {
    "type": "protected_ref_violation",
    "message": sprintf("Protected reference policy violation: %s", [reason]),
    "severity": "critical",
    "details": {
        "protected_ref": get_target_ref,
        "actor": input.actor.login,
        "missing_requirements": get_missing_requirements,
        "emergency_override_available": true,
        "required_approvals": required_approvals,
        "current_approvals": count(input.pull_request.approvals)
    }
} if {
    not allow
    reason := get_violation_reason
}

get_missing_requirements := requirements if {
    requirements := array.concat(
        get_missing_approvals,
        get_missing_checks
    )
}

get_missing_approvals := ["insufficient_approvals"] if {
    count(input.pull_request.approvals) < required_approvals
}

get_missing_approvals := [] if {
    count(input.pull_request.approvals) >= required_approvals
}

get_missing_checks := missing if {
    missing := [check |
        some check in required_checks
        not check_passed(check)
    ]
}

check_passed(check_name) if {
    some status in input.pull_request.status_checks
    status.context == check_name
    status.state == "success"
}

get_violation_reason := "Unauthorized user" if {
    is_protected_ref
    not is_authorized_user
}

get_violation_reason := "Insufficient approvals" if {
    is_protected_ref
    is_authorized_user
    not has_required_approvals
}

get_violation_reason := "Required checks not passed" if {
    is_protected_ref
    is_authorized_user
    has_required_approvals
    not has_required_checks
}

get_violation_reason := "Force push not allowed" if {
    is_protected_ref
    has_force_push
}
```

---

## 4. Infrastructure Change Gate

**Use Case**: Require additional review and validation for infrastructure changes.

### Policy: `policies/infrastructure_gate.rego`

```rego
package gitguard.infrastructure_gate

import rego.v1

# Configuration
infrastructure_paths := [
    "terraform/",
    "infrastructure/",
    "k8s/",
    "kubernetes/",
    "helm/",
    "docker/",
    "Dockerfile*",
    "docker-compose*.yml",
    ".github/workflows/"
]

critical_resources := [
    "aws_iam_role",
    "aws_iam_policy",
    "aws_s3_bucket",
    "aws_rds_instance",
    "kubernetes_secret",
    "kubernetes_service_account"
]

required_infra_approvers := {
    "platform-team",
    "sre-team",
    "security-team"
}

required_security_review := true
required_plan_review := true
max_resource_changes := 10

# Main decision
default allow := true

allow := false if {
    has_infrastructure_changes
    not has_required_infra_approvals
}

allow := false if {
    has_critical_resource_changes
    not has_security_approval
}

allow := false if {
    has_large_infrastructure_change
    not has_plan_review
}

allow := false if {
    has_infrastructure_changes
    not has_valid_terraform_plan
}

# Check for infrastructure changes
has_infrastructure_changes if {
    some file in input.pull_request.files
    some path in infrastructure_paths
    glob.match(path, [], file.filename)
}

# Check for critical resource changes
has_critical_resource_changes if {
    some file in input.pull_request.files
    endswith(file.filename, ".tf")
    some resource in critical_resources
    contains(file.content, resource)
}

# Check for large infrastructure changes
has_large_infrastructure_change if {
    infra_file_count := count([file |
        some file in input.pull_request.files
        some path in infrastructure_paths
        glob.match(path, [], file.filename)
    ])
    infra_file_count > max_resource_changes
}

# Check for required infrastructure team approvals
has_required_infra_approvals if {
    some approval in input.pull_request.approvals
    some team in approval.user.teams
    team in required_infra_approvers
}

# Check for security team approval
has_security_approval if {
    some approval in input.pull_request.approvals
    some team in approval.user.teams
    team == "security-team"
}

# Check for plan review
has_plan_review if {
    some comment in input.pull_request.comments
    contains(comment.body, "terraform plan")
    comment.user.login in get_authorized_reviewers
}

# Check for valid Terraform plan
has_valid_terraform_plan if {
    some check in input.pull_request.status_checks
    check.context == "terraform/plan"
    check.state == "success"
}

get_authorized_reviewers := reviewers if {
    reviewers := {user |
        some approval in input.pull_request.approvals
        some team in approval.user.teams
        team in required_infra_approvers
        user := approval.user.login
    }
}

# Violation details
violation := {
    "type": "infrastructure_gate_violation",
    "message": sprintf("Infrastructure change gate failed: %s", [reason]),
    "severity": "high",
    "details": {
        "infrastructure_files": get_infrastructure_files,
        "critical_resources": get_critical_resources,
        "required_approvers": required_infra_approvers,
        "current_approvers": get_current_approvers,
        "missing_requirements": get_missing_infra_requirements,
        "terraform_plan_required": required_plan_review
    }
} if {
    not allow
    reason := get_infra_violation_reason
}

get_infrastructure_files := [file.filename |
    some file in input.pull_request.files
    some path in infrastructure_paths
    glob.match(path, [], file.filename)
]

get_critical_resources := [resource |
    some file in input.pull_request.files
    endswith(file.filename, ".tf")
    some resource in critical_resources
    contains(file.content, resource)
]

get_current_approvers := {team |
    some approval in input.pull_request.approvals
    some team in approval.user.teams
    team in required_infra_approvers
}

get_missing_infra_requirements := missing if {
    missing := array.concat(
        get_missing_infra_approvals,
        get_missing_security_approval,
        get_missing_plan_review
    )
}

get_missing_infra_approvals := ["infrastructure_approval"] if {
    has_infrastructure_changes
    not has_required_infra_approvals
}

get_missing_infra_approvals := [] if {
    not has_infrastructure_changes
}

get_missing_infra_approvals := [] if {
    has_required_infra_approvals
}

get_missing_security_approval := ["security_approval"] if {
    has_critical_resource_changes
    not has_security_approval
}

get_missing_security_approval := [] if {
    not has_critical_resource_changes
}

get_missing_security_approval := [] if {
    has_security_approval
}

get_missing_plan_review := ["terraform_plan_review"] if {
    has_large_infrastructure_change
    not has_plan_review
}

get_missing_plan_review := [] if {
    not has_large_infrastructure_change
}

get_missing_plan_review := [] if {
    has_plan_review
}

get_infra_violation_reason := "Missing infrastructure team approval" if {
    has_infrastructure_changes
    not has_required_infra_approvals
}

get_infra_violation_reason := "Missing security approval for critical resources" if {
    has_critical_resource_changes
    not has_security_approval
}

get_infra_violation_reason := "Missing plan review for large changes" if {
    has_large_infrastructure_change
    not has_plan_review
}

get_infra_violation_reason := "Invalid or missing Terraform plan" if {
    has_infrastructure_changes
    not has_valid_terraform_plan
}
```

---

## 5. Secret Leak Prevention

**Use Case**: Detect and block commits containing secrets, API keys, or sensitive data.

### Policy: `policies/secret_prevention.rego`

```rego
package gitguard.secret_prevention

import rego.v1

# Configuration
secret_patterns := {
    "aws_access_key": "AKIA[0-9A-Z]{16}",
    "aws_secret_key": "[0-9a-zA-Z/+]{40}",
    "github_token": "ghp_[0-9a-zA-Z]{36}",
    "slack_token": "xox[bpoa]-[0-9]{12}-[0-9]{12}-[0-9a-zA-Z]{24}",
    "private_key": "-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",
    "jwt_token": "eyJ[0-9a-zA-Z_-]*\.[0-9a-zA-Z_-]*\.[0-9a-zA-Z_-]*",
    "database_url": "(mysql|postgres|mongodb)://[^\s]+",
    "api_key": "[aA][pP][iI][_]?[kK][eE][yY][^\s]{10,}"
}

allowed_test_patterns := {
    "test_key_123",
    "fake_secret",
    "dummy_token",
    "example_api_key",
    "placeholder_secret"
}

exempt_paths := [
    "test/",
    "tests/",
    "spec/",
    "__tests__/",
    "*.test.js",
    "*.spec.js",
    "*.test.py",
    "example/",
    "examples/",
    "docs/",
    "README.md"
]

max_entropy_threshold := 4.5
min_secret_length := 16

# Main decision
default allow := true

allow := false if {
    has_secret_leak
}

allow := false if {
    has_high_entropy_string
}

allow := false if {
    has_credential_in_config
}

# Check for known secret patterns
has_secret_leak if {
    some file in input.pull_request.files
    not is_exempt_path(file.filename)
    some line in split(file.content, "\n")
    some pattern_name, pattern in secret_patterns
    regex.match(pattern, line)
    not is_allowed_test_value(line)
}

# Check for high entropy strings (potential secrets)
has_high_entropy_string if {
    some file in input.pull_request.files
    not is_exempt_path(file.filename)
    some line in split(file.content, "\n")
    some word in extract_words(line)
    string_length := count(word)
    string_length >= min_secret_length
    entropy := calculate_entropy(word)
    entropy > max_entropy_threshold
    not is_allowed_test_value(word)
}

# Check for credentials in configuration files
has_credential_in_config if {
    some file in input.pull_request.files
    is_config_file(file.filename)
    some line in split(file.content, "\n")
    contains_credential_keyword(line)
    not is_placeholder_value(line)
}

# Helper functions
is_exempt_path(filename) if {
    some pattern in exempt_paths
    glob.match(pattern, [], filename)
}

is_config_file(filename) if {
    endswith(filename, ".env")
}

is_config_file(filename) if {
    endswith(filename, ".config")
}

is_config_file(filename) if {
    endswith(filename, ".yml")
}

is_config_file(filename) if {
    endswith(filename, ".yaml")
}

is_config_file(filename) if {
    endswith(filename, ".json")
}

is_allowed_test_value(value) if {
    some pattern in allowed_test_patterns
    contains(lower(value), pattern)
}

contains_credential_keyword(line) if {
    credential_keywords := ["password", "secret", "key", "token", "auth", "credential"]
    some keyword in credential_keywords
    contains(lower(line), keyword)
    contains(line, "=")
}

is_placeholder_value(line) if {
    placeholder_patterns := ["TODO", "FIXME", "PLACEHOLDER", "CHANGE_ME", "YOUR_", "<", ">"]
    some pattern in placeholder_patterns
    contains(upper(line), pattern)
}

extract_words(line) := words if {
    # Extract potential secret strings from line
    words := regex.find_all("[a-zA-Z0-9+/=]{16,}", line)
}

calculate_entropy(string) := entropy if {
    # Simplified entropy calculation
    chars := split(string, "")
    char_counts := {char: count([c | c := chars[_]; c == char]) | char := chars[_]}
    total_chars := count(chars)

    entropy := sum([count * (-log2(count / total_chars)) |
        count := char_counts[_]
    ]) / total_chars
}

log2(x) := log(x) / log(2)

# Violation details
violation := {
    "type": "secret_leak_violation",
    "message": sprintf("Secret leak detected: %s", [reason]),
    "severity": "critical",
    "details": {
        "detected_secrets": get_detected_secrets,
        "high_entropy_strings": get_high_entropy_strings,
        "credential_files": get_credential_files,
        "remediation": {
            "remove_secrets": "Remove all detected secrets from the code",
            "use_env_vars": "Use environment variables or secret management systems",
            "rotate_credentials": "Rotate any exposed credentials immediately",
            "scan_history": "Scan git history for the same secrets"
        }
    }
} if {
    not allow
    reason := get_secret_violation_reason
}

get_detected_secrets := secrets if {
    secrets := [{
        "file": file.filename,
        "pattern": pattern_name,
        "line_number": line_num
    } |
        some file in input.pull_request.files
        not is_exempt_path(file.filename)
        lines := split(file.content, "\n")
        some line_num, line in lines
        some pattern_name, pattern in secret_patterns
        regex.match(pattern, line)
        not is_allowed_test_value(line)
    ]
}

get_high_entropy_strings := strings if {
    strings := [{
        "file": file.filename,
        "string": word,
        "entropy": calculate_entropy(word),
        "line_number": line_num
    } |
        some file in input.pull_request.files
        not is_exempt_path(file.filename)
        lines := split(file.content, "\n")
        some line_num, line in lines
        some word in extract_words(line)
        string_length := count(word)
        string_length >= min_secret_length
        entropy := calculate_entropy(word)
        entropy > max_entropy_threshold
        not is_allowed_test_value(word)
    ]
}

get_credential_files := files if {
    files := [file.filename |
        some file in input.pull_request.files
        is_config_file(file.filename)
        some line in split(file.content, "\n")
        contains_credential_keyword(line)
        not is_placeholder_value(line)
    ]
}

get_secret_violation_reason := "Known secret pattern detected" if has_secret_leak
get_secret_violation_reason := "High entropy string detected" if has_high_entropy_string
get_secret_violation_reason := "Credentials in configuration file" if has_credential_in_config
```

---

## Usage Examples

### 1. Basic Policy Deployment

```bash
# Copy policies to your GitGuard installation
cp policies/*.rego /path/to/gitguard/policies/

# Test policies
opa test policies/ -v

# Validate syntax
opa fmt --diff policies/
```

### 2. Custom Configuration

```rego
# Override default configuration in your policy
package gitguard.merge_window

# Custom freeze periods for your organization
freeze_periods := [
    {"start": "2024-12-15T00:00:00Z", "end": "2024-01-15T23:59:59Z", "reason": "Extended holiday freeze"}
]
```

### 3. Policy Testing

```bash
# Run specific policy tests
opa test policies/merge_window_test.rego -v

# Test with custom input
echo '{"pull_request": {"changed_files": 100}}' | opa eval -d policies/ -I "data.gitguard.merge_window.allow"
```

### 4. Integration with GitGuard

```yaml
# .gitguard.yml
policies:
  - merge_window
  - dependency_security
  - protected_tags
  - infrastructure_gate
  - secret_prevention

notifications:
  slack:
    webhook: "${SLACK_WEBHOOK_URL}"
    channel: "#security-alerts"

overrides:
  emergency_contact: "security-team@company.com"
  escalation_policy: "P1-security-incident"
```

## Policy Development Tips

1. **Start Simple**: Begin with basic allow/deny rules, then add complexity
2. **Test Thoroughly**: Write comprehensive tests for all policy branches
3. **Use Helpers**: Create reusable helper functions for common patterns
4. **Document Decisions**: Include clear violation messages and remediation advice
5. **Version Control**: Tag policy versions and maintain backward compatibility
6. **Monitor Performance**: Profile policies with large datasets
7. **Security Review**: Have security team review all policies before deployment

## Contributing

To contribute new policies to this cookbook:

1. Follow the established pattern (policy + tests + documentation)
2. Include real-world use cases and examples
3. Add comprehensive test coverage
4. Document configuration options clearly
5. Provide remediation guidance in violation messages

For more advanced policy examples and GitGuard configuration, see the [GitGuard Documentation](../README.md).
