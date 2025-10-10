#!/usr/bin/env python3
"""
IOA Header Standardization Tool

Applies canonical SPDX/Apache-2.0 headers to source files and removes
agent/generator metadata from headers.
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Set, Optional

# File type mappings for comment syntax
COMMENT_SYNTAX = {
    'py': ('"""', '"""'),
    'js': ('//', ''),
    'ts': ('//', ''),
    'tsx': ('//', ''),
    'astro': ('<!--', '-->'),
    'rego': ('#', ''),
    'sh': ('#', ''),
    'bash': ('#', ''),
    'zsh': ('#', ''),
    'dockerfile': ('#', ''),
    'tf': ('#', ''),
    'sql': ('--', ''),
    'yml': ('#', ''),
    'yaml': ('#', ''),
    'md': ('<!--', '-->'),
    'html': ('<!--', '-->'),
    'css': ('/*', '*/'),
    'scss': ('/*', '*/'),
    'sass': ('/*', '*/'),
    'less': ('/*', '*/'),
}

# Files to skip
SKIP_PATTERNS = {
    '__pycache__',
    '.git',
    '.pytest_cache',
    'node_modules',
    '.coverage',
    'htmlcov',
    '*.pyc',
    '*.pyo',
    '*.so',
    '*.dll',
    '*.exe',
    '*.bin',
    '*.zip',
    '*.tar.gz',
    '*.tgz',
    'LICENSE',
    'CHANGELOG.md',
    'README.md',
    'CONTRIBUTING.md',
    'SECURITY.md',
    'CODE_OF_CONDUCT.md',
    'MANIFEST.txt',
    'NOTICE',
    'VERSION',
    'requirements.txt',
    'requirements-dev.txt',
    'requirements-docs.txt',
    'pyproject.toml',
    'setup.py',
    'setup.cfg',
    'tox.ini',
    'pytest.ini',
    'Makefile',
    'Dockerfile',
    'docker-compose.yml',
    'package.json',
    'package-lock.json',
    'yarn.lock',
    'pnpm-lock.yaml',
    '.gitignore',
    '.gitattributes',
    '.editorconfig',
    '.pre-commit-config.yaml',
    '.mdc',
    'mdc',
    'ioa-file-headers.mdc',
    'BRANDING_POLICY.md',
    'rebrand_script.py',
    'rebrand_inventory.json',
}

# Agent/generator patterns to remove
AGENT_PATTERNS = [
]

def should_skip_file(filepath: Path) -> bool:
    """Check if file should be skipped."""
    # Check skip patterns
    for pattern in SKIP_PATTERNS:
        if pattern in str(filepath) or filepath.name == pattern:
            return True
    
    # Skip binary files
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:
                return True
    except:
        return True
    
    return False

def get_file_extension(filepath: Path) -> str:
    """Get file extension, handling special cases."""
    name = filepath.name.lower()
    
    # Special cases
    if name == 'dockerfile':
        return 'dockerfile'
    elif name == 'makefile':
        return 'sh'
    elif name.endswith('.mdc'):
        return 'yaml'
    
    return filepath.suffix.lstrip('.').lower()

def get_canonical_header(filepath: Path, is_restricted: bool = False) -> str:
    """Generate canonical header for file type."""
    ext = get_file_extension(filepath)
    
    if ext not in COMMENT_SYNTAX:
        return ""
    
    start_comment, end_comment = COMMENT_SYNTAX[ext]
    
    # Base SPDX header
    lines = [
        f"{start_comment} SPDX-License-Identifier: Apache-2.0",
        f"{start_comment} Copyright (c) 2025 OrchIntel Systems Ltd.",
        f"{start_comment} https://orchintel.com | https://ioa.systems",
        f"{start_comment}",
    ]
    
    if is_restricted:
        lines.extend([
            f"{start_comment} Restricted Edition component.",
            f"{start_comment} Distribution and use are subject to Restricted Edition Terms.",
            f"{start_comment} Do not redistribute outside approved environments.",
        ])
    else:
        lines.append(f"{start_comment} Part of IOA Core (Open Source Edition). See LICENSE at repo root.")
    
    if end_comment:
        lines.append(end_comment)
    
    return '\n'.join(lines) + '\n\n'

def clean_agent_metadata(content: str) -> str:
    """Remove agent/generator metadata from content."""
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Check if line matches any agent pattern
        should_remove = False
        for pattern in AGENT_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                should_remove = True
                break
        
        if not should_remove:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def has_spdx_header(content: str) -> bool:
    """Check if content already has SPDX header."""
    return 'SPDX-License-Identifier: Apache-2.0' in content

def apply_header_to_file(filepath: Path, is_restricted: bool = False, dry_run: bool = False) -> bool:
    """Apply canonical header to a file."""
    if should_skip_file(filepath):
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Skip binary files
        return False
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    # Clean agent metadata
    content = clean_agent_metadata(content)
    
    # Check if already has SPDX header
    if has_spdx_header(content):
        # Just clean metadata if header exists
        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        return True
    
    # Generate new header
    header = get_canonical_header(filepath, is_restricted)
    if not header:
        return False
    
    # Add header to content
    new_content = header + content
    
    if not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return True

def process_repository(repo_path: Path, is_restricted: bool = False, dry_run: bool = False) -> Dict[str, int]:
    """Process entire repository for header standardization."""
    stats = {'processed': 0, 'skipped': 0, 'errors': 0}
    
    # Find all source files
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            filepath = Path(root) / file
            
            if should_skip_file(filepath):
                stats['skipped'] += 1
                continue
            
            try:
                if apply_header_to_file(filepath, is_restricted, dry_run):
                    stats['processed'] += 1
                    if dry_run:
                        print(f"Would process: {filepath}")
                    else:
                        print(f"Processed: {filepath}")
                else:
                    stats['skipped'] += 1
            except Exception as e:
                stats['errors'] += 1
                print(f"Error processing {filepath}: {e}")
    
    return stats

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Apply canonical SPDX headers to source files')
    parser.add_argument('--repo-root', default='.', help='Repository root directory')
    parser.add_argument('--restricted', action='store_true', help='Apply restricted edition headers')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--file', help='Process specific file only')
    
    args = parser.parse_args()
    
    repo_path = Path(args.repo_root).resolve()
    
    if not repo_path.exists():
        print(f"Error: Repository path {repo_path} does not exist")
        sys.exit(1)
    
    if args.file:
        # Process single file
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: File {filepath} does not exist")
            sys.exit(1)
        
        if apply_header_to_file(filepath, args.restricted, args.dry_run):
            print(f"Successfully processed {filepath}")
        else:
            print(f"Skipped {filepath}")
    else:
        # Process entire repository
        print(f"Processing repository: {repo_path}")
        print(f"Restricted edition: {args.restricted}")
        print(f"Dry run: {args.dry_run}")
        print()
        
        stats = process_repository(repo_path, args.restricted, args.dry_run)
        
        print(f"  Processed: {stats['processed']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"  Errors: {stats['errors']}")

if __name__ == '__main__':
    main()
