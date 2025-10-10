# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Test roundtable quorum example."""

import json
import subprocess


def test_roundtable_quorum():
    """Test that roundtable executes and calculates quorum."""
    result = subprocess.run(
        ["python", "examples/20_roundtable/roundtable_quorum.py", 
         "Test task that is ok"],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Parse JSON output
    data = json.loads(result.stdout)
    
    # Verify expected fields
    assert "votes" in data
    assert "quorum_approved" in data
    assert "evidence_id" in data
    assert "approve_count" in data
    
    # Verify vote structure
    assert isinstance(data["votes"], list)
    assert len(data["votes"]) == 3
    
    # Verify each vote has required fields
    for vote in data["votes"]:
        assert "model" in vote
        assert "vote" in vote
    
    # Since task contains "ok", quorum should be approved
    assert data["quorum_approved"] is True
    assert data["approve_count"] >= 2


if __name__ == "__main__":
    test_roundtable_quorum()
    print("✅ Roundtable test passed")

