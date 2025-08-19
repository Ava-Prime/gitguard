#!/usr/bin/env python3
"""
GitGuard Coverage Gate Detector

Determines appropriate coverage requirements based on:
1. Development phase indicators
2. Test file completeness
3. OPA fixture availability
4. File maturity markers

Usage:
    python scripts/coverage_gate_detector.py [--changed-files file1,file2,...]

Outputs JSON with coverage requirements and rationale.
"""

import argparse
import json
import re
import sys
from pathlib import Path


class CoverageGateDetector:
    """Detects appropriate coverage gates based on development phase and file completeness."""

    # Coverage thresholds for different phases
    COVERAGE_THRESHOLDS = {
        "initial_dev": 60,  # MVP/Prototype phase
        "feature_dev": 70,  # Active development
        "pre_production": 80,  # Stabilization phase
        "production": 85,  # Maintenance/production
    }

    # File patterns indicating different development phases
    INITIAL_DEV_PATTERNS = [
        r".*/(experimental|prototype|draft|poc)/.*",
        r".*/test_.*_draft\.py$",
        r".*/.*_experimental\.py$",
    ]

    PRODUCTION_PATTERNS = [
        r".*/apps/guard-(api|brain|codex|ci)/.*\.py$",
        r".*/policies/.*\.rego$",
        r".*/ops/.*\.(yml|yaml)$",
    ]

    # Markers indicating incomplete implementations
    INCOMPLETE_MARKERS = [
        "TODO: implement",
        "FIXME:",
        "XXX:",
        "HACK:",
        "NOTE: incomplete",
        "pass  # placeholder",
        "...  # placeholder",
        "raise NotImplementedError",
    ]

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def detect_development_phase(self, changed_files: list[str]) -> tuple[str, dict]:
        """Detect the development phase based on changed files and their content."""

        phase_indicators = {
            "initial_dev": 0,
            "feature_dev": 0,
            "pre_production": 0,
            "production": 0,
        }

        analysis = {
            "files_analyzed": len(changed_files),
            "incomplete_files": [],
            "missing_tests": [],
            "missing_opa_fixtures": [],
            "production_files": [],
            "experimental_files": [],
        }

        for file_path in changed_files:
            full_path = self.repo_root / file_path

            # Check file patterns
            if any(re.match(pattern, file_path) for pattern in self.INITIAL_DEV_PATTERNS):
                phase_indicators["initial_dev"] += 2
                analysis["experimental_files"].append(file_path)

            elif any(re.match(pattern, file_path) for pattern in self.PRODUCTION_PATTERNS):
                phase_indicators["production"] += 2
                analysis["production_files"].append(file_path)

            else:
                phase_indicators["feature_dev"] += 1

            # Analyze file content if it exists
            if full_path.exists() and full_path.suffix == ".py":
                content = full_path.read_text(encoding="utf-8", errors="ignore")

                # Check for incomplete implementation markers
                incomplete_count = sum(1 for marker in self.INCOMPLETE_MARKERS if marker in content)

                if incomplete_count > 0:
                    phase_indicators["initial_dev"] += incomplete_count
                    analysis["incomplete_files"].append(
                        {"file": file_path, "incomplete_markers": incomplete_count}
                    )

                # Check for comprehensive tests and docstrings
                if self._has_comprehensive_tests(content):
                    phase_indicators["pre_production"] += 1

            # Check for corresponding test files
            if file_path.endswith(".py") and not file_path.startswith("test_"):
                test_file = self._get_test_file_path(file_path)
                if not (self.repo_root / test_file).exists():
                    analysis["missing_tests"].append(file_path)
                    phase_indicators["initial_dev"] += 1

            # Check for OPA policy fixtures
            if file_path.endswith(".rego") and not file_path.endswith("_test.rego"):
                test_file = file_path.replace(".rego", "_test.rego")
                if not (self.repo_root / test_file).exists():
                    analysis["missing_opa_fixtures"].append(file_path)
                    phase_indicators["initial_dev"] += 1

        # Determine dominant phase
        dominant_phase = max(phase_indicators.items(), key=lambda x: x[1])[0]

        # Apply business rules
        if analysis["missing_tests"] or analysis["missing_opa_fixtures"]:
            if dominant_phase in ["pre_production", "production"]:
                dominant_phase = "feature_dev"  # Downgrade due to missing tests

        if len(analysis["incomplete_files"]) > len(changed_files) * 0.3:
            dominant_phase = "initial_dev"  # Too many incomplete files

        return dominant_phase, analysis

    def _has_comprehensive_tests(self, content: str) -> bool:
        """Check if code has comprehensive test coverage indicators."""
        indicators = [
            "@pytest.mark",
            "def test_",
            "class Test",
            "assert ",
            "@mock.patch",
            "with pytest.raises",
        ]
        return sum(1 for indicator in indicators if indicator in content) >= 3

    def _get_test_file_path(self, source_file: str) -> str:
        """Generate expected test file path for a source file."""
        if source_file.startswith("apps/"):
            # apps/guard-api/main.py -> tests/test_guard_api_main.py
            parts = source_file.split("/")
            app_name = parts[1].replace("-", "_")
            file_name = Path(parts[-1]).stem
            return f"tests/test_{app_name}_{file_name}.py"
        else:
            # src/module.py -> tests/test_module.py
            file_name = Path(source_file).stem
            return f"tests/test_{file_name}.py"

    def get_coverage_requirements(self, changed_files: list[str]) -> dict:
        """Get coverage requirements based on development phase analysis."""

        phase, analysis = self.detect_development_phase(changed_files)
        threshold = self.COVERAGE_THRESHOLDS[phase]

        # Calculate delta threshold (how much coverage can drop)
        delta_thresholds = {
            "initial_dev": -5.0,  # Allow significant drops during prototyping
            "feature_dev": -2.0,  # Standard development tolerance
            "pre_production": -1.0,  # Stricter as we approach production
            "production": -0.5,  # Very strict for production code
        }

        requirements = {
            "phase": phase,
            "coverage_threshold": threshold,
            "coverage_delta_threshold": delta_thresholds[phase],
            "enforce_policy_tests": phase in ["pre_production", "production"],
            "require_opa_fixtures": phase in ["pre_production", "production"],
            "allow_incomplete_tests": phase in ["initial_dev", "feature_dev"],
            "analysis": analysis,
            "rationale": self._generate_rationale(phase, analysis),
        }

        return requirements

    def _generate_rationale(self, phase: str, analysis: dict) -> str:
        """Generate human-readable rationale for coverage requirements."""

        rationales = {
            "initial_dev": "Relaxed coverage (60%) due to initial development phase. "
            "Focus on core functionality and critical paths.",
            "feature_dev": "Standard coverage (70%) for active development. "
            "Most functionality should be tested.",
            "pre_production": "High coverage (80%) required for stabilization phase. "
            "All critical paths must be tested.",
            "production": "Strict coverage (85%) for production-ready code. "
            "Comprehensive testing required.",
        }

        base_rationale = rationales[phase]

        # Add specific concerns
        concerns = []
        if analysis["missing_tests"]:
            concerns.append(f"{len(analysis['missing_tests'])} files missing tests")
        if analysis["missing_opa_fixtures"]:
            concerns.append(f"{len(analysis['missing_opa_fixtures'])} policies missing fixtures")
        if analysis["incomplete_files"]:
            concerns.append(
                f"{len(analysis['incomplete_files'])} files have incomplete implementations"
            )

        if concerns:
            base_rationale += f" Concerns: {', '.join(concerns)}."

        return base_rationale


