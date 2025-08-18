package repo.guard

import rego.v1

# Mock time functions for testing
mock_time_friday_afternoon := 1640275200000000000  # Friday 16:00 UTC
mock_time_saturday := 1640361600000000000         # Saturday 12:00 UTC
mock_time_sunday := 1640448000000000000           # Sunday 12:00 UTC
mock_time_monday_morning := 1640505600000000000    # Monday 07:00 UTC
mock_time_monday_late := 1640509200000000000       # Monday 08:00 UTC
mock_time_tuesday := 1640595600000000000          # Tuesday 12:00 UTC

# Test data for freeze window evaluation
test_pr_adr_no_conformance := {
    "action": "merge_pr",
    "pr": {
        "number": 123,
        "changed_paths": ["docs/adr/001-api-design.md"],
        "labels": ["documentation"]
    }
}

test_pr_adr_with_conformance := {
    "action": "merge_pr",
    "pr": {
        "number": 124,
        "changed_paths": ["docs/adr/001-api-design.md"],
        "labels": ["documentation", "conformance:ok"]
    }
}

test_pr_adr_with_code_change := {
    "action": "merge_pr",
    "pr": {
        "number": 125,
        "changed_paths": ["docs/adr/001-api-design.md", "src/api.py"],
        "labels": ["documentation"]
    }
}

test_pr_non_adr := {
    "action": "merge_pr",
    "pr": {
        "number": 126,
        "changed_paths": ["src/api.py", "tests/test_api.py"],
        "labels": ["feature"]
    }
}

# Test cases for freeze_active rule
test_freeze_active_friday_afternoon if {
    freeze_active with time.now_ns as mock_time_friday_afternoon
}

test_freeze_active_saturday if {
    freeze_active with time.now_ns as mock_time_saturday
}

test_freeze_active_sunday if {
    freeze_active with time.now_ns as mock_time_sunday
}

test_freeze_active_monday_morning if {
    freeze_active with time.now_ns as mock_time_monday_morning
}

test_not_freeze_active_monday_late if {
    not freeze_active with time.now_ns as mock_time_monday_late
}

test_not_freeze_active_tuesday if {
    not freeze_active with time.now_ns as mock_time_tuesday
}

# Test cases for needs_conformance rule
test_needs_conformance_adr_no_label if {
    needs_conformance with input as test_pr_adr_no_conformance
}

test_not_needs_conformance_with_label if {
    not needs_conformance with input as test_pr_adr_with_conformance
}

test_not_needs_conformance_with_code_change if {
    not needs_conformance with input as test_pr_adr_with_code_change
}

test_not_needs_conformance_non_adr if {
    not needs_conformance with input as test_pr_non_adr
}

# Test edge cases for ADR path matching
test_needs_conformance_nested_adr if {
    needs_conformance with input as {
        "action": "merge_pr",
        "pr": {
            "changed_paths": ["docs/adr/architecture/001-microservices.md"],
            "labels": []
        }
    }
}

test_not_needs_conformance_adr_like_path if {
    not needs_conformance with input as {
        "action": "merge_pr",
        "pr": {
            "changed_paths": ["src/adr/parser.py"],
            "labels": []
        }
    }
}

# Test multiple ADR files in single PR
test_needs_conformance_multiple_adrs if {
    needs_conformance with input as {
        "action": "merge_pr",
        "pr": {
            "changed_paths": [
                "docs/adr/001-api-design.md",
                "docs/adr/002-database-choice.md",
                "README.md"
            ],
            "labels": []
        }
    }
}

# Test conformance with mixed changes
test_not_needs_conformance_mixed_with_code if {
    not needs_conformance with input as {
        "action": "merge_pr",
        "pr": {
            "changed_paths": [
                "docs/adr/001-api-design.md",
                "src/api.py",
                "tests/test_api.py"
            ],
            "labels": []
        }
    }
}

# Test freeze window edge cases
test_freeze_boundary_friday_1559 if {
    # Just before freeze starts
    not freeze_active with time.now_ns as 1640274540000000000  # Friday 15:59 UTC
}

test_freeze_boundary_friday_1600 if {
    # Exactly when freeze starts
    freeze_active with time.now_ns as mock_time_friday_afternoon
}

test_freeze_boundary_monday_0759 if {
    # Just before freeze ends
    freeze_active with time.now_ns as 1640505540000000000  # Monday 07:59 UTC
}

test_freeze_boundary_monday_0800 if {
    # Exactly when freeze ends
    not freeze_active with time.now_ns as mock_time_monday_late
}

# Test different actions (not just merge_pr)
test_needs_conformance_different_action if {
    needs_conformance with input as {
        "action": "create_pr",
        "pr": {
            "changed_paths": ["docs/adr/001-api-design.md"],
            "labels": []
        }
    }
}

# Test empty changed_paths
test_not_needs_conformance_empty_paths if {
    not needs_conformance with input as {
        "action": "merge_pr",
        "pr": {
            "changed_paths": [],
            "labels": []
        }
    }
}

# Test case sensitivity
test_not_needs_conformance_case_sensitive if {
    not needs_conformance with input as {
        "action": "merge_pr",
        "pr": {
            "changed_paths": ["DOCS/ADR/001-api-design.md"],
            "labels": []
        }
    }
}