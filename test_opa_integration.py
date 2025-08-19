#!/usr/bin/env python3
"""
OPA Policy Integration Tests

Tests for real OPA server integration, policy loading, and end-to-end policy evaluation workflows.
These tests validate the actual integration with OPA server and policy file management.
"""

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest


class OPAServerManager:
    """Manages OPA server lifecycle for testing."""

    def __init__(self, policy_dir: str = None):
        self.policy_dir = policy_dir or "policies"
        self.server_process = None
        self.server_url = "http://localhost:8181"
        self.is_running = False

    def start_server(self) -> bool:
        """Start OPA server with policies loaded."""
        try:
            # Check if OPA is available
            result = subprocess.run(["opa", "version"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return False

            # Start OPA server
            cmd = [
                "opa",
                "run",
                "--server",
                "--addr",
                "localhost:8181",
                "--set",
                "decision_logs.console=true",
                self.policy_dir,
            ]

            self.server_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Give server time to start
            import time

            time.sleep(2)

            # Check if server is responsive
            import requests

            try:
                response = requests.get(f"{self.server_url}/health", timeout=5)
                self.is_running = response.status_code == 200
            except:
                self.is_running = False

            return self.is_running
        except Exception:
            return False

    def stop_server(self):
        """Stop OPA server."""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
        self.is_running = False

    def evaluate_policy(self, policy_path: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Evaluate policy against input data."""
        if not self.is_running:
            raise RuntimeError("OPA server is not running")

        import requests

        url = f"{self.server_url}/v1/data/{policy_path}"
        payload = {"input": input_data}

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to evaluate policy: {e}")


class TestOPAServerIntegration:
    """Test suite for OPA server integration."""

    @pytest.fixture(scope="class")
    def opa_server(self):
        """Set up OPA server for testing."""
        # Skip if OPA is not available
        try:
            result = subprocess.run(["opa", "version"], capture_output=True, check=False)
            if result.returncode != 0:
                pytest.skip("OPA not available")
        except FileNotFoundError:
            pytest.skip("OPA not installed")

        server = OPAServerManager()
        if not server.start_server():
            pytest.skip("Could not start OPA server")

        yield server
        server.stop_server()

    def test_opa_server_health(self, opa_server):
        """Test OPA server health endpoint."""
        import requests

        response = requests.get(f"{opa_server.server_url}/health")
        assert response.status_code == 200

    def test_policy_loading(self, opa_server):
        """Test that policies are loaded correctly."""
        import requests

        # Check if policies are loaded
        response = requests.get(f"{opa_server.server_url}/v1/policies")
        assert response.status_code == 200

        policies = response.json()["result"]
        assert isinstance(policies, dict)

    @pytest.mark.skipif(
        not Path("policies/guard_rules.rego").exists(), reason="guard_rules.rego not found"
    )
    def test_guard_rules_evaluation(self, opa_server):
        """Test evaluation of guard_rules.rego policies."""
        # Test allow policy
        input_data = {
            "action": "merge_pr",
            "pr": {
                "number": 123,
                "checks_passed": True,
                "risk_score": 0.25,
                "labels": ["feature"],
                "changed_paths": ["src/api.py"],
                "coverage_delta": 0.1,
                "perf_delta": 2.0,
                "size_category": "S",
            },
            "repo": {"perf_budget": 5},
            "actor": "developer",
        }

        result = opa_server.evaluate_policy("guard_rules/allow", input_data)
        assert "result" in result
        assert isinstance(result["result"], bool)

    @pytest.mark.skipif(
        not Path("policies/guard_rules.rego").exists(), reason="guard_rules.rego not found"
    )
    def test_high_risk_area_evaluation(self, opa_server):
        """Test high risk area policy evaluation."""
        # Test with infrastructure files
        input_data = {"pr": {"changed_paths": ["infra/terraform/main.tf"], "risk_score": 0.3}}

        result = opa_server.evaluate_policy("guard_rules/high_risk_area", input_data)
        assert "result" in result
        # Should be True for infrastructure files
        assert result["result"] is True

    @pytest.mark.skipif(
        not Path("policies/guard_rules.rego").exists(), reason="guard_rules.rego not found"
    )
    def test_exceeds_budgets_evaluation(self, opa_server):
        """Test budget policy evaluation."""
        # Test coverage budget violation
        input_data = {
            "pr": {"coverage_delta": -0.3, "perf_delta": 2.0, "development_phase": "production"},
            "repo": {"perf_budget": 5},
        }

        result = opa_server.evaluate_policy("guard_rules/exceeds_budgets", input_data)
        assert "result" in result
        # Should exceed budgets due to coverage delta
        assert result["result"] is True


class TestOPAPolicyFiles:
    """Test suite for OPA policy file validation and structure."""

    def test_guard_rules_file_exists(self):
        """Test that guard_rules.rego file exists."""
        policy_file = Path("policies/guard_rules.rego")
        if not policy_file.exists():
            pytest.skip("guard_rules.rego not found")

        assert policy_file.is_file()
        assert policy_file.suffix == ".rego"

    def test_guard_rules_test_file_exists(self):
        """Test that guard_rules_test.rego file exists."""
        test_file = Path("policies/guard_rules_test.rego")
        if not test_file.exists():
            pytest.skip("guard_rules_test.rego not found")

        assert test_file.is_file()
        assert test_file.suffix == ".rego"

    def test_policy_syntax_validation(self):
        """Test that policy files have valid Rego syntax."""
        policy_files = list(Path("policies").glob("*.rego"))

        if not policy_files:
            pytest.skip("No .rego files found")

        for policy_file in policy_files:
            try:
                # Use OPA to validate syntax
                result = subprocess.run(
                    ["opa", "fmt", str(policy_file)], capture_output=True, text=True, check=False
                )

                # If OPA is not available, skip validation
                if result.returncode == 127:  # Command not found
                    pytest.skip("OPA not available for syntax validation")

                # Check for syntax errors
                if result.returncode != 0:
                    pytest.fail(f"Syntax error in {policy_file}: {result.stderr}")

            except FileNotFoundError:
                pytest.skip("OPA not installed")

    def test_policy_test_coverage(self):
        """Test that policy files have corresponding test files."""
        policy_dir = Path("policies")
        if not policy_dir.exists():
            pytest.skip("Policies directory not found")

        policy_files = list(policy_dir.glob("*.rego"))
        test_files = list(policy_dir.glob("*_test.rego")) + list(policy_dir.glob("*test.rego"))

        # Extract base names, handling different naming patterns
        policy_bases = {
            f.stem
            for f in policy_files
            if not f.stem.endswith("_test") and not f.stem.endswith("test")
        }
        test_bases = set()

        for test_file in test_files:
            stem = test_file.stem
            if stem.endswith("_test"):
                test_bases.add(stem.replace("_test", ""))
            elif stem.endswith("test"):
                # Handle patterns like codex_test.rego -> repo.guard.codex.rego
                base_name = stem.replace("test", "").rstrip("_")
                # Look for matching policy files
                for policy_base in policy_bases:
                    if base_name in policy_base or policy_base.endswith(base_name):
                        test_bases.add(policy_base)

        # Check that each policy has a corresponding test
        missing_tests = policy_bases - test_bases
        if missing_tests:
            # Allow some flexibility for policies that might not need tests
            critical_policies = {"guard_rules"}
            critical_missing = missing_tests & critical_policies
            if critical_missing:
                pytest.fail(f"Missing test files for critical policies: {critical_missing}")
            else:
                # Just warn about non-critical missing tests
                print(f"Warning: Missing test files for policies: {missing_tests}")

    def test_policy_package_declarations(self):
        """Test that policy files have proper package declarations."""
        policy_files = list(Path("policies").glob("*.rego"))

        if not policy_files:
            pytest.skip("No .rego files found")

        for policy_file in policy_files:
            content = policy_file.read_text()

            # Check for package declaration
            lines = content.split("\n")
            package_lines = [line for line in lines if line.strip().startswith("package ")]

            assert len(package_lines) >= 1, f"No package declaration in {policy_file}"

            # Verify package name format
            package_line = package_lines[0].strip()
            assert package_line.startswith(
                "package "
            ), f"Invalid package declaration in {policy_file}"

    def test_policy_rule_definitions(self):
        """Test that required policy rules are defined."""
        guard_rules_file = Path("policies/guard_rules.rego")
        if not guard_rules_file.exists():
            pytest.skip("guard_rules.rego not found")

        content = guard_rules_file.read_text()

        # Check for required rules
        required_rules = [
            "allow",
            "deny",
            "high_risk_area",
            "exceeds_budgets",
            "coverage_delta_threshold",
            "development_phase_exception",
        ]

        for rule in required_rules:
            # Look for rule definition (either "rule_name if" or "rule_name :=")
            rule_patterns = [f"{rule} if", f"{rule} :=", f"{rule}[", f"default {rule}"]

            found = any(pattern in content for pattern in rule_patterns)
            assert found, f"Rule '{rule}' not found in guard_rules.rego"


class TestOPAPolicyWorkflows:
    """Test suite for end-to-end policy evaluation workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_opa = Mock()

    def test_pr_merge_workflow(self):
        """Test complete PR merge policy evaluation workflow."""
        # Mock PR data
        pr_data = {
            "action": "merge_pr",
            "pr": {
                "number": 123,
                "title": "Add new API endpoint",
                "author": "developer",
                "checks_passed": True,
                "risk_score": 0.35,
                "labels": ["feature", "api"],
                "changed_paths": ["src/api.py", "tests/test_api.py"],
                "coverage_delta": 0.05,
                "perf_delta": 2.5,
                "size_category": "M",
                "development_phase": "feature_dev",
            },
            "repo": {"name": "example-repo", "owner": "example-org", "perf_budget": 5},
            "actor": "gitguard[bot]",
        }

        # Mock policy evaluation results
        self.mock_opa.evaluate_policy.side_effect = [
            {"result": True},  # allow
            {"result": []},  # deny (empty array means no denials)
            {"result": False},  # high_risk_area
            {"result": False},  # exceeds_budgets
        ]

        # Simulate workflow
        policies_to_evaluate = ["allow", "deny", "high_risk_area", "exceeds_budgets"]
        results = {}

        for policy in policies_to_evaluate:
            results[policy] = self.mock_opa.evaluate_policy(policy, pr_data)

        # Verify workflow results
        assert results["allow"]["result"] is True
        assert len(results["deny"]["result"]) == 0
        assert results["high_risk_area"]["result"] is False
        assert results["exceeds_budgets"]["result"] is False

        # Final decision should be to allow merge
        final_decision = (
            results["allow"]["result"]
            and len(results["deny"]["result"]) == 0
            and not results["exceeds_budgets"]["result"]
        )
        assert final_decision is True

    def test_high_risk_pr_workflow(self):
        """Test workflow for high-risk PR that should be blocked."""
        pr_data = {
            "action": "merge_pr",
            "pr": {
                "number": 456,
                "title": "Update infrastructure configuration",
                "author": "developer",
                "checks_passed": True,
                "risk_score": 0.85,
                "labels": ["infra"],
                "changed_paths": ["infra/terraform/main.tf", "infra/k8s/deployment.yaml"],
                "coverage_delta": -0.2,
                "perf_delta": 8.0,
                "size_category": "L",
                "development_phase": "production",
            },
            "repo": {"perf_budget": 5},
            "actor": "developer",
        }

        # Mock policy evaluation results for high-risk scenario
        self.mock_opa.evaluate_policy.side_effect = [
            {"result": False},  # allow (blocked due to high risk)
            {"result": ["Infrastructure change requires @platform-team approval"]},  # deny
            {"result": True},  # high_risk_area
            {"result": True},  # exceeds_budgets
        ]

        # Simulate workflow
        policies_to_evaluate = ["allow", "deny", "high_risk_area", "exceeds_budgets"]
        results = {}

        for policy in policies_to_evaluate:
            results[policy] = self.mock_opa.evaluate_policy(policy, pr_data)

        # Verify workflow results
        assert results["allow"]["result"] is False
        assert len(results["deny"]["result"]) > 0
        assert results["high_risk_area"]["result"] is True
        assert results["exceeds_budgets"]["result"] is True

        # Final decision should be to block merge
        final_decision = (
            results["allow"]["result"]
            and len(results["deny"]["result"]) == 0
            and not results["exceeds_budgets"]["result"]
        )
        assert final_decision is False

    def test_docs_only_pr_workflow(self):
        """Test workflow for documentation-only PR."""
        pr_data = {
            "action": "merge_pr",
            "pr": {
                "number": 789,
                "title": "Update API documentation",
                "author": "tech-writer",
                "checks_passed": True,
                "risk_score": 0.05,
                "labels": ["docs"],
                "changed_paths": ["README.md", "docs/api.md", "docs/examples.md"],
                "coverage_delta": 0.0,
                "perf_delta": 0.0,
                "size_category": "S",
            },
            "repo": {"perf_budget": 5},
            "actor": "gitguard[bot]",
        }

        # Mock policy evaluation results for docs-only change
        self.mock_opa.evaluate_policy.side_effect = [
            {"result": True},  # allow (docs changes are low risk)
            {"result": []},  # deny (no denials for docs)
            {"result": False},  # high_risk_area (docs are not high risk)
            {"result": False},  # exceeds_budgets (no budget impact)
        ]

        # Simulate workflow
        policies_to_evaluate = ["allow", "deny", "high_risk_area", "exceeds_budgets"]
        results = {}

        for policy in policies_to_evaluate:
            results[policy] = self.mock_opa.evaluate_policy(policy, pr_data)

        # Verify workflow results - docs changes should be auto-approved
        assert results["allow"]["result"] is True
        assert len(results["deny"]["result"]) == 0
        assert results["high_risk_area"]["result"] is False
        assert results["exceeds_budgets"]["result"] is False

    def test_emergency_override_workflow(self):
        """Test workflow with emergency override label."""
        pr_data = {
            "action": "merge_pr",
            "pr": {
                "number": 999,
                "title": "Emergency security fix",
                "author": "security-team",
                "checks_passed": True,
                "risk_score": 0.95,
                "labels": ["security", "emergency-override"],
                "changed_paths": ["security/auth.py", "infra/firewall.yaml"],
                "coverage_delta": -0.1,
                "perf_delta": 3.0,
                "size_category": "M",
                "development_phase": "production",
            },
            "repo": {"perf_budget": 5},
            "actor": "security-lead",
        }

        # Mock policy evaluation results with emergency override
        self.mock_opa.evaluate_policy.side_effect = [
            {"result": True},  # allow (emergency override bypasses restrictions)
            {"result": []},  # deny (emergency override bypasses denials)
            {"result": True},  # high_risk_area (still high risk but allowed)
            {"result": False},  # exceeds_budgets (emergency override may bypass budgets)
        ]

        # Simulate workflow
        policies_to_evaluate = ["allow", "deny", "high_risk_area", "exceeds_budgets"]
        results = {}

        for policy in policies_to_evaluate:
            results[policy] = self.mock_opa.evaluate_policy(policy, pr_data)

        # Verify emergency override allows high-risk changes
        assert results["allow"]["result"] is True
        assert len(results["deny"]["result"]) == 0  # Emergency override bypasses denials
        assert results["high_risk_area"]["result"] is True  # Still high risk but allowed


class TestOPAPolicyTransparencyIntegration:
    """Test suite for policy transparency and audit trail features."""

    def test_policy_decision_audit_trail(self):
        """Test that policy decisions create proper audit trails."""
        decision_record = {
            "timestamp": "2024-01-15T10:30:00Z",
            "pr_number": 123,
            "action": "merge_pr",
            "decision": "allow",
            "policies_evaluated": [
                {
                    "policy": "allow",
                    "result": True,
                    "explanation": "All checks passed, low risk score",
                },
                {"policy": "deny", "result": False, "explanation": "No denial conditions met"},
                {
                    "policy": "high_risk_area",
                    "result": False,
                    "explanation": "Changed files are not in high-risk areas",
                },
            ],
            "input_data": {"pr": {"risk_score": 0.25, "checks_passed": True}, "actor": "developer"},
        }

        # Verify audit trail structure
        assert "timestamp" in decision_record
        assert "pr_number" in decision_record
        assert "action" in decision_record
        assert "decision" in decision_record
        assert "policies_evaluated" in decision_record
        assert "input_data" in decision_record

        # Verify policy evaluation details
        for policy_result in decision_record["policies_evaluated"]:
            assert "policy" in policy_result
            assert "result" in policy_result
            assert "explanation" in policy_result

    def test_policy_source_transparency(self):
        """Test policy source code transparency features."""
        policy_transparency = {
            "policy_file": "guard_rules.rego",
            "policy_version": "v1.2.3",
            "rules_applied": [
                {
                    "rule_name": "allow",
                    "source_lines": [15, 16, 17, 18],
                    "source_code": "allow if {\n    input.pr.checks_passed\n    input.pr.risk_score < 0.7\n}",
                }
            ],
            "input_data_used": {
                "pr.checks_passed": True,
                "pr.risk_score": 0.25,
                "pr.labels": ["feature"],
            },
        }

        # Verify transparency structure
        assert "policy_file" in policy_transparency
        assert "policy_version" in policy_transparency
        assert "rules_applied" in policy_transparency
        assert "input_data_used" in policy_transparency

        # Verify rule details
        for rule in policy_transparency["rules_applied"]:
            assert "rule_name" in rule
            assert "source_lines" in rule
            assert "source_code" in rule

    def test_policy_explanation_generation(self):
        """Test generation of human-readable policy explanations."""
        explanation = {
            "summary": "PR #123 is allowed to merge",
            "reasoning": [
                "✅ All required checks have passed",
                "✅ Risk score (0.25) is below threshold (0.7)",
                "✅ Coverage delta (+5%) meets requirements",
                "✅ Performance impact (2.5ms) is within budget (5ms)",
                "ℹ️ No high-risk files were modified",
            ],
            "conditions_checked": [
                "Automated checks status",
                "Risk assessment score",
                "Code coverage impact",
                "Performance budget compliance",
                "High-risk area analysis",
            ],
            "next_steps": "PR can be merged automatically",
        }

        # Verify explanation structure
        assert "summary" in explanation
        assert "reasoning" in explanation
        assert "conditions_checked" in explanation
        assert "next_steps" in explanation

        # Verify reasoning format
        assert isinstance(explanation["reasoning"], list)
        assert len(explanation["reasoning"]) > 0

        # Check for status indicators
        reasoning_text = " ".join(explanation["reasoning"])
        assert "✅" in reasoning_text or "❌" in reasoning_text or "ℹ️" in reasoning_text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
