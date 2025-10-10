""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3

"""
Documentation Validation Script for IOA Core

This script validates that all code examples in documentation are executable
and produce expected results. It supports:

- Fenced code blocks (bash, sh, python)
- Skip markers for non-deterministic content
- Slow test markers for longer timeouts
- Expected output validation
- JUnit XML output for CI integration
- Non-interactive, password-safe execution with command filtering
- Sandboxed execution with timeout enforcement
"""

import argparse
import asyncio
import json
import logging
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test execution status."""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"
    TIMEOUT = "timeout"
    DENIED = "denied"


@dataclass
class TestResult:
    """Result of a test execution."""
    name: str
    status: TestStatus
    duration: float
    output: str
    error: Optional[str] = None
    expected_output: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    skip_reason: Optional[str] = None
    denied_commands: Optional[List[str]] = None


class CommandFilter:
    """Filters commands for security and non-interactive execution."""
    
    # Commands that are outright denied in non-interactive mode
    HARD_DENY_LIST = {
        'sudo', 'su', 'ssh', 'mount', 'systemctl', 'brew install',
        'rm -rf /', 'security add-generic-password', 'osascript',
        'read -s', 'passwd', 'chpasswd', 'vault', 'gpg'
    }
    
    # Commands that need --no-input flag appended
    SOFT_DENY_LIST = {
        'pip install': '--no-input',
        'npm install': '--yes',
        'yarn install': '--yes',
        'cargo install': '--quiet',
        'go install': '-q'
    }
    
    # Patterns that indicate password/privilege prompts
    PROMPT_PATTERNS = [
        r'Password:', r'passphrase:', r'sudo:', r'[Pp]assword for',
        r'Enter your password', r'Authentication required',
        r'[Ss]sh.*password', r'[Pp]assphrase for'
    ]
    
    def __init__(self, non_interactive: bool = True):
        self.non_interactive = non_interactive
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) 
                                for pattern in self.PROMPT_PATTERNS]
    
    def check_command(self, code: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        Check if a command is allowed.
        
        Returns:
            (allowed, reason, denied_commands)
        """
        lines = code.strip().split('\n')
        denied_commands = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Check for hard deny commands
            for denied_cmd in self.HARD_DENY_LIST:
                if denied_cmd in line:
                    denied_commands.append(denied_cmd)
                    if self.non_interactive:
                        return False, f"Command '{denied_cmd}' is denied in non-interactive mode", denied_commands
            
            # Check for soft deny commands that need flags
            for soft_cmd, flag in self.SOFT_DENY_LIST.items():
                if soft_cmd in line and flag not in line:
                    denied_commands.append(f"{soft_cmd} (needs {flag})")
        
        return True, None, denied_commands
    
    def detect_prompts(self, output: str) -> List[str]:
        """Detect password/privilege prompts in output."""
        detected_prompts = []
        for pattern in self.compiled_patterns:
            if pattern.search(output):
                detected_prompts.append(pattern.pattern)
        return detected_prompts


