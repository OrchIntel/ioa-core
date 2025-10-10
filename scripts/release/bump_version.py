""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

class VersionBumper:
    """Handles version bumping for IOA Core releases."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent.parent.parent
        
    def get_current_version(self) -> str:
        """Get current version from pyproject.toml."""
        pyproject_path = self.project_root / "pyproject.toml"
        
        if not pyproject_path.exists():
            raise FileNotFoundError("pyproject.toml not found")
            
        content = pyproject_path.read_text()
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        
        if not version_match:
            raise ValueError("Version not found in pyproject.toml")
            
        return version_match.group(1)
    
        """Bump version according to SemVer rules."""
        major, minor, patch = map(int, current_version.split('.'))
        
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")
            
        return f"{major}.{minor}.{patch}"
    
        """Update version in pyproject.toml."""
        pyproject_path = self.project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        
        # Update version
        content = re.sub(
            r'version\s*=\s*["\'][^"\']+["\']',
            f'version = "{new_version}"',
            content
        )
        
        if not self.dry_run:
            pyproject_path.write_text(content)
            print(f"Updated pyproject.toml: version = {new_version}")
        else:
            print(f"[DRY RUN] Would update pyproject.toml: version = {new_version}")
    
        """Update version in package __init__.py files."""
        package_files = [
            "ioa/__init__.py",
            "ioa/core/__init__.py",
            "packages/core/__init__.py",
            "packages/enterprise/__init__.py",
            "packages/saas/__init__.py"
        ]
        
        for package_file in package_files:
            file_path = self.project_root / package_file
            if file_path.exists():
                content = file_path.read_text()
                
                # Update version
                content = re.sub(
                    r'__version__\s*=\s*["\'][^"\']+["\']',
                    f'__version__ = "{new_version}"',
                    content
                )
                
                if not self.dry_run:
                    file_path.write_text(content)
                    print(f"Updated {package_file}: __version__ = {new_version}")
                else:
                    print(f"[DRY RUN] Would update {package_file}: __version__ = {new_version}")
    
        """Update CHANGELOG.md with new version."""
        changelog_path = self.project_root / "CHANGELOG.md"
        
        if not changelog_path.exists():
            print("Warning: CHANGELOG.md not found, skipping changelog update")
            return
            
        content = changelog_path.read_text()
        
        # Find unreleased section
        unreleased_pattern = r'## \[Unreleased\].*?(?=## \[v\d+\.\d+\.\d+\]|$)'
        unreleased_match = re.search(unreleased_pattern, content, re.DOTALL)
        
        if unreleased_match:
            unreleased_content = unreleased_match.group(0)
            
            # Create new version section
            today = datetime.now().strftime("%Y-%m-%d")
            new_version_section = f"""## [v{new_version}] - {today}

### {bump_type.title()} Changes

{unreleased_content.replace('## [Unreleased]', '')}

"""
            
            # Replace unreleased with new version
            content = content.replace(unreleased_content, new_version_section)
            
            # Add unreleased section back
            content = f"""## [Unreleased]

### Added
- New features and enhancements

### Changed
- Updates and modifications

### Fixed
- Bug fixes and improvements

### Security
- Security-related changes

{content}"""
            
            if not self.dry_run:
                changelog_path.write_text(content)
                print(f"Updated CHANGELOG.md: Added v{new_version} section")
            else:
                print(f"[DRY RUN] Would update CHANGELOG.md: Add v{new_version} section")
        else:
            print("Warning: Unreleased section not found in CHANGELOG.md")
    
        """Create git tag for new version."""
        if self.dry_run:
            print(f"[DRY RUN] Would create git tag: v{new_version}")
            return
            
        import subprocess
        
        try:
            # Add all changes
            subprocess.run(["git", "add", "."], check=True)
            
            # Commit version bump
            commit_msg = f"Bump version to {new_version}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            
            # Create tag
            subprocess.run(["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"], check=True)
            
            print(f"Created git tag: v{new_version}")
            print("To push changes and tag:")
            print(f"  git push origin main")
            print(f"  git push origin v{new_version}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error creating git tag: {e}")
            print("Please commit changes manually and create tag")
    
    def run(self, bump_type: str) -> None:
        """Run the version bump process."""
        try:
            current_version = self.get_current_version()
            
            new_version = self.bump_version(current_version, bump_type)
            
            if self.dry_run:
                print("\n=== DRY RUN MODE ===")
            
            # Update files
            self.update_pyproject_toml(new_version)
            self.update_package_versions(new_version)
            self.update_changelog(new_version, bump_type)
            
            if not self.dry_run:
                self.create_git_tag(new_version)
            
            print(f"\nVersion bump to {new_version} completed successfully!")
            
        except Exception as e:
            print(f"Error during version bump: {e}")
            sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Bump IOA Core version")
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    
    args = parser.parse_args()
    
    bumper = VersionBumper(dry_run=args.dry_run)
    bumper.run(args.bump_type)

if __name__ == "__main__":
    main()
