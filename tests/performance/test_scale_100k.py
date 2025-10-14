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
from src.ioa_core.memory_fabric.fabric import MemoryFabric


@pytest.mark.heavy
@pytest.mark.asyncio
async def test_memoryfabric_scale_100k_sharded():
    """
    Test MemoryFabric with 100k records using sharding for validation.
    This test validates that our sharding implementation works correctly.
    """
    # Configure sharding
    os.environ["IOA_PERF_TUNE"] = "1"
    os.environ["IOA_SHARDS"] = "4"  # Use 4 shards for 100k test
    os.environ["IOA_STAGE_SIZE"] = "10000"  # 10k per stage
    os.environ["IOA_COMMIT_EVERY"] = "1000"  # Commit every 1k records
    os.environ["IOA_PRECOMPILE_SCHEMA"] = "1"
    os.environ["IOA_4D_CACHE_SIZE"] = "1024"
    os.environ["IOA_PROGRESS_T"] = "5"  # Progress every 5 seconds
    
    # Initialize MemoryFabric
    mf = MemoryFabric(
        backend="sqlite",
        config={"data_dir": "./artifacts/memory/"}
    )
    
    print(f"Sharding Configuration:")
    print(f"  Shards: {mf.shards}")
    print(f"  Stage Size: {mf.stage_size}")
    print(f"  Commit Every: {mf.commit_every}")
    print(f"  Progress Telemetry: {mf.progress_telemetry}s")
    
    # Generate 100k test records
    print("Generating 100k test records...")
    records = []
    for i in range(100000):
        records.append({
            "content": f"Validation test document {i} for 100k scale testing with sharding",
            "metadata": {
                "jurisdiction": "EU" if i % 3 == 0 else "US" if i % 3 == 1 else "APAC",
                "risk_level": "high" if i % 20 == 0 else "medium" if i % 5 == 0 else "low",
                "content_length": len(f"Validation test document {i}"),
                "batch_id": i // 1000,
                "test_type": "scale_validation"
            },
            "tags": [f"test_{i % 1000}", "sharding", "validation", "100k"],
            "memory_type": "conversation",
            "storage_tier": "hot"
        })
    
    print(f"Generated {len(records)} records")
    
    # Store with sharding
    print("Starting sharded batch storage...")
    start_time = time.time()
    
    record_ids = await mf.store_batch(records)
    
    end_time = time.time()
    duration = end_time - start_time
    rate = len(records) / duration if duration > 0 else 0
    
    print(f"Storage completed: {len(record_ids)} records in {duration:.2f}s ({rate:.0f} records/sec)")
    
    # Verify shard distribution
    print("Verifying shard distribution...")
    shard_counts = {}
    total_stored = 0
    
    if hasattr(mf, '_shard_connections') and mf._shard_connections:
        for i, conn in enumerate(mf._shard_connections):
            cursor = conn.execute("SELECT COUNT(*) FROM memory_records")
            count = cursor.fetchone()[0]
            shard_counts[i] = count
            total_stored += count
            print(f"  Shard {i}: {count} records")
    else:
        # Fallback to standard store
        all_records = mf.list_all()
        total_stored = len(all_records)
        print(f"  Standard store: {total_stored} records")
    
    print(f"Total stored: {total_stored} records")
    
    # Performance metrics
    print("\nPerformance Metrics:")
    print(f"  Records Processed: {len(records)}")
    print(f"  Records Stored: {total_stored}")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Rate: {rate:.0f} records/second")
    print(f"  Shards Used: {len(shard_counts) if shard_counts else 1}")
    
    # Shard distribution analysis
    if shard_counts:
        min_count = min(shard_counts.values())
        max_count = max(shard_counts.values())
        avg_count = sum(shard_counts.values()) / len(shard_counts)
        distribution_variance = sum((count - avg_count) ** 2 for count in shard_counts.values()) / len(shard_counts)
        
        print(f"\nShard Distribution Analysis:")
        print(f"  Min records per shard: {min_count}")
        print(f"  Max records per shard: {max_count}")
        print(f"  Average records per shard: {avg_count:.1f}")
        print(f"  Distribution variance: {distribution_variance:.1f}")
        print(f"  Distribution balance: {((max_count - min_count) / avg_count * 100):.1f}%")
    
    # Integrity checks
    print("\nIntegrity Checks:")
    integrity_passed = total_stored == len(records)
    print(f"  Record count match: {'PASS' if integrity_passed else 'FAIL'}")
    
    # Performance thresholds
    performance_passed = rate >= 1000  # At least 1000 records/sec
    print(f"  Performance threshold (1000 rec/sec): {'PASS' if performance_passed else 'FAIL'}")
    
    # Shard balance check (if using sharding)
    balance_passed = True
    if shard_counts and len(shard_counts) > 1:
        balance_threshold = 0.3  # 30% variance allowed
        balance_variance = (max_count - min_count) / avg_count if avg_count > 0 else 0
        balance_passed = balance_variance <= balance_threshold
        print(f"  Shard balance (30% variance): {'PASS' if balance_passed else 'FAIL'}")
    
    # Cleanup
    mf.close()
    
    # Assertions
    assert integrity_passed, f"Record count mismatch: expected {len(records)}, got {total_stored}"
    assert performance_passed, f"Performance below threshold: {rate:.0f} < 1000 records/sec"
    if shard_counts and len(shard_counts) > 1:
        assert balance_passed, f"Shard distribution too uneven: {balance_variance:.1%} variance"
    
    print("\n✅ 100k sharded validation test PASSED")
    return {
        "records_processed": len(records),
        "records_stored": total_stored,
        "duration_seconds": duration,
        "rate_per_second": rate,
        "shards_used": len(shard_counts) if shard_counts else 1,
        "integrity_passed": integrity_passed,
        "performance_passed": performance_passed,
        "balance_passed": balance_passed
    }


