#!/usr/bin/env python3
"""
Unit tests for GitGuard Risk Scoring Algorithm

These tests verify the risk scoring behavior documented in docs/risk-scoring.md
and ensure the algorithm produces consistent, predictable results.
"""

import os
import sys

import pytest

# Add the scripts directory to the path to import risk_score module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from risk_score import calculate_risk_score, categorize_size

# Risk threshold constants
AUTO_MERGE_THRESHOLD = 0.30
REVIEW_THRESHOLD = 0.70
DOCS_RISK = 0.05
FEAT_RISK = 0.25
DEFAULT_RISK = 0.20


class TestRiskScoringAlgorithm:
    """Test the core risk scoring algorithm with documented examples."""

    def test_low_risk_documentation_update(self) -> None:
        """Test Example 1 from docs: Low-risk documentation update."""
        ci_data = {
            "lines_changed": 25,
            "files_touched": 1,
            "coverage_delta": 0,
            "perf_delta": 0,
            "new_tests": False,
        }

        review_data = {
            "type": "docs",
            "security_flags": False,
            "rubric_failures": [],
            "perf_budget": 5,
        }

        risk_score = calculate_risk_score(ci_data, review_data)

        # Expected calculation from docs:
        # type_risk = 0.05 (docs)
        # size_risk = 25/800 = 0.031
        # churn_risk = 1/50 = 0.02
        # coverage_risk = 0.0
        # perf_risk = 0.0
        # security_risk = 0.0
        # rubric_risk = 0.0
        # test_bonus = 0.0
        # total = 0.101

        assert risk_score == pytest.approx(0.101, abs=0.001)
        assert risk_score < AUTO_MERGE_THRESHOLD  # Should be auto-merge eligible

    def test_medium_risk_feature_addition(self) -> None:
        """Test Example 2 from docs: Medium-risk feature addition."""
        ci_data = {
            "lines_changed": 300,
            "files_touched": 8,
            "coverage_delta": -5,
            "perf_delta": 2,
            "new_tests": True,
        }

        review_data = {
            "type": "feat",
            "security_flags": False,
            "rubric_failures": [],
            "perf_budget": 5,
        }

        risk_score = calculate_risk_score(ci_data, review_data)

        # Expected calculation from docs:
        # type_risk = 0.25 (feat)
        # size_risk = 300/800 = 0.375 → 0.25 (capped)
        # churn_risk = 8/50 = 0.16
        # coverage_risk = 5/100 = 0.05
        # perf_risk = 2/5 = 0.04
        # security_risk = 0.0
        # rubric_risk = 0.0
        # test_bonus = -0.15
        # total = 0.55

        assert risk_score == pytest.approx(0.55, abs=0.001)
        assert AUTO_MERGE_THRESHOLD <= risk_score < REVIEW_THRESHOLD  # Should require review

    def test_high_risk_security_change(self) -> None:
        """Test Example 3 from docs: High-risk security change."""
        ci_data = {
            "lines_changed": 150,
            "files_touched": 3,
            "coverage_delta": -10,
            "perf_delta": 1,
            "new_tests": False,
        }

        review_data = {
            "type": "fix",
            "security_flags": True,  # Security flag detected!
            "rubric_failures": [],
            "perf_budget": 5,
        }

        risk_score = calculate_risk_score(ci_data, review_data)

        # Expected calculation from docs:
        # type_risk = 0.20 (fix)
        # size_risk = 150/800 = 0.1875
        # churn_risk = 3/50 = 0.06
        # coverage_risk = 10/100 = 0.10
        # perf_risk = 1/5 = 0.02
        # security_risk = 0.30 (Security flag!)
        # rubric_risk = 0.0
        # test_bonus = 0.0
        # total = 0.8675

        assert risk_score == pytest.approx(0.868, abs=0.001)
        assert risk_score >= REVIEW_THRESHOLD  # Should require enhanced review


