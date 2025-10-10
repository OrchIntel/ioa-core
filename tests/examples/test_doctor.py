# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Test doctor check example."""

import json
import subprocess


def test_doctor_check():
    """Test that doctor check runs and returns health status."""
    result = subprocess.run(
        ["python", "examples/30_doctor/doctor_check.py"],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Parse JSON output
    data = json.loads(result.stdout)
    
    # Verify expected fields
    assert "python_version_ok" in data
    assert "env_provider_keys" in data
    assert "local_cache_writeable" in data
    assert "overall_health" in data
    
    # Python version should be OK (we're running this test)
    assert data["python_version_ok"] is True
    
    # Overall health should be healthy or issues_detected
    assert data["overall_health"] in ["healthy", "issues_detected"]


if __name__ == "__main__":
    test_doctor_check()
    print("✅ Doctor test passed")

