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
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


class WorkflowFixer:
    """Apply systematic fixes to GitHub Actions workflows."""
    
    def __init__(self, workflows_dir: str = ".github/workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.fixes_applied = []
        
    def fix_workflow(self, workflow_path: Path) -> Dict[str, Any]:
        """Apply all fixes to a single workflow file."""
        fixes = {
            "file": str(workflow_path),
            "changes": [],
            "errors": []
        }
        
        try:
            with open(workflow_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Apply fixes
            content = self._add_concurrency_control(content, fixes)
            content = self._add_permissions(content, fixes)
            content = self._normalize_runners(content, fixes)
            content = self._fix_python_setup(content, fixes)
            content = self._add_artifact_directories(content, fixes)
            content = self._fix_artifact_uploads(content, fixes)
            content = self._add_env_defaults(content, fixes)
            content = self._add_fork_guards(content, fixes)
            
            # Only write if changes were made
            if content != original_content:
                with open(workflow_path, 'w') as f:
                    f.write(content)
                fixes["changes"].append("File updated successfully")
            else:
                fixes["changes"].append("No changes needed")
                
        except Exception as e:
            fixes["errors"].append(f"Error processing file: {e}")
        
        return fixes
    
    def _add_concurrency_control(self, content: str, fixes: Dict) -> str:
        """Add concurrency control if missing."""
        if "concurrency:" not in content:
            # Find the jobs section and add concurrency before it
            jobs_match = re.search(r'^jobs:', content, re.MULTILINE)
            if jobs_match:
                concurrency_block = """concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

"""
                content = content[:jobs_match.start()] + concurrency_block + content[jobs_match.start():]
                fixes["changes"].append("Added concurrency control")
        return content
    
    def _add_permissions(self, content: str, fixes: Dict) -> str:
        """Add minimal permissions if missing."""
        if "permissions:" not in content:
            # Add after name and before on/trigger
            name_match = re.search(r'^name:.*$', content, re.MULTILINE)
            if name_match:
                permissions_block = """
permissions:
  contents: read
  pull-requests: write
  actions: read

"""
                # Find the next non-empty line after name
                lines = content.split('\n')
                insert_line = name_match.start()
                for i, line in enumerate(lines[name_match.start():], name_match.start()):
                    if line.strip() and not line.startswith('name:'):
                        insert_line = i
                        break
                
                lines.insert(insert_line, permissions_block)
                content = '\n'.join(lines)
                fixes["changes"].append("Added minimal permissions")
        return content
    
    def _normalize_runners(self, content: str, fixes: Dict) -> str:
        """Normalize runners to ubuntu-latest unless macOS is explicitly needed."""
        # Only change if it's clearly a macOS runner that can be changed
        macos_patterns = [
            (r'runs-on:\s*macos-latest', 'runs-on: ubuntu-latest'),
            (r'runs-on:\s*macos-12', 'runs-on: ubuntu-latest'),
            (r'runs-on:\s*macos-13', 'runs-on: ubuntu-latest'),
        ]
        
        for pattern, replacement in macos_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                fixes["changes"].append("Normalized runner to ubuntu-latest")
                break
        
        return content
    
    def _fix_python_setup(self, content: str, fixes: Dict) -> str:
        """Fix Python setup to use actions/setup-python@v5 with 3.11."""
        # Update existing setup-python actions
        content = re.sub(
            r'uses:\s*actions/setup-python@v[0-9]+',
            'uses: actions/setup-python@v5',
            content
        )
        
        # Update Python version to 3.11
        content = re.sub(
            content
        )
        
        # Add Python setup if missing in jobs that need it
        if 'actions/setup-python' not in content and ('pip install' in content or 'python -m' in content):
            # Find jobs that need Python setup
            job_pattern = r'(\s+)([a-zA-Z0-9_-]+):\s*\n(\s+)runs-on:.*\n((?:\s+.*\n)*?)(\s+steps:)'
            
            def add_python_setup(match):
                indent = match.group(1)
                job_name = match.group(2)
                job_content = match.group(4)
                steps_line = match.group(5)
                
                # Check if this job needs Python
                if 'pip install' in job_content or 'python -m' in job_content:
                    python_setup = f"""{indent}  - name: Set up Python
{indent}    uses: actions/setup-python@v5
{indent}    with:
{indent}      cache: 'pip'

"""
                    return match.group(0).replace(steps_line, python_setup + steps_line)
                return match.group(0)
            
            content = re.sub(job_pattern, add_python_setup, content, flags=re.MULTILINE)
            fixes["changes"].append("Updated Python setup to v5 with 3.11")
        
        return content
    
    def _add_artifact_directories(self, content: str, fixes: Dict) -> str:
        """Add artifact directory creation before upload steps."""
        # Find upload-artifact steps and add directory creation before them
        upload_pattern = r'(\s+)(- uses: actions/upload-artifact@v[0-9]+)'
        
        def add_directory_creation(match):
            indent = match.group(1)
            upload_line = match.group(2)
            
            # Check if directory creation already exists nearby
            lines_before = content[:match.start()].split('\n')
            has_mkdir = any('mkdir -p artifacts' in line for line in lines_before[-10:])
            
            if not has_mkdir:
                dir_creation = f"""{indent}- name: Ensure artifacts directories exist
{indent}  run: mkdir -p artifacts/lens || true

{indent}{upload_line}"""
                return dir_creation
            return match.group(0)
        
        new_content = re.sub(upload_pattern, add_directory_creation, content)
        if new_content != content:
            fixes["changes"].append("Added artifact directory creation")
            content = new_content
        
        return content
    
    def _fix_artifact_uploads(self, content: str, fixes: Dict) -> str:
        """Fix artifact uploads to use if-no-files-found: warn."""
        # Update upload-artifact actions to include if-no-files-found: warn
        upload_pattern = r'(- uses: actions/upload-artifact@v[0-9]+(?:\s+with:)?(?:\s+.*\n)*?)(\s+name:.*\n)(\s+path:.*\n)'
        
        def add_if_no_files_found(match):
            upload_line = match.group(1)
            name_line = match.group(2)
            path_line = match.group(3)
            
            # Check if if-no-files-found is already present
            if 'if-no-files-found:' not in match.group(0):
                return f"""{upload_line}
{name_line}{path_line}        if-no-files-found: warn"""
            return match.group(0)
        
        new_content = re.sub(upload_pattern, add_if_no_files_found, content, flags=re.MULTILINE)
        if new_content != content:
            fixes["changes"].append("Added if-no-files-found: warn to artifact uploads")
            content = new_content
        
        return content
    
    def _add_env_defaults(self, content: str, fixes: Dict) -> str:
        """Add environment defaults if not present."""
        if 'CI_GATES_MODE:' not in content and 'env:' not in content:
            # Add env section after name
            name_match = re.search(r'^name:.*$', content, re.MULTILINE)
            if name_match:
                env_block = """
env:
  CI_GATES_MODE: monitor
  PYTHONWARNINGS: error

"""
                lines = content.split('\n')
                insert_line = name_match.start() + 1
                lines.insert(insert_line, env_block)
                content = '\n'.join(lines)
                fixes["changes"].append("Added environment defaults")
        return content
    
    def _add_fork_guards(self, content: str, fixes: Dict) -> str:
        """Add fork guards for secret-requiring steps."""
        # This is a complex pattern, so we'll be conservative
        # Only add guards to steps that clearly need secrets
        secret_steps = [
            'GITHUB_TOKEN',
            'secrets.GITHUB_TOKEN',
            'secrets.',
        ]
        
        for secret in secret_steps:
            if secret in content and 'github.event.pull_request.head.repo.fork' not in content:
                # Add a comment about fork safety
                content = f"# Fork safety: Steps requiring secrets should be guarded with:\n# if: ${{{{ github.event.pull_request.head.repo.fork == false }}}}\n{content}"
                fixes["changes"].append("Added fork safety comment")
                break
        
        return content
    
    def fix_all_workflows(self) -> List[Dict[str, Any]]:
        """Fix all workflow files in the directory."""
        results = []
        
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        
        for workflow_file in workflow_files:
            print(f"Fixing {workflow_file.name}...")
            result = self.fix_workflow(workflow_file)
            results.append(result)
            
            if result["changes"]:
                print(f"  Changes: {', '.join(result['changes'])}")
            if result["errors"]:
                print(f"  Errors: {', '.join(result['errors'])}")
        
        return results


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix GitHub Actions workflows")
    parser.add_argument("--workflows-dir", default=".github/workflows", help="Workflows directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    
    args = parser.parse_args()
    
    fixer = WorkflowFixer(args.workflows_dir)
    
    if args.dry_run:
        print("DRY RUN - No files will be modified")
        # TODO: Implement dry run mode
        return
    
    results = fixer.fix_all_workflows()
    
    # Summary
    total_files = len(results)
    files_changed = len([r for r in results if r["changes"] and "File updated successfully" in r["changes"]])
    total_changes = sum(len(r["changes"]) for r in results)
    total_errors = sum(len(r["errors"]) for r in results)
    
    print(f"  Files processed: {total_files}")
    print(f"  Files changed: {files_changed}")
    print(f"  Total changes: {total_changes}")
    print(f"  Total errors: {total_errors}")


if __name__ == "__main__":
    main()
