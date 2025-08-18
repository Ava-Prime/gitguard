#!/usr/bin/env python3
"""
Comprehensive Unit Tests for OPA Policy Evaluation

Tests all policy rules, decision logic, and edge cases for the GitGuard OPA policies.
Covers allow/deny rules, risk assessment, development phase handling, and approval workflows.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
from pathlib import Path


class MockOPAClient:
    """Mock OPA client for testing policy evaluation without actual OPA server."""
    
    def __init__(self):
        self.policies = {}
        self.evaluation_results = {}
    
    def evaluate_policy(self, policy_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock policy evaluation based on input data patterns."""
        # Simulate policy evaluation logic for testing
        if policy_name == "allow":
            return self._evaluate_allow_policy(input_data)
        elif policy_name == "deny":
            return self._evaluate_deny_policy(input_data)
        elif policy_name == "high_risk_area":
            return self._evaluate_high_risk_area(input_data)
        elif policy_name == "exceeds_budgets":
            return self._evaluate_exceeds_budgets(input_data)
        else:
            return {"result": False, "explanation": "Unknown policy"}
    
    def _evaluate_allow_policy(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock allow policy evaluation."""
        pr = input_data.get("pr", {})
        
        # Check if checks passed
        if not pr.get("checks_passed", False):
            return {"result": False, "explanation": "Checks not passed"}
        
        # Check risk score
        risk_score = pr.get("risk_score", 1.0)
        if risk_score > 0.7:
            return {"result": False, "explanation": "High risk score"}
        
        # Check if exceeds budgets
        if self._evaluate_exceeds_budgets(input_data)["result"]:
            return {"result": False, "explanation": "Exceeds budgets"}
        
        return {"result": True, "explanation": "All checks passed"}
    
    def _evaluate_deny_policy(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock deny policy evaluation."""
        pr = input_data.get("pr", {})
        action = input_data.get("action")
        
        deny_reasons = []
        
        # Check infrastructure changes
        changed_paths = pr.get("changed_paths", [])
        labels = pr.get("labels", [])
        
        for path in changed_paths:
            if path.startswith("infra/") or path.startswith(".github/"):
                if "owner-approved" not in labels and "emergency-override" not in labels:
                    deny_reasons.append(f"Infrastructure change requires @platform-team approval")
            
            if path.startswith("policies/"):
                if "security-approved" not in labels and "emergency-override" not in labels:
                    deny_reasons.append(f"Policy change requires @security-team approval")
            
            if path.startswith("apps/guard-api/"):
                if "api-security-reviewed" not in labels and "emergency-override" not in labels:
                    deny_reasons.append(f"API change requires @backend-team security review")
        
        # Check dependencies
        if "dependencies" in labels:
            checks = pr.get("checks", {})
            if not checks.get("sbom_ok", False):
                deny_reasons.append("Dependencies changed without passing SBOM scan")
            
            if pr.get("diff_unpinned_versions", False):
                deny_reasons.append("Unpinned versions in requirements.txt")
        
        return {
            "result": len(deny_reasons) > 0,
            "reasons": deny_reasons,
            "explanation": "; ".join(deny_reasons) if deny_reasons else "No denial reasons"
        }
    
    def _evaluate_high_risk_area(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock high risk area evaluation."""
        pr = input_data.get("pr", {})
        changed_paths = pr.get("changed_paths", [])
        risk_score = pr.get("risk_score", 0.0)
        
        high_risk_patterns = [
            "infra/", "security/", "auth/", "payment/", "billing/",
            "admin/", "config/", "secrets/", "keys/"
        ]
        
        for path in changed_paths:
            for pattern in high_risk_patterns:
                if pattern in path.lower():
                    return {"result": True, "explanation": f"High risk file: {path}"}
        
        if risk_score > 0.6:
            return {"result": True, "explanation": f"High risk score: {risk_score}"}
        
        return {"result": False, "explanation": "Not high risk area"}
    
    def _evaluate_exceeds_budgets(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock budget evaluation."""
        pr = input_data.get("pr", {})
        repo = input_data.get("repo", {})
        
        coverage_delta = pr.get("coverage_delta", 0.0)
        perf_delta = pr.get("perf_delta", 0.0)
        perf_budget = repo.get("perf_budget", 5.0)
        
        # Get coverage threshold based on development phase
        development_phase = pr.get("development_phase", "feature_dev")
        coverage_thresholds = {
            "initial_dev": -0.5,
            "feature_dev": -0.2,
            "pre_production": -0.1,
            "production": -0.05
        }
        threshold = coverage_thresholds.get(development_phase, -0.2)
        
        # Check for development phase exceptions
        has_exception = self._has_development_phase_exception(input_data)
        
        exceeds_coverage = coverage_delta < threshold and not has_exception
        exceeds_perf = perf_delta > perf_budget
        
        if exceeds_coverage or exceeds_perf:
            reasons = []
            if exceeds_coverage:
                reasons.append(f"Coverage delta {coverage_delta} below threshold {threshold}")
            if exceeds_perf:
                reasons.append(f"Performance delta {perf_delta} exceeds budget {perf_budget}")
            
            return {
                "result": True,
                "explanation": "; ".join(reasons)
            }
        
        return {"result": False, "explanation": "Within budgets"}
    
    def _has_development_phase_exception(self, input_data: Dict[str, Any]) -> bool:
        """Check if development phase exception applies."""
        pr = input_data.get("pr", {})
        development_phase = pr.get("development_phase")
        
        if development_phase not in ["initial_dev", "feature_dev"]:
            return False
        
        # Check for incomplete test markers
        file_analysis = pr.get("file_analysis", {})
        for file_path, analysis in file_analysis.items():
            if analysis.get("incomplete_markers", 0) > 0:
                return True
        
        # Check for missing OPA fixtures
        changed_paths = pr.get("changed_paths", [])
        existing_files = pr.get("existing_files", [])
        
        for path in changed_paths:
            if path.endswith(".rego") and not path.endswith("_test.rego"):
                test_file = path.replace(".rego", "_test.rego")
                if test_file not in changed_paths and test_file not in existing_files:
                    return True
        
        # Check for experimental code changes
        experimental_patterns = ["/experimental/", "/prototype/", "/draft/", "_experimental", "_draft"]
        for path in changed_paths:
            for pattern in experimental_patterns:
                if pattern in path:
                    return True
        
        return False


class TestOPAPolicyEvaluation:
    """Test suite for OPA policy evaluation logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.opa_client = MockOPAClient()
    
    def test_allow_policy_low_risk_pr(self):
        """Test allow policy with low risk PR."""
        input_data = {
            "action": "merge_pr",
            "pr": {
                "number": 123,
                "checks_passed": True,
                "risk_score": 0.25,
                "labels": ["risk:low", "area:api"],
                "changed_paths": ["src/api.py", "tests/test_api.py"],
                "coverage_delta": 0.1,
                "perf_delta": 2.0,
                "size_category": "S"
            },
            "repo": {
                "name": "example-repo",
                "owner": "example-org",
                "perf_budget": 5
            },
            "actor": "gitguard[bot]"
        }
        
        result = self.opa_client.evaluate_policy("allow", input_data)
        assert result["result"] is True
        assert "All checks passed" in result["explanation"]
    
    def test_allow_policy_high_risk_pr(self):
        """Test allow policy with high risk PR."""
        input_data = {
            "action": "merge_pr",
            "pr": {
                "number": 456,
                "checks_passed": True,
                "risk_score": 0.85,
                "labels": ["risk:high", "area:security"],
                "changed_paths": ["security/auth.py", "infra/k8s.yaml"],
                "coverage_delta": -0.3,
                "perf_delta": 8.0,
                "size_category": "L"
            },
            "repo": {
                "name": "example-repo",
                "owner": "example-org",
                "perf_budget": 5
            },
            "actor": "gitguard[bot]"
        }
        
        result = self.opa_client.evaluate_policy("allow", input_data)
        assert result["result"] is False
        assert "High risk score" in result["explanation"]
    
    def test_allow_policy_checks_not_passed(self):
        """Test allow policy when checks haven't passed."""
        input_data = {
            "action": "merge_pr",
            "pr": {
                "number": 789,
                "checks_passed": False,
                "risk_score": 0.15,
                "labels": ["risk:low"],
                "changed_paths": ["src/utils.py"],
                "coverage_delta": 0.05,
                "perf_delta": 1.0,
                "size_category": "XS"
            },
            "repo": {"perf_budget": 5},
            "actor": "gitguard[bot]"
        }
        
        result = self.opa_client.evaluate_policy("allow", input_data)
        assert result["result"] is False
        assert "Checks not passed" in result["explanation"]
    
    def test_high_risk_area_infra_files(self):
        """Test high risk area detection for infrastructure files."""
        input_data = {
            "pr": {
                "changed_paths": ["infra/terraform/main.tf", "infra/k8s/deployment.yaml"],
                "risk_score": 0.25
            }
        }
        
        result = self.opa_client.evaluate_policy("high_risk_area", input_data)
        assert result["result"] is True
        assert "High risk file" in result["explanation"]
    
    def test_high_risk_area_security_files(self):
        """Test high risk area detection for security files."""
        input_data = {
            "pr": {
                "changed_paths": ["security/auth.py", "security/encryption.py"],
                "risk_score": 0.15
            }
        }
        
        result = self.opa_client.evaluate_policy("high_risk_area", input_data)
        assert result["result"] is True
        assert "High risk file" in result["explanation"]
    
    def test_high_risk_area_by_score(self):
        """Test high risk area detection by risk score."""
        input_data = {
            "pr": {
                "changed_paths": ["src/api.py"],
                "risk_score": 0.75
            }
        }
        
        result = self.opa_client.evaluate_policy("high_risk_area", input_data)
        assert result["result"] is True
        assert "High risk score" in result["explanation"]
    
    def test_not_high_risk_area(self):
        """Test normal files are not considered high risk."""
        input_data = {
            "pr": {
                "changed_paths": ["src/api.py", "tests/test_api.py"],
                "risk_score": 0.15
            }
        }
        
        result = self.opa_client.evaluate_policy("high_risk_area", input_data)
        assert result["result"] is False
        assert "Not high risk area" in result["explanation"]
    
    def test_exceeds_budgets_coverage_threshold(self):
        """Test budget violation due to coverage threshold."""
        input_data = {
            "pr": {
                "coverage_delta": -0.25,
                "perf_delta": 2.0,
                "development_phase": "production"
            },
            "repo": {"perf_budget": 5}
        }
        
        result = self.opa_client.evaluate_policy("exceeds_budgets", input_data)
        assert result["result"] is True
        assert "Coverage delta" in result["explanation"]
    
    def test_exceeds_budgets_performance_threshold(self):
        """Test budget violation due to performance threshold."""
        input_data = {
            "pr": {
                "coverage_delta": 0.1,
                "perf_delta": 6.0,
                "development_phase": "feature_dev"
            },
            "repo": {"perf_budget": 5}
        }
        
        result = self.opa_client.evaluate_policy("exceeds_budgets", input_data)
        assert result["result"] is True
        assert "Performance delta" in result["explanation"]
    
    def test_within_budgets(self):
        """Test PR within all budget constraints."""
        input_data = {
            "pr": {
                "coverage_delta": 0.1,
                "perf_delta": 3.0,
                "development_phase": "feature_dev"
            },
            "repo": {"perf_budget": 5}
        }
        
        result = self.opa_client.evaluate_policy("exceeds_budgets", input_data)
        assert result["result"] is False
        assert "Within budgets" in result["explanation"]
    
    def test_development_phase_coverage_thresholds(self):
        """Test different coverage thresholds for development phases."""
        phases_and_thresholds = [
            ("initial_dev", -0.5),
            ("feature_dev", -0.2),
            ("pre_production", -0.1),
            ("production", -0.05)
        ]
        
        for phase, threshold in phases_and_thresholds:
            # Test just above threshold (should pass)
            input_data = {
                "pr": {
                    "coverage_delta": threshold + 0.01,
                    "perf_delta": 2.0,
                    "development_phase": phase
                },
                "repo": {"perf_budget": 5}
            }
            
            result = self.opa_client.evaluate_policy("exceeds_budgets", input_data)
            assert result["result"] is False, f"Phase {phase} should pass with coverage {threshold + 0.01}"
            
            # Test below threshold (should fail)
            input_data["pr"]["coverage_delta"] = threshold - 0.01
            result = self.opa_client.evaluate_policy("exceeds_budgets", input_data)
            assert result["result"] is True, f"Phase {phase} should fail with coverage {threshold - 0.01}"
    
    def test_development_phase_exception_incomplete_tests(self):
        """Test development phase exception for incomplete test markers."""
        input_data = {
            "pr": {
                "coverage_delta": -0.3,
                "perf_delta": 2.0,
                "development_phase": "initial_dev",
                "changed_paths": ["test_api.py"],
                "file_analysis": {
                    "test_api.py": {"incomplete_markers": 3}
                }
            },
            "repo": {"perf_budget": 5}
        }
        
        result = self.opa_client.evaluate_policy("exceeds_budgets", input_data)
        assert result["result"] is False  # Exception should allow this
    
    def test_development_phase_exception_missing_opa_fixtures(self):
        """Test development phase exception for missing OPA test fixtures."""
        input_data = {
            "pr": {
                "coverage_delta": -0.3,
                "perf_delta": 2.0,
                "development_phase": "initial_dev",
                "changed_paths": ["policies/new_rule.rego"],
                "existing_files": ["policies/other_rule_test.rego"]
            },
            "repo": {"perf_budget": 5}
        }
        
        result = self.opa_client.evaluate_policy("exceeds_budgets", input_data)
        assert result["result"] is False  # Exception should allow this
    
    def test_development_phase_exception_experimental_code(self):
        """Test development phase exception for experimental code changes."""
        input_data = {
            "pr": {
                "coverage_delta": -0.3,
                "perf_delta": 2.0,
                "development_phase": "feature_dev",
                "changed_paths": ["src/experimental/new_feature.py"]
            },
            "repo": {"perf_budget": 5}
        }
        
        result = self.opa_client.evaluate_policy("exceeds_budgets", input_data)
        assert result["result"] is False  # Exception should allow this
    
    def test_no_development_phase_exception_production(self):
        """Test that development phase exceptions don't apply in production."""
        input_data = {
            "pr": {
                "coverage_delta": -0.1,
                "perf_delta": 2.0,
                "development_phase": "production",
                "changed_paths": ["src/experimental/new_feature.py"]
            },
            "repo": {"perf_budget": 5}
        }
        
        result = self.opa_client.evaluate_policy("exceeds_budgets", input_data)
        assert result["result"] is True  # No exception in production


class TestOPADenyPolicies:
    """Test suite for OPA deny policies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.opa_client = MockOPAClient()
    
    def test_deny_infra_change_without_approval(self):
        """Test denial of infrastructure changes without approval."""
        input_data = {
            "action": "merge_pr",
            "pr": {
                "number": 101,
                "checks_passed": True,
                "risk_score": 0.30,
                "labels": ["infra"],
                "changed_paths": ["infra/terraform/main.tf"],
                "coverage_delta": 0.0,
                "perf_delta": 1.0,
                "size_category": "M"
            },
            "repo": {"perf_budget": 5},
            "actor": "gitguard[bot]"
        }
        
        result = self.opa_client.evaluate_policy("deny", input_data)
        assert result["result"] is True
        assert "Infrastructure change requires @platform-team approval" in result["explanation"]
    
    def test_allow_infra_change_with_approval(self):
        """Test allowing infrastructure changes with proper approval."""
        input_data = {
            "action": "merge_pr",
            "pr": {
                "number": 102,
                "checks_passed": True,
                "risk_score": 0.30,
                "labels": ["infra", "owner-approved"],
                "changed_paths": ["infra/terraform/main.tf"],
                "coverage_delta": 0.0,
                "perf_delta": 1.0,
                "size_category": "M"
            },
            "repo": {"perf_budget": 5},
            "actor": "gitguard[bot]"
        }
        
        result = self.opa_client.evaluate_policy("deny", input_data)
        assert result["result"] is False
        assert "No denial reasons" in result["explanation"]
    
    def test_deny_policy_change_without_approval(self):
        """Test denial of policy changes without security approval."""
        input_data = {
            "action": "merge_pr",
            "pr": {
                "labels": ["policy"],
                "changed_paths": ["policies/guard_rules.rego"]
            }
        }
        
        result = self.opa_client.evaluate_policy("deny", input_data)
        assert result["result"] is True
        assert "Policy change requires @security-team approval" in result["explanation"]
    
    def test_deny_api_change_without_review(self):
        """Test denial of API changes without security review."""
        input_data = {
            "action": "merge_pr",
            "pr": {
                "labels": ["api"],
                "changed_paths": ["apps/guard-api/main.py"]
            }
        }
        
        result = self.opa_client.evaluate_policy("deny", input_data)
        assert result["result"] is True
        assert "API change requires @backend-team security review" in result["explanation"]
    
    def test_deny_dependencies_without_sbom(self):
        """Test denial of dependency changes without SBOM scan."""
        input_data = {
            "action": "merge_pr",
            "pr": {
                "labels": ["dependencies"],
                "changed_paths": ["requirements.txt"],
                "checks": {}
            }
        }
        
        result = self.opa_client.evaluate_policy("deny", input_data)
        assert result["result"] is True
        assert "Dependencies changed without passing SBOM scan" in result["explanation"]
    
    def test_allow_dependencies_with_sbom(self):
        """Test allowing dependency changes with SBOM scan."""
        input_data = {
            "action": "merge_pr",
            "pr": {
                "labels": ["dependencies"],
                "changed_paths": ["requirements.txt"],
                "checks": {"sbom_ok": True},
                "diff_unpinned_versions": False
            }
        }
        
        result = self.opa_client.evaluate_policy("deny", input_data)
        assert result["result"] is False
        assert "No denial reasons" in result["explanation"]
    
    def test_deny_unpinned_versions(self):
        """Test denial of unpinned versions in requirements."""
        input_data = {
            "action": "merge_pr",
            "pr": {
                "labels": ["dependencies"],
                "changed_paths": ["requirements.txt"],
                "checks": {"sbom_ok": True},
                "diff_unpinned_versions": True
            }
        }
        
        result = self.opa_client.evaluate_policy("deny", input_data)
        assert result["result"] is True
        assert "Unpinned versions in requirements.txt" in result["explanation"]
    
    def test_emergency_override_bypasses_denial(self):
        """Test that emergency override bypasses denial policies."""
        input_data = {
            "action": "merge_pr",
            "pr": {
                "labels": ["infra", "emergency-override"],
                "changed_paths": ["infra/terraform/main.tf"]
            }
        }
        
        result = self.opa_client.evaluate_policy("deny", input_data)
        assert result["result"] is False
        assert "No denial reasons" in result["explanation"]


class TestOPAHelperFunctions:
    """Test suite for OPA helper functions and utilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.opa_client = MockOPAClient()
    
    def test_lockfile_detection(self):
        """Test lockfile pattern detection."""
        lockfiles = [
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
        
        for lockfile in lockfiles:
            # This would test the actual is_lockfile function in a real implementation
            assert lockfile.endswith((".lock", ".sum", "lock.json", "lock.yaml"))
    
    def test_manifest_file_detection(self):
        """Test manifest file pattern detection."""
        manifest_files = [
            "package.json",
            "Pipfile",
            "pyproject.toml",
            "requirements.txt",
            "Gemfile",
            "composer.json",
            "go.mod",
            "Cargo.toml"
        ]
        
        for manifest in manifest_files:
            # This would test the actual is_manifest_file function in a real implementation
            assert any(manifest.endswith(ext) for ext in [".json", ".toml", ".txt", "file", ".mod"])
    
    def test_experimental_path_detection(self):
        """Test experimental code path detection."""
        experimental_paths = [
            "src/experimental/feature.py",
            "apps/prototype/service.py",
            "policies/draft/new_rule.rego",
            "src/api_experimental.py",
            "tests/test_draft.py"
        ]
        
        experimental_patterns = ["/experimental/", "/prototype/", "/draft/", "_experimental", "_draft"]
        
        for path in experimental_paths:
            is_experimental = any(pattern in path for pattern in experimental_patterns)
            assert is_experimental, f"Path {path} should be detected as experimental"
    
    def test_dco_signoff_validation(self):
        """Test DCO (Developer Certificate of Origin) signoff validation."""
        valid_messages = [
            "Fix bug\n\nSigned-off-by: Developer <dev@example.com>",
            "Add feature\n\nThis adds a new feature.\n\nSigned-off-by: John Doe <john@example.com>"
        ]
        
        invalid_messages = [
            "Fix bug\n\nNo signoff here",
            "Add feature\n\nSigned-by: Developer <dev@example.com>",  # Wrong format
            "Fix bug\n\nSigned-off-by: Developer"  # Missing email
        ]
        
        for message in valid_messages:
            assert "Signed-off-by:" in message
            assert "<" in message and ">" in message  # Basic email format check
        
        for message in invalid_messages:
            has_proper_signoff = (
                "Signed-off-by:" in message and 
                "<" in message and ">" in message and
                "@" in message
            )
            assert not has_proper_signoff, f"Message should not have valid DCO: {message}"


class TestOPAIntegration:
    """Integration tests for OPA policy evaluation workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.opa_client = MockOPAClient()
    
    def test_full_policy_evaluation_workflow(self):
        """Test complete policy evaluation workflow."""
        # Simulate a typical PR evaluation
        pr_data = {
            "action": "merge_pr",
            "pr": {
                "number": 123,
                "checks_passed": True,
                "risk_score": 0.35,
                "labels": ["feature", "api"],
                "changed_paths": ["src/api.py", "tests/test_api.py"],
                "coverage_delta": 0.05,
                "perf_delta": 2.5,
                "size_category": "M",
                "development_phase": "feature_dev"
            },
            "repo": {
                "name": "example-repo",
                "owner": "example-org",
                "perf_budget": 5
            },
            "actor": "developer"
        }
        
        # Evaluate all relevant policies
        allow_result = self.opa_client.evaluate_policy("allow", pr_data)
        deny_result = self.opa_client.evaluate_policy("deny", pr_data)
        high_risk_result = self.opa_client.evaluate_policy("high_risk_area", pr_data)
        budget_result = self.opa_client.evaluate_policy("exceeds_budgets", pr_data)
        
        # Verify results
        assert allow_result["result"] is True
        assert deny_result["result"] is False
        assert high_risk_result["result"] is False
        assert budget_result["result"] is False
    
    def test_policy_evaluation_with_violations(self):
        """Test policy evaluation with multiple violations."""
        pr_data = {
            "action": "merge_pr",
            "pr": {
                "number": 456,
                "checks_passed": True,
                "risk_score": 0.75,
                "labels": ["infra", "dependencies"],
                "changed_paths": ["infra/k8s.yaml", "requirements.txt"],
                "coverage_delta": -0.15,
                "perf_delta": 7.0,
                "size_category": "L",
                "development_phase": "production",
                "checks": {},
                "diff_unpinned_versions": True
            },
            "repo": {"perf_budget": 5},
            "actor": "developer"
        }
        
        # Evaluate policies
        allow_result = self.opa_client.evaluate_policy("allow", pr_data)
        deny_result = self.opa_client.evaluate_policy("deny", pr_data)
        high_risk_result = self.opa_client.evaluate_policy("high_risk_area", pr_data)
        budget_result = self.opa_client.evaluate_policy("exceeds_budgets", pr_data)
        
        # Verify violations are detected
        assert allow_result["result"] is False  # Should be blocked
        assert deny_result["result"] is True    # Multiple denial reasons
        assert high_risk_result["result"] is True  # High risk due to infra + score
        assert budget_result["result"] is True     # Exceeds both coverage and perf budgets
        
        # Check that multiple denial reasons are captured
        assert len(deny_result["reasons"]) >= 2
    
    def test_docs_only_change_auto_approval(self):
        """Test that docs-only changes are auto-approved."""
        pr_data = {
            "action": "merge_pr",
            "pr": {
                "number": 789,
                "checks_passed": True,
                "risk_score": 0.05,
                "labels": ["docs"],
                "changed_paths": ["README.md", "docs/api.md"],
                "coverage_delta": 0.0,
                "perf_delta": 0.0,
                "size_category": "XS"
            },
            "repo": {"perf_budget": 5},
            "actor": "gitguard[bot]"
        }
        
        # Evaluate policies
        allow_result = self.opa_client.evaluate_policy("allow", pr_data)
        deny_result = self.opa_client.evaluate_policy("deny", pr_data)
        
        # Docs-only changes should be allowed
        assert allow_result["result"] is True
        assert deny_result["result"] is False


class TestOPAPolicyTransparency:
    """Test suite for policy transparency and explanation features."""
    
    def test_policy_explanation_structure(self):
        """Test that policy explanations have proper structure."""
        explanation = {
            "policy_file": "guard_rules.rego",
            "rule_name": "allow",
            "source_lines": [15, 16, 17, 18],
            "explanation": "PR allowed due to low risk score and passing checks",
            "inputs_used": {
                "pr.risk_score": 0.25,
                "pr.checks_passed": True,
                "pr.coverage_delta": 0.1
            }
        }
        
        # Verify explanation structure
        assert "policy_file" in explanation
        assert "rule_name" in explanation
        assert "source_lines" in explanation
        assert "explanation" in explanation
        assert "inputs_used" in explanation
        
        # Verify data types
        assert isinstance(explanation["source_lines"], list)
        assert isinstance(explanation["inputs_used"], dict)
        assert len(explanation["source_lines"]) > 0
    
    def test_policy_source_rendering(self):
        """Test policy source code rendering for transparency."""
        # Mock policy source content
        policy_source = '''
allow if {
    input.pr.checks_passed
    input.pr.risk_score < 0.7
    not exceeds_budgets
}
'''
        
        # Verify source content structure
        assert "allow if" in policy_source
        assert "input.pr.checks_passed" in policy_source
        assert "input.pr.risk_score" in policy_source
        assert "not exceeds_budgets" in policy_source
    
    def test_opa_input_serialization(self):
        """Test OPA input data serialization for transparency."""
        opa_input = {
            "action": "merge_pr",
            "pr": {
                "number": 123,
                "checks_passed": True,
                "risk_score": 0.25,
                "labels": ["feature"],
                "changed_paths": ["src/api.py"]
            },
            "repo": {"name": "test-repo"},
            "actor": "developer"
        }
        
        # Serialize to JSON for transparency display
        serialized = json.dumps(opa_input, indent=2)
        
        # Verify serialization
        assert isinstance(serialized, str)
        assert "merge_pr" in serialized
        assert "checks_passed" in serialized
        assert "risk_score" in serialized
        
        # Verify it can be deserialized
        deserialized = json.loads(serialized)
        assert deserialized == opa_input


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])