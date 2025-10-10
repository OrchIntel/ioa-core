""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

import subprocess
import sys
import os
import json
import logging
import yaml
import fnmatch
import re
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from pathlib import Path

# PATCH: Cursor-2025-01-11 DISPATCH-OPS-20250911-CURSOR-HYGIENE-AUTO-COMMIT <hygiene auto-commit system>

@dataclass
class HygieneResult:
    """Result of hygiene check operation."""
    passed: bool
    errors: List[str]
    warnings: List[str]
    commit_sha: Optional[str] = None
    remote_sync: bool = False
    pr_url: Optional[str] = None
    files_staged: int = 0
    files_skipped: int = 0
    target_repo: Optional[str] = None
    target_branch: Optional[str] = None
    target_mode: Optional[str] = None

@dataclass
class HygieneConfig:
    """Hygiene router configuration."""
    default_repo: str
    default_branch: str
    default_mode: str
    routes: Dict[str, Dict[str, str]]
    guards: Dict[str, any]

@dataclass
class SecretScanResult:
    """Result of secret scanning."""
    passed: bool
    secrets_found: List[str]
    files_checked: int

class GitHubHygiene:
    """GitHub hygiene checker for dispatch completion."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.logger = self._setup_logger()
        self.workspace_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        self.hygiene_config = self._load_hygiene_config()
        self.ignore_patterns = self._load_ignore_patterns()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for hygiene operations."""
        logger = logging.getLogger('github_hygiene')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _load_hygiene_config(self) -> HygieneConfig:
        """Load hygiene router configuration."""
        config_path = os.path.join(self.workspace_root, '.hygienerc.yml')
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            return HygieneConfig(
                default_repo=config_data['default']['repo'],
                default_branch=config_data['default']['branch'],
                default_mode=config_data['default']['mode'],
                routes=config_data.get('routes', {}),
                guards=config_data.get('guards', {})
            )
        except Exception as e:
            self.logger.warning(f"Failed to load hygiene config: {e}, using defaults")
            return HygieneConfig(
                default_repo="OrchIntel/ioa",
                default_branch="main",
                default_mode="pr",
                routes={},
                guards={}
            )
    
    def _load_ignore_patterns(self) -> List[str]:
        """Load ignore patterns from .hygieneignore file."""
        ignore_path = os.path.join(self.workspace_root, '.hygieneignore')
        patterns = []
        try:
            with open(ignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception as e:
            self.logger.warning(f"Failed to load ignore patterns: {e}")
        
        return patterns
    
    def _should_ignore_file(self, file_path: str) -> bool:
        """Check if file should be ignored based on patterns."""
        for pattern in self.ignore_patterns:
            if pattern.startswith('!'):
                # Negation pattern - force include
                if fnmatch.fnmatch(file_path, pattern[1:]):
                    return False
            else:
                # Normal pattern - ignore if matches
                if fnmatch.fnmatch(file_path, pattern):
                    return True
        return False
    
    def _scan_for_secrets(self, file_path: str) -> List[str]:
        """Scan file for potential secrets."""
        secrets = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Common secret patterns
            secret_patterns = [
                (r'api[_-]?key["\s]*[:=]["\s]*[a-zA-Z0-9]{20,}', 'API Key'),
                (r'secret["\s]*[:=]["\s]*[a-zA-Z0-9]{20,}', 'Secret'),
                (r'password["\s]*[:=]["\s]*[^\s]{8,}', 'Password'),
                (r'token["\s]*[:=]["\s]*[a-zA-Z0-9]{20,}', 'Token'),
                (r'-----BEGIN [A-Z ]+-----', 'Private Key'),
                (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI API Key'),
                (r'pk_[a-zA-Z0-9]{20,}', 'Stripe Public Key'),
                (r'sk_[a-zA-Z0-9]{20,}', 'Stripe Secret Key'),
            ]
            
            for pattern, secret_type in secret_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    secrets.append(f"{secret_type} in {file_path}: {match[:20]}...")
                    
        except Exception as e:
            self.logger.warning(f"Failed to scan {file_path} for secrets: {e}")
        
        return secrets
    
    def _determine_target_route(self, dispatch_code: str, dispatch_title: str) -> Tuple[str, str, str]:
        """Determine target repository, branch, and mode for dispatch."""
        # Check for dispatch-specific overrides in status reports
        status_report_path = f"docs/ops/status_reports/STATUS_REPORT_{dispatch_code.replace('-', '_')}.md"
        full_path = os.path.join(self.workspace_root, status_report_path)
        
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                
                # Look for YAML front-matter
                if content.startswith('---'):
                    yaml_end = content.find('---', 3)
                    if yaml_end > 0:
                        yaml_content = content[3:yaml_end]
                        try:
                            front_matter = yaml.safe_load(yaml_content)
                            if 'dispatch' in front_matter:
                                dispatch_config = front_matter['dispatch']
                                
                                # Check for explicit repo/branch/mode
                                if 'target_repo' in dispatch_config:
                                    return (
                                        dispatch_config['target_repo'],
                                        dispatch_config.get('target_branch', self.hygiene_config.default_branch),
                                        dispatch_config.get('target_mode', self.hygiene_config.default_mode)
                                    )
                                
                                # Check for route name
                                if 'target_route' in dispatch_config:
                                    route = dispatch_config['target_route']
                                    if route in self.hygiene_config.routes:
                                        route_config = self.hygiene_config.routes[route]
                                        return (
                                            route_config['repo'],
                                            route_config['branch'],
                                            route_config['mode']
                                        )
                        except Exception as e:
                            self.logger.warning(f"Failed to parse dispatch config: {e}")
            except Exception as e:
                self.logger.warning(f"Failed to read dispatch config file: {e}")
        
        # Use default route
        return (
            self.hygiene_config.default_repo,
            self.hygiene_config.default_branch,
            self.hygiene_config.default_mode
        )
    
    def run_command(self, cmd: List[str], cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        if cwd is None:
            cwd = self.workspace_root
            
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env or os.environ.copy(),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out after 5 minutes"
        except Exception as e:
            return -1, "", str(e)
    
    def check_secret_scan(self) -> Tuple[bool, List[str]]:
        """Scan staged files for secrets."""
        self.logger.info("Running secret scan...")
        errors = []
        secrets_found = []
        
        # Get list of staged files
        exit_code, stdout, stderr = self.run_command(['git', 'diff', '--cached', '--name-only'])
        if exit_code != 0:
            errors.append(f"Failed to get staged files: {stderr}")
            return False, errors
        
        staged_files = [f.strip() for f in stdout.split('\n') if f.strip()]
        
        for file_path in staged_files:
            # Skip ignored files
            if self._should_ignore_file(file_path):
                continue
                
            # Skip binary files
            if not os.path.isfile(file_path):
                continue
                
            try:
                # Check if file is text
                with open(file_path, 'rb') as f:
                    chunk = f.read(1024)
                    if b'\0' in chunk:
                        continue  # Skip binary files
            except:
                continue
            
            # Scan for secrets
            file_secrets = self._scan_for_secrets(file_path)
            secrets_found.extend(file_secrets)
        
        if secrets_found:
            errors.append(f"Secrets detected: {len(secrets_found)} found")
            errors.extend(secrets_found[:10])  # Show first 10 secrets
            return False, errors
        
        self.logger.info("Secret scan passed")
        return True, errors

    def check_pre_commit_hooks(self) -> Tuple[bool, List[str]]:
        """Run pre-commit hooks (lint, format, spellcheck)."""
        self.logger.info("Running pre-commit hooks...")
        errors = []
        
        # Check if pre-commit is available
        exit_code, stdout, stderr = self.run_command(['pre-commit', '--version'])
        if exit_code != 0:
            self.logger.warning("pre-commit not available, skipping pre-commit hooks")
            return True, []
        
        # Ensure PRE_COMMIT_HOME is set to a writable dir
        env = os.environ.copy()
        if 'PRE_COMMIT_HOME' not in env:
            local_cache = os.path.join(self.workspace_root, 'artifacts', '.pre-commit')
            os.makedirs(local_cache, exist_ok=True)
            env['PRE_COMMIT_HOME'] = local_cache

        # Run pre-commit on all files via active interpreter
        exit_code, stdout, stderr = self.run_command([sys.executable, '-m', 'pre_commit', 'run', '--all-files'], env=env)
        if exit_code != 0:
            errors.append(f"Pre-commit hooks failed: {stderr}")
            return False, errors
        
        self.logger.info("Pre-commit hooks passed")
        return True, errors
    
    def check_ci_dry_run(self) -> Tuple[bool, List[str]]:
        """Simulate CI workflow with dry-run."""
        self.logger.info("Running CI dry-run simulation...")
        errors = []
        
        # Check if GitHub CLI is available
        exit_code, stdout, stderr = self.run_command(['gh', '--version'])
        if exit_code != 0:
            self.logger.warning("GitHub CLI not available, skipping CI dry-run")
            return True, []
        
        # Run targeted pytest (assurance slice) with zero warnings using active interpreter
        self.logger.info("Running pytest (assurance slice) with zero warnings...")
        exit_code, stdout, stderr = self.run_command([
            sys.executable, '-m', 'pytest', 'tests/test_assurance_calc.py', '-q', '-W', 'error'
        ])
        if exit_code != 0:
            errors.append(f"Pytest failed: {stderr}")
            return False, errors
        
        # Run mkdocs build --strict
        self.logger.info("Running mkdocs build --strict...")
        exit_code, stdout, stderr = self.run_command(['mkdocs', 'build', '--strict'])
        if exit_code != 0:
            errors.append(f"MkDocs build failed: {stderr}")
            return False, errors
        
        self.logger.info("CI dry-run simulation passed")
        return True, errors
    
    def check_merge_conflicts(self) -> Tuple[bool, List[str]]:
        """Simulate merge with main branch."""
        self.logger.info("Checking for merge conflicts...")
        errors = []
        
        # Fetch latest changes
        exit_code, stdout, stderr = self.run_command(['git', 'fetch', 'origin', 'main'])
        if exit_code != 0:
            errors.append(f"Failed to fetch main: {stderr}")
            return False, errors
        
        # Check for merge conflicts
        exit_code, stdout, stderr = self.run_command(['git', 'merge', '--no-commit', 'origin/main'])
        if exit_code != 0:
            errors.append(f"Merge conflicts detected: {stderr}")
            # Reset the merge attempt
            self.run_command(['git', 'merge', '--abort'])
            return False, errors
        
        # Reset the merge attempt (we only wanted to check for conflicts)
        self.run_command(['git', 'merge', '--abort'])
        
        self.logger.info("No merge conflicts detected")
        return True, errors
    
    def stage_files_with_ignore(self) -> Tuple[bool, int, int, List[str]]:
        """Stage files while respecting .hygieneignore patterns."""
        self.logger.info("Staging files with ignore patterns...")
        errors = []
        files_staged = 0
        files_skipped = 0
        
        # Get all changed files
        exit_code, stdout, stderr = self.run_command(['git', 'status', '--porcelain'])
        if exit_code != 0:
            errors.append(f"Failed to check git status: {stderr}")
            return False, 0, 0, errors
        
        if not stdout.strip():
            self.logger.info("No changes to stage")
            return True, 0, 0, errors
        
        # Process each file
        for line in stdout.strip().split('\n'):
            if not line.strip():
                continue
                
            # Parse git status line (XY filename)
            status = line[:2]
            file_path = line[3:].strip()
            
            # Skip if file is ignored
            if self._should_ignore_file(file_path):
                files_skipped += 1
                self.logger.debug(f"Skipping ignored file: {file_path}")
                continue
            
            # Stage the file
            exit_code, stdout_stage, stderr_stage = self.run_command(['git', 'add', file_path])
            if exit_code != 0:
                errors.append(f"Failed to stage {file_path}: {stderr_stage}")
                continue
            
            files_staged += 1
            self.logger.debug(f"Staged file: {file_path}")
        
        self.logger.info(f"Staged {files_staged} files, skipped {files_skipped} files")
        return True, files_staged, files_skipped, errors

    def commit_changes(self, dispatch_code: str, dispatch_title: str, target_repo: str, target_branch: str, target_mode: str, files_staged: int, files_skipped: int) -> Tuple[bool, Optional[str], List[str]]:
        """Commit staged files with routing information."""
        self.logger.info("Committing changes...")
        errors = []
        
        # Check if there are staged changes
        exit_code, stdout, stderr = self.run_command(['git', 'diff', '--cached', '--name-only'])
        if exit_code != 0:
            errors.append(f"Failed to check staged files: {stderr}")
            return False, None, errors
        
        if not stdout.strip():
            self.logger.info("No staged changes to commit")
            return True, None, errors
        
        # Create commit message with routing info
        commit_msg = f"chore(hygiene): {dispatch_code} auto-commit after checks green\n- Target: {target_repo}#{target_branch} ({target_mode})\n- Files committed: {files_staged}, Skipped: {files_skipped}"
        
        # Commit changes
        exit_code, stdout, stderr = self.run_command(['git', 'commit', '-m', commit_msg])
        if exit_code != 0:
            errors.append(f"Failed to commit: {stderr}")
            return False, None, errors
        
        # Get commit SHA
        exit_code, stdout, stderr = self.run_command(['git', 'rev-parse', 'HEAD'])
        if exit_code != 0:
            errors.append(f"Failed to get commit SHA: {stderr}")
            return False, None, errors
        
        commit_sha = stdout.strip()
        self.logger.info(f"Changes committed with SHA: {commit_sha}")
        return True, commit_sha, errors
    
    def create_pr(self, dispatch_code: str, target_repo: str, target_branch: str) -> Tuple[bool, Optional[str], List[str]]:
        """Create a pull request for the changes."""
        self.logger.info(f"Creating PR for {target_repo}#{target_branch}...")
        errors = []
        
        # Check if GitHub CLI is available
        exit_code, stdout, stderr = self.run_command(['gh', '--version'])
        if exit_code != 0:
            errors.append("GitHub CLI not available, cannot create PR")
            return False, None, errors
        
        # Create feature branch name
        safe_slug = dispatch_code.lower().replace('_', '-').replace('dispatch-', '')
        branch_name = f"hygiene/{safe_slug}-{datetime.now().strftime('%Y%m%d')}"
        
        # Create and push feature branch
        exit_code, stdout, stderr = self.run_command(['git', 'checkout', '-b', branch_name])
        if exit_code != 0:
            errors.append(f"Failed to create branch: {stderr}")
            return False, None, errors
        
        exit_code, stdout, stderr = self.run_command(['git', 'push', '-u', 'origin', branch_name])
        if exit_code != 0:
            errors.append(f"Failed to push branch: {stderr}")
            return False, None, errors
        
        # Create PR
        pr_title = f"hygiene/{dispatch_code}-{datetime.now().strftime('%Y%m%d')}"
        
        exit_code, stdout, stderr = self.run_command([
            'gh', 'pr', 'create',
            '--base', target_branch,
            '--head', branch_name,
            '--title', pr_title,
            '--body', pr_body,
            '--label', 'hygiene,ops'
        ])
        
        if exit_code != 0:
            errors.append(f"Failed to create PR: {stderr}")
            return False, None, errors
        
        pr_url = stdout.strip()
        self.logger.info(f"PR created: {pr_url}")
        return True, pr_url, errors

    def push_to_remote(self, target_repo: str, target_branch: str, target_mode: str) -> Tuple[bool, Optional[str], List[str]]:
        """Push changes to remote or create PR based on mode."""
        if target_mode == "pr":
            return self.create_pr("DISPATCH", target_repo, target_branch)
        else:
            # Direct push mode
            self.logger.info(f"Pushing directly to {target_repo}#{target_branch}...")
            errors = []
            
            exit_code, stdout, stderr = self.run_command(['git', 'push', 'origin', target_branch])
            if exit_code != 0:
                errors.append(f"Failed to push to remote: {stderr}")
                return False, None, errors
            
            self.logger.info(f"Successfully pushed to {target_repo}#{target_branch}")
            return True, None, errors
    
    def sync_with_remote(self) -> Tuple[bool, List[str]]:
        """Ensure local repo matches remote main."""
        self.logger.info("Syncing with remote main...")
        errors = []
        
        # Fetch latest changes
        exit_code, stdout, stderr = self.run_command(['git', 'fetch', 'origin', 'main'])
        if exit_code != 0:
            errors.append(f"Failed to fetch main: {stderr}")
            return False, errors
        
        # Check if local is behind remote
        exit_code, stdout, stderr = self.run_command(['git', 'rev-list', '--count', 'HEAD..origin/main'])
        if exit_code != 0:
            errors.append(f"Failed to check commit count: {stderr}")
            return False, errors
        
        behind_count = int(stdout.strip())
        if behind_count > 0:
            # Pull latest changes
            exit_code, stdout, stderr = self.run_command(['git', 'pull', 'origin', 'main'])
            if exit_code != 0:
                errors.append(f"Failed to pull latest changes: {stderr}")
                return False, errors
        
        self.logger.info("Local repo synced with remote main")
        return True, errors
    
    def run_dry_run_preview(self, dispatch_code: str, dispatch_title: str) -> Tuple[bool, str, List[str]]:
        """Run dry-run preview showing what would be committed."""
        self.logger.info("Running dry-run preview...")
        errors = []
        
        # Determine target route
        target_repo, target_branch, target_mode = self._determine_target_route(dispatch_code, dispatch_title)
        
        # Safety check - never push to ioa-core
        if "ioa-core" in target_repo and "ioa-core-public" not in target_repo:
            errors.append("SAFETY: Cannot push to ioa-core public repo")
            return False, "", errors
        
        # Stage files with ignore patterns
        passed, files_staged, files_skipped, stage_errors = self.stage_files_with_ignore()
        if not passed:
            errors.extend(stage_errors)
            return False, "", errors
        
        # Get staged files list
        exit_code, stdout, stderr = self.run_command(['git', 'diff', '--cached', '--name-only'])
        if exit_code != 0:
            errors.append(f"Failed to get staged files: {stderr}")
            return False, "", errors
        
        staged_files = [f.strip() for f in stdout.split('\n') if f.strip()]
        
        # Create preview summary
        preview = f"""
DRY-RUN PREVIEW
===============
Target: {target_repo}#{target_branch} ({target_mode})
Files staged: {files_staged}
Files skipped: {files_skipped}
Staged files:
{chr(10).join(f'  - {f}' for f in staged_files[:20])}
{'  ... and more' if len(staged_files) > 20 else ''}
"""
        
        return True, preview, errors

    def run_hygiene_checks(self, dispatch_code: str, dispatch_title: str, dry_run_only: bool = False) -> HygieneResult:
        """Run complete hygiene check workflow with routing and safety guards."""
        self.logger.info(f"Starting hygiene checks for {dispatch_code}")
        errors = []
        warnings = []
        
        # Determine target route
        target_repo, target_branch, target_mode = self._determine_target_route(dispatch_code, dispatch_title)
        
        # Safety check - never push to ioa-core
        if "ioa-core" in target_repo and "ioa-core-public" not in target_repo:
            errors.append("SAFETY: Cannot push to ioa-core public repo")
            return HygieneResult(passed=False, errors=errors, warnings=warnings)
        
        # Step 1: Dry-run preview
        passed, preview, preview_errors = self.run_dry_run_preview(dispatch_code, dispatch_title)
        if not passed:
            errors.extend(preview_errors)
            return HygieneResult(passed=False, errors=errors, warnings=warnings)
        
        print(preview)
        
        if dry_run_only:
            return HygieneResult(
                passed=True,
                errors=errors,
                warnings=warnings,
                target_repo=target_repo,
                target_branch=target_branch,
                target_mode=target_mode
            )
        
        # Step 2: Stage files with ignore patterns
        passed, files_staged, files_skipped, stage_errors = self.stage_files_with_ignore()
        if not passed:
            errors.extend(stage_errors)
            return HygieneResult(passed=False, errors=errors, warnings=warnings)
        
        # Step 3: Secret scan
        passed, secret_errors = self.check_secret_scan()
        if not passed:
            errors.extend(secret_errors)
            return HygieneResult(passed=False, errors=errors, warnings=warnings)
        
        # Step 4: Pre-commit hooks
        passed, hook_errors = self.check_pre_commit_hooks()
        if not passed:
            errors.extend(hook_errors)
        
        # Step 5: CI dry-run
        passed, ci_errors = self.check_ci_dry_run()
        if not passed:
            errors.extend(ci_errors)
        
        # Step 6: Merge conflict check
        passed, merge_errors = self.check_merge_conflicts()
        if not passed:
            errors.extend(merge_errors)
        
        # If hygiene fails, abort
        if errors:
            self.logger.error("Hygiene checks failed, aborting push")
            return HygieneResult(passed=False, errors=errors, warnings=warnings)
        
        # Step 7: Commit changes
        passed, commit_sha, commit_errors = self.commit_changes(
            dispatch_code, dispatch_title, target_repo, target_branch, target_mode, 
            files_staged, files_skipped
        )
        if not passed:
            errors.extend(commit_errors)
            return HygieneResult(passed=False, errors=errors, warnings=warnings)
        
        # Step 8: Push to remote or create PR
        passed, pr_url, push_errors = self.push_to_remote(target_repo, target_branch, target_mode)
        if not passed:
            errors.extend(push_errors)
            return HygieneResult(
                passed=False, 
                errors=errors, 
                warnings=warnings,
                commit_sha=commit_sha,
                files_staged=files_staged,
                files_skipped=files_skipped,
                target_repo=target_repo,
                target_branch=target_branch,
                target_mode=target_mode
            )
        
        # Step 9: Sync with remote (if direct push)
        if target_mode != "pr":
            passed, sync_errors = self.sync_with_remote()
            if not passed:
                errors.extend(sync_errors)
                return HygieneResult(
                    passed=False, 
                    errors=errors, 
                    warnings=warnings,
                    commit_sha=commit_sha,
                    pr_url=pr_url,
                    files_staged=files_staged,
                    files_skipped=files_skipped,
                    target_repo=target_repo,
                    target_branch=target_branch,
                    target_mode=target_mode,
                    remote_sync=False
                )
        
        self.logger.info("✅ Dispatch complete and synced.")
        return HygieneResult(
            passed=True,
            errors=errors,
            warnings=warnings,
            commit_sha=commit_sha,
            pr_url=pr_url,
            files_staged=files_staged,
            files_skipped=files_skipped,
            target_repo=target_repo,
            target_branch=target_branch,
            target_mode=target_mode,
            remote_sync=(target_mode != "pr")
        )

def main():
    """Main entry point for GitHub hygiene script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub hygiene checks for dispatch completion')
    parser.add_argument('--dispatch-code', required=True, help='Dispatch code (e.g., DISPATCH-123)')
    parser.add_argument('--dispatch-title', required=True, help='Dispatch title')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true', help='Run dry-run preview only')
    
    args = parser.parse_args()
    
    hygiene = GitHubHygiene(verbose=args.verbose)
    result = hygiene.run_hygiene_checks(args.dispatch_code, args.dispatch_title, dry_run_only=args.dry_run)
    
    # Print summary
    print("\n" + "="*60)
    print("HYGIENE CHECK SUMMARY")
    print("="*60)
    print(f"Hygiene Check: {'PASS' if result.passed else 'FAIL'}")
    if result.target_repo:
        print(f"Target: {result.target_repo}#{result.target_branch} ({result.target_mode})")
    if result.files_staged > 0:
        print(f"Files staged: {result.files_staged}, skipped: {result.files_skipped}")
    if result.commit_sha:
        print(f"Commit SHA: {result.commit_sha}")
    if result.pr_url:
        print(f"PR URL: {result.pr_url}")
    print(f"Remote Sync: {'PASS' if result.remote_sync else 'FAIL'}")
    
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for i, error in enumerate(result.errors[:10], 1):  # Top 10 errors
            print(f"  {i}. {error}")
        if len(result.errors) > 10:
            print(f"  ... and {len(result.errors) - 10} more errors")
    
    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for i, warning in enumerate(result.warnings, 1):
            print(f"  {i}. {warning}")
    
    print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if result.passed else 1)

if __name__ == '__main__':
    main()