class TestChangeTypeWeights:
    """Test change type risk weights."""

    def test_docs_lowest_risk(self) -> None:
        """Documentation changes should have lowest base risk."""
        ci_data = {"lines_changed": 0, "files_touched": 0, "coverage_delta": 0, "perf_delta": 0}
        review_data = {"type": "docs", "security_flags": False, "rubric_failures": []}

        risk_score = calculate_risk_score(ci_data, review_data)
        assert risk_score == DOCS_RISK  # Only type risk

    def test_feat_highest_risk(self) -> None:
        """Feature changes should have highest base risk."""
        ci_data = {"lines_changed": 0, "files_touched": 0, "coverage_delta": 0, "perf_delta": 0}
        review_data = {"type": "feat", "security_flags": False, "rubric_failures": []}

        risk_score = calculate_risk_score(ci_data, review_data)
        assert risk_score == FEAT_RISK  # Only type risk

    def test_unknown_type_default(self) -> None:
        """Unknown change types should use default weight."""
        ci_data = {"lines_changed": 0, "files_touched": 0, "coverage_delta": 0, "perf_delta": 0}
        review_data = {"type": "unknown", "security_flags": False, "rubric_failures": []}

        risk_score = calculate_risk_score(ci_data, review_data)
        assert risk_score == DEFAULT_RISK  # Default weight


class TestSizeImpact:
    """Test size-based risk calculations."""

    def test_size_risk_calculation(self) -> None:
        """Test size risk scales with lines changed."""
        base_data = {
            "files_touched": 1,
            "coverage_delta": 0,
            "perf_delta": 0,
            "new_tests": False,
        }
        review_data = {"type": "docs", "security_flags": False, "rubric_failures": []}

        # Test various sizes
        test_cases = [
            (100, 0.05 + 100 / 800 + 1 / 50),  # docs + size + churn
            (400, 0.05 + 400 / 800 + 1 / 50),  # docs + size + churn
            (800, 0.05 + 0.25 + 1 / 50),  # docs + capped size + churn
            (1600, 0.05 + 0.25 + 1 / 50),  # docs + capped size + churn
        ]

        for lines_changed, expected_risk in test_cases:
            ci_data = {**base_data, "lines_changed": lines_changed}
            risk_score = calculate_risk_score(ci_data, review_data)
            assert risk_score == pytest.approx(expected_risk, abs=0.001)

    def test_size_risk_capping(self) -> None:
        """Test that size risk is capped at 0.25."""
        ci_data = {
            "lines_changed": 10000,  # Very large change
            "files_touched": 1,
            "coverage_delta": 0,
            "perf_delta": 0,
        }
        review_data = {"type": "docs", "security_flags": False, "rubric_failures": []}

        risk_score = calculate_risk_score(ci_data, review_data)

        # Should be: docs(0.05) + capped_size(0.25) + churn(0.02) = 0.32
        assert risk_score == pytest.approx(0.32, abs=0.001)


class TestCoverageImpact:
    """Test coverage-based risk calculations."""

    def test_coverage_improvement_no_penalty(self) -> None:
        """Coverage improvements should not add risk."""
        ci_data = {
            "lines_changed": 100,
            "files_touched": 1,
            "coverage_delta": 5,  # Coverage improved
            "perf_delta": 0,
        }
        review_data = {"type": "feat", "security_flags": False, "rubric_failures": []}

        risk_score = calculate_risk_score(ci_data, review_data)

        # Should be: feat(0.25) + size(0.125) + churn(0.02) + coverage(0.0) = 0.395
        assert risk_score == pytest.approx(0.395, abs=0.001)

    def test_coverage_regression_penalty(self) -> None:
        """Coverage regressions should add risk."""
        ci_data = {
            "lines_changed": 100,
            "files_touched": 1,
            "coverage_delta": -10,  # Coverage dropped
            "perf_delta": 0,
        }
        review_data = {"type": "feat", "security_flags": False, "rubric_failures": []}

        risk_score = calculate_risk_score(ci_data, review_data)

        # Should be: feat(0.25) + size(0.125) + churn(0.02) + coverage(0.10) = 0.495
        assert risk_score == pytest.approx(0.495, abs=0.001)

    def test_coverage_risk_capping(self) -> None:
        """Coverage risk should be capped at 0.20."""
        ci_data = {
            "lines_changed": 100,
            "files_touched": 1,
            "coverage_delta": -50,  # Massive coverage drop
            "perf_delta": 0,
        }
        review_data = {"type": "feat", "security_flags": False, "rubric_failures": []}

        risk_score = calculate_risk_score(ci_data, review_data)

        # Should be: feat(0.25) + size(0.125) + churn(0.02) + capped_coverage(0.20) = 0.595
        assert risk_score == pytest.approx(0.595, abs=0.001)


