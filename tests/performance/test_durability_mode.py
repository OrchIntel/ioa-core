""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import pytest
import os
from pathlib import Path

# Import IOA Core modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ioa_core.memory_fabric.fabric import MemoryFabric


@pytest.mark.durability
def test_durability_mode():
    """Test durability mode with checksum verification."""

    mf = MemoryFabric(backend="sqlite")

    # Enable durability mode
    mf.enable_durability(True)

    # Store test records
    test_records = []
    for i in range(100):
        record_id = mf.store(
            content=f"durability_test_record_{i}_content",
            metadata={"test_id": f"durability_{i}", "index": i}
        )
        test_records.append((record_id, f"durability_test_record_{i}_content"))

    # Verify durability immediately after storage
    assert mf.verify_durability() == True, "Initial durability verification failed"

    # Verify all records can be retrieved and content matches
    verified_count = 0
    for record_id, expected_content in test_records:
        record = mf.retrieve(record_id)
        assert record is not None, f"Failed to retrieve record {record_id}"
        assert record.content == expected_content, f"Content mismatch for record {record_id}"
        verified_count += 1

    assert verified_count == 100, f"Expected 100 verified records, got {verified_count}"

    # Test durability verification after retrievals
    assert mf.verify_durability() == True, "Durability verification failed after retrievals"

    # Disable durability and verify it no longer works
    mf.enable_durability(False)
    assert mf.verify_durability() == False, "Durability verification should fail when disabled"

    print("✅ Durability mode test passed")
    print(f"Verified {verified_count} records with 100% integrity")
