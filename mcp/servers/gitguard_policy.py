#!/usr/bin/env python3
"""GitGuard Policy Explanation MCP Server

Provides policy rule retrieval and visualization capabilities for enhanced
developer experience with GitGuard policy management.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        EmbeddedResource,
        ImageContent,
        Resource,
        TextContent,
        Tool,
    )
except ImportError:
    print("MCP library not found. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)


class GitGuardPolicyServer:
    """MCP Server for GitGuard policy explanation and visualization."""

    def __init__(self):
        self.repo_path = Path(os.getenv("GITGUARD_REPO_PATH", "."))
        self.policies_dir = Path(os.getenv("GITGUARD_POLICIES_DIR", "./policies"))
        self.api_base_url = os.getenv("GITGUARD_API_BASE_URL", "http://localhost:8000")

    def get_rego_rule(self, rule_name: str, policy_file: str | None = None) -> dict[str, Any]:
        """Retrieve a specific Rego policy rule.

        Args:
            rule_name: Name of the rule to retrieve
            policy_file: Optional specific policy file to search in

        Returns:
            Dictionary containing rule details, source, and metadata
        """
        try:
            if policy_file:
                policy_files = [self.policies_dir / policy_file]
            else:
                policy_files = list(self.policies_dir.glob("*.rego"))

            for policy_path in policy_files:
                if not policy_path.exists():
                    continue

                with open(policy_path, encoding="utf-8") as f:
                    content = f.read()

                # Simple rule extraction (could be enhanced with proper Rego parsing)
                lines = content.split("\n")
                rule_found = False
                rule_lines = []

                for i, line in enumerate(lines):
                    if rule_name in line and ("=" in line or "{" in line):
                        rule_found = True
                        rule_lines.append(line)

                        # Collect rule body
                        brace_count = line.count("{") - line.count("}")
                        j = i + 1
                        while j < len(lines) and (
                            brace_count > 0 or not rule_lines[-1].strip().endswith("}")
                        ):
                            rule_lines.append(lines[j])
                            brace_count += lines[j].count("{") - lines[j].count("}")
                            j += 1
                        break

                if rule_found:
                    return {
                        "rule_name": rule_name,
                        "policy_file": policy_path.name,
                        "rule_source": "\n".join(rule_lines),
                        "file_path": str(policy_path),
                        "line_number": i + 1,
                        "description": self._extract_rule_description(lines, i),
                    }

            return {
                "error": f"Rule '{rule_name}' not found in policy files",
                "searched_files": [str(p) for p in policy_files],
            }

        except Exception as e:
            return {"error": f"Failed to retrieve rule: {str(e)}", "rule_name": rule_name}

    def render_policy_block(self, pr_number: int | None = None, **kwargs) -> dict[str, Any]:
        """Render policy block visualization for a pull request.

        Args:
            pr_number: Pull request number for context
            **kwargs: Additional context parameters

        Returns:
            Dictionary containing rendered policy block and metadata
        """
        try:
            # Mock policy evaluation result (in real implementation, this would
            # integrate with GitGuard's policy engine)
            policy_result = {
                "pr_number": pr_number,
                "timestamp": "2024-01-15T10:30:00Z",
                "policies_evaluated": [
                    {
                        "name": "guard_rules.security_review",
                        "status": "PASS",
                        "message": "Security review completed successfully",
                    },
                    {
                        "name": "guard_rules.code_coverage",
                        "status": "WARN",
                        "message": "Code coverage below threshold (85% < 90%)",
                    },
                    {
                        "name": "guard_rules.breaking_changes",
                        "status": "FAIL",
                        "message": "Breaking API changes detected without version bump",
                    },
                ],
                "overall_status": "BLOCKED",
                "merge_allowed": False,
            }

            # Generate visual representation
            visual_block = self._generate_policy_visual(policy_result)

            return {
                "policy_result": policy_result,
                "visual_representation": visual_block,
                "markdown_summary": self._generate_markdown_summary(policy_result),
                "action_items": self._extract_action_items(policy_result),
            }

        except Exception as e:
            return {"error": f"Failed to render policy block: {str(e)}", "pr_number": pr_number}

    def _extract_rule_description(self, lines: list[str], rule_line: int) -> str:
        """Extract description from comments above the rule."""
        description_lines = []
        i = rule_line - 1

        while i >= 0 and (lines[i].strip().startswith("#") or lines[i].strip() == ""):
            if lines[i].strip().startswith("#"):
                description_lines.insert(0, lines[i].strip()[1:].strip())
            i -= 1

        return " ".join(description_lines) if description_lines else "No description available"

    def _generate_policy_visual(self, policy_result: dict[str, Any]) -> str:
        """Generate ASCII art visualization of policy status."""
        status_symbols = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️"}

        visual = []
        visual.append("┌─ GitGuard Policy Evaluation ─────────────────────┐")
        visual.append(f"│ PR #{policy_result.get('pr_number', 'N/A'):<45} │")
        visual.append("├───────────────────────────────────────────────────┤")

        for policy in policy_result.get("policies_evaluated", []):
            symbol = status_symbols.get(policy["status"], "❓")
            name = policy["name"][:35] + "..." if len(policy["name"]) > 35 else policy["name"]
            visual.append(f"│ {symbol} {name:<43} │")

        visual.append("├───────────────────────────────────────────────────┤")
        overall_symbol = "🚫" if not policy_result.get("merge_allowed", True) else "✅"
        status = policy_result.get("overall_status", "UNKNOWN")
        visual.append(f"│ {overall_symbol} Overall: {status:<37} │")
        visual.append("└───────────────────────────────────────────────────┘")

        return "\n".join(visual)

    def _generate_markdown_summary(self, policy_result: dict[str, Any]) -> str:
        """Generate markdown summary of policy evaluation."""
        md = []
        md.append(f"## Policy Evaluation Summary - PR #{policy_result.get('pr_number', 'N/A')}")
        md.append("")

        status_emoji = {
            "PASS": ":white_check_mark:",
            "WARN": ":warning:",
            "FAIL": ":x:",
            "SKIP": ":fast_forward:",
        }

        for policy in policy_result.get("policies_evaluated", []):
            emoji = status_emoji.get(policy["status"], ":question:")
            md.append(f"- {emoji} **{policy['name']}**: {policy['message']}")

        md.append("")
        merge_status = (
            ":white_check_mark: Merge allowed"
            if policy_result.get("merge_allowed")
            else ":no_entry: Merge blocked"
        )
        md.append(f"**Status**: {merge_status}")

        return "\n".join(md)

    def _extract_action_items(self, policy_result: dict[str, Any]) -> list[str]:
        """Extract actionable items from policy failures."""
        action_items = []

        for policy in policy_result.get("policies_evaluated", []):
            if policy["status"] in ["FAIL", "WARN"]:
                if "coverage" in policy["name"].lower():
                    action_items.append("Add tests to increase code coverage above 90%")
                elif "security" in policy["name"].lower():
                    action_items.append("Address security review findings")
                elif "breaking" in policy["name"].lower():
                    action_items.append(
                        "Update version number for breaking changes or modify API to maintain compatibility"
                    )
                else:
                    action_items.append(f"Resolve issue in {policy['name']}: {policy['message']}")

        return action_items


def create_server() -> Server:
    """Create and configure the GitGuard Policy MCP server."""
    server = Server("gitguard-policy-explainer")
    policy_server: GitGuardPolicyServer = GitGuardPolicyServer()

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="get_rego_rule",
                description="Retrieve a specific Rego policy rule with source code and metadata",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "rule_name": {
                            "type": "string",
                            "description": "Name of the rule to retrieve",
                        },
                        "policy_file": {
                            "type": "string",
                            "description": "Optional specific policy file to search in",
                        },
                    },
                    "required": ["rule_name"],
                },
            ),
            Tool(
                name="render_policy_block",
                description="Render policy block visualization for a pull request",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pr_number": {
                            "type": "integer",
                            "description": "Pull request number for context",
                        }
                    },
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        if name == "get_rego_rule":
            result = policy_server.get_rego_rule(
                rule_name=arguments["rule_name"], policy_file=arguments.get("policy_file")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "render_policy_block":
            result = policy_server.render_policy_block(pr_number=arguments.get("pr_number"))
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    return server


async def main() -> None:
    """Main entry point for the MCP server."""
    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gitguard-policy-explainer",
                server_version="1.0.0",
                capabilities=server.get_capabilities(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
