# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Test workflow example."""

import json
import subprocess


def test_workflow_runs():
    """Test that workflow runner executes and returns JSON."""
    result = subprocess.run(
        ["python", "examples/10_workflows/run_workflow.py"],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Parse JSON output
    data = json.loads(result.stdout)
    
    # Verify expected fields
    assert "task" in data
    assert "policy" in data
    assert "result" in data
    assert "evidence_id" in data
    assert "audit_chain_verified" in data
    
    # Verify values
    assert data["result"] == "OK"
    assert data["evidence_id"] == "ev-0001"
    assert data["audit_chain_verified"] is True


if __name__ == "__main__":
    test_workflow_runs()
    print("✅ Workflow test passed")

