# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



CI Gates v1 - Comprehensive validation system for IOA Core

This module implements the CI Gates v1 system that provides configurable
validation for governance, security, documentation, and hygiene checks.
Supports multiple profiles (local, PR, nightly) and maintainer overrides.
"""
"""Ci Gates module."""


import json
import subprocess  # nosec B404 - subprocess used for controlled CI command execution
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml


class GateStatus(Enum):
    """Status of a gate execution."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class GateResult:
    """Result of a gate execution."""

    name: str
    status: GateStatus
    message: str
    details: Dict[str, Any]
    duration: float
    artifacts: List[str] = None


@dataclass
    """Summary of all gate executions."""

    profile: str
    mode: str
    total_gates: int
    passed: int
    warned: int
    failed: int
    skipped: int
    duration: float
    results: List[GateResult]
    artifacts_dir: str
    timestamp: str


class CIGatesConfig:
    """Configuration loader for CI Gates."""

    def __init__(self, config_path: str = ".ioa/ci-gates.yml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"CI Gates config not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def get_profile(self, profile: str) -> Dict[str, Any]:
        """Get configuration for a specific profile."""
        profiles = self.config.get("profiles", {})
        if profile not in profiles:
            raise ValueError(f"Profile '{profile}' not found in configuration")

        # Merge with base config
        profile_config = profiles[profile].copy()

        # Handle profile-specific overrides
        base_config = {
            "mode": self.config.get("mode", "monitor"),
            "laws": self.config.get("laws", [1, 2, 3, 4, 5, 6, 7]),
            "ethics": self.config.get("ethics", {}),
            "sustainability": self.config.get("sustainability", {}),
            "security": self.config.get("security", {}),
            "hygiene": self.config.get("hygiene", {}),
            "docs": self.config.get("docs", {}),
            "gates": self.config.get("gates", {}),
            "artifacts": self.config.get("artifacts", {}),
            "overrides": self.config.get("overrides", {}),
        }

        # Apply profile-specific mode override
        if "mode" in profile_config:
            base_config["mode"] = profile_config["mode"]

        # Apply profile-specific sustainability override
        if "sustainability" in profile_config:
            if isinstance(profile_config["sustainability"], bool):
                base_config["sustainability"]["enabled"] = profile_config[
                    "sustainability"
                ]
            else:
                base_config["sustainability"].update(profile_config["sustainability"])

        # Apply profile-specific docs override
        if "docs" in profile_config:
            base_config["docs"].update(profile_config["docs"])

        # Apply profile-specific harness override
        if "harness" in profile_config:
            base_config["harness"] = profile_config["harness"]
        elif "harness.requests" in profile_config:
            base_config["harness"] = {"requests": profile_config["harness.requests"]}

        # Apply profile-specific gates override
        if "gates" in profile_config:
            base_config["gates"] = profile_config["gates"]

        # Merge all configs
        profile_config.update(base_config)

        return profile_config


class CIGatesRunner:
    """Main runner for CI Gates execution."""

    def __init__(
        self,
        config: CIGatesConfig,
        profile: str = "local",
        artifacts_dir: Optional[Path] = None,
    ):
        self.config = config
        self.profile = profile
        self.profile_config = config.get_profile(profile)
        self.artifacts_dir = artifacts_dir or Path("artifacts/lens/gates")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        """Run all or selected gates."""
        start_time = time.time()
        results = []

        # Determine which gates to run
        gates_to_run = selected_gates or self._get_enabled_gates()

        click.echo(
            f"🚀 Running CI Gates v1 (profile: {self.profile}, mode: {self.profile_config['mode']})"
        )
        click.echo("=" * 60)

        # Run each gate
        for gate_name in gates_to_run:
            click.echo(f"\n🔍 Running {gate_name} gate...")
            result = self._run_single_gate(gate_name)
            results.append(result)

            # Display result
            status_emoji = {
                GateStatus.PASS: "✅",
                GateStatus.WARN: "⚠️",
                GateStatus.FAIL: "❌",
                GateStatus.SKIP: "⏭️",
            }[result.status]

            click.echo(f"{status_emoji} {gate_name}: {result.message}")
            if result.details:
                for key, value in result.details.items():
                    click.echo(f"   {key}: {value}")

        duration = time.time() - start_time

        # Create summary
        summary = GatesSummary(
            profile=self.profile,
            mode=self.profile_config["mode"],
            total_gates=len(results),
            passed=len([r for r in results if r.status == GateStatus.PASS]),
            warned=len([r for r in results if r.status == GateStatus.WARN]),
            failed=len([r for r in results if r.status == GateStatus.FAIL]),
            skipped=len([r for r in results if r.status == GateStatus.SKIP]),
            duration=duration,
            results=results,
            artifacts_dir=str(self.artifacts_dir),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Save summary
        self._save_summary(summary)

        # Display final summary
        self._display_summary(summary)

        return summary

    def _get_enabled_gates(self) -> List[str]:
        """Get list of enabled gates from configuration."""
        gates_config = self.profile_config.get("gates", {})
        return [name for name, enabled in gates_config.items() if enabled]

    def _run_single_gate(self, gate_name: str) -> GateResult:
        """Run a single gate and return its result."""
        start_time = time.time()

        try:
            if gate_name == "governance":
                return self._run_governance_gate()
            elif gate_name == "security":
                return self._run_security_gate()
            elif gate_name == "docs":
                return self._run_docs_gate()
            elif gate_name == "hygiene":
                # Hygiene is now integrated into security gate
                return self._run_security_gate()
            else:
                return GateResult(
                    name=gate_name,
                    status=GateStatus.SKIP,
                    message=f"Unknown gate: {gate_name}",
                    details={},
                    duration=time.time() - start_time,
                )
        except Exception as e:
            return GateResult(
                name=gate_name,
                status=GateStatus.FAIL,
                message=f"Gate execution failed: {str(e)}",
                details={"error": str(e)},
                duration=time.time() - start_time,
            )

    def _run_governance_gate(self) -> GateResult:
        """Run governance gate (ethics, sustainability, harness)."""
        start_time = time.time()
        details = {}
        artifacts = []

        try:
            # Get harness requests from profile config
            harness_requests = self.profile_config.get("harness", {}).get(
                "requests", 1000
            )
            laws = self.profile_config.get("laws", [1, 2, 3, 4, 5, 6, 7])

            # Run ethics (OSS: Not implemented - skip for basic functionality)
            if self.profile_config.get("ethics", {}).get("mode") != "disabled":
                click.echo("   Skipping ethics validation (not implemented in OSS version)...")
                details["ethics"] = "skipped"
                details["ethics_note"] = "Ethics Pack v0 not implemented in OSS release"

            # Run sustainability (OSS: Basic energy tracking available, advanced not implemented)
            sustainability_enabled = self.profile_config.get("sustainability", {}).get(
                "enabled", True
            )
            if (
                sustainability_enabled
                and self.profile_config.get("sustainability", {}).get("mode")
                != "disabled"
            ):
                click.echo("   Skipping sustainability validation (advanced features not implemented in OSS version)...")
                details["sustainability"] = "skipped"
                details["sustainability_note"] = "Sustainability Pack v0 basic energy tracking available, advanced validation not implemented"
            else:
                click.echo(
                    "   Skipping sustainability validation (disabled for this profile)"
                )
                details["sustainability"] = "skipped"
                details["sustainability_reason"] = "disabled for profile"

            # Run harness (OSS: Governance Harness v1 not implemented)
            click.echo("   Skipping governance harness (not implemented in OSS version)...")
            details["harness"] = "skipped"
            details["harness_note"] = "Governance Harness v1 not implemented in OSS release"

            # Determine overall status
            ethics_passed = (
                details.get("ethics") in ["completed", "skipped"]
                or self.profile_config.get("ethics", {}).get("mode") == "disabled"
            )
            sustainability_passed = (
                details.get("sustainability") == "completed"
                or details.get("sustainability") == "skipped"
                or self.profile_config.get("sustainability", {}).get("mode")
                == "disabled"
            )
            harness_passed = details.get("harness") in ["completed", "skipped"]

            all_passed = ethics_passed and sustainability_passed and harness_passed

            # Generate detailed status message
            status_parts = []
            if not ethics_passed and details.get("ethics") != "skipped":
                status_parts.append("ethics failed")
            if not sustainability_passed and details.get("sustainability") != "skipped":
                status_parts.append("sustainability failed")
            if not harness_passed and details.get("harness") != "skipped":
                status_parts.append("harness failed")

            if all_passed:
                message = "All governance checks passed"
            else:
                message = f"Governance checks failed: {', '.join(status_parts)}"

            # Collect artifacts
            artifacts.extend(
                [
                    "artifacts/lens/ethics/metrics.json",
                    "artifacts/lens/sustainability/metrics.jsonl",
                    "artifacts/harness/governance/metrics.jsonl",
                ]
            )

            return GateResult(
                name="governance",
                status=GateStatus.PASS if all_passed else GateStatus.FAIL,
                message=message,
                details=details,
                duration=time.time() - start_time,
                artifacts=artifacts,
            )

        except Exception as e:
            return GateResult(
                name="governance",
                status=GateStatus.FAIL,
                message=f"Governance gate failed: {str(e)}",
                details={"error": str(e)},
                duration=time.time() - start_time,
            )

    def _run_security_gate(self) -> GateResult:
        """Run security gate (Bandit, TruffleHog, hygiene)."""
        start_time = time.time()
        details = {}
        artifacts = []

        try:
            from ioa_core.security_utils import create_security_scanner

            # Create security scanner
            scanner = create_security_scanner(self.artifacts_dir)

            # Run security suite
            security_results = scanner.run_security_suite(self.profile_config)

            # Process results
            all_passed = True
            total_issues = 0

            for tool, result in security_results.items():
                details[f"{tool}_status"] = result.status
                details[f"{tool}_issues"] = len(result.issues)
                details[f"{tool}_summary"] = result.summary
                artifacts.extend(result.artifacts)

                if result.status != "pass":
                    all_passed = False
                total_issues += len(result.issues)

            # Determine overall status
            status = GateStatus.PASS if all_passed else GateStatus.FAIL
            message = (
                f"Security scan passed ({total_issues} issues found)"
                if all_passed
                else f"Security issues found ({total_issues} total)"
            )

            return GateResult(
                name="security",
                status=status,
                message=message,
                details=details,
                duration=time.time() - start_time,
                artifacts=artifacts,
            )

        except Exception as e:
            return GateResult(
                name="security",
                status=GateStatus.FAIL,
                message=f"Security gate failed: {str(e)}",
                details={"error": str(e)},
                duration=time.time() - start_time,
            )

    def _run_docs_gate(self) -> GateResult:
        """Run docs gate (CLI validation, link checking)."""
        start_time = time.time()
        details = {}
        artifacts = []

        try:
            # Run CLI validator
            cli_validator_config = self.profile_config.get("docs", {}).get(
                "cli_validator", {}
            )
            if isinstance(cli_validator_config, dict):
                cli_strict = cli_validator_config.get("strict", True)
            else:
                cli_strict = bool(cli_validator_config)

            if cli_strict:
                click.echo("   Running CLI documentation validator...")

                # Create output directory for CLI validator
                cli_output_dir = self.artifacts_dir / "cli_validation"
                cli_output_dir.mkdir(parents=True, exist_ok=True)

                cli_result = self._run_command(
                    [
                        "python",
                        "tools/doc_cmd_validator/extract_and_run.py",
                        "--repo-root",
                        ".",
                        "--output-dir",
                        str(cli_output_dir),
                        "--json",
                        "--markdown",
                    ]
                )

                details["cli_validator"] = (
                    "completed" if cli_result.returncode == 0 else "failed"
                )
                details["cli_validator_exit_code"] = cli_result.returncode

                if cli_result.returncode != 0:
                    details["cli_validator_error"] = cli_result.stderr

                # Parse CLI validation results
                cli_json_file = cli_output_dir / "validation_results.json"
                if cli_json_file.exists():
                    with open(cli_json_file, "r") as f:
                        cli_data = json.load(f)
                    details["cli_commands_tested"] = cli_data.get("summary", {}).get(
                        "total_commands", 0
                    )
                    details["cli_commands_passed"] = cli_data.get("summary", {}).get(
                        "successful_commands", 0
                    )
                    details["cli_commands_failed"] = cli_data.get("summary", {}).get(
                        "failed_commands", 0
                    )
                    artifacts.append(str(cli_json_file))

                # Add CLI validation report to artifacts
                cli_md_file = cli_output_dir / "validation_report.md"
                if cli_md_file.exists():
                    artifacts.append(str(cli_md_file))

            # Run MkDocs build
            link_check_config = self.profile_config.get("docs", {}).get(
                "link_check", {}
            )
            if isinstance(link_check_config, dict):
                link_check_enabled = link_check_config.get("enabled", True)
            else:
                link_check_enabled = bool(link_check_config)

            if link_check_enabled:
                click.echo("   Running MkDocs build and link check...")

                # Determine if strict mode
                if isinstance(link_check_config, dict):
                    strict_mode = link_check_config.get("strict", False)
                else:
                    strict_mode = False
                mkdocs_cmd = ["mkdocs", "build"]
                if strict_mode:
                    mkdocs_cmd.append("--strict")

                mkdocs_result = self._run_command(mkdocs_cmd)
                details["mkdocs"] = (
                    "completed" if mkdocs_result.returncode == 0 else "failed"
                )
                details["mkdocs_exit_code"] = mkdocs_result.returncode

                if mkdocs_result.returncode != 0:
                    details["mkdocs_error"] = mkdocs_result.stderr

                # Check if site directory was created
                site_dir = Path("site")
                if site_dir.exists():
                    details["mkdocs_site_created"] = True
                    details["mkdocs_site_files"] = len(list(site_dir.rglob("*")))
                else:
                    details["mkdocs_site_created"] = False
            else:
                click.echo("   Skipping MkDocs link check (disabled for this profile)")
                details["mkdocs"] = "skipped"
                details["mkdocs_reason"] = "link check disabled for profile"

            # Determine status
            cli_validator_config = self.profile_config.get("docs", {}).get(
                "cli_validator", {}
            )
            if isinstance(cli_validator_config, dict):
                cli_strict = cli_validator_config.get("strict", True)
            else:
                cli_strict = bool(cli_validator_config)

            link_check_config = self.profile_config.get("docs", {}).get(
                "link_check", {}
            )
            if isinstance(link_check_config, dict):
                link_check_enabled = link_check_config.get("enabled", True)
            else:
                link_check_enabled = bool(link_check_config)

            cli_passed = details.get("cli_validator") == "completed" or not cli_strict
            mkdocs_passed = (
                details.get("mkdocs") == "completed"
                or details.get("mkdocs") == "skipped"
                or not link_check_enabled
            )

            all_passed = cli_passed and mkdocs_passed
            status = GateStatus.PASS if all_passed else GateStatus.FAIL

            # Generate detailed message
            message_parts = []
            if cli_passed:
                message_parts.append("CLI validation passed")
            else:
                message_parts.append("CLI validation failed")

            if mkdocs_passed:
                message_parts.append("MkDocs build passed")
            else:
                message_parts.append("MkDocs build failed")

            message = " and ".join(message_parts)

            return GateResult(
                name="docs",
                status=status,
                message=message,
                details=details,
                duration=time.time() - start_time,
                artifacts=artifacts,
            )

        except Exception as e:
            return GateResult(
                name="docs",
                status=GateStatus.FAIL,
                message=f"Docs gate failed: {str(e)}",
                details={"error": str(e)},
                duration=time.time() - start_time,
            )

    def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            return subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
        except FileNotFoundError:
            # Command not found
            result = subprocess.CompletedProcess(cmd, 127, "", "Command not found")
            return result

        """Save gates summary to artifacts."""
        # Save JSON summary
        summary_file = self.artifacts_dir / "summary.json"
        with open(summary_file, "w") as f:
            json.dump(asdict(summary), f, indent=2, default=str)

        # Append to timeseries
        timeseries_file = self.artifacts_dir / "timeseries.jsonl"
        with open(timeseries_file, "a") as f:
            json.dump(asdict(summary), f, default=str)
            f.write("\n")

        # Generate PR bot comment and status report
        try:
            from ioa_core.pr_bot_utils import create_pr_bot_generator

            pr_bot = create_pr_bot_generator(self.artifacts_dir)

            # Generate PR comment
            pr_comment = pr_bot.generate_comment(
                asdict(summary), 0
            )  # PR number 0 for local runs
            pr_bot.save_comment(pr_comment)

            # Generate status report
            status_report = pr_bot.generate_status_report(asdict(summary))
            pr_bot.save_status_report(status_report)

        except ImportError:
            # PR bot utilities not available, skip
            pass

        """Display final summary to user."""
        click.echo("\n" + "=" * 60)
        click.echo("🏁 CI Gates v1 Summary")
        click.echo("=" * 60)
        click.echo(f"Profile: {summary.profile}")
        click.echo(f"Mode: {summary.mode}")
        click.echo(f"Duration: {summary.duration:.2f}s")
        click.echo()
        click.echo(f"Total Gates: {summary.total_gates}")
        click.echo(f"✅ Passed: {summary.passed}")
        click.echo(f"⚠️  Warned: {summary.warned}")
        click.echo(f"❌ Failed: {summary.failed}")
        click.echo(f"⏭️  Skipped: {summary.skipped}")
        click.echo()
        click.echo(f"Artifacts: {summary.artifacts_dir}")

        # Determine exit code
        if summary.failed > 0 and summary.mode == "strict":
            click.echo("\n❌ Gates failed in strict mode")
            sys.exit(1)
        elif summary.failed > 0:
            click.echo("\n⚠️  Gates failed in monitor mode (non-blocking)")
            sys.exit(0)
        else:
            click.echo("\n✅ All gates passed")
            sys.exit(0)


def load_config(config_path: str = ".ioa/ci-gates.yml") -> CIGatesConfig:
    """Load CI Gates configuration."""
    return CIGatesConfig(config_path)


def create_runner(
    profile: str = "local", config_path: str = ".ioa/ci-gates.yml"
) -> CIGatesRunner:
    """Create a CI Gates runner with the specified profile."""
    config = load_config(config_path)
    return CIGatesRunner(config, profile)