@pytest.mark.heavy
@pytest.mark.asyncio
async def test_memoryfabric_scale_100k_standard():
    """
    Test MemoryFabric with 100k records using standard (non-sharded) approach for comparison.
    """
    # Configure standard approach
    os.environ["IOA_PERF_TUNE"] = "1"
    os.environ["IOA_SHARDS"] = "1"  # No sharding
    os.environ["IOA_STAGE_SIZE"] = "20000"
    os.environ["IOA_COMMIT_EVERY"] = "1000"
    os.environ["IOA_PRECOMPILE_SCHEMA"] = "1"
    os.environ["IOA_4D_CACHE_SIZE"] = "1024"
    
    # Initialize MemoryFabric
    mf = MemoryFabric(
        backend="sqlite",
        config={"data_dir": "./artifacts/memory/"}
    )
    
    print(f"Standard Configuration:")
    print(f"  Shards: {mf.shards}")
    print(f"  Stage Size: {mf.stage_size}")
    
    # Generate 100k test records
    print("Generating 100k test records for standard test...")
    records = []
    for i in range(100000):
        records.append({
            "content": f"Standard test document {i} for 100k scale testing",
            "metadata": {
                "jurisdiction": "EU" if i % 2 == 0 else "US",
                "risk_level": "high" if i % 10 == 0 else "medium",
                "content_length": len(f"Standard test document {i}"),
                "batch_id": i // 1000,
                "test_type": "standard_validation"
            },
            "tags": [f"test_{i % 1000}", "standard", "validation", "100k"],
            "memory_type": "conversation",
            "storage_tier": "hot"
        })
    
    print(f"Generated {len(records)} records")
    
    # Store with standard approach
    print("Starting standard batch storage...")
    start_time = time.time()
    
    record_ids = await mf.store_batch(records)
    
    end_time = time.time()
    duration = end_time - start_time
    rate = len(records) / duration if duration > 0 else 0
    
    print(f"Standard storage completed: {len(record_ids)} records in {duration:.2f}s ({rate:.0f} records/sec)")
    
    # Verify storage
    all_records = mf.list_all()
    total_stored = len(all_records)
    
    print(f"Total stored: {total_stored} records")
    
    # Performance metrics
    print("\nStandard Performance Metrics:")
    print(f"  Records Processed: {len(records)}")
    print(f"  Records Stored: {total_stored}")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Rate: {rate:.0f} records/second")
    
    # Cleanup
    mf.close()
    
    # Assertions
    assert total_stored == len(records), f"Record count mismatch: expected {len(records)}, got {total_stored}"
    
    print("\n✅ 100k standard validation test PASSED")
    return {
        "records_processed": len(records),
        "records_stored": total_stored,
        "duration_seconds": duration,
        "rate_per_second": rate,
        "approach": "standard"
    }

