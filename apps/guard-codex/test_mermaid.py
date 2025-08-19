#!/usr/bin/env python3
"""Test script for Mermaid graph generation functionality."""


def _mermaid(pr_num: int, changed: list[str], policies: list[str]) -> str:
    """Generate Mermaid graph showing PR touches and governance relationships."""
    lines = ["```mermaid", "graph LR", f'  PR["PR #{pr_num}"]']
    for i, f in enumerate(changed[:20]):  # cap to keep it readable
        lines.append(f"  PR -->|touches| F{i}[\"{'...' + f[-30:] if len(f) > 30 else f}\"]")
    for j, p in enumerate((policies or [])[:10]):
        lines.append(f"  PR -->|governed_by| P{j}[\"{'...' + p[-20:] if len(p) > 20 else p}\"]")
    lines.append("```")
    return "\n".join(lines)


if __name__ == "__main__":
    print("=== Testing Mermaid Graph Generation ===")

    # Test with sample PR data
    pr_num = 123
    changed_files = [
        "src/api/handlers.py",
        "tests/test_handlers.py",
        "config/settings.yaml",
        "docs/api.md",
    ]
    policies = ["allow", "high_risk_area"]

    result = _mermaid(pr_num, changed_files, policies)
    print("\nGenerated Mermaid graph:")
    print(result)

    # Test with long file names
    print("\n=== Testing with Long File Names ===")
    long_files = [
        "src/very/deep/nested/directory/structure/with/long/filename.py",
        "another/extremely/long/path/to/some/configuration/file.yaml",
    ]
    long_policies = ["very_long_policy_name_that_exceeds_limit"]

    result2 = _mermaid(456, long_files, long_policies)
    print("\nGenerated Mermaid graph with truncation:")
    print(result2)

    # Test with empty data
    print("\n=== Testing with Empty Data ===")
    result3 = _mermaid(789, [], [])
    print("\nGenerated Mermaid graph (empty):")
    print(result3)

    print("\n🎉 All Mermaid tests completed successfully!")
