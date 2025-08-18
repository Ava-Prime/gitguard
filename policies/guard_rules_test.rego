package repo.guard

import rego.v1

# Test data for policy evaluation
test_pr_low_risk := {
    "action": "merge_pr",
    "pr": {
        "number": 123,
        "checks_passed": true,
        "risk_score": 0.25,
        "labels": ["risk:low", "area:api", "automerge:allowed"],
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

test_pr_high_risk := {
    "action": "merge_pr",
    "pr": {
        "number": 456,
        "checks_passed": true,
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

test_pr_docs_only := {
    "action": "merge_pr",
    "pr": {
        "number": 789,
        "checks_passed": true,
        "risk_score": 0.05,
        "labels": ["docs"],
        "changed_paths": ["README.md", "docs/api.md"],
        "coverage_delta": 0.0,
        "perf_delta": 0.0,
        "size_category": "XS"
    },
    "repo": {
        "name": "example-repo",
        "owner": "example-org",
        "perf_budget": 5
    },
    "actor": "gitguard[bot]"
}

test_pr_infra_no_approval := {
    "action": "merge_pr",
    "pr": {
        "number": 101,
        "checks_passed": true,
        "risk_score": 0.30,
        "labels": ["infra"],
        "changed_paths": ["infra/terraform/main.tf"],
        "coverage_delta": 0.0,
        "perf_delta": 1.0,
        "size_category": "M"
    },
    "repo": {
        "name": "example-repo",
        "owner": "example-org",
        "perf_budget": 5
    },
    "actor": "gitguard[bot]"
}

test_pr_infra_approved := {
    "action": "merge_pr",
    "pr": {
        "number": 102,
        "checks_passed": true,
        "risk_score": 0.30,
        "labels": ["infra", "owner-approved"],
        "changed_paths": ["infra/terraform/main.tf"],
        "coverage_delta": 0.0,
        "perf_delta": 1.0,
        "size_category": "M"
    },
    "repo": {
        "name": "example-repo",
        "owner": "example-org",
        "perf_budget": 5
    },
    "actor": "gitguard[bot]"
}

test_pr_dependencies_no_sbom := {
    "action": "merge_pr",
    "pr": {
        "number": 201,
        "checks_passed": true,
        "risk_score": 0.20,
        "labels": ["dependencies"],
        "changed_paths": ["requirements.txt"],
        "coverage_delta": 0.0,
        "perf_delta": 0.0,
        "size_category": "S",
        "checks": {}
    },
    "repo": {
        "name": "example-repo",
        "owner": "example-org",
        "perf_budget": 5
    },
    "actor": "gitguard[bot]"
}

test_pr_dependencies_sbom_ok := {
    "action": "merge_pr",
    "pr": {
        "number": 202,
        "checks_passed": true,
        "risk_score": 0.20,
        "labels": ["dependencies"],
        "changed_paths": ["requirements.txt"],
        "coverage_delta": 0.0,
        "perf_delta": 0.0,
        "size_category": "S",
        "checks": {"sbom_ok": true},
        "diff_unpinned_versions": false
    },
    "repo": {
        "name": "example-repo",
        "owner": "example-org",
        "perf_budget": 5
    },
    "actor": "gitguard[bot]"
}

# Test cases for allow rule
test_allow_low_risk_pr if {
    allow with input as test_pr_low_risk
}

test_allow_docs_only_pr if {
    allow with input as test_pr_docs_only
}

test_deny_high_risk_pr if {
    not allow with input as test_pr_high_risk
}

# Test cases for high_risk_area rule
test_high_risk_area_infra if {
    high_risk_area with input as {
        "pr": {
            "changed_paths": ["infra/k8s.yaml"],
            "risk_score": 0.25
        }
    }
}

test_high_risk_area_security if {
    high_risk_area with input as {
        "pr": {
            "changed_paths": ["security/auth.py"],
            "risk_score": 0.15
        }
    }
}

test_not_high_risk_area_normal if {
    not high_risk_area with input as {
        "pr": {
            "changed_paths": ["src/api.py"],
            "risk_score": 0.15
        }
    }
}

# Test cases for exceeds_budgets rule
test_exceeds_budgets_coverage if {
    exceeds_budgets with input as {
        "pr": {
            "coverage_delta": -0.25,
            "perf_delta": 2.0
        },
        "repo": {"perf_budget": 5}
    }
}

test_exceeds_budgets_performance if {
    exceeds_budgets with input as {
        "pr": {
            "coverage_delta": 0.1,
            "perf_delta": 6.0
        },
        "repo": {"perf_budget": 5}
    }
}

test_not_exceeds_budgets if {
    not exceeds_budgets with input as {
        "pr": {
            "coverage_delta": 0.1,
            "perf_delta": 3.0
        },
        "repo": {"perf_budget": 5}
    }
}

# Test cases for development phase coverage thresholds
test_coverage_threshold_initial_dev if {
    coverage_delta_threshold == -0.5 with input as {
        "pr": {"development_phase": "initial_dev"}
    }
}

test_coverage_threshold_feature_dev if {
    coverage_delta_threshold == -0.2 with input as {
        "pr": {"development_phase": "feature_dev"}
    }
}

test_coverage_threshold_pre_production if {
    coverage_delta_threshold == -0.1 with input as {
        "pr": {"development_phase": "pre_production"}
    }
}

test_coverage_threshold_production if {
    coverage_delta_threshold == -0.05 with input as {
        "pr": {"development_phase": "production"}
    }
}

test_coverage_threshold_default if {
    coverage_delta_threshold == -0.2 with input as {
        "pr": {"other_field": "value"}
    }
}

# Test cases for development phase exceptions
test_development_phase_exception_incomplete_tests if {
    development_phase_exception with input as {
        "pr": {
            "development_phase": "initial_dev",
            "changed_paths": ["test_api.py"],
            "file_analysis": {
                "test_api.py": {"incomplete_markers": 3}
            }
        }
    }
}

test_development_phase_exception_missing_opa_fixtures if {
    development_phase_exception with input as {
        "pr": {
            "development_phase": "initial_dev",
            "changed_paths": ["policies/new_rule.rego"],
            "existing_files": ["policies/other_rule_test.rego"]
        }
    }
}

test_development_phase_exception_experimental_code if {
    development_phase_exception with input as {
        "pr": {
            "development_phase": "feature_dev",
            "changed_paths": ["src/experimental/new_feature.py"]
        }
    }
}

test_not_development_phase_exception_production if {
    not development_phase_exception with input as {
        "pr": {
            "development_phase": "production",
            "changed_paths": ["src/experimental/new_feature.py"]
        }
    }
}

# Test cases for experimental path detection
test_path_indicates_experimental_folder if {
    path_indicates_experimental("src/experimental/feature.py")
}

test_path_indicates_experimental_prototype if {
    path_indicates_experimental("apps/prototype/service.py")
}

test_path_indicates_experimental_draft if {
    path_indicates_experimental("policies/draft/new_rule.rego")
}

test_path_indicates_experimental_suffix if {
    path_indicates_experimental("src/api_experimental.py")
}

test_not_path_indicates_experimental if {
    not path_indicates_experimental("src/api.py")
}

# Test cases for budget violations with development phases
test_exceeds_budgets_with_phase_exception if {
    not exceeds_budgets with input as {
        "pr": {
            "development_phase": "initial_dev",
            "coverage_delta": -0.3,
            "changed_paths": ["test_api.py"],
            "file_analysis": {
                "test_api.py": {"incomplete_markers": 2}
            },
            "perf_delta": 2.0
        },
        "repo": {"perf_budget": 5}
    }
}

test_exceeds_budgets_without_phase_exception if {
    exceeds_budgets with input as {
        "pr": {
            "development_phase": "production",
            "coverage_delta": -0.1,
            "changed_paths": ["src/api.py"],
            "perf_delta": 2.0
        },
        "repo": {"perf_budget": 5}
    }
}

# Test cases for auto-merge with development phases
test_automerge_approved_prototype_only if {
    automerge_approved with input as {
        "pr": {
            "development_phase": "initial_dev",
            "changed_paths": ["src/experimental/feature.py", "docs/README.md"],
            "labels": ["prototype:auto-merge"]
        }
    }
}

test_requires_manual_review_phase_transition if {
    requires_manual_review with input as {
        "pr": {
            "development_phase": "pre_production",
            "changed_paths": ["src/experimental/feature.py", "apps/guard-api/main.py"]
        }
    }
}

test_requires_manual_review_coverage_regression if {
    requires_manual_review with input as {
        "pr": {
            "development_phase": "production",
            "coverage_delta": -0.02,
            "changed_paths": ["apps/guard-api/service.py"]
        }
    }
}

test_not_requires_manual_review_small_change if {
    not requires_manual_review with input as {
        "pr": {
            "development_phase": "feature_dev",
            "coverage_delta": 0.1,
            "changed_paths": ["src/utils.py"]
        }
    }
}

# Test cases for automerge_approved rule
test_automerge_approved_label if {
    automerge_approved with input as {
        "pr": {"labels": ["automerge:allowed"]}
    }
}

test_automerge_approved_size_xs if {
    automerge_approved with input as {
        "pr": {"size_category": "XS"}
    }
}

test_automerge_approved_size_s if {
    automerge_approved with input as {
        "pr": {"size_category": "S"}
    }
}

test_automerge_approved_docs_only if {
    automerge_approved with input as test_pr_docs_only
}

# Test cases for docs_only_change rule
test_docs_only_change_readme if {
    docs_only_change with input as {
        "pr": {"changed_paths": ["README.md"]}
    }
}

test_docs_only_change_docs_dir if {
    docs_only_change with input as {
        "pr": {"changed_paths": ["docs/api.md", "docs/guide.md"]}
    }
}

test_docs_only_change_mixed_md if {
    docs_only_change with input as {
        "pr": {"changed_paths": ["README.md", "CHANGELOG.md", "docs/api.md"]}
    }
}

test_not_docs_only_change_mixed if {
    not docs_only_change with input as {
        "pr": {"changed_paths": ["README.md", "src/api.py"]}
    }
}

# Test cases for infra owner approval deny rule
test_deny_infra_no_approval if {
    count(deny) > 0 with input as test_pr_infra_no_approval
}

test_allow_infra_with_approval if {
    count(deny) == 0 with input as test_pr_infra_approved
}

# Test cases for dependency SBOM deny rule
test_deny_dependencies_no_sbom if {
    count(deny) > 0 with input as test_pr_dependencies_no_sbom
}

test_allow_dependencies_with_sbom if {
    count(deny) == 0 with input as test_pr_dependencies_sbom_ok
}

# Test cases for unpinned versions deny rule
test_deny_unpinned_versions if {
    count(deny) > 0 with input as {
        "action": "merge_pr",
        "pr": {
            "labels": ["dependencies"],
            "changed_paths": ["requirements.txt"],
            "diff_unpinned_versions": true
        }
    }
}

test_allow_pinned_versions if {
    count(deny) == 0 with input as test_pr_dependencies_sbom_ok
}