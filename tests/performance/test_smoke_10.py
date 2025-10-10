""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import os
import pytest
import time
from pathlib import Path

# Import IOA Core modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ioa_core.memory_fabric.fabric import MemoryFabric


@pytest.mark.smoke
def test_smoke_10():
    """Smoke test with 10 records for basic MemoryFabric functionality."""
    n = int(os.getenv("IOA_TEST_RECORDS", "10"))
    mf = MemoryFabric(backend="sqlite")  # Use sqlite for consistency
    total = n

    # Store records and collect record IDs
    record_ids = []
    for i in range(n):
        record_id = mf.store(
            content=f"payload {i}",
            metadata={"id": f"doc{i}", "phase": "store", "index": i}
        )
        record_ids.append(record_id)
        if i % max(1, n//10) == 0:
            print(f'progress={{"phase":"store","done":{i},"total":{total}}}', flush=True)

    # Retrieve phase with progress
    got = 0
    for i, record_id in enumerate(record_ids):
        record = mf.retrieve(record_id)
        if record and record.content == f"payload {i}":
            got += 1
    print(f'progress={{"phase":"retrieve","done":{got},"total":{total}}}', flush=True)

    assert got == n
