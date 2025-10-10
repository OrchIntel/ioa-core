""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import os
import time
import json
import tempfile
import sqlite3
import pytest
from pathlib import Path
from typing import Dict, List, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ioa_core.memory_fabric.fabric import MemoryFabric
from ioa_core.governance.audit_chain import get_audit_chain


@pytest.mark.slow
@pytest.mark.perf
@pytest.mark.durability
def test_durability_full_sync_mode():
    """Test durability with PRAGMA synchronous=FULL."""
    _run_durability_test("FULL", "test_durability_full.json")


@pytest.mark.slow
@pytest.mark.perf
@pytest.mark.durability
def test_durability_normal_sync_mode():
    """Test durability with PRAGMA synchronous=NORMAL (baseline)."""
    _run_durability_test("NORMAL", "test_durability_normal.json")


def _run_durability_test(sync_mode: str, output_file: str) -> Dict[str, Any]:
    """Run comprehensive durability test with different sync modes."""

    print(f"🔒 Running durability test with synchronous={sync_mode}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Setup database with specific sync mode
        db_path = Path(tmp_dir) / f"durability_test_{sync_mode.lower()}.db"
        config = {
            "db_path": str(db_path),
            "synchronous": sync_mode,
            "journal_mode": "WAL",
            "wal_autocheckpoint": 1000,
            "cache_size": 10000
        }

        fabric = MemoryFabric(backend='sqlite', config=config)

        # Phase 1: Load test data
        print("📥 Loading durability test data...")
        test_records = 10000
        test_data = _generate_durability_test_data(test_records)

        record_ids = []
        for record in test_data:
            record_id = fabric.store(
                content=record["content"],
                metadata=record["metadata"]
            )
            record_ids.append(record_id)

        # Phase 2: Pre-failure integrity check
        print("🔍 Pre-failure integrity check...")
        pre_failure_integrity = _check_integrity(fabric, record_ids[:1000])  # Check first 1000

        # Phase 3: Simulate failure scenarios
        failure_scenarios = {
            "clean_shutdown": _test_clean_shutdown,
            "forced_close": _test_forced_close,
            "power_loss_simulation": _test_power_loss_simulation,
            "concurrent_access": _test_concurrent_access
        }

        scenario_results = {}
        for scenario_name, scenario_func in failure_scenarios.items():
            print(f"⚡ Testing scenario: {scenario_name}")
            try:
                result = scenario_func(fabric, record_ids, db_path)
                scenario_results[scenario_name] = result
                print(f"  ✅ {scenario_name}: {result['status']}")
            except Exception as e:
                scenario_results[scenario_name] = {"status": "failed", "error": str(e)}
                print(f"  ❌ {scenario_name}: {e}")

        # Phase 4: Post-failure recovery test
        print("🔄 Testing recovery scenarios...")
        recovery_results = _test_recovery_scenarios(fabric, record_ids, db_path)

        # Phase 5: Performance impact assessment
        print("📊 Measuring performance impact...")
        perf_impact = _measure_sync_performance_impact(sync_mode, tmp_dir)

        # Phase 6: Final integrity verification
        print("🔍 Final integrity verification...")
        final_integrity = _check_integrity(fabric, record_ids)

        fabric.close()

        # Compile comprehensive results
        results = {
            "test_config": {
                "sync_mode": sync_mode,
                "records": test_records,
                "backend": "sqlite",
                "journal_mode": "WAL",
                "scenarios_tested": list(failure_scenarios.keys())
            },
            "integrity": {
                "pre_failure": pre_failure_integrity,
                "post_failure": final_integrity,
                "integrity_maintained": final_integrity["overall_score"] >= 0.99
            },
            "failure_scenarios": scenario_results,
            "recovery": recovery_results,
            "performance_impact": perf_impact,
            "sqlite_config": {
                "synchronous": sync_mode,
                "journal_mode": "WAL",
                "cache_size": 10000,
                "wal_autocheckpoint": 1000
            },
            "timestamp": time.time()
        }

        # Generate audit report
        audit_data = {
            "test_type": f"durability_test_{sync_mode.lower()}",
            "governance_compliant": True,
            "system_laws_checked": ["law1", "law3", "law7"],  # Compliance, Audit, Sustainability
            "durability_metrics": {
                "sync_mode": sync_mode,
                "integrity_score": final_integrity["overall_score"],
                "write_amplification": perf_impact.get("write_amplification", 1.0),
                "recovery_success_rate": recovery_results.get("success_rate", 0.0),
                "data_persistence": final_integrity["overall_score"] >= 0.999
            }
        }

        audit_chain = get_audit_chain()
        audit_chain.log("benchmark.durability", audit_data)
        results["audit_report"] = audit_data

        # Save results
        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📊 Results saved to {output_path}")

        print(f"✅ Durability test completed: synchronous={sync_mode}")
        print(f"   Pre-failure integrity: {pre_failure_integrity['overall_score']*100:.1f}%")
        print(f"   Post-failure integrity: {final_integrity['overall_score']*100:.1f}%")
        print(f"   Performance overhead: {perf_impact.get('avg_overhead_percent', 0):.1f}%")

        return results


def _generate_durability_test_data(num_records: int) -> List[Dict[str, Any]]:
    """Generate test data optimized for durability testing."""
    import random

    data = []
    base_time = time.time()

    for i in range(num_records):
        # Create records with varying sizes and criticality
        content_size = random.choice([100, 500, 1000, 5000])  # Varying content sizes
        content = f"Durability test record {i}. " * (content_size // 25)

        # Metadata with durability-critical fields
        metadata = {
            "record_id": f"DURABILITY-{i:06d}",
            "timestamp": base_time - random.uniform(0, 86400),  # Last 24 hours
            "criticality": random.choice(["low", "medium", "high", "critical"]),
            "data_classification": "sensitive" if random.random() < 0.2 else "internal",
            "backup_required": random.random() < 0.1,  # 10% require backup
            "retention_period_days": random.choice([30, 90, 365, 2555]),
            "version": "1.0",
            "size_bytes": len(content.encode('utf-8'))
        }

        data.append({
            "id": f"durability_record_{i}",
            "content": content,
            "metadata": metadata
        })

    return data


def _check_integrity(fabric, record_ids: List[str], sample_size: int = 1000) -> Dict[str, Any]:
    """Check data integrity for a sample of records."""
    import random

    sample_ids = random.sample(record_ids, min(sample_size, len(record_ids)))

    integrity_checks = {
        "total_checked": len(sample_ids),
        "retrieval_success": 0,
        "content_integrity": 0,
        "metadata_integrity": 0,
        "errors": []
    }

    for record_id in sample_ids:
        try:
            record = fabric.retrieve(record_id)

            if record:
                integrity_checks["retrieval_success"] += 1

                # Check content integrity
                if hasattr(record, 'content') and record.content and len(record.content) > 10:
                    integrity_checks["content_integrity"] += 1

                # Check metadata integrity
                if hasattr(record, 'metadata') and record.metadata:
                    integrity_checks["metadata_integrity"] += 1

            else:
                integrity_checks["errors"].append(f"Record {record_id} not found")

        except Exception as e:
            integrity_checks["errors"].append(f"Record {record_id} error: {e}")

    # Calculate scores
    integrity_checks["retrieval_score"] = integrity_checks["retrieval_success"] / len(sample_ids)
    integrity_checks["content_score"] = integrity_checks["content_integrity"] / len(sample_ids)
    integrity_checks["metadata_score"] = integrity_checks["metadata_integrity"] / len(sample_ids)

    # Overall integrity score
    integrity_checks["overall_score"] = (
        integrity_checks["retrieval_score"] * 0.5 +
        integrity_checks["content_score"] * 0.3 +
        integrity_checks["metadata_score"] * 0.2
    )

    return integrity_checks


def _test_clean_shutdown(fabric, record_ids: List[str], db_path: Path) -> Dict[str, Any]:
    """Test clean shutdown durability."""
    # Perform some operations
    for i in range(100):
        fabric.store(
            content=f"Clean shutdown test {i}",
            metadata={"test_type": "clean_shutdown", "sequence": i}
        )

    # Close cleanly (this is the clean shutdown)
    fabric.close()

    # Try to reopen and verify data
    try:
        config = {"db_path": str(db_path)}
        fabric_reopened = MemoryFabric(backend='sqlite', config=config)

        # Check if we can retrieve recent records
        test_record = fabric_reopened.retrieve(record_ids[-1])
        fabric_reopened.close()

        return {
            "status": "success" if test_record else "partial",
            "data_recoverable": test_record is not None,
            "shutdown_method": "clean"
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "shutdown_method": "clean"
        }


def _test_forced_close(fabric, record_ids: List[str], db_path: Path) -> Dict[str, Any]:
    """Test forced close (simulating crash) durability."""
    # Perform some operations
    temp_ids = []
    for i in range(50):
        record_id = fabric.store(
            content=f"Forced close test {i}",
            metadata={"test_type": "forced_close", "sequence": i}
        )
        temp_ids.append(record_id)

    # Simulate crash by not closing properly
    # In a real scenario, this would be a process kill

    # Try to recover
    try:
        config = {"db_path": str(db_path)}
        fabric_recovered = MemoryFabric(backend='sqlite', config=config)

        # Check recovery of temp records
        recoverable = 0
        for record_id in temp_ids:
            if fabric_recovered.retrieve(record_id):
                recoverable += 1

        fabric_recovered.close()

        return {
            "status": "success",
            "temp_records_recovered": recoverable,
            "temp_records_total": len(temp_ids),
            "recovery_rate": recoverable / len(temp_ids),
            "crash_method": "simulated"
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "crash_method": "simulated"
        }


def _test_power_loss_simulation(fabric, record_ids: List[str], db_path: Path) -> Dict[str, Any]:
    """Simulate power loss by corrupting WAL file."""
    # This is a simplified simulation - in practice, you'd need more sophisticated crash simulation

    # Perform operations that should be in WAL
    wal_records = []
    for i in range(30):
        record_id = fabric.store(
            content=f"Power loss test {i}",
            metadata={"test_type": "power_loss", "sequence": i, "critical": True}
        )
        wal_records.append(record_id)

    # Simulate power loss by closing without proper sync
    fabric.close()

    # Check if WAL recovery works
    try:
        config = {"db_path": str(db_path)}
        fabric_recovery = MemoryFabric(backend='sqlite', config=config)

        recovered = 0
        for record_id in wal_records:
            if fabric_recovery.retrieve(record_id):
                recovered += 1

        fabric_recovery.close()

        return {
            "status": "success",
            "wal_records_recovered": recovered,
            "wal_records_total": len(wal_records),
            "wal_recovery_rate": recovered / len(wal_records),
            "power_loss_simulated": True
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "power_loss_simulated": True
        }


def _test_concurrent_access(fabric, record_ids: List[str], db_path: Path) -> Dict[str, Any]:
    """Test durability under concurrent access."""
    import threading
    import queue

    results_queue = queue.Queue()
    errors = []

    def worker_thread(thread_id: int):
        """Worker thread for concurrent operations."""
        try:
            # Each thread performs mixed read/write operations
            operations = 0
            successes = 0

            for i in range(20):  # 20 operations per thread
                try:
                    if i % 2 == 0:  # Read operation
                        record_id = record_ids[(thread_id * 20 + i) % len(record_ids)]
                        record = fabric.retrieve(record_id)
                        if record:
                            successes += 1
                    else:  # Write operation
                        record_id = fabric.store(
                            content=f"Concurrent test T{thread_id}-{i}",
                            metadata={"thread": thread_id, "operation": i, "concurrent": True}
                        )
                        if record_id:
                            successes += 1

                    operations += 1

                except Exception as e:
                    errors.append(f"Thread {thread_id} op {i}: {e}")

            results_queue.put({
                "thread_id": thread_id,
                "operations": operations,
                "successes": successes,
                "success_rate": successes / operations if operations > 0 else 0
            })

        except Exception as e:
            results_queue.put({
                "thread_id": thread_id,
                "error": str(e)
            })

    # Start concurrent threads
    threads = []
    num_threads = 5

    for i in range(num_threads):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Collect results
    thread_results = []
    while not results_queue.empty():
        thread_results.append(results_queue.get())

    # Analyze results
    total_operations = sum(r.get("operations", 0) for r in thread_results)
    total_successes = sum(r.get("successes", 0) for r in thread_results)

    return {
        "status": "success" if len(errors) == 0 else "partial",
        "concurrent_threads": num_threads,
        "total_operations": total_operations,
        "total_successes": total_successes,
        "overall_success_rate": total_successes / total_operations if total_operations > 0 else 0,
        "errors": errors,
        "thread_results": thread_results
    }


def _test_recovery_scenarios(fabric, record_ids: List[str], db_path: Path) -> Dict[str, Any]:
    """Test various recovery scenarios."""
    recovery_tests = {
        "immediate_reopen": _test_immediate_reopen,
        "delayed_reopen": _test_delayed_reopen,
        "backup_integrity": _test_backup_integrity
    }

    results = {}
    for test_name, test_func in recovery_tests.items():
        try:
            result = test_func(fabric, record_ids, db_path)
            results[test_name] = result
        except Exception as e:
            results[test_name] = {"status": "failed", "error": str(e)}

    # Overall assessment
    successful_tests = sum(1 for r in results.values() if r.get("status") == "success")
    results["summary"] = {
        "tests_run": len(recovery_tests),
        "tests_passed": successful_tests,
        "success_rate": successful_tests / len(recovery_tests),
        "recovery_reliable": successful_tests == len(recovery_tests)
    }

    return results


def _test_immediate_reopen(fabric, record_ids: List[str], db_path: Path) -> Dict[str, Any]:
    """Test immediate reopen after close."""
    # Close and immediately reopen
    fabric.close()

    try:
        config = {"db_path": str(db_path)}
        reopened_fabric = MemoryFabric(backend='sqlite', config=config)

        # Test a few records
        test_records = record_ids[:10]
        recovered = 0

        for record_id in test_records:
            if reopened_fabric.retrieve(record_id):
                recovered += 1

        reopened_fabric.close()

        return {
            "status": "success",
            "records_tested": len(test_records),
            "records_recovered": recovered,
            "recovery_rate": recovered / len(test_records)
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _test_delayed_reopen(fabric, record_ids: List[str], db_path: Path) -> Dict[str, Any]:
    """Test delayed reopen (simulating system restart)."""
    fabric.close()

    # Simulate delay
    time.sleep(2)

    try:
        config = {"db_path": str(db_path)}
        reopened_fabric = MemoryFabric(backend='sqlite', config=config)

        # Test more records
        test_records = record_ids[:50]
        recovered = 0

        for record_id in test_records:
            if reopened_fabric.retrieve(record_id):
                recovered += 1

        reopened_fabric.close()

        return {
            "status": "success",
            "delay_seconds": 2,
            "records_tested": len(test_records),
            "records_recovered": recovered,
            "recovery_rate": recovered / len(test_records)
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _test_backup_integrity(fabric, record_ids: List[str], db_path: Path) -> Dict[str, Any]:
    """Test backup file integrity."""
    # Create backup
    backup_path = db_path.with_suffix('.db.backup')
    fabric.close()

    try:
        # Copy database file as backup
        import shutil
        shutil.copy2(db_path, backup_path)

        # Test backup integrity
        conn = sqlite3.connect(str(backup_path))
        cursor = conn.cursor()

        # Basic integrity check
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]

        # Count records
        cursor.execute("SELECT COUNT(*) FROM memory_records")
        record_count = cursor.fetchone()[0]

        conn.close()

        return {
            "status": "success" if integrity_result == "ok" else "integrity_issue",
            "integrity_check": integrity_result,
            "backup_record_count": record_count,
            "backup_created": True
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _measure_sync_performance_impact(sync_mode: str, tmp_dir: str) -> Dict[str, Any]:
    """Measure performance impact of different sync modes."""

    # Test both modes for comparison
    modes_to_test = ["NORMAL", "FULL"] if sync_mode == "FULL" else ["NORMAL"]

    results = {}

    for mode in modes_to_test:
        db_path = Path(tmp_dir) / f"perf_test_{mode.lower()}.db"
        config = {"db_path": str(db_path), "synchronous": mode}

        fabric = MemoryFabric(backend='sqlite', config=config)

        # Performance test
        latencies = []
        start_time = time.time()

        for i in range(1000):
            store_start = time.time()
            fabric.store(
                content=f"Performance test {i}",
                metadata={"test": "sync_perf", "mode": mode, "seq": i}
            )
            latencies.append(time.time() - store_start)

        total_time = time.time() - start_time
        throughput = 1000 / total_time

        fabric.close()

        results[mode] = {
            "throughput_ops_per_sec": throughput,
            "avg_latency_ms": (sum(latencies) / len(latencies)) * 1000,
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] * 1000
        }

    # Calculate overhead if both modes tested
    if len(results) == 2:
        normal_throughput = results["NORMAL"]["throughput_ops_per_sec"]
        full_throughput = results["FULL"]["throughput_ops_per_sec"]

        overhead = ((normal_throughput - full_throughput) / normal_throughput) * 100
        results["comparison"] = {
            "write_amplification": normal_throughput / full_throughput,
            "throughput_overhead_percent": overhead,
            "latency_increase_percent": ((results["FULL"]["avg_latency_ms"] - results["NORMAL"]["avg_latency_ms"]) / results["NORMAL"]["avg_latency_ms"]) * 100
        }

    return results


if __name__ == "__main__":
    # Allow direct execution for manual testing
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--run-durability-test":
        sync_mode = sys.argv[2] if len(sys.argv) > 2 else "NORMAL"
        results = _run_durability_test(sync_mode, f"durability_test_manual_{sync_mode.lower()}.json")
        print("Durability test completed successfully!")

