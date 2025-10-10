""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Tuple

# Organization keywords that should not appear in Core paths
ORGANIZATION_KEYWORDS = [
    r'organization-repo',
    r'@ioa-organization-team',
    r'packages\.organization',
    r'ioa-organization',
    r'organization\.env',
    r'organization\.yaml',
    r'organization\.yml',
    r'organization\.json',
]

# Paths to exclude from scanning (these are allowed to contain organization references)
EXCLUDED_PATHS = {
    'docs/README_ORGANIZATION.md',  # Organization documentation
    'docs/ops/qa_archive/**',     # QA archive
    'docs/ops/organization/**',     # Organization artifacts and reports
    'docs/ops/qa/dispatch-032/**',  # Dispatch reports with organization references
    'tests/infra/test_shim_aliases.py',  # Organization test file (properly gated)
    'tests/policy/test_no_stray_xfail_skip.py',  # Organization mark definition
    'pyproject.toml',  # Optional dependency groups
}

# Paths to scan for organization references
CORE_PATHS = [
    'src',
    'config',
    'docs',
    'tests',
    'examples',
    'schemas',
]

def should_exclude_path(file_path: str) -> bool:
    """Check if a file path should be excluded from scanning."""
    for excluded in EXCLUDED_PATHS:
        if excluded.endswith('**'):
            # Handle wildcard paths
            base_path = excluded.replace('/**', '')
            if file_path.startswith(base_path):
                return True
        elif file_path == excluded:
            return True
    return False

def scan_file_for_organization_keywords(file_path: str) -> List[Tuple[str, int, str]]:
    """Scan a file for organization keywords and return violations."""
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                for keyword in ORGANIZATION_KEYWORDS:
                    if re.search(keyword, line, re.IGNORECASE):
                        violations.append((keyword, line_num, line.strip()))
    except (UnicodeDecodeError, PermissionError):
        # Skip binary files or files we can't read
        pass
    
    return violations

def scan_directory_for_organization_references() -> List[Tuple[str, str, int, str]]:
    """Scan directories for organization references and return violations."""
    violations = []
    
    for core_path in CORE_PATHS:
        if not os.path.exists(core_path):
            continue
            
        for root, dirs, files in os.walk(core_path):
            for file in files:
                # Skip binary files and common non-text files
                if file.endswith(('.pyc', '.pyo', '.so', '.dll', '.exe', '.bin', '.zip', '.tar.gz')):
                    continue
                    
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path)
                
                # Skip excluded paths
                if should_exclude_path(relative_path):
                    continue
                
                # Scan for organization keywords
                file_violations = scan_file_for_organization_keywords(file_path)
                for keyword, line_num, line_content in file_violations:
                    violations.append((relative_path, keyword, line_num, line_content))
    
    return violations

def main():
    """Main function to run the organization guard."""
    print("🔍 Scanning Core paths for organization references...")
    
    violations = scan_directory_for_organization_references()
    
    if violations:
        print("❌ Organization references found in Core paths!")
        print("\nViolations:")
        print("=" * 80)
        
        for file_path, keyword, line_num, line_content in violations:
            print(f"File: {file_path}:{line_num}")
            print(f"Keyword: {keyword}")
            print(f"Content: {line_content}")
            print("-" * 80)
        
        print(f"\nTotal violations: {len(violations)}")
        print("\nCore repository must not contain organization references.")
        print("Move organization-specific content to the Organization repository.")
        sys.exit(1)
    else:
        print("✅ No organization references found in Core paths")
        print("Organization guard passed successfully!")

if __name__ == "__main__":
    main()
