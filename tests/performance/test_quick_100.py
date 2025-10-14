"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import pytest
import os
from pathlib import Path

# Import IOA Core modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ioa_core.memory_fabric.fabric import MemoryFabric


@pytest.mark.quick
def test_quick_100():
    """Quick test with 100 records for rapid MemoryFabric validation."""
    n = int(os.getenv("IOA_TEST_RECORDS", "100"))
    mf = MemoryFabric(backend="sqlite")

    # Store all records and collect first record ID
    first_record_id = None
    for i in range(n):
        record_id = mf.store(
            content="x",
            metadata={"id": f"q{i}", "data": "x"}
        )
        if i == 0:
            first_record_id = record_id

    # Verify retrieval of first record
    record = mf.retrieve(first_record_id)
    assert record is not None
    assert record.content == "x"
