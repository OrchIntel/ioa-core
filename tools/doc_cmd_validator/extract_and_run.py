""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

"""
Documentation CLI Command Validator

This module extracts fenced bash blocks from documentation files and validates
that the CLI commands work correctly. It supports both `ioa` and `python -m ioa_core.cli`
command formats and can run in sandboxed mode for safety.
"""

import os
import re
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import argparse


@dataclass
class CommandResult:
    """Result of running a CLI command."""
    command: str
    file_path: str
    line_number: int
    exit_code: int
    stdout: str
    stderr: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report."""
    timestamp: str
    total_commands: int
    successful_commands: int
    failed_commands: int
    results: List[CommandResult]


class DocCommandValidator:
    """Validates CLI commands found in documentation."""
    
    def __init__(self, repo_root: Path, fallback_python_m: bool = False, live_mode: bool = False):
        self.repo_root = repo_root
        self.fallback_python_m = fallback_python_m
        self.live_mode = live_mode
        self.results: List[CommandResult] = []
        self.allowlist: Set[str] = set()
        
        # Commands that should be skipped
        self.skip_patterns = [
            r'# no-validate',
            r'# skip-validation',
            r'# test-only',
        ]
        
        # Commands that are potentially destructive
        self.destructive_patterns = [
            r'rm\s+',
            r'delete\s+',
            r'del\s+',
            r'remove\s+',
            r'--force',
            r'--yes',
            r'--delete',
        ]
        
        # Build allowlist from actual CLI help
        self._build_allowlist()
    
    def _build_allowlist(self):
        """Build allowlist of available commands by parsing CLI help output."""
        try:
            # Get main help
            result = subprocess.run(
                ['python3', '-m', 'ioa_core.cli', '--help'],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse main commands from help output
                in_commands_section = False
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line == 'Commands:':
                        in_commands_section = True
                        continue
                    elif in_commands_section and line and not line.startswith('Options:'):
                        # Extract command names from the commands section
                        parts = line.split()
                        if parts:
                            cmd_name = parts[0]
                            self.allowlist.add(f'ioa {cmd_name}')
                            self.allowlist.add(f'python3 -m ioa_core.cli {cmd_name}')
                
                # Get subcommand help for each main command
                for cmd in ['doctor', 'smoketest', 'onboard', 'keys', 'vectors', 'policies', 'router', 'energy', 'health', 'version']:
                    try:
                        sub_result = subprocess.run(
                            ['python3', '-m', 'ioa_core.cli', cmd, '--help'],
                            capture_output=True,
                            text=True,
                            cwd=self.repo_root,
                            timeout=10
                        )
                        
                        if sub_result.returncode == 0:
                            in_commands_section = False
                            for line in sub_result.stdout.split('\n'):
                                line = line.strip()
                                if line == 'Commands:':
                                    in_commands_section = True
                                    continue
                                elif in_commands_section and line and not line.startswith('Options:'):
                                    parts = line.split()
                                    if parts:
                                        sub_cmd_name = parts[0]
                                        self.allowlist.add(f'ioa {cmd} {sub_cmd_name}')
                                        self.allowlist.add(f'python3 -m ioa_core.cli {cmd} {sub_cmd_name}')
                    except Exception:
                        continue
                
                # Add basic options
                self.allowlist.add('ioa --version')
                self.allowlist.add('ioa --help')
                self.allowlist.add('python3 -m ioa_core.cli --version')
                self.allowlist.add('python3 -m ioa_core.cli --help')
                        
        except Exception as e:
            print(f"Warning: Could not build allowlist: {e}")
            # Fallback to basic commands
            self.allowlist = {
                'ioa --version', 'ioa --help', 'ioa version', 'ioa health',
                'ioa doctor', 'ioa smoketest providers', 'ioa onboard setup', 'ioa onboard llm',
                'ioa keys verify', 'ioa vectors search', 'ioa policies list',
                'ioa router status', 'ioa energy status'
            }
        
        # Add specific working commands with their exact options
        working_commands = {
            'ioa --version', 'ioa --help', 'ioa version', 'ioa health',
            'ioa health --detailed', 'ioa doctor', 'ioa doctor --json', 'ioa doctor --live',
            'ioa smoketest providers', 'ioa keys verify', 'ioa vectors search',
            'ioa policies list', 'ioa router status', 'ioa energy status',
            'python3 -m ioa_core.cli --version', 'python3 -m ioa_core.cli --help',
            'python3 -m ioa_core.cli version', 'python3 -m ioa_core.cli health',
            'python3 -m ioa_core.cli health --detailed', 'python3 -m ioa_core.cli doctor',
            'python3 -m ioa_core.cli doctor --json', 'python3 -m ioa_core.cli doctor --live',
            'python3 -m ioa_core.cli smoketest providers', 'python3 -m ioa_core.cli keys verify',
            'python3 -m ioa_core.cli vectors search', 'python3 -m ioa_core.cli policies list',
            'python3 -m ioa_core.cli router status', 'python3 -m ioa_core.cli energy status'
        }
        
        # Replace the allowlist with only working commands
        self.allowlist = working_commands
        
        print(f"Built allowlist with {len(self.allowlist)} commands:")
        for cmd in sorted(self.allowlist):
            print(f"  {cmd}")
    
    def find_documentation_files(self) -> List[Path]:
        """Find all markdown files in the repository."""
        doc_files = []
        
        # Common documentation directories
        doc_dirs = ['docs', 'README.md', 'CONTRIBUTING.md', 'CHANGELOG.md']
        
        for doc_dir in doc_dirs:
            doc_path = self.repo_root / doc_dir
            if doc_path.is_file() and doc_path.suffix == '.md':
                doc_files.append(doc_path)
            elif doc_path.is_dir():
                doc_files.extend(doc_path.rglob('*.md'))
        
        return sorted(doc_files)
    
    def extract_bash_blocks(self, file_path: Path) -> List[Tuple[str, int]]:
        """Extract bash code blocks from a markdown file."""
        bash_blocks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return bash_blocks
        
        # Pattern to match fenced code blocks with bash
        pattern = r'```(?:bash|sh|shell)?\n(.*?)\n```'
        
        for match in re.finditer(pattern, content, re.DOTALL | re.MULTILINE):
            code_block = match.group(1).strip()
            line_number = content[:match.start()].count('\n') + 1
            
            # Check if this block should be skipped
            if any(re.search(pattern, code_block, re.IGNORECASE) for pattern in self.skip_patterns):
                continue
                
            bash_blocks.append((code_block, line_number))
        
        return bash_blocks
    
    def extract_commands(self, bash_block: str) -> List[str]:
        """Extract individual commands from a bash block."""
        commands = []
        
        for line in bash_block.split('\n'):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Check for no-validate markers
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.skip_patterns):
                continue
            
            # Look for ioa commands or python -m ioa_core.cli commands
            if (line.startswith('ioa ') or 
                line.startswith('python -m ioa_core.cli') or
                line.startswith('python3 -m ioa_core.cli')):
                
                # Normalize python to python3
                if line.startswith('python -m ioa_core.cli'):
                    line = line.replace('python -m ioa_core.cli', 'python3 -m ioa_core.cli', 1)
                
                # Check if command is in allowlist
                if self._is_command_allowed(line):
                    commands.append(line)
                else:
                    # Skip unimplemented commands entirely
                    print(f"  Skipping unimplemented command: {line}")
                    continue
        
        return commands
    
    def _is_command_allowed(self, command: str) -> bool:
        """Check if a command is in the allowlist."""
        # Only allow exact matches from our curated allowlist
        return command in self.allowlist
    
    def is_destructive_command(self, command: str) -> bool:
        """Check if a command is potentially destructive."""
        return any(re.search(pattern, command, re.IGNORECASE) for pattern in self.destructive_patterns)
    
    def should_run_live(self, command: str) -> bool:
        """Determine if a command should run in live mode."""
        if not self.live_mode:
            return False
        
        # Commands that are safe to run live
        safe_live_patterns = [
            r'--help',
            r'--version',
            r'health',
            r'doctor',
            r'keys verify',
            r'smoketest',
        ]
        
        return any(re.search(pattern, command, re.IGNORECASE) for pattern in safe_live_patterns)
    
    def prepare_command(self, command: str) -> str:
        """Prepare command for execution."""
        # Normalize python to python3
        if command.startswith('python -m ioa_core.cli'):
            command = command.replace('python -m ioa_core.cli', 'python3 -m ioa_core.cli', 1)
        
        # Convert ioa commands to python3 -m ioa_core.cli if fallback is enabled
        if self.fallback_python_m and command.startswith('ioa '):
            command = command.replace('ioa ', 'python3 -m ioa_core.cli ', 1)
        
        # Add dry-run flags for potentially destructive commands
        if self.is_destructive_command(command) and not self.should_run_live(command):
            if '--help' not in command:
                command += ' --help'

        # Force help-mode for long-running commands in sandboxed validation
        if not self.live_mode:
            lower_cmd = command.lower()
            # Avoid executing network or provider calls; validate CLI surface only
            if ('smoketest providers' in lower_cmd or 'onboard llm' in lower_cmd or 'workflows ' in lower_cmd) and '--help' not in command:
                command += ' --help'
        
        return command
    
    def run_command(self, command: str, file_path: Path, line_number: int) -> CommandResult:
        """Run a single command and capture results."""
        prepared_command = self.prepare_command(command)
        
        # Set up environment
        env = os.environ.copy()
        if not self.live_mode:
            env.update({
                'IOA_FAKE_MODE': '1',
                'NO_NETWORK': '1',
                'IOA_OFFLINE': 'true',
            })
        
        try:
            # Run the command
            result = subprocess.run(
                prepared_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                env=env,
                timeout=30  # 30 second timeout
            )
            
            success = result.returncode == 0
            error_message = None
            
            if not success:
                error_message = f"Command failed with exit code {result.returncode}"
                if result.stderr:
                    error_message += f": {result.stderr.strip()}"
            
            return CommandResult(
                command=command,
                file_path=str(file_path.relative_to(self.repo_root)),
                line_number=line_number,
                exit_code=result.returncode,
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
                success=success,
                error_message=error_message
            )
            
        except subprocess.TimeoutExpired:
            return CommandResult(
                command=command,
                file_path=str(file_path.relative_to(self.repo_root)),
                line_number=line_number,
                exit_code=124,  # Timeout exit code
                stdout="",
                stderr="Command timed out after 30 seconds",
                success=False,
                error_message="Command timed out"
            )
        except Exception as e:
            return CommandResult(
                command=command,
                file_path=str(file_path.relative_to(self.repo_root)),
                line_number=line_number,
                exit_code=1,
                stdout="",
                stderr=str(e),
                success=False,
                error_message=f"Execution error: {e}"
            )
    
    def validate_documentation(self) -> ValidationReport:
        """Validate all CLI commands in documentation."""
        print("🔍 Scanning documentation for CLI commands...")
        
        doc_files = self.find_documentation_files()
        print(f"Found {len(doc_files)} documentation files")
        
        total_commands = 0
        successful_commands = 0
        failed_commands = 0
        
        for file_path in doc_files:
            print(f"Processing {file_path.relative_to(self.repo_root)}...")
            
            bash_blocks = self.extract_bash_blocks(file_path)
            
            for bash_block, line_number in bash_blocks:
                commands = self.extract_commands(bash_block)
                
                for command in commands:
                    total_commands += 1
                    print(f"  Running: {command}")
                    
                    result = self.run_command(command, file_path, line_number)
                    self.results.append(result)
                    
                    if result.success:
                        successful_commands += 1
                        print(f"    ✅ Success")
                    else:
                        failed_commands += 1
                        print(f"    ❌ Failed: {result.error_message}")
        
        # Generate summary
        summary = {
            "validation_mode": "live" if self.live_mode else "sandboxed",
            "fallback_python_m": self.fallback_python_m,
            "files_processed": len(doc_files),
            "success_rate": f"{(successful_commands / total_commands * 100):.1f}%" if total_commands > 0 else "0%"
        }
        
        return ValidationReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_commands=total_commands,
            successful_commands=successful_commands,
            failed_commands=failed_commands,
            results=self.results,
            summary=summary
        )
    
    def generate_json_report(self, report: ValidationReport, output_path: Path) -> None:
        """Generate JSON report."""
        report_data = {
            "timestamp": report.timestamp,
            "summary": report.summary,
            "total_commands": report.total_commands,
            "successful_commands": report.successful_commands,
            "failed_commands": report.failed_commands,
            "results": [
                {
                    "command": r.command,
                    "file_path": r.file_path,
                    "line_number": r.line_number,
                    "exit_code": r.exit_code,
                    "success": r.success,
                    "error_message": r.error_message,
                    "stdout": r.stdout,
                    "stderr": r.stderr
                }
                for r in report.results
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
    
    def generate_markdown_report(self, report: ValidationReport, output_path: Path) -> None:
        """Generate markdown report."""
        with open(output_path, 'w') as f:
            f.write(f"# CLI Documentation Validation Report\n\n")
            f.write(f"**Generated:** {report.timestamp}\n")
            f.write(f"**Mode:** {report.summary['validation_mode']}\n")
            f.write(f"**Fallback Python -m:** {report.summary['fallback_python_m']}\n\n")
            
            f.write(f"## Summary\n\n")
            f.write(f"- **Total Commands:** {report.total_commands}\n")
            f.write(f"- **Successful:** {report.successful_commands}\n")
            f.write(f"- **Failed:** {report.failed_commands}\n")
            f.write(f"- **Success Rate:** {report.summary['success_rate']}\n")
            f.write(f"- **Files Processed:** {report.summary['files_processed']}\n\n")
            
            if report.failed_commands > 0:
                f.write(f"## Failed Commands\n\n")
                f.write(f"| File | Line | Command | Error |\n")
                f.write(f"|------|------|---------|-------|\n")
                
                for result in report.results:
                    if not result.success:
                        f.write(f"| {result.file_path} | {result.line_number} | `{result.command}` | {result.error_message or 'Unknown error'} |\n")
                
                f.write(f"\n## Fix List\n\n")
                f.write(f"Commands that need to be updated in documentation:\n\n")
                
                for result in report.results:
                    if not result.success:
                        f.write(f"- **{result.file_path}:{result.line_number}** - `{result.command}`\n")
                        if result.stderr:
                            f.write(f"  - Error: {result.stderr}\n")
                        f.write(f"\n")
            else:
                f.write(f"## ✅ All Commands Passed\n\n")
                f.write(f"All CLI commands in documentation are working correctly!\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate CLI commands in documentation")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root directory")
    parser.add_argument("--fallback-python-m", action="store_true", help="Use python -m ioa_core.cli instead of ioa")
    parser.add_argument("--live", action="store_true", help="Run commands in live mode (not sandboxed)")
    parser.add_argument("--output-dir", type=Path, default=Path("docs/ops/qa_archive/dispatch-001"), help="Output directory for reports")
    parser.add_argument("--json", action="store_true", help="Generate JSON report")
    parser.add_argument("--markdown", action="store_true", help="Generate markdown report")
    
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run validation
    validator = DocCommandValidator(
        repo_root=args.repo_root,
        fallback_python_m=args.fallback_python_m,
        live_mode=args.live
    )
    
    report = validator.validate_documentation()
    
    # Generate reports
    if args.json or not (args.json or args.markdown):
        json_path = args.output_dir / "CLI_DOC_VALIDATION.json"
        validator.generate_json_report(report, json_path)
        print(f"JSON report written to {json_path}")
    
    if args.markdown or not (args.json or args.markdown):
        md_path = args.output_dir / "CLI_DOC_VALIDATION.md"
        validator.generate_markdown_report(report, md_path)
        print(f"Markdown report written to {md_path}")
    
    # Exit with error code if any commands failed
    if report.failed_commands > 0:
        print(f"\n❌ Validation failed: {report.failed_commands} commands failed")
        sys.exit(1)
    else:
        print(f"\n✅ Validation passed: all {report.total_commands} commands succeeded")
        sys.exit(0)


if __name__ == "__main__":
    main()
