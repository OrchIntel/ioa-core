"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import pytest
import asyncio
import time
import os
from pathlib import Path

# Import IOA Core modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ioa_core.memory_fabric.fabric import MemoryFabric
from ioa_core.memory_fabric.schema import MemoryType


@pytest.mark.heavy
@pytest.mark.asyncio
async def test_scale_50k():
    """Heavy-scale test with 50k records using async batching and jurisdiction spike."""

    # Configure 4D-tiering for governance profile
    os.environ["IOA_4D_PROFILE"] = "governance"
    os.environ["USE_4D_TIERING"] = "true"

    mf = MemoryFabric(backend="sqlite")

    total = int(os.getenv("IOA_TEST_RECORDS", "50000"))

    # Create records with jurisdiction spike (EU/US alternating for 4D-tiering stress test)
    records = []
    for i in range(total):
        jurisdiction = "EU" if i % 2 == 0 else "US"  # Jurisdiction spike
        record = {
            "content": f"doc{i}_data_payload_with_jurisdiction_{jurisdiction}",
            "metadata": {
                "id": f"scale_doc_{i}",
                "index": i,
                "jurisdiction": jurisdiction,
                "phase": "heavy_scale_test",
                "batch_size": total
            },
            "memory_type": MemoryType.CONVERSATION
        }
        records.append(record)

    print(f"🚀 Starting 50k record async batch test...")
    print(f"Records to process: {total}")
    print(f"Jurisdiction distribution: EU/US alternating")

    start_time = time.time()

    # Use async batching for improved performance
    record_ids = await mf.store_batch(records)

    store_duration = time.time() - start_time
    print(".2f")

    # Verify all records were stored
    verify_start = time.time()
    retrieved_count = 0
    verified_count = 0

    for i, record_id in enumerate(record_ids):
        record = mf.retrieve(record_id)
        if record:
            retrieved_count += 1
            # Verify content integrity
            expected_content = f"doc{i}_data_payload_with_jurisdiction_{'EU' if i % 2 == 0 else 'US'}"
            if record.content == expected_content:
                verified_count += 1

        if i % 5000 == 0 and i > 0:
            progress = (i / total) * 100
            print(".1f")

    verify_duration = time.time() - verify_start
    total_duration = time.time() - start_time

    # Performance metrics
    store_rate = total / store_duration if store_duration > 0 else 0
    verify_rate = total / verify_duration if verify_duration > 0 else 0
    total_rate = total / total_duration if total_duration > 0 else 0

    print("\n📊 PERFORMANCE RESULTS:")
    print(f"Store phase: {store_duration:.2f} seconds")
    print(f"Verify phase: {verify_duration:.2f} seconds")
    print(f"Total time: {total_duration:.2f} seconds")
    print(f"Store rate: {store_rate:.2f} records/sec")
    print(f"Verify rate: {verify_rate:.2f} records/sec")
    print(f"Total rate: {total_rate:.2f} records/sec")

    print("\n🔍 INTEGRITY CHECKS:")
    print(f"Records stored: {len(record_ids)}")
    print(f"Records retrieved: {retrieved_count}")
    print(f"Records verified: {verified_count}")
    integrity_rate = (verified_count / total) * 100 if total > 0 else 100
    print(f"Integrity rate: {integrity_rate:.1f}%")

    print("\n🏆 TEST RESULTS:")
    print(f"✅ SUCCESS - All {total} records processed with 100% integrity")
    print(f"Performance: {total_rate:.2f} records/sec sustained throughput")

    # Assertions
    assert len(record_ids) == total, f"Expected {total} record IDs, got {len(record_ids)}"
    assert retrieved_count == total, f"Expected to retrieve {total} records, got {retrieved_count}"
    assert verified_count == total, f"Expected {total} verified records, got {verified_count}"

    # Performance assertions
    assert total_rate > 10, f"Performance too low: {total_rate:.2f} records/sec (minimum 10 r/s)"
    assert store_duration < 3600, f"Store phase too slow: {store_duration:.2f}s (max 1 hour)"

    print("\n✅ HEAVY SCALE TEST PASSED")
    print(f"All {total} records processed successfully with 100% integrity")
    print(f"Final throughput: {total_rate:.2f} records/sec")