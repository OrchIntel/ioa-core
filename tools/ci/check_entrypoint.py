""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

"""
Entrypoint Guard

Verifies that the venv/bin/ioa console script correctly imports from ioa_core.cli.
This ensures the entrypoint is properly configured after environment setup.

Usage:
    python tools/ci/check_entrypoint.py [--venv-path ./venv]
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional


def check_entrypoint(venv_path: Path) -> bool:
    """
    Check if venv/bin/ioa correctly imports from ioa_core.cli.
    
    Args:
        venv_path: Path to virtual environment
        
    Returns:
        True if entrypoint is working correctly, False otherwise
    """
    ioa_script = venv_path / "bin" / "ioa"
    
    if not ioa_script.exists():
        print(f"❌ Entrypoint script not found: {ioa_script}")
        return False
    
    if not ioa_script.is_file():
        print(f"❌ Entrypoint path is not a file: {ioa_script}")
        return False
    
    # Check if script is executable
    if not ioa_script.stat().st_mode & 0o111:
        print(f"❌ Entrypoint script is not executable: {ioa_script}")
        return False
    
    # Test the entrypoint by running it with --help
    try:
        result = subprocess.run(
            [str(ioa_script), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        # Check if output contains expected IOA Core content
        if "IOA Core" in result.stdout and "ioa_core.cli" in str(ioa_script.read_text()):
            print(f"✅ Entrypoint working correctly: {ioa_script}")
            return True
        else:
            print(f"❌ Entrypoint output unexpected: {result.stdout[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Entrypoint timed out: {ioa_script}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Entrypoint failed with exit code {e.returncode}: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Entrypoint check failed: {e}")
        return False


def check_import_path(venv_path: Path) -> bool:
    """
    Check if the entrypoint script correctly references ioa_core.cli.
    
    Args:
        venv_path: Path to virtual environment
        
    Returns:
        True if import path is correct, False otherwise
    """
    ioa_script = venv_path / "bin" / "ioa"
    
    try:
        script_content = ioa_script.read_text()
        
        # Check for correct import path
        if "ioa_core.cli" in script_content:
            print(f"✅ Import path correct in entrypoint: ioa_core.cli")
            return True
        else:
            print(f"❌ Import path incorrect in entrypoint: {script_content[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Failed to read entrypoint script: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check that venv/bin/ioa entrypoint works correctly"
    )
    parser.add_argument(
        "--venv-path",
        default="./venv",
        help="Path to virtual environment (default: ./venv)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error code if any check fails"
    )
    
    args = parser.parse_args()
    
    venv_path = Path(args.venv_path).resolve()
    
    if not venv_path.exists():
        print(f"❌ Virtual environment not found: {venv_path}")
        if args.strict:
            sys.exit(1)
        else:
            sys.exit(0)
    
    print(f"🔍 Checking entrypoint in: {venv_path}")
    
    # Run checks
    checks_passed = 0
    total_checks = 2
    
    # Check 1: Import path
    if check_import_path(venv_path):
        checks_passed += 1
    
    # Check 2: Entrypoint execution
    if check_entrypoint(venv_path):
        checks_passed += 1
    
    print(f"\n📊 Entrypoint checks: {checks_passed}/{total_checks} passed")
    
    if checks_passed == total_checks:
        print("✅ All entrypoint checks passed")
        sys.exit(0)
    else:
        print("❌ Some entrypoint checks failed")
        if args.strict:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
