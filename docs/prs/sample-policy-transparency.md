# PR #123: Add API rate limiting feature

**Risk:** 0.25 • **Checks:** ✓  
**Coverage Δ:** -0.1% • **Perf Δ:** 2.5 • **Labels:** risk:low, area:api  
**Release window:** open • [GitHub](https://github.com/example-org/example-repo/pull/123)

## Summary
Implements rate limiting for the public API to prevent abuse and ensure fair usage across all clients. Includes Redis-based token bucket implementation with configurable limits per endpoint.

## Changed Files
- `src/api.py`
- `tests/test_api.py`
- `config/rate_limits.yaml`
- `requirements.txt`

## Governance
- Policies: allow, high_risk_area, exceeds_budgets
- ADRs impacted: ADR-001-api-design, ADR-003-performance-budgets

## Policy Evaluation

**Evaluated policies:** allow, high_risk_area, exceeds_budgets

<details><summary>OPA inputs used</summary>

```json
{
  "action": "merge_pr",
  "pr": {
    "number": 123,
    "checks_passed": true,
    "risk_score": 0.25,
    "labels": ["risk:low", "area:api"],
    "changed_paths": ["src/api.py", "tests/test_api.py"],
    "coverage_delta": -0.1,
    "perf_delta": 2.5,
    "size_category": "M"
  },
  "repo": {
    "name": "example-repo",
    "owner": "example-org",
    "perf_budget": 5
  },
  "actor": "gitguard[bot]"
}
```
</details>

<details><summary>Source: <code>allow</code></summary>

```rego
# Auto-merge allowed for low-risk PRs
allow if {
    input.action == "merge_pr"
    input.pr.checks_passed == true
    input.pr.risk_score <= 0.30
    not high_risk_area
    not exceeds_budgets
    automerge_approved
}
```
</details>

<details><summary>Source: <code>high_risk_area</code></summary>

```rego
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
```
</details>

<details><summary>Source: <code>exceeds_budgets</code></summary>

```rego
# Performance budget enforcement
exceeds_budgets if {
    input.pr.perf_delta > input.repo.perf_budget
}

exceeds_budgets if {
    input.pr.coverage_delta < -5.0
}
```
</details>

---

**Policy Decision:** ✅ **APPROVED FOR AUTO-MERGE**

**Reasoning:**
- ✅ All checks passed
- ✅ Risk score (0.25) is below threshold (0.30)
- ✅ No high-risk areas touched (infra/, security/)
- ✅ Performance delta (2.5) within budget (5.0)
- ✅ Coverage delta (-0.1%) acceptable

This PR meets all governance criteria and can be safely auto-merged. The policy evaluation shows exactly why this decision was made, teaching engineers about the guardrails through transparency.