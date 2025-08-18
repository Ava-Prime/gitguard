#!/usr/bin/env python3
"""
Test script to demonstrate the policy explanation integration.
This shows how the policy transparency feature works on PR pages.
"""

import json
from pathlib import Path
from policy_explain import render_policy_block

def test_policy_explanation():
    """Test the policy explanation functionality with sample data."""
    
    # Sample PR data that would come from the Guard API
    sample_pr_data = {
        "policies": ["allow", "high_risk_area", "exceeds_budgets"],
        "opa_input": {
            "action": "merge_pr",
            "pr": {
                "number": 123,
                "checks_passed": True,
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
    }
    
    # Path to policies directory
    policies_dir = str(Path("C:/Users/Ava/codessa-platform/gitguard/gitguard/policies"))
    
    print("=== Policy Transparency Demo ===")
    print("\nThis demonstrates how policy evaluation details are shown on PR pages.")
    print("When a gate trips (or passes), engineers can see:")
    print("1. The exact policies that were evaluated")
    print("2. The OPA inputs that were used")
    print("3. The source code of each policy rule")
    print("\n" + "="*60 + "\n")
    
    # Generate the policy explanation block
    policy_explanation = render_policy_block(
        sample_pr_data["policies"],
        sample_pr_data["opa_input"],
        policies_dir
    )
    
    print(policy_explanation)
    
    print("\n" + "="*60)
    print("\n✅ Policy explanation generated successfully!")
    print("\nThis content would appear in the PR documentation, teaching")
    print("engineers about the governance rules through the guardrail.")
    
    return policy_explanation

def test_empty_policies():
    """Test handling of PRs with no policies."""
    print("\n=== Testing Empty Policies ===")
    
    empty_result = render_policy_block([], {}, "")
    print(empty_result)
    
    return empty_result

if __name__ == "__main__":
    # Test with sample data
    test_policy_explanation()
    
    # Test edge case
    test_empty_policies()
    
    print("\n🎉 All tests completed successfully!")
    print("\nThe policy transparency feature is ready to make Codex")
    print("feel inevitable to every engineer who touches a PR.")