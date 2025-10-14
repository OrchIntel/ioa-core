"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import ast
import os
from pathlib import Path
from typing import List, Set, Tuple


def collect_pytest_markers(file_path: Path) -> List[Tuple[str, int, str]]:
    """Collect all pytest markers from a Python file."""
    markers = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'pytest' and
                    node.func.attr in ['mark', 'xfail', 'skip']):
                    
                    # Handle @pytest.mark.xfail, @pytest.mark.skip, etc.
                    if node.func.attr == 'mark':
                        if (node.args and 
                            isinstance(node.args[0], ast.Attribute) and
                            node.args[0].attr in ['xfail', 'skip']):
                            markers.append((node.args[0].attr, node.lineno, str(node)))
                    else:
                        # Handle @pytest.xfail, @pytest.skip directly
                        # Extract the actual arguments for better analysis
                        if node.args:
                            # Get the first argument (usually the reason)
                            first_arg = node.args[0]
                            if isinstance(first_arg, ast.Constant):
                                arg_value = str(first_arg.value)
                            elif isinstance(first_arg, ast.JoinedStr):
                                # Handle f-strings by extracting the string parts
                                parts = []
                                for part in first_arg.values:
                                    if isinstance(part, ast.Constant):
                                        parts.append(str(part.value))
                                    else:
                                        parts.append(str(part))
                                arg_value = "".join(parts)
                            else:
                                arg_value = str(first_arg)
                        else:
                            arg_value = ""
                        markers.append((node.func.attr, node.lineno, arg_value))
                        
    except (SyntaxError, UnicodeDecodeError):
        # Skip files that can't be parsed
        pass
    
    return markers


def test_no_stray_xfail_skip_markers():
    """Ensure no stray xfail/skip markers exist outside allowed contexts."""
    # Allowed markers that are permitted
    ALLOWED_MARKERS = {
        'interactive',  # For interactive tests that require user input
        'network',      # For network-dependent tests
        'slow',         # For slow tests that can be excluded by default
        'performance',  # For performance tests
        'integration',  # For integration tests
        'asyncio',      # For async tests
        'live',         # For live API tests
        'perf',         # For performance tests
        'timeout',      # For timeout tests
        'organization'    # For organization package tests (IOA_TEST_ORGANIZATION=1)
    }
    
    # Find all Python test files
    test_dir = Path(__file__).parent.parent
    test_files = list(test_dir.rglob("*.py"))
    
    violations = []
    
    for test_file in test_files:
        if test_file.name.startswith('__'):
            continue
            
        markers = collect_pytest_markers(test_file)
        
        for marker_type, line_num, marker_code in markers:
            if marker_type in ['xfail', 'skip']:
                # Check if this is a skipif with a legitimate reason
                if marker_type == 'skipif' and 'not available' in marker_code:
                    # This is a legitimate skipif for missing dependencies
                    continue
                    
                # Check if this is a skipif with a legitimate condition
                if marker_type == 'skipif' and any(reason in marker_code.lower() for reason in [
                    'skip', 'xfail', 'not available', 'missing', 'unavailable'
                ]):
                    continue
                
                # Check if this is a pytest.skip() with a legitimate reason
                if marker_type == 'skip' and any(reason in marker_code.lower() for reason in [
                    'not available', 'missing', 'unavailable', 'module not available',
                    'enterprise testing not enabled', 'organization testing not enabled'
                ]):
                    # This is a legitimate skip for missing dependencies
                    continue
                
                # Allowlist specific skip that depends on backend capability
                candidate = f"{test_file}:{line_num} - {marker_type}: {marker_code}"
                allowlist_suffixes = {
                    "/tests/memory/test_cold_bridge.py:75 - skip: Cold storage retrieval not supported",
                    "tests/memory/test_cold_bridge.py:75 - skip: Cold storage retrieval not supported",
                    "/tests/memory_fabric/test_s3_live.py:131 - skip: IOA_FABRIC_KEY not set - skipping encryption test",
                    "tests/memory_fabric/test_s3_live.py:131 - skip: IOA_FABRIC_KEY not set - skipping encryption test",
                }
                # Normalize paths to POSIX style to compare reliably
                norm_candidate = candidate.replace(str(Path.cwd()), "").replace("\\", "/")
                if not any(norm_candidate.endswith(suffix) for suffix in allowlist_suffixes):
                    # If we get here, it's a potential violation
                    violations.append(norm_candidate)
    
    # Report violations
    if violations:
        violation_msg = "\n".join(violations)
        raise AssertionError(
            f"Found {len(violations)} potential stray xfail/skip markers:\n{violation_msg}\n\n"
            f"Only these markers are allowed: {', '.join(sorted(ALLOWED_MARKERS))}\n"
            "Use skipif with legitimate conditions (e.g., missing dependencies) or remove unnecessary markers."
        )
    
    # If we get here, no violations found
    assert True, "No stray xfail/skip markers found - policy compliance verified"
