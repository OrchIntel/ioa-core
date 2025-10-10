""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


class GHAAuditor:
    """Audit GitHub Actions workflows for common failure patterns and issues."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.workflows_dir = self.repo_path / ".github" / "workflows"
        self.artifacts_dir = self.repo_path / "artifacts" / "lens" / "gha_audit"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Common failure patterns to detect
        self.failure_patterns = {
            "no_files_found": [
                "No files were found with the provided path: artifacts/",
                "No files were found with the provided path: 'artifacts/",
                "No files were found with the provided path: artifacts/lens"
            ],
            "python_not_found": [
                "Python was not found",
                "python: command not found",
                "python3: command not found"
            ],
            "python_wrong_version": [
                "Python 3.10",
                "Python 3.9",
                "Python 3.8"
            ],
            "secret_missing": [
                "Secret not found",
                "Resource not accessible by integration",
                "Resource not accessible by integration: Secret"
            ],
            "macos_failure": [
                "macOS",
                "macos-latest",
                "The operation was canceled"
            ],
            "permission_denied": [
                "Permission denied",
                "Resource not accessible by integration",
                "403 Forbidden"
            ],
            "timeout": [
                "Timeout",
                "The operation was canceled",
                "Job timed out"
            ]
        }
    
    def check_gh_cli(self) -> bool:
        """Check if GitHub CLI is available."""
        # PATCH: Cursor-2025-09-21 DISPATCH-OPS-20250921-GHA-AUDIT+REMEDIATION-V2.1-FINALIZE
        # Allow forcing offline mode to avoid long network calls during local runs/credit constraints
        if os.environ.get("GHA_AUDIT_OFFLINE", "").lower() in {"1", "true", "yes"}:
            return False
        try:
            result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_workflow_runs(self, workflow_file: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent runs for a workflow using GitHub CLI."""
        if not self.check_gh_cli():
            print(f"Warning: GitHub CLI not available, cannot fetch runs for {workflow_file}")
            return []
        
        try:
            # Get workflow runs
            cmd = [
                "gh", "run", "list", 
                "--workflow", workflow_file,
                "--limit", str(limit),
                "--json", "databaseId,status,conclusion,createdAt,headBranch,displayTitle"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
            
            if result.returncode != 0:
                print(f"Error fetching runs for {workflow_file}: {result.stderr}")
                return []
            
            runs = json.loads(result.stdout)
            
            # Get detailed logs for failed runs
            for run in runs:
                if run.get("conclusion") in ["failure", "cancelled", "timed_out"]:
                    run_id = run["databaseId"]
                    logs_cmd = ["gh", "run", "view", str(run_id), "--log"]
                    logs_result = subprocess.run(logs_cmd, capture_output=True, text=True, cwd=self.repo_path)
                    run["logs"] = logs_result.stdout
                    run["error_patterns"] = self._analyze_logs(logs_result.stdout)
            
            return runs
            
        except Exception as e:
            print(f"Error processing {workflow_file}: {e}")
            return []
    
    def _analyze_logs(self, logs: str) -> List[str]:
        """Analyze logs for common failure patterns."""
        found_patterns = []
        logs_lower = logs.lower()
        
        for pattern_type, patterns in self.failure_patterns.items():
            for pattern in patterns:
                if pattern.lower() in logs_lower:
                    found_patterns.append(f"{pattern_type}: {pattern}")
        
        return found_patterns
    
    def analyze_workflow_file(self, workflow_path: Path) -> Dict[str, Any]:
        """Analyze a single workflow file for structural issues."""
        issues = []
        recommendations = []
        
        try:
            with open(workflow_path, 'r') as f:
                workflow = yaml.safe_load(f)
        except Exception as e:
            return {
                "file": str(workflow_path),
                "error": f"Failed to parse YAML: {e}",
                "issues": [],
                "recommendations": []
            }
        
        # Check for common structural issues
        jobs = workflow.get("jobs", {})
        
        for job_name, job_config in jobs.items():
            steps = job_config.get("steps", [])
            
            # Check for Python setup
            has_python_setup = any(
                step.get("uses", "").startswith("actions/setup-python")
                for step in steps
            )
            if not has_python_setup:
                issues.append(f"Job '{job_name}': No Python setup found")
            
            # Check for artifact uploads without directory creation
            has_upload_artifact = any(
                step.get("uses", "").startswith("actions/upload-artifact")
                for step in steps
            )
            has_mkdir_artifacts = any(
                "mkdir -p artifacts" in step.get("run", "")
                for step in steps
            )
            if has_upload_artifact and not has_mkdir_artifacts:
                issues.append(f"Job '{job_name}': Upload artifact without directory creation")
                recommendations.append("Add 'mkdir -p artifacts/lens || true' before upload steps")
            
            # Check for macOS runners
            runner = job_config.get("runs-on", "")
            if "macos" in runner.lower():
                issues.append(f"Job '{job_name}': Uses macOS runner ({runner})")
                recommendations.append("Consider switching to ubuntu-latest unless macOS is required")
            
            # Check for missing concurrency control
            if "concurrency" not in workflow:
                issues.append("Workflow: Missing concurrency control")
                recommendations.append("Add concurrency block to prevent overlapping runs")
            
            # Check for missing permissions
            if "permissions" not in workflow:
                issues.append("Workflow: Missing explicit permissions")
                recommendations.append("Add minimal required permissions")
        
        return {
            "file": str(workflow_path),
            "issues": issues,
            "recommendations": recommendations
        }
    
    def audit_all_workflows(self, limit: int = 20) -> Dict[str, Any]:
        """Audit all workflows in the repository."""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workflows": {},
            "summary": {
                "total_workflows": 0,
                "failed_runs": 0,
                "common_issues": {},
                "top_failure_patterns": {}
            }
        }
        
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        results["summary"]["total_workflows"] = len(workflow_files)
        
        all_patterns = []
        
        for workflow_file in workflow_files:
            print(f"Auditing {workflow_file.name}...")
            
            # Analyze workflow structure
            file_analysis = self.analyze_workflow_file(workflow_file)
            
            # Get recent runs
            runs = self.get_workflow_runs(workflow_file.name, limit)
            
            # Count failures
            failed_runs = [r for r in runs if r.get("conclusion") in ["failure", "cancelled", "timed_out"]]
            results["summary"]["failed_runs"] += len(failed_runs)
            
            # Collect failure patterns
            for run in failed_runs:
                patterns = run.get("error_patterns", [])
                all_patterns.extend(patterns)
            
            results["workflows"][workflow_file.name] = {
                "file_analysis": file_analysis,
                "runs": runs,
                "failed_runs": len(failed_runs),
                "total_runs": len(runs)
            }
        
        # Analyze common patterns
        pattern_counts = {}
        for pattern in all_patterns:
            pattern_type = pattern.split(":")[0]
            pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
        
        results["summary"]["top_failure_patterns"] = dict(
            sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return results
    
    def generate_status_report(self, results: Dict[str, Any]) -> str:
        """Generate a markdown status report."""
        report = f"""# GitHub Actions Audit Status Report

**Generated:** {results['timestamp']}
**Total Workflows:** {results['summary']['total_workflows']}
**Failed Runs (last 20 per workflow):** {results['summary']['failed_runs']}

## Top Failure Patterns

"""
        
        for pattern, count in results['summary']['top_failure_patterns'].items():
            report += f"- **{pattern}**: {count} occurrences\n"
        
        report += "\n## Workflow Analysis\n\n"
        
        for workflow_name, data in results['workflows'].items():
            file_analysis = data['file_analysis']
            failed_runs = data['failed_runs']
            total_runs = data['total_runs']
            
            report += f"### {workflow_name}\n"
            report += f"- **Status**: {failed_runs}/{total_runs} failed runs\n"
            
            if file_analysis.get('issues'):
                report += "- **Issues**:\n"
                for issue in file_analysis['issues']:
                    report += f"  - {issue}\n"
            
            if file_analysis.get('recommendations'):
                report += "- **Recommendations**:\n"
                for rec in file_analysis['recommendations']:
                    report += f"  - {rec}\n"
            
            report += "\n"
        
        return report


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Audit GitHub Actions workflows")
    parser.add_argument("--limit", type=int, default=20, help="Number of recent runs to analyze per workflow")
    parser.add_argument("--out", default="artifacts/lens/gha_audit/runs.json", help="Output JSON file")
    parser.add_argument("--report", default="docs/ops/status_reports/STATUS_REPORT_GHA_AUDIT_V1.md", help="Status report file")
    
    args = parser.parse_args()
    
    auditor = GHAAuditor()
    results = auditor.audit_all_workflows(args.limit)
    
    # Save JSON results
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate and save status report
    report_content = auditor.generate_status_report(results)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    print(f"Audit complete. Results saved to {output_path}")
    print(f"Status report saved to {report_path}")
    print(f"Found {results['summary']['failed_runs']} failed runs across {results['summary']['total_workflows']} workflows")


if __name__ == "__main__":
    main()
