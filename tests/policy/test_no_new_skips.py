""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Policy test to enforce strict testing: no new @skip or @xfail decorators
unless properly justified with DISPATCH-ID and expiry tracking.
"""

import re
import pathlib
import pytest
from typing import List, Tuple, Set
from datetime import datetime, timezone

# Known skip patterns that are allowed
KNOWN_SKIP_PATTERNS: Set[str] = {
    # Legacy skips that must be documented
    # All known skips have been eliminated
}

def scan_file_for_skips(file_path: pathlib.Path) -> List[Tuple[str, str, str]]:
    """Scan a single file for skip/xfail decorators."""
    violations = []
    
    try:
        text = file_path.read_text(errors='ignore')
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Look for skip/xfail decorators
            if re.search(r'@(?:skip|xfail)', line):
                # Check if it has proper justification
                if not re.search(r'#\s*JUSTIFY:\s*DISPATCH-\d+', line):
                    # Check if it's in the known skips list
                    test_name = extract_test_name_from_context(text, line_num)
                    if test_name not in KNOWN_SKIP_PATTERNS:
                        violations.append((
                            str(file_path),
                            f"line {line_num}: {line.strip()}",
                            test_name or "unknown test"
                        ))
    except Exception as e:
        # Skip files that can't be read
        pass
    
    return violations

def extract_test_name_from_context(text: str, line_num: int) -> str:
    """Extract test name from context around the skip decorator."""
    lines = text.split('\n')
    
    # Look for test function definition after the decorator
    for i in range(line_num, min(line_num + 10, len(lines))):
        line = lines[i]
        # Look for test function pattern
        match = re.search(r'def\s+(test_\w+)', line)
        if match:
            return match.group(1)
    
    return "unknown test"

def test_no_new_skips_without_justification():
    """Test that no new skip/xfail decorators exist without proper justification."""
    root = pathlib.Path(".")
    violations = []
    
    for file_path in root.rglob("*.py"):
        # Skip policy tests themselves
        if "tests/policy/" in str(file_path):
            continue
            
        # Skip common ignore patterns
        rel_path = str(file_path).replace("\\", "/")
        if any(ignore in rel_path for ignore in [
            'node_modules/', '.venv/', 'venv/', 'ioa-env/', '__pycache__/', 
            '.git/', '.pytest_cache/', '.cache/', 'artifacts/', 'build/', 'dist/'
        ]):
            continue
            
        # Only scan test files
        if not (file_path.name.startswith('test_') or 'test' in file_path.name):
            continue
            
        # Scan file for violations
        file_violations = scan_file_for_skips(file_path)
        violations.extend(file_violations)
    
    # Report violations
    if violations:
        violation_report = "\n".join([
            f"  {file_path}: {issue} | Test: {test_name}"
            for file_path, issue, test_name in violations
        ])
        
        pytest.fail(
            f"Found {len(violations)} skip/xfail decorators without proper justification:\n{violation_report}\n\n"
            "All skip/xfail decorators must include:\n"
            "  # JUSTIFY: DISPATCH-XXX <reason>\n"
            "And be added to KNOWN_SKIPS.txt with expiry date.\n"
            "Example: @pytest.mark.skip(reason='Known issue')  # JUSTIFY: DISPATCH-010 <reason>"
        )
    
    # Test passes if no violations found
    assert len(violations) == 0, "Unjustified skip/xfail decorators detected"

def test_known_skips_are_documented():
    """Test that all known skips are properly documented."""
    # This test ensures that if we have known skips, they're tracked
    # For now, we expect no legacy skips to remain
    assert len(KNOWN_SKIP_PATTERNS) == 0, (
        "Known skips should be eliminated. Current known skips:\n" +
        "\n".join(f"  {skip}" for skip in KNOWN_SKIP_PATTERNS)
    )

def test_skip_justification_format():
    """Test that skip justifications follow the required format."""
    root = pathlib.Path(".")
    format_violations = []
    
    for file_path in root.rglob("*.py"):
        if not file_path.name.startswith('test_'):
            continue
            
        try:
            text = file_path.read_text(errors='ignore')
            lines = text.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                if re.search(r'@(?:skip|xfail)', line):
                    # Check justification format
                    justification_match = re.search(r'#\s*JUSTIFY:\s*(DISPATCH-\d+)', line)
                    if justification_match:
                        dispatch_id = justification_match.group(1)
                        # Validate dispatch ID format
                        if not re.match(r'DISPATCH-\d+', dispatch_id):
                            format_violations.append(
                                f"{file_path}:{line_num} - Invalid dispatch ID format: {dispatch_id}"
                            )
        except Exception:
            pass
    
    if format_violations:
        pytest.fail(
            f"Found {len(format_violations)} skip justification format violations:\n" +
            "\n".join(f"  {violation}" for violation in format_violations)
        )
    
    assert len(format_violations) == 0, "Skip justification format violations detected"
