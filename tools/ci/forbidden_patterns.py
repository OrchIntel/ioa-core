"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import argparse
import fnmatch
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import yaml


def load_config(config_path: str = ".ioa/ci-gates.yml") -> Dict[str, Any]:
    """Load CI gates configuration."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: {config_path} not found, using defaults")
        return {
            'hygiene': {
                'forbidden_patterns': ["**/*.pem", "**/.env*", "**/*_private_key*", "**/id_rsa*"]
            },
            'mode': 'monitor'
        }
    except yaml.YAMLError as e:
        print(f"Error parsing {config_path}: {e}")
        sys.exit(1)


def should_ignore_path(path: str) -> bool:
    """Check if path should be ignored during scanning."""
    ignore_patterns = [
        '.git/',
        'venv/',
        'ioa-env/',
        'artifacts/',
        '__pycache__/',
        '.pytest_cache/',
        'htmlcov/',
        'site/',
        'node_modules/',
        '.tox/',
        'build/',
        'dist/',
        '*.egg-info/',
        '.coverage',
        '.mypy_cache/',
        '.ruff_cache/'
    ]
    
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(path, pattern) or pattern.rstrip('/') in path:
            return True
    return False


def find_matching_files(patterns: List[str], root_dir: str = ".") -> List[str]:
    """Find files matching forbidden patterns."""
    matches = []
    root_path = Path(root_dir).resolve()
    
    for pattern in patterns:
        for root, dirs, files in os.walk(root_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not should_ignore_path(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_path)
                
                if should_ignore_path(rel_path):
                    continue
                
                # Check multiple pattern variations
                if (fnmatch.fnmatch(rel_path, pattern) or 
                    fnmatch.fnmatch(file, pattern) or
                    fnmatch.fnmatch(rel_path.replace(os.sep, '/'), pattern) or
                    fnmatch.fnmatch(f"**/{file}", pattern) or
                    fnmatch.fnmatch(f"**/{rel_path}", pattern)):
                    matches.append(rel_path)
    
    return sorted(set(matches))


def main():
    """Main entry point for forbidden patterns checker."""
    parser = argparse.ArgumentParser(description="Check for forbidden patterns in repository")
    parser.add_argument("--config", default=".ioa/ci-gates.yml", help="Path to CI gates config")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--root", default=".", help="Root directory to scan")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    patterns = config.get('hygiene', {}).get('forbidden_patterns', [])
    mode = config.get('mode', 'monitor')
    
    if not patterns:
        if args.json:
            print(json.dumps({"matches": [], "count": 0, "mode": mode}))
        else:
            print("No forbidden patterns configured")
        sys.exit(0)
    
    # Find matching files
    matches = find_matching_files(patterns, args.root)
    
    if args.json:
        result = {
            "matches": matches,
            "count": len(matches),
            "mode": mode,
            "patterns": patterns
        }
        print(json.dumps(result, indent=2))
    else:
        if matches:
            print(f"Found {len(matches)} files matching forbidden patterns:")
            for match in matches:
                print(f"  - {match}")
        else:
            print("No forbidden patterns found")
    
    # Exit code based on mode and matches
    if matches and mode == 'strict':
        if not args.json:
            print(f"\nError: Found {len(matches)} forbidden files in strict mode")
        sys.exit(1)
    elif matches and mode == 'monitor':
        if not args.json:
            print(f"\nWarning: Found {len(matches)} forbidden files in monitor mode")
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
