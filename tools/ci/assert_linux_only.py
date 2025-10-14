"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import os
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any


def scan_workflows(workflows_dir: Path) -> List[Dict[str, Any]]:
    """Scan all workflow files for non-Linux runners."""
    issues = []
    
    for workflow_file in workflows_dir.glob("*.yml"):
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # Use regex-based scanning instead of YAML parsing for robustness
            issues.extend(scan_content_for_non_linux_runners(content, workflow_file))
                                
        except Exception as e:
            issues.append({
                'file': str(workflow_file),
                'job': 'unknown',
                'type': 'file-error',
                'value': str(e),
                'line': 0
            })
    
    return issues


def scan_content_for_non_linux_runners(content: str, workflow_file: Path) -> List[Dict[str, Any]]:
    """Scan file content for non-Linux runners using regex."""
    import re
    issues = []
    
    # Find all runs-on declarations
    runs_on_pattern = r'runs-on:\s*([^\n]+)'
    for match in re.finditer(runs_on_pattern, content, re.MULTILINE):
        runs_on_value = match.group(1).strip()
        line_num = content[:match.start()].count('\n') + 1
        
        # Check if it's a non-Linux runner
        if runs_on_value not in ['ubuntu-latest', 'ubuntu-22.04', 'ubuntu-20.04', '${{ matrix.os }}']:
            # Skip if it's a variable reference
            if not runs_on_value.startswith('${{'):
                issues.append({
                    'file': str(workflow_file),
                    'job': 'unknown',
                    'type': 'runs-on',
                    'value': runs_on_value,
                    'line': line_num
                })
    
    # Find matrix OS arrays
    matrix_os_pattern = r'os:\s*\[([^\]]+)\]'
    for match in re.finditer(matrix_os_pattern, content, re.MULTILINE):
        os_values_str = match.group(1)
        line_num = content[:match.start()].count('\n') + 1
        
        # Parse OS values
        os_values = [v.strip().strip("'\"") for v in os_values_str.split(',')]
        for os_value in os_values:
            if os_value not in ['ubuntu-latest', 'ubuntu-22.04', 'ubuntu-20.04']:
                issues.append({
                    'file': str(workflow_file),
                    'job': 'unknown',
                    'type': 'matrix-os',
                    'value': os_value,
                    'line': line_num
                })
    
    return issues


def find_line_number(content: str, search_text: str) -> int:
    """Find line number for a specific text."""
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if search_text in line:
            return i
    return 0


def main():
    """Main entry point."""
    workflows_dir = Path(".github/workflows")
    
    if not workflows_dir.exists():
        print("❌ .github/workflows directory not found")
        sys.exit(1)
    
    print("🔍 Scanning GitHub Actions workflows for non-Linux runners...")
    
    issues = scan_workflows(workflows_dir)
    
    if issues:
        print(f"❌ Found {len(issues)} non-Linux runner(s):")
        print()
        
        for issue in issues:
            print(f"  File: {issue['file']}")
            print(f"  Job: {issue['job']}")
            print(f"  Type: {issue['type']}")
            print(f"  Value: {issue['value']}")
            if issue['line'] > 0:
                print(f"  Line: {issue['line']}")
            print()
        
        print("💡 All workflows must use ubuntu-latest, ubuntu-22.04, or ubuntu-20.04")
        print("💡 Remove macOS and Windows runners to comply with CI platform policy")
        sys.exit(1)
    else:
        print("✅ All workflows use Linux runners only")
        sys.exit(0)


if __name__ == "__main__":
    main()
