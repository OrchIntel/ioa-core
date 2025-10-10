# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



PR Bot Comment Utilities for CI Gates v1

This module provides utilities for generating PR bot comments and managing
GitHub integration for CI Gates validation results.
"""

"""Pr Bot Utils module."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class PRCommentData:
    """Data structure for PR comment generation."""

    pr_number: int
    profile: str
    mode: str
    duration: float
    total_gates: int
    passed: int
    warned: int
    failed: int
    skipped: int
    results: List[Dict[str, Any]]
    artifacts_dir: str
    timestamp: str


class PRBotCommentGenerator:
    """Generator for PR bot comments."""

    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir

    def generate_comment(self, summary_data: Dict[str, Any], pr_number: int) -> str:
        """Generate PR bot comment from gates summary."""
        comment_lines = []

        # Header
        comment_lines.append(f"## CI Gates v1 — Summary (PR #{pr_number})")
        comment_lines.append("")

        # Basic info with mode-specific messaging
        profile = summary_data["profile"]
        mode = summary_data["mode"]
        comment_lines.append(f"**Profile:** {profile}  ")
        comment_lines.append(f"**Mode:** {mode}  ")
        comment_lines.append(f"**Duration:** {summary_data['duration']:.2f}s  ")
        comment_lines.append("")

        # Profile-specific information
        if profile == "pr":
            comment_lines.append("**PR Profile Notes:**")
            comment_lines.append("- ✅ Governance (monitor, sample=500)")
            comment_lines.append("- ⚠️ Sustainability (nightly only)")
            comment_lines.append("- ✅ Security scan (Bandit/TruffleHog)")
            comment_lines.append("- ✅ Docs drift (monitor)")
            comment_lines.append("")
        elif profile == "nightly":
            comment_lines.append("**Nightly Profile Notes:**")
            comment_lines.append("- ✅ Full governance harness (sample=10k)")
            comment_lines.append("- ✅ Sustainability pack enabled")
            comment_lines.append("- ✅ Docs drift + link-check (strict)")
            comment_lines.append("")

        # Gate results table
        comment_lines.append("| Gate | Status | Message |")
        comment_lines.append("|------|--------|---------|")

        for result in summary_data["results"]:
            status_emoji = self._get_status_emoji(result["status"])
            message = result["message"]
            if len(message) > 50:
                message = message[:47] + "..."
            comment_lines.append(f"| {result['name']} | {status_emoji} | {message} |")

        comment_lines.append("")

        # Summary stats
        comment_lines.append(f"- ✅ Passed: {summary_data['passed']}")
        comment_lines.append(f"- ⚠️ Warned: {summary_data['warned']}")
        comment_lines.append(f"- ❌ Failed: {summary_data['failed']}")
        comment_lines.append(f"- ⏭️ Skipped: {summary_data['skipped']}")
        comment_lines.append("")

        # Detailed results
        comment_lines.append("**Details:**")
        for result in summary_data["results"]:
            if result["status"] != "pass":
                comment_lines.append(f"- **{result['name']}:** {result['message']}")
                if result.get("details"):
                    for key, value in result["details"].items():
                        if (
                            isinstance(value, (str, int, float))
                            and len(str(value)) < 100
                        ):
                            comment_lines.append(f"  - {key}: {value}")

        comment_lines.append("")

        # Artifacts
        comment_lines.append("**Artifacts:**")
        comment_lines.append(
            f"- [summary.json]({summary_data['artifacts_dir']}/summary.json)"
        )
        comment_lines.append(
            f"- [timeseries.jsonl]({summary_data['artifacts_dir']}/timeseries.jsonl)"
        )

        # Add specific artifacts if available
        for result in summary_data["results"]:
            if result.get("artifacts"):
                for artifact in result["artifacts"]:
                    artifact_name = Path(artifact).name
                    comment_lines.append(f"- [{artifact_name}]({artifact})")

        comment_lines.append("")

        # Re-run command
        comment_lines.append(
            f"**Re-run locally:** `ioa gates doctor --mode {summary_data['mode']} --requests 500`"
        )

        return "\n".join(comment_lines)

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for gate status."""
        status_emojis = {"pass": "✅", "warn": "⚠️", "fail": "❌", "skip": "⏭️"}
        return status_emojis.get(status, "❓")

    def generate_status_report(self, summary_data: Dict[str, Any]) -> str:
        """Generate status report for nightly runs."""
        report_lines = []

        # Header
        report_lines.append("# CI Gates v1 Status Report")
        report_lines.append("")
        report_lines.append(f"**Generated:** {summary_data['timestamp']}  ")
        report_lines.append(f"**Profile:** {summary_data['profile']}  ")
        report_lines.append(f"**Mode:** {summary_data['mode']}  ")
        report_lines.append(f"**Duration:** {summary_data['duration']:.2f}s  ")
        report_lines.append("")

        # Summary
        report_lines.append("## Summary")
        report_lines.append("")
        report_lines.append(f"- **Total Gates:** {summary_data['total_gates']}")
        report_lines.append(f"- **✅ Passed:** {summary_data['passed']}")
        report_lines.append(f"- **⚠️ Warned:** {summary_data['warned']}")
        report_lines.append(f"- **❌ Failed:** {summary_data['failed']}")
        report_lines.append(f"- **⏭️ Skipped:** {summary_data['skipped']}")
        report_lines.append("")

        # Gate results
        report_lines.append("## Gate Results")
        report_lines.append("")

        for result in summary_data["results"]:
            status_emoji = self._get_status_emoji(result["status"])
            report_lines.append(f"### {status_emoji} {result['name']}")
            report_lines.append(f"**Status:** {result['status']}  ")
            report_lines.append(f"**Message:** {result['message']}  ")
            report_lines.append(f"**Duration:** {result['duration']:.2f}s  ")
            report_lines.append("")

            if result.get("details"):
                report_lines.append("**Details:**")
                for key, value in result["details"].items():
                    if isinstance(value, (str, int, float)):
                        report_lines.append(f"- {key}: {value}")
                    elif isinstance(value, dict):
                        report_lines.append(f"- {key}: {json.dumps(value, indent=2)}")
                report_lines.append("")

            if result.get("artifacts"):
                report_lines.append("**Artifacts:**")
                for artifact in result["artifacts"]:
                    report_lines.append(f"- {artifact}")
                report_lines.append("")

        # Artifacts section
        report_lines.append("## Artifacts")
        report_lines.append("")
        report_lines.append(
            f"All artifacts are stored in: `{summary_data['artifacts_dir']}`"
        )
        report_lines.append("")
        report_lines.append(
        )
        report_lines.append(
            f"- **Timeseries:** `{summary_data['artifacts_dir']}/timeseries.jsonl`"
        )
        report_lines.append("")

        # Next steps
        report_lines.append("## Next Steps")
        report_lines.append("")
        report_lines.append("1. Review any failed gates and address issues")
        report_lines.append("2. Check artifacts for detailed information")
        report_lines.append("3. Update configuration if needed")
        report_lines.append("4. Monitor trends in timeseries data")

        return "\n".join(report_lines)

    def save_comment(self, comment: str, filename: str = "pr_comment.md") -> Path:
        """Save PR comment to file."""
        comment_file = self.artifacts_dir / filename
        with open(comment_file, "w") as f:
            f.write(comment)
        return comment_file

    def save_status_report(
        self, report: str, filename: str = "status_report.md"
    ) -> Path:
        """Save status report to file."""
        report_file = self.artifacts_dir / filename
        with open(report_file, "w") as f:
            f.write(report)
        return report_file


def create_pr_bot_generator(artifacts_dir: Path) -> PRBotCommentGenerator:
    """Create a PR bot comment generator."""
    return PRBotCommentGenerator(artifacts_dir)
