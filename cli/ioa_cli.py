""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3

"""
CLI Entry Point Script for IOA Core

This script handles the path setup and imports for the CLI,
ensuring it works from any installation location.
"""

import sys
import os
from pathlib import Path

def setup_paths():
    """Setup Python paths to find IOA modules."""
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    
    # Add src directory to Python path
    src_path = script_dir / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Add project root to Python path
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

def main():
    """Main entry point."""
    # Setup paths first
    setup_paths()
    
    try:
        # Import and run the CLI
        from src.cli.main import app
        app()
    except ImportError as e:
        print(f"❌ Error importing CLI modules: {e}")
        print("Please ensure you're running from the project root directory.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ CLI error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
