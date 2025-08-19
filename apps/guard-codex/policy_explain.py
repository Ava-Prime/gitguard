#!/usr/bin/env python3
"""
Policy transparency module for GitGuard Codex.
Provides detailed policy explanations and rule sources for PR pages.
"""

import json
from pathlib import Path


def load_rego_snippet(policy_name: str, policies_dir: Path) -> str:
    """
    Load a snippet of Rego code containing the specified policy.

    Args:
        policy_name: Name of the policy to find
        policies_dir: Directory containing .rego policy files

    Returns:
        Formatted code block with ~30 lines of context around the policy
    """
    snippet = []

    # Search through all .rego files in the policies directory
    for f in policies_dir.glob("**/*.rego"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            if policy_name in text:
                # Find the first occurrence and grab context around it
                lines = text.splitlines()
                for i, line in enumerate(lines):
                    if policy_name in line:
                        # Get 15 lines before and after for context
                        lo, hi = max(0, i - 15), min(len(lines), i + 15)
                        snippet = lines[lo:hi]
                        break
                if snippet:
                    break
        except Exception:
            # Skip files that can't be read
            continue

    if snippet:
        return "```rego\n" + "\n".join(snippet) + "\n```"
    else:
        return "_rule source not found_"


def render_policy_block(policies: list[str], opa_inputs: dict, policies_dir: str) -> str:
    """
    Render a complete policy evaluation block for PR documentation.

    Args:
        policies: List of policy names that were evaluated
        opa_inputs: Input data that was passed to OPA for evaluation
        policies_dir: Path to the policies directory

    Returns:
        Markdown content showing policy evaluation details
    """
    parts = ["## Policy Evaluation\n"]

    if not policies:
        return "## Policy Evaluation\n_No policies recorded._"

    # Show which policies were evaluated
    parts.append("**Evaluated policies:** " + ", ".join(policies))

    # Add collapsible section for OPA inputs
    parts.append(
        "\n<details><summary>OPA inputs used</summary>\n\n```json\n"
        + json.dumps(opa_inputs or {}, indent=2)
        + "\n```\n</details>\n"
    )

    # Add collapsible sections for each policy's source code
    policies_path = Path(policies_dir)
    for policy in policies:
        parts.append(
            f"\n<details><summary>Source: <code>{policy}</code></summary>\n\n"
            + load_rego_snippet(policy, policies_path)
            + "\n</details>\n"
        )

    return "\n".join(parts)


def explain_policy_decision(
    policy_name: str, decision: bool, inputs: dict, policies_dir: str
) -> str:
    """
    Generate an explanation for a specific policy decision.

    Args:
        policy_name: Name of the policy
        decision: Whether the policy passed (True) or failed (False)
        inputs: Input data used for the decision
        policies_dir: Path to policies directory

    Returns:
        Human-readable explanation of the policy decision
    """
    status = "✅ PASSED" if decision else "❌ FAILED"

    explanation = f"### {policy_name} - {status}\n\n"

    # Add policy source
    policies_path = Path(policies_dir)
    source = load_rego_snippet(policy_name, policies_path)

    explanation += f"<details><summary>Policy Rule</summary>\n\n{source}\n</details>\n\n"

    # Add relevant inputs
    if inputs:
        explanation += f"<details><summary>Evaluation Inputs</summary>\n\n```json\n{json.dumps(inputs, indent=2)}\n```\n</details>\n\n"

    return explanation
