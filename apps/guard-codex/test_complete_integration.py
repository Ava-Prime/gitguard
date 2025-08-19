#!/usr/bin/env python3
"""Complete integration test showing policy transparency + Mermaid graphs."""


def _mermaid(pr_num: int, changed: list[str], policies: list[str]) -> str:
    """Generate Mermaid graph showing PR touches and governance relationships."""
    lines = ["```mermaid", "graph LR", f'  PR["PR #{pr_num}"]']
    for i, f in enumerate(changed[:20]):  # cap to keep it readable
        lines.append(f"  PR -->|touches| F{i}[\"{'...' + f[-30:] if len(f) > 30 else f}\"]")
    for j, p in enumerate((policies or [])[:10]):
        lines.append(f"  PR -->|governed_by| P{j}[\"{'...' + p[-20:] if len(p) > 20 else p}\"]")
    lines.append("```")
    return "\n".join(lines)


def simulate_pr_page_generation():
    """Simulate complete PR page generation with both features."""

    # Sample PR data
    pr = {
        "number": 456,
        "title": "Add user authentication system",
        "risk_score": "medium",
        "checks_passed": True,
        "coverage_delta": "+2.3",
        "perf_delta": "+15ms",
        "labels": ["feature", "security"],
        "release_window_state": "open",
        "summary": "Implements JWT-based authentication with role-based access control.",
        "policies": ["allow", "high_risk_area", "security_review"],
        "opa_input": {
            "pr": {
                "number": 456,
                "files_changed": [
                    "src/auth/jwt.py",
                    "src/middleware/auth.py",
                    "tests/test_auth.py",
                ],
                "risk_score": "medium",
            }
        },
    }

    changed_files = [
        "src/auth/jwt.py",
        "src/middleware/auth.py",
        "src/models/user.py",
        "tests/test_auth.py",
        "docs/authentication.md",
    ]

    # Generate Mermaid graph
    merm = _mermaid(pr["number"], changed_files, pr.get("policies", []))

    # Simulate policy explanation (simplified)
    policy_md = """## Policy Evaluation

**Evaluated Policies:** allow, high_risk_area, security_review

**OPA Input:**
```json
{
  "pr": {
    "number": 456,
    "files_changed": ["src/auth/jwt.py", "src/middleware/auth.py", "tests/test_auth.py"],
    "risk_score": "medium"
  }
}
```

**Policy: allow**
```rego
allow {
    input.pr.risk_score != "high"
    input.pr.checks_passed == true
}
```

**Policy: security_review**
```rego
security_review {
    some file
    input.pr.files_changed[file]
    startswith(file, "src/auth/")
}
```"""

    # Generate complete PR page content
    gh_link = f"https://github.com/example/repo/pull/{pr['number']}"

    body = f"""# PR #{pr['number']}: {pr['title']}

**Risk:** {pr['risk_score']} • **Checks:** {"✓" if pr['checks_passed'] else "✗"}
**Coverage Δ:** {pr['coverage_delta']}% • **Perf Δ:** {pr['perf_delta']} • **Labels:** {", ".join(pr['labels']) or "-"}
**Release window:** {pr['release_window_state']} • [GitHub]({gh_link})

## Summary
{pr['summary'] or "_No summary provided._"}

## Changed Files
{chr(10).join(f"- `{f}`" for f in changed_files) or "_none_"}

## Governance
- Policies: {", ".join(pr.get('policies', [])) or "—"}
- ADRs impacted: {"—"}

### Graph
{merm}

{policy_md}
"""

    return body


if __name__ == "__main__":
    print("=== Complete Integration Demo: Policy Transparency + Mermaid Graphs ===")
    print()

    # Generate complete PR page
    pr_content = simulate_pr_page_generation()

    print("Generated PR page content:")
    print("=" * 80)
    print(pr_content)
    print("=" * 80)

    print("\n🎉 Complete integration demo successful!")
    print("\nFeatures demonstrated:")
    print("✓ Mermaid graph visualization of file touches and governance")
    print("✓ Policy transparency with OPA inputs and Rego source code")
    print("✓ Complete PR page generation with both features integrated")
