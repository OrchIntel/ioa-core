""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Security utilities for CI Gates v1

This module provides security scanning utilities including Bandit integration,
TruffleHog secret detection, and hygiene pattern checking for the CI Gates system.
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import click


@dataclass
class SecurityScanResult:
    """Result of a security scan."""

    tool: str
    status: str  # "pass", "warn", "fail"
    issues: List[Dict[str, Any]]
    artifacts: List[str]
    error: Optional[str] = None


class SecurityScanner:
    """Security scanner for CI Gates."""

    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def run_bandit_scan(
        self, source_dir: str = "src/", config: Dict[str, Any] = None
    ) -> SecurityScanResult:
        """Run Bandit security scan."""
        config = config or {}
        block_levels = config.get("block_levels", ["HIGH", "MEDIUM"])

        try:
            # Run Bandit
            bandit_file = self.artifacts_dir / "bandit_results.json"
            cmd = [
                "bandit",
                "-r",
                source_dir,
                "-f",
                "json",
                "-o",
                str(bandit_file),
                "--exclude",
                ".venv",
                "--exclude",
                "venv",
                "--exclude",
                "ioa-env",
                "--exclude",
                "env",
                "--exclude",
                ".env",
                "--exclude",
                "node_modules",
                "--exclude",
                ".git",
                "--exclude",
                "__pycache__",
                "--exclude",
                "site-packages",
                "--exclude",
                "dist",
                "--exclude",
                "build",
            ]

            # Add severity filter - only fail on HIGH/MEDIUM issues
            if "HIGH" in block_levels and "MEDIUM" in block_levels:
                # Both HIGH and MEDIUM - use -lll for HIGH (includes MEDIUM)
                cmd.extend(["-lll"])
            elif "HIGH" in block_levels:
                # Only HIGH - use -lll for HIGH
                cmd.extend(["-lll"])
            elif "MEDIUM" in block_levels:
                # Only MEDIUM - use -ll for MEDIUM
                cmd.extend(["-ll"])
            else:
                # If no blocking levels specified, only fail on HIGH issues
                cmd.extend(["-lll"])

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

            # Parse results
            issues = []
            summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

            if bandit_file.exists():
                with open(bandit_file, "r") as f:
                    bandit_data = json.load(f)

                # Extract issues
                issues = bandit_data.get("results", [])

                # Extract summary
                metrics = bandit_data.get("metrics", {}).get("_totals", {})
                summary = {
                    "HIGH": metrics.get("SEVERITY.HIGH", 0),
                    "MEDIUM": metrics.get("SEVERITY.MEDIUM", 0),
                    "LOW": metrics.get("SEVERITY.LOW", 0),
                }

            # Determine status
            has_blocking_issues = False
            if "HIGH" in block_levels and summary["HIGH"] > 0:
                has_blocking_issues = True
            if "MEDIUM" in block_levels and summary["MEDIUM"] > 0:
                has_blocking_issues = True

            status = "fail" if has_blocking_issues else "pass"

            return SecurityScanResult(
                tool="bandit",
                status=status,
                issues=issues,
                summary=summary,
                artifacts=[str(bandit_file)],
            )

        except FileNotFoundError:
            return SecurityScanResult(
                tool="bandit",
                status="fail",
                issues=[],
                summary={"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                artifacts=[],
                error="Bandit not found - install with: pip install bandit",
            )
        except Exception as e:
            return SecurityScanResult(
                tool="bandit",
                status="fail",
                issues=[],
                summary={"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                artifacts=[],
                error=str(e),
            )

    def run_trufflehog_scan(self, config: Dict[str, Any] = None) -> SecurityScanResult:
        """Run TruffleHog secret detection scan."""
        config = config or {}

        try:
            # Run TruffleHog
            cmd = [
                "trufflehog",
                ".",
                "--json",
                "--repo_path",
                ".",
                "--exclude_paths",
                ".trufflehogignore",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

            # Parse results from stdout
            issues = []
            summary = {"secrets": 0}

            if result.stdout.strip():
                try:
                    # Parse JSON output from stdout
                    trufflehog_data = json.loads(result.stdout)

                    if isinstance(trufflehog_data, list):
                        issues = trufflehog_data
                        summary["secrets"] = len(issues)
                    else:
                        # Handle single object case
                        issues = [trufflehog_data] if trufflehog_data else []
                        summary["secrets"] = len(issues)
                except json.JSONDecodeError:
                    # If not JSON, treat as text output
                    if result.stdout.strip():
                        issues = [{"raw_output": result.stdout.strip()}]
                        summary["secrets"] = 1

            # Determine status
            status = "fail" if summary["secrets"] > 0 else "pass"

            # Write results to file for artifacts
            trufflehog_file = self.artifacts_dir / "trufflehog_results.json"
            artifacts = []
            if issues:
                with open(trufflehog_file, "w") as f:
                    json.dump(issues, f, indent=2)
                artifacts.append(str(trufflehog_file))

            return SecurityScanResult(
                tool="trufflehog",
                status=status,
                issues=issues,
                summary=summary,
                artifacts=artifacts,
            )

        except FileNotFoundError:
            return SecurityScanResult(
                tool="trufflehog",
                status="fail",
                issues=[],
                summary={"secrets": 0},
                artifacts=[],
                error="TruffleHog not found - install with: pip install trufflehog",
            )
        except Exception as e:
            return SecurityScanResult(
                tool="trufflehog",
                status="fail",
                issues=[],
                summary={"secrets": 0},
                artifacts=[],
                error=str(e),
            )

    def run_hygiene_check(
        self, forbidden_patterns: List[str], config: Dict[str, Any] = None
    ) -> SecurityScanResult:
        """Run hygiene check for forbidden patterns."""
        config = config or {}
        violations = []

        try:
            # Exclude virtual environment directories
            exclude_dirs = [
                "venv",
                ".venv",
                "ioa-env",
                "env",
                ".env",
                "node_modules",
                ".git",
                "__pycache__",
                "site-packages",
                "dist",
                "build",
            ]

            for pattern in forbidden_patterns:
                # Convert glob pattern to find command
                if pattern.startswith("**/"):
                    pattern = pattern[3:]  # Remove **/ prefix

                # Build find command with exclusions
                find_cmd = ["find", ".", "-name", pattern, "-type", "f"]
                for exclude_dir in exclude_dirs:
                    find_cmd.extend(["-not", "-path", f"*/{exclude_dir}/*"])

                # Use find command to search for patterns
                find_result = subprocess.run(
                    find_cmd, capture_output=True, text=True, cwd=Path.cwd()
                )

                if find_result.returncode == 0 and find_result.stdout.strip():
                    files = find_result.stdout.strip().split("\n")
                    for file_path in files:
                        violations.append(
                            {"file": file_path, "pattern": pattern, "severity": "HIGH"}
                        )

            # Save violations to artifacts
            artifacts = []
            if violations:
                violations_file = self.artifacts_dir / "hygiene_violations.json"
                with open(violations_file, "w") as f:
                    json.dump(violations, f, indent=2)
                artifacts.append(str(violations_file))

            # Determine status
            status = "fail" if violations else "pass"

            return SecurityScanResult(
                tool="hygiene",
                status=status,
                issues=violations,
                summary={"violations": len(violations)},
                artifacts=artifacts,
            )

        except Exception as e:
            return SecurityScanResult(
                tool="hygiene",
                status="fail",
                issues=[],
                summary={"violations": 0},
                artifacts=[],
                error=str(e),
            )

    def run_security_suite(
        self, config: Dict[str, Any]
    ) -> Dict[str, SecurityScanResult]:
        """Run complete security suite."""
        results = {}

        # Run Bandit if enabled
        if config.get("security", {}).get("tools", {}).get("bandit", True):
            click.echo("   Running Bandit security scan...")
            results["bandit"] = self.run_bandit_scan(config=config.get("security", {}))

        # Run TruffleHog if enabled
        if config.get("security", {}).get("tools", {}).get("trufflehog", True):
            click.echo("   Running TruffleHog secrets scan...")
            results["trufflehog"] = self.run_trufflehog_scan(
                config=config.get("security", {})
            )

        # Run hygiene check
        forbidden_patterns = config.get("hygiene", {}).get("forbidden_patterns", [])
        if forbidden_patterns:
            click.echo("   Running hygiene pattern check...")
            results["hygiene"] = self.run_hygiene_check(
                forbidden_patterns=forbidden_patterns, config=config.get("hygiene", {})
            )

        return results

    def generate_security_report(self, results: Dict[str, SecurityScanResult]) -> str:
        """Generate security report from scan results."""
        report_lines = []
        report_lines.append("# Security Scan Report")
        report_lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
        report_lines.append("")

        # Overall status
        all_passed = all(result.status == "pass" for result in results.values())
        overall_status = "✅ PASS" if all_passed else "❌ FAIL"
        report_lines.append(f"**Overall Status:** {overall_status}")
        report_lines.append("")

        # Individual tool results
        for tool, result in results.items():
            status_emoji = "✅" if result.status == "pass" else "❌"
            report_lines.append(f"## {status_emoji} {tool.title()}")
            report_lines.append(f"**Status:** {result.status.upper()}")
            report_lines.append("")

                for key, value in result.summary.items():
                    report_lines.append(f"- {key}: {value}")
                report_lines.append("")

            if result.issues:
                report_lines.append("**Issues Found:**")
                for issue in result.issues[:10]:  # Limit to first 10
                    if isinstance(issue, dict):
                        if "file" in issue and "pattern" in issue:
                            report_lines.append(
                                f"- {issue['file']} (pattern: {issue['pattern']})"
                            )
                        elif "filename" in issue and "test_id" in issue:
                            report_lines.append(
                                f"- {issue['filename']}:{issue['line_number']} - {issue['test_id']}"
                            )
                        else:
                            report_lines.append(f"- {str(issue)}")
                    else:
                        report_lines.append(f"- {str(issue)}")

                if len(result.issues) > 10:
                    report_lines.append(
                        f"- ... and {len(result.issues) - 10} more issues"
                    )
                report_lines.append("")

            if result.artifacts:
                report_lines.append("**Artifacts:**")
                for artifact in result.artifacts:
                    report_lines.append(f"- {artifact}")
                report_lines.append("")

        return "\n".join(report_lines)


def create_security_scanner(artifacts_dir: Path) -> SecurityScanner:
    """Create a security scanner instance."""
    return SecurityScanner(artifacts_dir)