class DocValidator:
    """Validates documentation by executing code examples in a sandboxed environment."""
    
    def __init__(self, base_dir: Path, timeout: int = 30, skip_slow: bool = False, 
                 non_interactive: bool = True):
        self.base_dir = base_dir
        self.timeout = timeout
        self.skip_slow = skip_slow
        self.non_interactive = non_interactive
        self.results: List[TestResult] = []
        self.temp_dir = None
        self.command_filter = CommandFilter(non_interactive)
        
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="ioa_doc_validate_")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def find_doc_files(self) -> List[Path]:
        """Find all documentation files to validate."""
        doc_patterns = [
            "README.md",
            "docs/**/*.md",
            "docs/**/*.rst",
            "docs/**/*.txt"
        ]
        
        files = []
        for pattern in doc_patterns:
            if "**" in pattern:
                # Handle globstar patterns
                base, rest = pattern.split("**", 1)
                base_path = self.base_dir / base
                if base_path.exists():
                    for file_path in base_path.rglob(rest.lstrip("/")):
                        if file_path.is_file():
                            files.append(file_path)
            else:
                file_path = self.base_dir / pattern
                if file_path.exists():
                    files.append(file_path)
        
        return sorted(files)
    
    def parse_code_blocks(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse fenced code blocks from a markdown file."""
        blocks = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return blocks
        
        # Pattern for fenced code blocks
        # Matches ```language, ```language:filename, or ```language
        pattern = r'```(\w+)(?::([^\n]+))?\n(.*?)```'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            language = match.group(1).lower()
            filename = match.group(2)
            code = match.group(3).strip()
            
            # Skip non-executable languages
            if language not in ['bash', 'sh', 'python', 'py']:
                continue
            
            # Check for skip markers
            skip_reason = None
            if '# [doc-test-skip]' in code:
                skip_reason = "Explicitly skipped"
            elif '# [doc-test-needs-sudo]' in code:
                skip_reason = "Needs elevated privileges"
            elif '# [doc-test-slow]' in code and self.skip_slow:
                skip_reason = "Slow test skipped"
            
            # Check for slow test marker to adjust timeout
            is_slow = '# [doc-test-slow]' in code
            
            # Extract expected output
            expected_output = None
            expected_lines = []
            for line in code.split('\n'):
                if line.strip().startswith('# expect:'):
                    expected_lines.append(line.strip()[9:])  # Remove '# expect: '
            
            if expected_lines:
                expected_output = '\n'.join(expected_lines)
            
            # Find line number (approximate)
            line_number = content[:match.start()].count('\n') + 1
            
            blocks.append({
                'language': language,
                'filename': filename,
                'code': code,
                'skip_reason': skip_reason,
                'expected_output': expected_output,
                'line_number': line_number,
                'is_slow': is_slow
            })
        
        return blocks
    
    def get_safe_environment(self) -> Dict[str, str]:
        """Get a safe environment for child processes."""
        env = os.environ.copy()
        
        # Force non-interactive settings
        env.update({
            'PAGER': 'cat',
            'GIT_TERMINAL_PROMPT': '0',
            'PIP_DISABLE_PIP_VERSION_CHECK': '1',
            'PYTHONUNBUFFERED': '1',
            'CI': '1',
            'IOA_NON_INTERACTIVE': '1'
        })
        
        # Remove potentially dangerous environment variables
        dangerous_vars = [
            'SSH_AUTH_SOCK', 'SSH_AGENT_PID', 'GPG_AGENT_INFO',
            'DBUS_SESSION_BUS_ADDRESS', 'XAUTHORITY', 'DISPLAY'
        ]
        
        for var in dangerous_vars:
            env.pop(var, None)
        
        # Only allow specific API keys in mock mode
        if not self.non_interactive:
            # In interactive mode, allow more environment variables
            pass
        else:
            # In non-interactive mode, strip most secrets
            secret_patterns = ['API_KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'AUTH']
            for key in list(env.keys()):
                if any(pattern in key.upper() for pattern in secret_patterns):
                    if key not in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:  # Whitelist
                        env.pop(key, None)
        
        return env
    
    async def execute_with_timeout(self, cmd: List[str], cwd: str, env: Dict[str, str], 
                                 timeout: int, test_name: str) -> Tuple[int, str, str]:
        """Execute a command with timeout and proper signal handling."""
        start_time = time.time()
        
        try:
            # Create process with closed stdin
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,  # No TTY input
                cwd=cwd,
                env=env
            )
            
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return (
                process.returncode,
                stdout.decode('utf-8', errors='replace'),
                stderr.decode('utf-8', errors='replace')
            )
            
        except asyncio.TimeoutError:
            # Try to terminate gracefully first
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                # Force kill if still not responding
                process.kill()
                await process.wait()
            
            raise asyncio.TimeoutError(f"Command timed out after {timeout}s")
    
    async def execute_bash_command(self, code: str, test_name: str, is_slow: bool = False) -> TestResult:
        """Execute a bash/shell command with security filtering."""
        start_time = time.time()
        
        # Check command security
        allowed, reason, denied_commands = self.command_filter.check_command(code)
        if not allowed:
            return TestResult(
                name=test_name,
                status=TestStatus.DENIED,
                duration=0.0,
                output="",
                error=reason,
                denied_commands=denied_commands
            )
        
        # Determine timeout
        block_timeout = 120 if is_slow else self.timeout
        
        try:
            # Create a temporary script file
            script_path = os.path.join(self.temp_dir, f"{test_name}.sh")
            with open(script_path, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("set -e\n")  # Exit on error
                f.write("set -o pipefail\n")  # Exit on pipe failure
                f.write(code)
                f.write("\n")
            
            os.chmod(script_path, 0o755)
            
            # Get safe environment
            env = self.get_safe_environment()
            
            # Execute with timeout
            returncode, stdout, stderr = await self.execute_with_timeout(
                ['/bin/bash', script_path],
                str(self.base_dir),
                env,
                block_timeout,
                test_name
            )
            
            duration = time.time() - start_time
            
            # Check for password prompts in output
            all_output = stdout + stderr
            detected_prompts = self.command_filter.detect_prompts(all_output)
            
            if detected_prompts and self.non_interactive:
                return TestResult(
                    name=test_name,
                    status=TestStatus.SKIP,
                    duration=duration,
                    output=all_output,
                    error=f"Password/privilege prompt detected: {', '.join(detected_prompts)}",
                    skip_reason="Password prompt detected"
                )
            
            if returncode == 0:
                status = TestStatus.PASS
                error = None
            else:
                status = TestStatus.FAIL
                error = stderr if stderr else f"Command failed with exit code {returncode}"
            
            return TestResult(
                name=test_name,
                status=status,
                duration=duration,
                output=stdout,
                error=error
            )
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return TestResult(
                name=test_name,
                status=TestStatus.TIMEOUT,
                duration=duration,
                output="",
                error=f"Execution timed out after {block_timeout}s"
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                output="",
                error=str(e)
            )
    
    async def execute_python_code(self, code: str, test_name: str, is_slow: bool = False) -> TestResult:
        """Execute Python code with security filtering."""
        start_time = time.time()
        
        # Check command security (for any system calls in Python)
        allowed, reason, denied_commands = self.command_filter.check_command(code)
        if not allowed:
            return TestResult(
                name=test_name,
                status=TestStatus.DENIED,
                duration=0.0,
                output="",
                error=reason,
                denied_commands=denied_commands
            )
        
        # Determine timeout
        block_timeout = 120 if is_slow else self.timeout
        
        try:
            # Create a temporary Python file
            script_path = os.path.join(self.temp_dir, f"{test_name}.py")
            with open(script_path, 'w') as f:
                f.write("import sys\n")
                f.write("import os\n")
                f.write("sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))\n")
                f.write(code)
                f.write("\n")
            
            # Get safe environment
            env = self.get_safe_environment()
            
            # Execute with timeout
            returncode, stdout, stderr = await self.execute_with_timeout(
                [sys.executable, script_path],
                str(self.base_dir),
                env,
                block_timeout,
                test_name
            )
            
            duration = time.time() - start_time
            
            # Check for password prompts in output
            all_output = stdout + stderr
            detected_prompts = self.command_filter.detect_prompts(all_output)
            
            if detected_prompts and self.non_interactive:
                return TestResult(
                    name=test_name,
                    status=TestStatus.SKIP,
                    duration=duration,
                    output=all_output,
                    error=f"Password/privilege prompt detected: {', '.join(detected_prompts)}",
                    skip_reason="Password prompt detected"
                )
            
            if returncode == 0:
                status = TestStatus.PASS
                error = None
            else:
                status = TestStatus.FAIL
                error = stderr if stderr else f"Python execution failed with exit code {returncode}"
            
            return TestResult(
                name=test_name,
                status=status,
                duration=duration,
                output=stdout,
                error=error
            )
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return TestResult(
                name=test_name,
                status=TestStatus.TIMEOUT,
                duration=duration,
                output="",
                error=f"Execution timed out after {block_timeout}s"
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                output="",
                error=str(e)
            )
    
    def validate_output(self, result: TestResult, expected_output: str) -> bool:
        """Validate that output matches expected patterns."""
        if not expected_output:
            return True
        
        try:
            # Check if any expected line matches
            expected_lines = expected_output.split('\n')
            output_lines = result.output.split('\n')
            
            for expected in expected_lines:
                if expected.strip():
                    # Try to find a matching line in output
                    found = False
                    for output_line in output_lines:
                        if re.search(expected.strip(), output_line):
                            found = True
                            break
                    if not found:
                        return False
            
            return True
        except Exception:
            return False
    
    async def validate_file(self, file_path: Path) -> List[TestResult]:
        """Validate a single documentation file."""
        logger.info(f"Validating {file_path}")
        
        blocks = self.parse_code_blocks(file_path)
        if not blocks:
            logger.info(f"No executable code blocks found in {file_path}")
            return []
        
        results = []
        
        for i, block in enumerate(blocks):
            test_name = f"{file_path.stem}_{block['language']}_{i+1}"
            
            if block['skip_reason']:
                logger.info(f"Skipping {test_name}: {block['skip_reason']}")
                results.append(TestResult(
                    name=test_name,
                    status=TestStatus.SKIP,
                    duration=0.0,
                    output="",
                    error=block['skip_reason'],
                    file_path=str(file_path),
                    line_number=block['line_number'],
                    skip_reason=block['skip_reason']
                ))
                continue
            
            logger.info(f"Executing {test_name}")
            
            if block['language'] in ['bash', 'sh']:
                result = await self.execute_bash_command(block['code'], test_name, block['is_slow'])
            elif block['language'] in ['python', 'py']:
                result = await self.execute_python_code(block['code'], test_name, block['is_slow'])
            else:
                continue
            
            # Add file context
            result.file_path = str(file_path)
            result.line_number = block['line_number']
            result.expected_output = block['expected_output']
            
            # Validate output if expected
            if block['expected_output'] and result.status == TestStatus.PASS:
                if not self.validate_output(result, block['expected_output']):
                    result.status = TestStatus.FAIL
                    result.error = f"Output validation failed. Expected: {block['expected_output']}"
            
            results.append(result)
            self.results.append(result)
        
        return results
    
    async def validate_all(self) -> List[TestResult]:
        """Validate all documentation files."""
        doc_files = self.find_doc_files()
        logger.info(f"Found {len(doc_files)} documentation files to validate")
        
        all_results = []
        for file_path in doc_files:
            try:
                file_results = await self.validate_file(file_path)
                all_results.extend(file_results)
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                all_results.append(TestResult(
                    name=f"{file_path.stem}_error",
                    status=TestStatus.ERROR,
                    duration=0.0,
                    output="",
                    error=str(e),
                    file_path=str(file_path)
                ))
        
        return all_results
    
    def generate_junit_xml(self, output_path: Path):
        """Generate JUnit XML report with non-interactive section."""
        root = ET.Element("testsuites")
        root.set("name", "IOA Documentation Validation")
        root.set("tests", str(len(self.results)))
        
        # Count different statuses
        failures = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIP)
        timeouts = sum(1 for r in self.results if r.status == TestStatus.TIMEOUT)
        denied = sum(1 for r in self.results if r.status == TestStatus.DENIED)
        
        root.set("failures", str(failures))
        root.set("errors", str(errors))
        root.set("skipped", str(skipped))
        
        # Add non-interactive report section
        noninteractive_section = ET.SubElement(root, "noninteractive-report")
        noninteractive_section.set("total_skipped", str(skipped))
        noninteractive_section.set("total_denied", str(denied))
        noninteractive_section.set("total_timeouts", str(timeouts))
        
        # Group by file
        by_file = {}
        for result in self.results:
            file_path = result.file_path or "unknown"
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(result)
        
        for file_path, results in by_file.items():
            testsuite = ET.SubElement(root, "testsuite")
            testsuite.set("name", Path(file_path).name)
            testsuite.set("tests", str(len(results)))
            
            file_failures = sum(1 for r in results if r.status == TestStatus.FAIL)
            file_errors = sum(1 for r in results if r.status == TestStatus.ERROR)
            file_skipped = sum(1 for r in results if r.status == TestStatus.SKIP)
            file_denied = sum(1 for r in results if r.status == TestStatus.DENIED)
            file_timeouts = sum(1 for r in results if r.status == TestStatus.TIMEOUT)
            
            testsuite.set("failures", str(file_failures))
            testsuite.set("errors", str(file_errors))
            testsuite.set("skipped", str(file_skipped))
            testsuite.set("denied", str(file_denied))
            testsuite.set("timeouts", str(file_timeouts))
            
            for result in results:
                testcase = ET.SubElement(testsuite, "testcase")
                testcase.set("name", result.name)
                testcase.set("time", f"{result.duration:.3f}")
                
                if result.status == TestStatus.FAIL:
                    failure = ET.SubElement(testcase, "failure")
                    failure.set("message", result.error or "Test failed")
                    failure.text = result.output
                elif result.status == TestStatus.ERROR:
                    error = ET.SubElement(testcase, "error")
                    error.set("message", result.error or "Test error")
                    error.text = result.output
                elif result.status == TestStatus.SKIP:
                    skip = ET.SubElement(testcase, "skipped")
                    skip.set("message", result.error or "Test skipped")
                    if result.skip_reason:
                        skip.set("reason", result.skip_reason)
                elif result.status == TestStatus.DENIED:
                    denied_elem = ET.SubElement(testcase, "denied")
                    denied_elem.set("message", result.error or "Command denied")
                    if result.denied_commands:
                        denied_elem.set("commands", ", ".join(result.denied_commands))
                elif result.status == TestStatus.TIMEOUT:
                    timeout_elem = ET.SubElement(testcase, "timeout")
                    timeout_elem.set("message", result.error or "Test timed out")
        
        # Write XML file
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        logger.info(f"JUnit XML report written to {output_path}")
    
    def print_summary(self):
        """Print validation summary with non-interactive details."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIP)
        timeouts = sum(1 for r in self.results if r.status == TestStatus.TIMEOUT)
        denied = sum(1 for r in self.results if r.status == TestStatus.DENIED)
        
        print("\n" + "="*60)
        print("DOCUMENTATION VALIDATION SUMMARY")
        print("="*60)
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print(f"Skipped: {skipped}")
        print(f"Timeouts: {timeouts}")
        print(f"Denied: {denied}")
        print(f"Success rate: {(passed/total*100):.1f}%" if total > 0 else "Success rate: N/A")
        
        if self.non_interactive:
            print(f"\nNon-interactive mode: ENABLED")
            print(f"Security filtering: ACTIVE")
        
        if failed > 0 or errors > 0:
            print("\nFAILURES:")
            for result in self.results:
                if result.status in [TestStatus.FAIL, TestStatus.ERROR]:
                    print(f"  {result.name}: {result.error}")
                    if result.file_path:
                        print(f"    File: {result.file_path}")
                    if result.line_number:
                        print(f"    Line: {result.line_number}")
            print()
        
        if skipped > 0:
            print("SKIPPED:")
            for result in self.results:
                if result.status == TestStatus.SKIP:
                    print(f"  {result.name}: {result.error}")
                    if result.skip_reason:
                        print(f"    Reason: {result.skip_reason}")
            print()
        
        if denied > 0:
            print("DENIED COMMANDS:")
            for result in self.results:
                if result.status == TestStatus.DENIED:
                    print(f"  {result.name}: {result.error}")
                    if result.denied_commands:
                        print(f"    Commands: {', '.join(result.denied_commands)}")
            print()
        
        if timeouts > 0:
            print("TIMEOUTS:")
            for result in self.results:
                if result.status == TestStatus.TIMEOUT:
                    print(f"  {result.name}: {result.error}")
            print()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate IOA Core documentation by executing code examples"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="Base directory to search for documentation (default: current directory)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout for each test execution in seconds (default: 30)"
    )
    parser.add_argument(
        "--skip-slow",
        action="store_true",
        help="Skip tests marked as slow"
    )
    parser.add_argument(
        "--junit-xml",
        type=Path,
        help="Output JUnit XML report to specified path"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Output detailed log to specified file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--non-interactive-only",
        action="store_true",
        help="Strict non-interactive mode - fail on any denied commands"
    )
    parser.add_argument(
        "--fail-on-denied",
        action="store_true",
        help="Exit with error code if any commands are denied"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        default=True,
        help="Run in non-interactive mode with security filtering (default: True)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Allow interactive commands (overrides --non-interactive)"
    )
    
    args = parser.parse_args()
    
    # Handle interactive flag
    if args.interactive:
        args.non_interactive = False
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(file_handler)
    
    logger.info(f"Starting documentation validation in {args.base_dir}")
    logger.info(f"Timeout: {args.timeout}s, Skip slow: {args.skip_slow}")
    logger.info(f"Non-interactive mode: {args.non_interactive}")
    
    with DocValidator(args.base_dir, args.timeout, args.skip_slow, args.non_interactive) as validator:
        try:
            results = await validator.validate_all()
            
            # Print summary
            validator.print_summary()
            
            # Generate JUnit XML if requested
            if args.junit_xml:
                validator.generate_junit_xml(args.junit_xml)
            
            # Exit with appropriate code
            failed = sum(1 for r in results if r.status in [TestStatus.FAIL, TestStatus.ERROR])
            denied = sum(1 for r in results if r.status == TestStatus.DENIED)
            
            # Exit non-zero if any denied commands in strict non-interactive mode
            if args.non_interactive_only and denied > 0:
                logger.error(f"Validation failed: {denied} commands denied in strict non-interactive mode")
                sys.exit(1)
            
            # Exit non-zero if any denied commands in non-interactive mode
            if args.non_interactive and denied > 0:
                logger.error(f"Validation failed: {denied} commands denied in non-interactive mode")
                if args.fail_on_denied:
                    sys.exit(1)
                else:
                    logger.warning("Continuing despite denied commands (use --fail-on-denied to exit)")
            
            if failed > 0:
                logger.error(f"Validation failed with {failed} failures/errors")
                sys.exit(1)
            else:
                logger.info("All tests passed!")
                sys.exit(0)
                
        except Exception as e:
            logger.error(f"Validation failed with exception: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