class TestPerformanceImpact:
    """Test performance-based risk calculations."""

    def test_performance_improvement_no_penalty(self) -> None:
        """Performance improvements should not add risk."""
        ci_data = {
            "lines_changed": 100,
            "files_touched": 1,
            "coverage_delta": 0,
            "perf_delta": -2,  # Performance improved
        }
        review_data = {
            "type": "feat",
            "security_flags": False,
            "rubric_failures": [],
            "perf_budget": 5,
        }

        risk_score = calculate_risk_score(ci_data, review_data)

        # Should be: feat(0.25) + size(0.125) + churn(0.02) + perf(0.0) = 0.395
        assert risk_score == pytest.approx(0.395, abs=0.001)

    def test_performance_regression_penalty(self) -> None:
        """Performance regressions should add risk."""
        ci_data = {
            "lines_changed": 100,
            "files_touched": 1,
            "coverage_delta": 0,
            "perf_delta": 3,  # Performance degraded
        }
        review_data = {
            "type": "feat",
            "security_flags": False,
            "rubric_failures": [],
            "perf_budget": 5,
        }

        risk_score = calculate_risk_score(ci_data, review_data)

        # Should be: feat(0.25) + size(0.125) + churn(0.02) + perf(0.06) = 0.455
        assert risk_score == pytest.approx(0.455, abs=0.001)

    def test_performance_risk_capping(self) -> None:
        """Performance risk should be capped at 0.20."""
        ci_data = {
            "lines_changed": 100,
            "files_touched": 1,
            "coverage_delta": 0,
            "perf_delta": 50,  # Massive performance regression
        }
        review_data = {
            "type": "feat",
            "security_flags": False,
            "rubric_failures": [],
            "perf_budget": 5,
        }

        risk_score = calculate_risk_score(ci_data, review_data)

        # Should be: feat(0.25) + size(0.125) + churn(0.02) + capped_perf(0.20) = 0.595
        assert risk_score == pytest.approx(0.595, abs=0.001)


class TestSecurityFlags:
    """Test security flag impact on risk."""

    def test_security_flag_penalty(self) -> None:
        """Security flags should add significant risk."""
        ci_data = {
            "lines_changed": 50,
            "files_touched": 1,
            "coverage_delta": 0,
            "perf_delta": 0,
        }

        # Without security flags
        review_data_safe = {"type": "fix", "security_flags": False, "rubric_failures": []}
        safe_score = calculate_risk_score(ci_data, review_data_safe)

        # With security flags
        review_data_risky = {"type": "fix", "security_flags": True, "rubric_failures": []}
        risky_score = calculate_risk_score(ci_data, review_data_risky)

        # Security flag should add exactly 0.30 risk
        assert risky_score == pytest.approx(safe_score + 0.30, abs=0.001)


class TestTestBonus:
    """Test bonus for adding tests."""

    def test_test_addition_bonus(self) -> None:
        """Adding tests should reduce risk."""
        ci_data_base = {
            "lines_changed": 100,
            "files_touched": 1,
            "coverage_delta": 0,
            "perf_delta": 0,
        }
        review_data = {"type": "feat", "security_flags": False, "rubric_failures": []}

        # Without new tests
        ci_data_no_tests = {**ci_data_base, "new_tests": False}
        score_no_tests = calculate_risk_score(ci_data_no_tests, review_data)

        # With new tests
        ci_data_with_tests = {**ci_data_base, "new_tests": True}
        score_with_tests = calculate_risk_score(ci_data_with_tests, review_data)

        # Test bonus should reduce risk by exactly 0.15
        assert score_with_tests == pytest.approx(score_no_tests - 0.15, abs=0.001)


