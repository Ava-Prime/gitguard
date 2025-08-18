#!/usr/bin/env python3
"""
GitGuard Coverage Delta Validator

Validates that coverage changes in a PR don't exceed acceptable thresholds.
Compares coverage between base and head commits to ensure quality gates.

Usage:
    python scripts/validate_coverage_delta.py --threshold=-2.0 --base-ref=main --head-ref=HEAD
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


class CoverageDeltaValidator:
    """Validates coverage delta between commits."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        
    def get_coverage_for_ref(self, git_ref: str) -> Optional[Dict]:
        """Get coverage data for a specific git reference."""
        
        try:
            # Checkout the reference
            subprocess.run(
                ["git", "checkout", git_ref],
                cwd=self.repo_root,
                check=True,
                capture_output=True
            )
            
            # Run tests to generate coverage
            result = subprocess.run(
                [
                    "python", "-m", "pytest",
                    "--cov=./apps",
                    "--cov-report=json",
                    "--quiet",
                    "--tb=no"
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True
            )
            
            # Read coverage report
            coverage_file = self.repo_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                return {
                    "total_coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
                    "files": coverage_data.get("files", {}),
                    "summary": coverage_data.get("totals", {})
                }
                
        except subprocess.CalledProcessError as e:
            print(f"Error getting coverage for {git_ref}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error for {git_ref}: {e}")
            return None
            
        return None
    
    def calculate_delta(self, base_coverage: Dict, head_coverage: Dict) -> Dict:
        """Calculate coverage delta between base and head."""
        
        base_total = base_coverage.get("total_coverage", 0)
        head_total = head_coverage.get("total_coverage", 0)
        
        delta = {
            "total_delta": head_total - base_total,
            "base_coverage": base_total,
            "head_coverage": head_total,
            "file_deltas": {},
            "new_files": [],
            "removed_files": [],
        }
        
        base_files = set(base_coverage.get("files", {}).keys())
        head_files = set(head_coverage.get("files", {}).keys())
        
        # Files present in both commits
        common_files = base_files & head_files
        for file_path in common_files:
            base_file_cov = base_coverage["files"][file_path].get("summary", {}).get("percent_covered", 0)
            head_file_cov = head_coverage["files"][file_path].get("summary", {}).get("percent_covered", 0)
            
            file_delta = head_file_cov - base_file_cov
            if abs(file_delta) > 0.1:  # Only track significant changes
                delta["file_deltas"][file_path] = {
                    "base": base_file_cov,
                    "head": head_file_cov,
                    "delta": file_delta
                }
        
        # New and removed files
        delta["new_files"] = list(head_files - base_files)
        delta["removed_files"] = list(base_files - head_files)
        
        return delta
    
    def validate_delta(self, delta: Dict, threshold: float) -> Dict:
        """Validate coverage delta against threshold."""
        
        total_delta = delta["total_delta"]
        passed = total_delta >= threshold
        
        validation = {
            "passed": passed,
            "total_delta": total_delta,
            "threshold": threshold,
            "base_coverage": delta["base_coverage"],
            "head_coverage": delta["head_coverage"],
            "violations": [],
            "warnings": [],
            "summary": ""
        }
        
        # Check for violations
        if not passed:
            validation["violations"].append({
                "type": "total_coverage_drop",
                "message": f"Total coverage dropped by {abs(total_delta):.2f}%, exceeding threshold of {abs(threshold):.2f}%",
                "severity": "error"
            })
        
        # Check individual file regressions
        for file_path, file_delta in delta["file_deltas"].items():
            if file_delta["delta"] < -5.0:  # Significant file regression
                validation["violations"].append({
                    "type": "file_coverage_regression",
                    "file": file_path,
                    "message": f"File {file_path} coverage dropped by {abs(file_delta['delta']):.2f}%",
                    "severity": "error"
                })
            elif file_delta["delta"] < -2.0:  # Minor regression warning
                validation["warnings"].append({
                    "type": "file_coverage_warning",
                    "file": file_path,
                    "message": f"File {file_path} coverage dropped by {abs(file_delta['delta']):.2f}%",
                    "severity": "warning"
                })
        
        # Generate summary
        if passed:
            if total_delta > 0:
                validation["summary"] = f"✅ Coverage improved by {total_delta:.2f}% ({delta['base_coverage']:.1f}% → {delta['head_coverage']:.1f}%)"
            else:
                validation["summary"] = f"✅ Coverage change ({total_delta:.2f}%) within acceptable threshold"
        else:
            validation["summary"] = f"❌ Coverage regression ({total_delta:.2f}%) exceeds threshold ({threshold:.2f}%)"
        
        return validation
    
    def run_validation(self, base_ref: str, head_ref: str, threshold: float) -> Dict:
        """Run complete coverage delta validation."""
        
        print(f"Validating coverage delta: {base_ref} → {head_ref}")
        print(f"Threshold: {threshold:.2f}%")
        
        # Store current branch
        current_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        ).stdout.strip()
        
        try:
            # Get coverage for base
            print(f"Getting coverage for base ref: {base_ref}")
            base_coverage = self.get_coverage_for_ref(base_ref)
            if not base_coverage:
                return {
                    "passed": False,
                    "error": f"Could not get coverage for base ref: {base_ref}"
                }
            
            # Get coverage for head
            print(f"Getting coverage for head ref: {head_ref}")
            head_coverage = self.get_coverage_for_ref(head_ref)
            if not head_coverage:
                return {
                    "passed": False,
                    "error": f"Could not get coverage for head ref: {head_ref}"
                }
            
            # Calculate and validate delta
            delta = self.calculate_delta(base_coverage, head_coverage)
            validation = self.validate_delta(delta, threshold)
            
            return validation
            
        finally:
            # Restore original branch
            try:
                subprocess.run(
                    ["git", "checkout", current_branch],
                    cwd=self.repo_root,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                print(f"Warning: Could not restore original branch {current_branch}")


def main():
    parser = argparse.ArgumentParser(description="Validate coverage delta")
    parser.add_argument(
        "--threshold",
        type=float,
        required=True,
        help="Coverage delta threshold (negative values allow drops)"
    )
    parser.add_argument(
        "--base-ref",
        required=True,
        help="Base git reference for comparison"
    )
    parser.add_argument(
        "--head-ref",
        required=True,
        help="Head git reference for comparison"
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root directory"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "text"],
        default="text",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    repo_root = Path(args.repo_root).resolve()
    validator = CoverageDeltaValidator(repo_root)
    
    result = validator.run_validation(
        args.base_ref,
        args.head_ref,
        args.threshold
    )
    
    if args.output_format == "json":
        print(json.dumps(result, indent=2))
    else:
        # Text output
        print("\n" + "="*60)
        print("COVERAGE DELTA VALIDATION RESULT")
        print("="*60)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return 1
        
        print(result["summary"])
        
        if result["violations"]:
            print("\n🚨 VIOLATIONS:")
            for violation in result["violations"]:
                print(f"  • {violation['message']}")
        
        if result["warnings"]:
            print("\n⚠️  WARNINGS:")
            for warning in result["warnings"]:
                print(f"  • {warning['message']}")
        
        print(f"\nBase Coverage: {result.get('base_coverage', 0):.2f}%")
        print(f"Head Coverage: {result.get('head_coverage', 0):.2f}%")
        print(f"Delta: {result.get('total_delta', 0):+.2f}%")
        print(f"Threshold: {result.get('threshold', 0):+.2f}%")
    
    return 0 if result.get("passed", False) else 1


if __name__ == "__main__":
    sys.exit(main())