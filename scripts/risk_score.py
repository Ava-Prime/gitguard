#!/usr/bin/env python3
"""
GitGuard Risk Scoring Algorithm
"""
import json
import sys
from typing import Dict, List

def calculate_risk_score(ci_data: Dict, review_data: Dict, settings: Dict = None) -> float:
    """
    Calculate PR risk score based on multiple factors
    
    Returns: float between 0.0 and 1.0 (higher = riskier)
    """
    if settings is None:
        settings = {
            'change_type_weights': {
                'docs': 0.05, 'chore': 0.10, 'fix': 0.20,
                'feat': 0.25, 'refactor': 0.20
            },
            'size_threshold': 800,
            'max_files': 50,
            'security_penalty': 0.30,
            'test_bonus': -0.15
        }
    
    # Base risk from change type
    change_type = review_data.get('type', 'feat')
    type_risk = settings['change_type_weights'].get(change_type, 0.20)
    
    # Size impact (lines changed)
    lines_changed = ci_data.get('lines_changed', 0)
    size_risk = min(lines_changed / settings['size_threshold'], 0.25)
    
    # File churn impact
    files_touched = ci_data.get('files_touched', 0)
    churn_risk = min(files_touched / settings['max_files'], 0.10)
    
    # Coverage delta penalty
    coverage_delta = ci_data.get('coverage_delta', 0)
    coverage_risk = max(-coverage_delta / 1.0, 0) if coverage_delta < 0 else 0
    coverage_risk = min(coverage_risk, 0.20)
    
    # Performance impact
    perf_delta = ci_data.get('perf_delta', 0)
    perf_budget = review_data.get('perf_budget', 5)
    perf_risk = min(max(perf_delta / perf_budget, 0), 0.20)
    
    # Security flags
    security_risk = settings['security_penalty'] if review_data.get('security_flags') else 0.0
    
    # Test addition bonus
    test_bonus = settings['test_bonus'] if ci_data.get('new_tests', False) else 0.0
    
    # Code review rubric failures
    rubric_failures = review_data.get('rubric_failures', [])
    rubric_risk = min(sum(1 for failure in rubric_failures if failure > 0) * 0.05, 0.25)
    
    # Calculate total risk
    total_risk = (
        type_risk + size_risk + churn_risk + 
        coverage_risk + perf_risk + security_risk + 
        rubric_risk + test_bonus
    )
    
    # Clamp to valid range
    return max(0.0, min(1.0, round(total_risk, 3)))

def categorize_size(lines_changed: int) -> str:
    """Categorize PR size"""
    if lines_changed <= 20:
        return "XS"
    elif lines_changed <= 80:
        return "S" 
    elif lines_changed <= 200:
        return "M"
    elif lines_changed <= 500:
        return "L"
    else:
        return "XL"

if __name__ == "__main__":
    # Read JSON data from stdin
    try:
        ci_data = json.loads(sys.stdin.readline().strip())
        review_data = json.loads(sys.stdin.readline().strip())
        
        risk_score = calculate_risk_score(ci_data, review_data)
        size_category = categorize_size(ci_data.get('lines_changed', 0))
        
        result = {
            'risk_score': risk_score,
            'size_category': size_category,
            'breakdown': {
                'change_type': review_data.get('type', 'feat'),
                'lines_changed': ci_data.get('lines_changed', 0),
                'files_touched': ci_data.get('files_touched', 0),
                'coverage_delta': ci_data.get('coverage_delta', 0),
                'perf_delta': ci_data.get('perf_delta', 0),
                'security_flags': review_data.get('security_flags', False),
                'new_tests': ci_data.get('new_tests', False)
            }
        }
        
        print(json.dumps(result, indent=2))
        
    except (json.JSONDecodeError, IndexError) as e:
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        sys.exit(1)