def main():
    parser = argparse.ArgumentParser(description="Detect coverage gate requirements")
    parser.add_argument("--changed-files", help="Comma-separated list of changed files", default="")
    parser.add_argument("--repo-root", help="Repository root directory", default=".")
    parser.add_argument(
        "--output-format", choices=["json", "env"], default="json", help="Output format"
    )

    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    changed_files = [f.strip() for f in args.changed_files.split(",") if f.strip()]

    detector = CoverageGateDetector(repo_root)
    requirements = detector.get_coverage_requirements(changed_files)

    if args.output_format == "json":
        print(json.dumps(requirements, indent=2))
    elif args.output_format == "env":
        # Output environment variables for CI
        print(f"COVERAGE_THRESHOLD={requirements['coverage_threshold']}")
        print(f"COVERAGE_DELTA_THRESHOLD={requirements['coverage_delta_threshold']}")
        print(f"DEVELOPMENT_PHASE={requirements['phase']}")
        print(f"ENFORCE_POLICY_TESTS={str(requirements['enforce_policy_tests']).lower()}")
        print(f"REQUIRE_OPA_FIXTURES={str(requirements['require_opa_fixtures']).lower()}")
        print(f"ALLOW_INCOMPLETE_TESTS={str(requirements['allow_incomplete_tests']).lower()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
