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
Environment Snapshot Tool

Generates .ioa/env.lock.json with complete environment specification for
reproducible builds across Cursor and local environments.

Usage:
    python tools/dev/env_snapshot.py [--output .ioa/env.lock.json]
"""

import json
import sys
import subprocess
import platform
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import argparse


def get_python_version() -> str:
    """Get Python version string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_platform_info() -> str:
    """Get platform information."""
    return f"{platform.system()}-{platform.machine()}"


def get_pip_freeze() -> List[str]:
    """Get pip freeze output as list of package specifications."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to get pip freeze: {e}", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("Warning: pip not found", file=sys.stderr)
        return []


def get_git_sha() -> Optional[str]:
    """Get current git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_ioa_core_version() -> str:
    """Get IOA Core version from package."""
    try:
        # Try to import from installed package
        import ioa_core
        return getattr(ioa_core, "__version__", "unknown")
    except ImportError:
        # Fallback to pyproject.toml
        try:
            import tomllib
            with open("pyproject.toml", "rb") as f:
                data = tomllib.load(f)
                return data.get("project", {}).get("version", "unknown")
        except Exception:
            return "unknown"


def get_entrypoint_target() -> str:
    """Get the entrypoint target for the ioa command."""
    return "ioa_core.cli:main"


def get_optional_sdks() -> List[str]:
    """Get list of optional SDKs that are installed."""
    optional_sdks = []
    
    # Check for common optional packages
    optional_packages = [
        "anthropic",
        "google-generativeai", 
        "openai",
        "pymongo",
        "redis",
        "sqlalchemy",
        "fastapi",
        "uvicorn"
    ]
    
    for package in optional_packages:
        try:
            __import__(package)
            optional_sdks.append(package)
        except ImportError:
            pass
    
    return optional_sdks


def create_env_lock() -> Dict[str, Any]:
    """Create environment lock dictionary."""
    return {
        "python_version": get_python_version(),
        "platform": get_platform_info(),
        "pip_freeze": get_pip_freeze(),
        "entrypoint_target": get_entrypoint_target(),
        "ioa_core_version": get_ioa_core_version(),
        "git_sha": get_git_sha(),
        "optional_sdks": get_optional_sdks(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "snapshot_version": "1.0"
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate environment snapshot for reproducible builds"
    )
    parser.add_argument(
        "--output",
        default=".ioa/env.lock.json",
        help="Output file path (default: .ioa/env.lock.json)"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print JSON output"
    )
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate environment lock
    env_lock = create_env_lock()
    
    # Write to file
    with open(output_path, "w") as f:
        if args.pretty:
            json.dump(env_lock, f, indent=2, sort_keys=True)
        else:
            json.dump(env_lock, f, separators=(",", ":"))
    
    print(f"Environment snapshot written to: {output_path}")
    print(f"Python: {env_lock['python_version']}")
    print(f"Platform: {env_lock['platform']}")
    print(f"IOA Core: {env_lock['ioa_core_version']}")
    print(f"Packages: {len(env_lock['pip_freeze'])}")
    print(f"Optional SDKs: {', '.join(env_lock['optional_sdks']) or 'none'}")


if __name__ == "__main__":
    main()
