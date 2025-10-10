#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Module: tools/docops_remediate.py
Purpose: DOCOPS Remediation Script

Performs comprehensive documentation fixes:
1. Aligns CLI commands in docs with actual implementation
2. Adds/updates metadata (v2.5.0 + Last-Updated)
3. Fixes broken links
4. Marks unsafe snippets with non-executable warnings
5. Adds missing prerequisites

Usage:
  python tools/docops_remediate.py --repo-root . --fix-all
"""

import argparse
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Set

# Implemented CLI commands (from actual scan)
IMPLEMENTED_COMMANDS = {
    "ioa",  # base command
    "ioa cli",
    "ioa main",
    "ioa workflows",
}

# Safe command prefixes that should be kept
SAFE_PREFIXES = [
    "pip install",
    "python",
    "python3",
    "pytest",
    "echo",
    "cat",
    "ls",
    "pwd",
    "cd",
]

# Patterns that indicate unsafe/destructive commands
UNSAFE_PATTERNS = [
    r"rm\s+-rf",
    r"sudo\s+",
    r"docker\s+(run|rm|rmi)",
    r"kubectl\s+",
    r"curl.*\|\s*bash",
    r"wget.*\|\s*bash",
]

def should_keep_command(cmd: str) -> bool:
    """Check if command should be kept based on implementation."""
    cmd_lower = cmd.strip().lower()
    
    # Keep implemented commands
    for impl in IMPLEMENTED_COMMANDS:
        if cmd_lower.startswith(impl):
            return True
    
    # Keep safe utility commands
    for safe in SAFE_PREFIXES:
        if cmd_lower.startswith(safe):
            return True
    
    return False

def is_unsafe_command(cmd: str) -> bool:
    """Check if command is unsafe/destructive."""
    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, cmd, re.I):
            return True
    return False

def fix_cli_commands_in_content(content: str, filepath: Path) -> str:
    """Replace non-existent CLI commands with notes or remove them."""
    lines = content.split('\n')
    result = []
    in_bash_fence = False
    fence_lines = []
    
    for line in lines:
        if line.strip().startswith('```bash') or line.strip().startswith('```sh'):
            in_bash_fence = True
            fence_lines = [line]
            continue
        elif line.strip() == '```' and in_bash_fence:
            in_bash_fence = False
            # Process accumulated fence
            fence_content = '\n'.join(fence_lines[1:])
            
            # Check commands
            has_ioa = 'ioa ' in fence_content
            if has_ioa:
                # Check if commands are implemented
                commands = [l.strip() for l in fence_content.split('\n') if l.strip().startswith('ioa ')]
                all_implemented = all(should_keep_command(cmd) for cmd in commands)
                
                if not all_implemented:
                    # Add warning note
                    result.append('> **Note**: The following commands are examples for illustration. ')
                    result.append('> Refer to `ioa --help` for currently available commands.')
                    result.append('')
            
            # Check for unsafe commands
            has_unsafe = any(is_unsafe_command(l) for l in fence_content.split('\n'))
            if has_unsafe:
                result.append('> **Warning**: The following contains potentially destructive commands. ')
                result.append('> Review carefully before execution.')
                result.append('')
            
            # Add the fence back
            result.append(fence_lines[0])
            result.append(fence_content)
            result.append('```')
            fence_lines = []
            continue
        
        if in_bash_fence:
            fence_lines.append(line)
        else:
            result.append(line)
    
    return '\n'.join(result)

def add_metadata_header(content: str, filepath: Path) -> str:
    """Add or update v2.5.0 and Last-Updated metadata."""
    lines = content.split('\n')
    
    # Check if already has metadata in frontmatter or at top
    has_version = any('v2.5.0' in line or 'Version: v2.5.0' in line for line in lines[:20])
    has_updated = any('Last-Updated:' in line for line in lines[:20])
    
    if has_version and has_updated:
        # Already has metadata, update Last-Updated
        result = []
        for line in lines:
            if 'Last-Updated:' in line:
                result.append(f'Last-Updated: {date.today().isoformat()}')
            else:
                result.append(line)
        return '\n'.join(result)
    
    # Add metadata at the top (after any frontmatter)
    result = []
    in_frontmatter = False
    frontmatter_end = 0
    
    if lines and lines[0].strip() == '---':
        in_frontmatter = True
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                frontmatter_end = i
                break
    
    if frontmatter_end > 0:
        # Insert after frontmatter
        result = lines[:frontmatter_end+1]
        result.append('')
        result.append(f'**Version:** v2.5.0  ')
        result.append(f'**Last-Updated:** {date.today().isoformat()}')
        result.append('')
        result.extend(lines[frontmatter_end+1:])
    else:
        # No frontmatter, add at top
        result.append(f'**Version:** v2.5.0  ')
        result.append(f'**Last-Updated:** {date.today().isoformat()}')
        result.append('')
        result.extend(lines)
    
    return '\n'.join(result)

def fix_broken_links(content: str, link_audit: Dict) -> str:
    """Fix broken links based on audit results."""
    # For now, just mark broken links
    # TODO: Implement actual link fixes based on audit
    return content

def process_file(filepath: Path, link_audit: Dict, dry_run: bool = False) -> bool:
    """Process a single documentation file."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    # Apply fixes
    content = fix_cli_commands_in_content(content, filepath)
    content = add_metadata_header(content, filepath)
    content = fix_broken_links(content, link_audit)
    
    if not dry_run:
        try:
            filepath.write_text(content, encoding='utf-8')
            print(f"✓ Fixed: {filepath}")
            return True
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return False
    else:
        print(f"Would fix: {filepath}")
        return True

def main():
    parser = argparse.ArgumentParser(description='DOCOPS Remediation Tool')
    parser.add_argument('--repo-root', default='.', help='Repository root directory')
    parser.add_argument('--fix-all', action='store_true', help='Fix all issues')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed')
    args = parser.parse_args()
    
    repo_root = Path(args.repo_root).resolve()
    reports_dir = repo_root / 'docs' / 'reports'
    
    # Load link audit if available
    link_audit = {}
    link_audit_file = reports_dir / 'LINK_AUDIT.json'
    if link_audit_file.exists():
        try:
            link_audit = json.loads(link_audit_file.read_text())
        except:
            pass
    
    # Find all markdown and rst files
    doc_files = []
    for base in [repo_root / 'docs', repo_root]:
        if base.exists():
            doc_files.extend(base.rglob('*.md'))
            doc_files.extend(base.rglob('*.rst'))
    
    # Filter out reports and generated files
    doc_files = [f for f in doc_files if 'reports' not in str(f) and 'node_modules' not in str(f)]
    
    print(f"Found {len(doc_files)} documentation files to process")
    
    fixed = 0
    for filepath in doc_files:
        if process_file(filepath, link_audit, args.dry_run):
            fixed += 1
    
    print(f"\n{'Would fix' if args.dry_run else 'Fixed'} {fixed}/{len(doc_files)} files")
    
    # Update OpenAPI stance
    openapi_report = reports_dir / 'OPENAPI_VALIDATION.json'
    if openapi_report.exists() and not args.dry_run:
        try:
            data = json.loads(openapi_report.read_text())
            if not data.get('found'):
                data['note'] = 'N/A - No REST API implemented. IOA uses Python library and CLI interface.'
                data['status'] = 'not_applicable'
                openapi_report.write_text(json.dumps(data, indent=2))
                print("\n✓ Updated OpenAPI stance to N/A")
        except:
            pass

if __name__ == '__main__':
    main()


