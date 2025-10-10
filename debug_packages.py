""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
Debug script to test packages import structure in CI environment.
"""

import os
import sys

def debug_packages():
    """Debug the packages import structure."""
    print("=== Packages Debug Info ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    print("\n=== Directory Structure ===")
    if os.path.exists("packages"):
        print("✅ packages/ directory exists")
        for item in os.listdir("packages"):
            item_path = os.path.join("packages", item)
            if os.path.isdir(item_path):
                print(f"  📁 {item}/")
                if os.path.exists(os.path.join(item_path, "__init__.py")):
                    print(f"    ✅ {item}/__init__.py exists")
                else:
                    print(f"    ❌ {item}/__init__.py missing")
            else:
                print(f"  📄 {item}")
    else:
        print("❌ packages/ directory missing")
    
    print("\n=== Import Tests ===")
    try:
        import packages
        print("✅ import packages successful")
        print(f"   packages.__file__: {getattr(packages, '__file__', 'N/A')}")
    except ImportError as e:
        print(f"❌ import packages failed: {e}")
    
    try:
        import packages.core
        print("✅ import packages.core successful")
    except ImportError as e:
        print(f"❌ import packages.core failed: {e}")
    
    # Enterprise package test - only run if explicitly enabled
    if os.getenv("IOA_TEST_ENTERPRISE") == "1":
        try:
            import packages.enterprise
            print("✅ import packages.enterprise successful")
        except ImportError as e:
            print(f"❌ import packages.enterprise failed: {e}")
    else:
        print("⏭️  packages.enterprise test skipped (IOA_TEST_ENTERPRISE != 1)")
    
    try:
        import packages.saas
        print("✅ import packages.saas successful")
    except ImportError as e:
        print(f"❌ import packages.saas failed: {e}")

if __name__ == "__main__":
    debug_packages()