class TestRubricFailures:
    """Test rubric failure impact."""

    def test_rubric_failure_penalty(self) -> None:
        """Rubric failures should add risk."""
        ci_data = {
            "lines_changed": 100,
            "files_touched": 1,
            "coverage_delta": 0,
            "perf_delta": 0,
        }

        # No rubric failures
        review_data_clean = {"type": "feat", "security_flags": False, "rubric_failures": []}
        clean_score = calculate_risk_score(ci_data, review_data_clean)

        # Multiple rubric failures
        review_data_failures = {
            "type": "feat",
            "security_flags": False,
            "rubric_failures": [1, 1, 0, 1],
        }
        failure_score = calculate_risk_score(ci_data, review_data_failures)

        # Should add 3 failures * 0.05 = 0.15 risk
        assert failure_score == pytest.approx(clean_score + 0.15, abs=0.001)

    def test_rubric_risk_capping(self) -> None:
        """Rubric risk should be capped at 0.25."""
        ci_data = {
            "lines_changed": 100,
            "files_touched": 1,
            "coverage_delta": 0,
            "perf_delta": 0,
        }

        # Many rubric failures (more than cap)
        review_data = {
            "type": "feat",
            "security_flags": False,
            "rubric_failures": [1] * 10,  # 10 failures
        }

        risk_score = calculate_risk_score(ci_data, review_data)

        # Base risk + capped rubric risk
        expected_base = 0.25 + 100 / 800 + 1 / 50  # feat + size + churn
        expected_total = expected_base + 0.25  # + capped rubric risk

        assert risk_score == pytest.approx(expected_total, abs=0.001)


class TestRiskClamping:
    """Test risk score clamping to valid range."""

    def test_minimum_risk_clamping(self) -> None:
        """Risk scores should not go below 0.0."""
        ci_data = {
            "lines_changed": 1,
            "files_touched": 1,
            "coverage_delta": 0,
            "perf_delta": 0,
            "new_tests": True,  # Large bonus
        }
        review_data = {"type": "docs", "security_flags": False, "rubric_failures": []}

        risk_score = calculate_risk_score(ci_data, review_data)

        # Even with test bonus, should not go below 0.0
        assert risk_score >= 0.0

    def test_maximum_risk_clamping(self) -> None:
        """Risk scores should not exceed 1.0."""
        # Create extreme high-risk scenario
        ci_data = {
            "lines_changed": 10000,  # Massive change
            "files_touched": 1000,  # Many files
            "coverage_delta": -50,  # Coverage destroyed
            "perf_delta": 1000,  # Performance destroyed
        }
        review_data = {
            "type": "feat",
            "security_flags": True,  # Security issues
            "rubric_failures": [1] * 20,  # Many failures
            "perf_budget": 5,
        }

        risk_score = calculate_risk_score(ci_data, review_data)

        # Should be clamped to 1.0
        assert risk_score <= 1.0


class TestSizeCategories:
    """Test size categorization function."""

    def test_size_categorization(self) -> None:
        """Test that size categories are correctly assigned."""
        test_cases = [
            (10, "XS"),
            (50, "S"),
            (150, "M"),
            (400, "L"),
            (1000, "XL"),
        ]

        for lines_changed, expected_category in test_cases:
            category = categorize_size(lines_changed)
            assert category == expected_category


class TestCustomSettings:
    """Test risk calculation with custom settings."""

    def test_custom_weights(self) -> None:
        """Test risk calculation with custom weight settings."""
        custom_settings = {
            "change_type_weights": {
                "docs": 0.10,  # Higher than default
                "feat": 0.15,  # Lower than default
            },
            "size_threshold": 400,  # Lower threshold
            "max_files": 25,  # Lower threshold
            "security_penalty": 0.50,  # Higher penalty
            "test_bonus": -0.25,  # Larger bonus
        }

        ci_data = {
            "lines_changed": 200,
            "files_touched": 10,
            "coverage_delta": 0,
            "perf_delta": 0,
            "new_tests": True,
        }
        review_data = {"type": "feat", "security_flags": False, "rubric_failures": []}

        risk_score = calculate_risk_score(ci_data, review_data, custom_settings)

        # Expected: feat(0.15) + size(200/400=0.5→0.25) + churn(10/25=0.4→0.10) + test_bonus(-0.25) = 0.25
        assert risk_score == pytest.approx(0.25, abs=0.001)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
