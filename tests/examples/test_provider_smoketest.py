# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Test provider smoketest example."""

import json
import subprocess
import os


def test_provider_smoketest_mock():
    """Test that provider smoketest works with mock provider."""
    env = os.environ.copy()
    env["IOA_PROVIDER"] = "mock"
    
    result = subprocess.run(
        ["python", "examples/40_providers/provider_smoketest.py"],
        capture_output=True,
        text=True,
        check=True,
        env=env
    )
    
    # Parse JSON output
    data = json.loads(result.stdout)
    
    # Verify expected fields
    assert "provider" in data
    assert "status" in data
    assert "mode" in data
    
    # Verify values for mock provider
    assert data["provider"] == "mock"
    assert data["status"] == "ok"
    assert data["mode"] == "offline-mock"


if __name__ == "__main__":
    test_provider_smoketest_mock()
    print("✅ Provider smoketest test passed")

