# Coverage Gates and Test Requirements

This document explains GitGuard's dynamic coverage gate system that adapts requirements based on development phases and code maturity.

## Overview

GitGuard implements a flexible coverage gate system that:
- Adjusts coverage thresholds based on development phase
- Provides exceptions for incomplete test files and OPA fixtures
- Prevents false early-stage failures during initial development
- Maintains quality standards as code matures toward production

## Development Phases

### 1. Initial Development (`initial_dev`)
**Coverage Threshold:** 60%
**Coverage Delta Threshold:** -5.0%
**Policy Tests:** Relaxed enforcement

**Characteristics:**
- MVP/Prototype phase
- Experimental code and proof-of-concepts
- Incomplete test implementations allowed
- Missing OPA fixtures permitted
- Focus on core functionality

**Triggers:**
- Files in `/experimental/`, `/prototype/`, `/draft/` directories
- Files with `_experimental`, `_draft` suffixes
- High count of incomplete implementation markers (`TODO`, `FIXME`, `XXX`, `HACK`)
- Missing test files for source code
- Missing OPA test fixtures for policies

**Example:**
```python
# This would trigger initial_dev phase
def new_feature():
    # TODO: implement core logic
    pass  # placeholder
```

### 2. Feature Development (`feature_dev`)
**Coverage Threshold:** 70%
**Coverage Delta Threshold:** -2.0%
**Policy Tests:** Standard enforcement

**Characteristics:**
- Active development phase
- Most functionality should be tested
- Some incomplete implementations acceptable
- Standard development tolerance

**Triggers:**
- Regular source code changes
- Moderate incomplete implementation markers
- Some missing test coverage

### 3. Pre-Production (`pre_production`)
**Coverage Threshold:** 80%
**Coverage Delta Threshold:** -1.0%
**Policy Tests:** Strict enforcement

**Characteristics:**
- Stabilization phase
- All critical paths must be tested
- Manual review required for phase transitions
- High coverage standards

**Triggers:**
- Production-ready code paths (`apps/guard-*`)
- Comprehensive test coverage
- Minimal incomplete markers
- Phase transitions from experimental to production

### 4. Production (`production`)
**Coverage Threshold:** 85%
**Coverage Delta Threshold:** -0.5%
**Policy Tests:** Strict enforcement

**Characteristics:**
- Production-ready code
- Comprehensive testing required
- Very strict coverage regression limits
- Manual review for any coverage drops

**Triggers:**
- Established production code
- Complete test suites
- No incomplete implementation markers
- Maintenance and bug fixes

## Coverage Gate Detection

The system automatically detects the appropriate development phase using:

### File Pattern Analysis
```bash
# Initial development patterns
.*/(experimental|prototype|draft|poc)/.*
.*/test_.*_draft\.py$
.*/.*_experimental\.py$

# Production patterns
.*/apps/guard-(api|brain|codex|ci)/.*\.py$
.*/policies/.*\.rego$
.*/ops/.*\.(yml|yaml)$
```

### Content Analysis
- **Incomplete markers:** `TODO: implement`, `FIXME:`, `XXX:`, `HACK:`, `pass # placeholder`
- **Test completeness:** Presence of `@pytest.mark`, `def test_`, `assert` statements
- **Documentation:** Comprehensive docstrings and comments

### Missing Dependencies
- **Test files:** Source files without corresponding test files
- **OPA fixtures:** Policy files (`.rego`) without test files (`_test.rego`)

## Exception Rules

### Development Phase Exceptions

Coverage requirements are relaxed when:

1. **Incomplete Test Markers** (initial_dev, feature_dev)
   ```python
   def test_new_feature():
       # TODO: implement comprehensive tests
       pass  # placeholder
   ```

2. **Missing OPA Fixtures** (initial_dev only)
   ```rego
   # policies/new_rule.rego exists
   # policies/new_rule_test.rego missing - exception granted
   ```

3. **Experimental Code Changes** (initial_dev, feature_dev)
   ```
   src/experimental/new_algorithm.py
   apps/prototype/service_draft.py
   ```

### Auto-merge Conditions

**Standard Auto-merge:**
- `automerge:allowed` label
- Small changes (XS, S) without manual review requirements
- Documentation-only changes

**Development Phase Auto-merge:**
- Initial development with `prototype:auto-merge` label
- Prototype-only changes (experimental paths + docs)

**Manual Review Required:**
- Phase transitions (experimental → production)
- Coverage regression in production code
- Pre-production phase changes

## CI Integration

### Workflow Steps

1. **Coverage Gate Detection**
   ```bash
   python scripts/coverage_gate_detector.py \
     --changed-files="$CHANGED_FILES" \
     --output-format=env
   ```

