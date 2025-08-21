# GitGuard Risk Scoring Algorithm

GitGuard uses a transparent, multi-factor risk assessment algorithm to automatically evaluate the safety of pull requests. This document explains how risk scores are calculated and provides examples for verification.

## Overview

Risk scores range from **0.0 (safest)** to **1.0 (highest risk)** and are calculated by combining multiple weighted factors:

- **Change Type Weight** (0.05-0.25): Based on conventional commit types
- **Size Impact** (0.0-0.25): Lines changed relative to threshold
- **File Churn** (0.0-0.10): Number of files modified
- **Coverage Impact** (0.0-0.20): Test coverage regression penalty
- **Performance Impact** (0.0-0.20): Performance budget breach penalty
- **Security Flags** (0.0-0.30): High-risk pattern detection
- **Code Review Rubric** (0.0-0.25): Rubric failure penalties
- **Test Bonus** (-0.15): Reward for adding tests

## Algorithm Details

### 1. Change Type Risk (Base Risk)

Based on conventional commit types, reflecting typical impact:

```python
change_type_weights = {
    "docs": 0.05,      # Documentation changes (lowest risk)
    "chore": 0.10,     # Maintenance tasks
    "fix": 0.20,       # Bug fixes
    "feat": 0.25,      # New features (highest base risk)
    "refactor": 0.20,  # Code restructuring
}
```

**Example**: A documentation update (`docs`) starts with 0.05 risk, while a new feature (`feat`) starts with 0.25.

### 2. Size Impact Risk

Larger changes carry more risk due to increased complexity:

```python
size_risk = min(lines_changed / size_threshold, 0.25)
# Default size_threshold = 800 lines
```

**Examples**:
- 100 lines changed: `100/800 = 0.125` risk
- 800+ lines changed: `0.25` risk (capped)
- 50 lines changed: `50/800 = 0.0625` risk

### 3. File Churn Risk

Touching many files increases coordination complexity:

```python
churn_risk = min(files_touched / max_files, 0.10)
# Default max_files = 50
```

**Examples**:
- 5 files: `5/50 = 0.01` risk
- 25 files: `25/50 = 0.05` risk
- 50+ files: `0.10` risk (capped)

### 4. Coverage Impact Risk

Test coverage regressions increase risk:

```python
coverage_risk = max(-coverage_delta / 1.0, 0) if coverage_delta < 0 else 0
coverage_risk = min(coverage_risk, 0.20)  # Capped at 0.20
```

**Examples**:
- Coverage increases (+5%): `0.0` risk (no penalty)
- Coverage drops (-10%): `0.10` risk
- Coverage drops (-25%): `0.20` risk (capped)

### 5. Performance Impact Risk

Performance budget breaches add risk:

```python
perf_risk = min(max(perf_delta / perf_budget, 0), 0.20)
# Default perf_budget = 5ms
```

**Examples**:
- Performance improves (-2ms): `0.0` risk
- Performance degrades (+3ms): `3/5 = 0.06` risk
- Performance degrades (+10ms): `0.20` risk (capped)

### 6. Security Flags Risk

High-risk security patterns trigger significant penalties:

```python
security_risk = 0.30 if security_flags_detected else 0.0
```

**Security patterns include**:
- Hardcoded secrets or API keys
- SQL injection vulnerabilities
- XSS attack vectors
- Insecure cryptographic practices
- Dependency vulnerabilities

### 7. Code Review Rubric Risk

Failed rubric checks accumulate risk:

```python
rubric_risk = min(sum(1 for failure in rubric_failures if failure > 0) * 0.05, 0.25)
```

**Examples**:
- 0 rubric failures: `0.0` risk
- 2 rubric failures: `2 * 0.05 = 0.10` risk
- 5+ rubric failures: `0.25` risk (capped)

### 8. Test Addition Bonus

Adding tests reduces overall risk:

```python
test_bonus = -0.15 if new_tests_added else 0.0
```

## Risk Calculation Formula

```python
total_risk = (
    type_risk +
    size_risk +
    churn_risk +
    coverage_risk +
    perf_risk +
    security_risk +
    rubric_risk +
    test_bonus
)

# Clamp to valid range [0.0, 1.0]
final_risk = max(0.0, min(1.0, round(total_risk, 3)))
```

## Risk Thresholds

GitGuard uses configurable thresholds for decision-making:

