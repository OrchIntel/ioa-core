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


@pytest.mark.step
def test_step_1k():
    """Step-up test with 1000 records for MemoryFabric scaling."""
    n = int(os.getenv("IOA_TEST_RECORDS", "1000"))
    mf = MemoryFabric(backend="sqlite")

    # Store all records and collect last record ID
    last_record_id = None
    for i in range(n):
        record_id = mf.store(
            content="x",
            metadata={"id": f"k{i}", "data": "x"}
        )
        last_record_id = record_id  # Keep updating to get the last one

    # Verify retrieval of last record
    record = mf.retrieve(last_record_id)
    assert record is not None
    assert record.content == "x"
