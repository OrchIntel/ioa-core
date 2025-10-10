# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Test Ollama turbo mode example."""

import json
import subprocess


def test_ollama_turbo_mode():
    """Test that Ollama turbo demo returns performance metrics."""
    # Run turbo mode
    result_turbo = subprocess.run(
        ["python", "examples/50_ollama/turbo_mode_demo.py", "turbo_cloud"],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Parse JSON output
    data_turbo = json.loads(result_turbo.stdout)
    
    # Verify expected fields
    assert "mode" in data_turbo
    assert "p50_ms" in data_turbo
    assert "expected_improvement" in data_turbo
    assert "optimizations" in data_turbo
    
    # Verify mode
    assert data_turbo["mode"] == "turbo_cloud"
    
    # Verify p50_ms is an integer
    assert isinstance(data_turbo["p50_ms"], int)
    assert data_turbo["p50_ms"] > 0
    
    # Run baseline mode
    result_baseline = subprocess.run(
        ["python", "examples/50_ollama/turbo_mode_demo.py", "local_preset"],
        capture_output=True,
        text=True,
        check=True
    )
    
    data_baseline = json.loads(result_baseline.stdout)
    
    # Verify baseline has metrics
    assert isinstance(data_baseline["p50_ms"], int)
    assert data_baseline["mode"] == "local_preset"
    
    # Note: We don't assert turbo is faster in CI (hardware dependent)
    # Just verify both modes return valid data


if __name__ == "__main__":
    test_ollama_turbo_mode()
    print("✅ Ollama turbo test passed")