```yaml
risk:
  thresholds:
    auto_merge: 0.30      # Auto-merge below this score
    require_review: 0.70  # Require human review above this score
    block_merge: 0.85     # Block merge above this score
```

## Example Calculations

### Example 1: Low-Risk Documentation Update

**Input**:
- Change type: `docs`
- Lines changed: 25
- Files touched: 1
- Coverage delta: 0%
- Performance delta: 0ms
- Security flags: None
- New tests: No

**Calculation**:
```python
type_risk = 0.05        # docs
size_risk = 25/800 = 0.031
churn_risk = 1/50 = 0.02
coverage_risk = 0.0
perf_risk = 0.0
security_risk = 0.0
rubric_risk = 0.0
test_bonus = 0.0

total_risk = 0.05 + 0.031 + 0.02 + 0.0 + 0.0 + 0.0 + 0.0 + 0.0 = 0.101
```

**Result**: `0.101` (Low Risk - Auto-merge eligible)

### Example 2: Medium-Risk Feature Addition

**Input**:
- Change type: `feat`
- Lines changed: 300
- Files touched: 8
- Coverage delta: -5%
- Performance delta: +2ms
- Security flags: None
- New tests: Yes

**Calculation**:
```python
type_risk = 0.25        # feat
size_risk = 300/800 = 0.375 → 0.25 (capped)
churn_risk = 8/50 = 0.16
coverage_risk = 5/100 = 0.05
perf_risk = 2/5 = 0.04
security_risk = 0.0
rubric_risk = 0.0
test_bonus = -0.15

total_risk = 0.25 + 0.25 + 0.16 + 0.05 + 0.04 + 0.0 + 0.0 - 0.15 = 0.55
```

**Result**: `0.55` (Medium Risk - Requires review)

### Example 3: High-Risk Security Change

**Input**:
- Change type: `fix`
- Lines changed: 150
- Files touched: 3
- Coverage delta: -10%
- Performance delta: +1ms
- Security flags: **Detected** (hardcoded API key)
- New tests: No

**Calculation**:
```python
type_risk = 0.20        # fix
size_risk = 150/800 = 0.1875
churn_risk = 3/50 = 0.06
coverage_risk = 10/100 = 0.10
perf_risk = 1/5 = 0.02
security_risk = 0.30    # Security flag detected!
rubric_risk = 0.0
test_bonus = 0.0

total_risk = 0.20 + 0.1875 + 0.06 + 0.10 + 0.02 + 0.30 + 0.0 + 0.0 = 0.8675
```

**Result**: `0.868` (High Risk - Blocked for security review)

## Configuration

Risk scoring can be customized via `config/gitguard.settings.yaml`:

```yaml
risk:
  weights:
    complexity: 0.3      # Code complexity factor
    coverage: 0.2        # Test coverage impact
    security: 0.4        # Security scan results
    history: 0.1         # Historical patterns

  thresholds:
    auto_merge: 0.30     # Auto-merge below this score
    require_review: 0.70 # Require review above this score
    block_merge: 0.85    # Block merge above this score

  settings:
    size_threshold: 800  # Lines changed threshold
    max_files: 50        # File churn threshold
    security_penalty: 0.30
    test_bonus: -0.15
```

## Monitoring and Metrics

GitGuard tracks risk scoring metrics via Prometheus:

- `guard_api_risk_score_calculations_total{result_category}` - Risk score distribution
- `guard_api_risk_score_distribution` - Histogram of calculated scores
- `guard_api_policy_decisions_total{decision}` - Policy decision outcomes

## Validation and Testing

The risk scoring algorithm includes comprehensive unit tests in `tests/test_risk_scoring.py` that verify:

- Correct calculation for each risk factor
- Proper clamping to [0.0, 1.0] range
- Edge cases and boundary conditions
- Configuration parameter effects
- Integration with policy decisions

## Transparency and Auditability

Every risk calculation includes a detailed breakdown showing:

- Individual factor contributions
- Configuration values used
- Input data processed
- Final score and decision rationale

This information is available via:
- API endpoint: `GET /api/v1/risk-analysis/{pr_number}`
- Grafana dashboards: Risk Score Distribution
- PR comments: Automated risk assessment summaries

## See Also

- [Policy Cookbook](policy-cookbook.md) - Example policies using risk scores
- [Getting Started](../GETTING_STARTED.md) - Configuration examples
- [API Documentation](../apps/guard-api/README.md) - Risk scoring endpoints
- [Monitoring Guide](../ops/README.md) - Risk metrics and alerting