2. **Dynamic Test Execution**
   ```bash
   pytest \
     --cov-fail-under=$COVERAGE_THRESHOLD \
     -m 'not (incomplete_fixtures or requires_full_implementation)' \
     -v
   ```

3. **Coverage Delta Validation**
   ```bash
   python scripts/validate_coverage_delta.py \
     --threshold=$COVERAGE_DELTA_THRESHOLD \
     --base-ref=${{ github.event.pull_request.base.sha }}
   ```

### Environment Variables

The CI workflow sets these variables based on phase detection:

```bash
COVERAGE_THRESHOLD=70           # Dynamic threshold
COVERAGE_DELTA_THRESHOLD=-2.0   # Allowed coverage drop
DEVELOPMENT_PHASE=feature_dev   # Detected phase
ENFORCE_POLICY_TESTS=true       # OPA test enforcement
REQUIRE_OPA_FIXTURES=false      # OPA fixture requirement
ALLOW_INCOMPLETE_TESTS=true     # Incomplete test tolerance
```

## Policy Integration

### OPA Policy Rules

The guard policies (`policies/guard_rules.rego`) implement:

```rego
# Dynamic coverage thresholds
coverage_delta_threshold := -0.5 if {
    input.pr.development_phase == "initial_dev"
}

# Development phase exceptions
development_phase_exception if {
    input.pr.development_phase in {"initial_dev", "feature_dev"}
    has_incomplete_test_markers
}

# Budget violations with exceptions
exceeds_budgets if {
    input.pr.coverage_delta < coverage_delta_threshold
    not development_phase_exception
}
```

### Policy Input Structure

```json
{
  "pr": {
    "development_phase": "feature_dev",
    "coverage_delta": -1.5,
    "changed_paths": ["src/api.py", "test_api_draft.py"],
    "file_analysis": {
      "test_api_draft.py": {"incomplete_markers": 3}
    },
    "existing_files": ["policies/rule_test.rego"]
  }
}
```

## Best Practices

### For Developers

1. **Start with Prototypes**
   - Use `/experimental/` or `/prototype/` directories
   - Add `_draft` or `_experimental` suffixes
   - Include `prototype:auto-merge` label for quick iterations

2. **Progressive Test Development**
   ```python
   def test_new_feature():
       # TODO: implement edge case testing
       assert basic_functionality_works()
       # FIXME: add error handling tests
   ```

3. **Phase Transitions**
   - Move code from experimental to production paths gradually
   - Ensure comprehensive tests before production promotion
   - Remove incomplete markers as implementation matures

### For Reviewers

1. **Phase-Appropriate Reviews**
   - Focus on architecture and approach in initial_dev
   - Emphasize test coverage in pre_production
   - Strict quality gates in production

2. **Coverage Regression Analysis**
   - Review coverage delta reports
   - Understand phase-specific thresholds
   - Approve exceptions for legitimate experimental work

## Configuration Files

### pytest.ini
```ini
[tool:pytest]
markers =
    initial_dev: Initial development phase tests
    incomplete_fixtures: Tests with incomplete OPA fixtures
    requires_full_implementation: Tests requiring complete implementation
```

### .coveragerc
```ini
[run]
source = apps

[report]
# Phase-specific thresholds
fail_under = 80  # Default, overridden by CI

[html]
directory = htmlcov
```

## Troubleshooting

### Common Issues

1. **Unexpected Phase Detection**
   ```bash
   # Debug phase detection
   python scripts/coverage_gate_detector.py --changed-files="file1.py,file2.py"
   ```

2. **Coverage Delta Failures**
   ```bash
   # Validate coverage changes
   python scripts/validate_coverage_delta.py \
     --threshold=-2.0 --base-ref=main --head-ref=HEAD
   ```

3. **Policy Test Failures**
   ```bash
   # Test policy rules
   opa test policies/ -v
   ```

### Override Mechanisms

1. **Manual Phase Override**
   - Add `phase:initial_dev` label to PR
   - Use `coverage:ignore` for exceptional cases

2. **Emergency Bypasses**
   - `automerge:allowed` for critical fixes
   - `owner-approved` for infrastructure changes

## Monitoring and Metrics

### Coverage Trends
- Track coverage evolution across development phases
- Monitor phase transition success rates
- Identify patterns in coverage regression

### Policy Effectiveness
- Measure false positive rates by phase
- Track developer satisfaction with gate flexibility
- Monitor production quality outcomes

---

*This documentation is part of the GitGuard quality assurance system. For questions or suggestions, please open an issue or contact the development team.*
