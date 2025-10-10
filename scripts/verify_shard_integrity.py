""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

import os
import sys
import sqlite3
import json
from typing import Dict, List, Tuple
from datetime import datetime, timezone

def verify_shard_integrity(data_dir: str = "./artifacts/memory/") -> Dict[str, any]:
    """
    Verify shard integrity and distribution.
    
    Returns:
        Dict with verification results
    """
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "shards_found": 0,
        "total_records": 0,
        "unique_records": 0,
        "shard_distribution": {},
        "integrity_status": "UNKNOWN",
        "distribution_balance": 0.0,
        "max_deviation": 0.0,
        "errors": []
    }
    
    try:
        # Find all shard databases
        shard_dbs = []
        for file in os.listdir(data_dir):
            if file.startswith("mf_shard_") and file.endswith(".db"):
                shard_dbs.append(os.path.join(data_dir, file))
        
        shard_dbs.sort()
        results["shards_found"] = len(shard_dbs)
        
        if not shard_dbs:
            results["errors"].append("No shard databases found")
            results["integrity_status"] = "FAIL"
            return results
        
        # Check each shard
        shard_counts = {}
        all_pks = set()
        
        for db_path in shard_dbs:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.execute("SELECT COUNT(*) FROM memory_records")
                count = cursor.fetchone()[0]
                shard_counts[db_path] = count
                results["total_records"] += count
                
                # Get all primary keys for uniqueness check
                cursor = conn.execute("SELECT pk FROM memory_records")
                pks = [row[0] for row in cursor.fetchall()]
                all_pks.update(pks)
                
                conn.close()
                
            except Exception as e:
                results["errors"].append(f"Error reading {db_path}: {e}")
        
        results["unique_records"] = len(all_pks)
        results["shard_distribution"] = shard_counts
        
        # Check integrity
        if results["total_records"] == results["unique_records"]:
            results["integrity_status"] = "PASS"
        else:
            results["integrity_status"] = "FAIL"
            results["errors"].append(f"Record count mismatch: {results['total_records']} total vs {results['unique_records']} unique")
        
        # Check distribution balance
        if shard_counts:
            counts = list(shard_counts.values())
            avg_count = sum(counts) / len(counts)
            max_count = max(counts)
            min_count = min(counts)
            
            if avg_count > 0:
                max_deviation = max(abs(max_count - avg_count), abs(min_count - avg_count))
                results["max_deviation"] = (max_deviation / avg_count) * 100
                results["distribution_balance"] = 100 - results["max_deviation"]
                
                if results["max_deviation"] <= 5.0:
                    results["distribution_status"] = "BALANCED"
                else:
                    results["distribution_status"] = "UNBALANCED"
                    results["errors"].append(f"Distribution deviation {results['max_deviation']:.1f}% exceeds 5% threshold")
        
        return results
        
    except Exception as e:
        results["errors"].append(f"Verification failed: {e}")
        results["integrity_status"] = "ERROR"
        return results

def print_verification_report(results: Dict[str, any]):
    """Print a formatted verification report."""
    print("=" * 60)
    print("MEMORYFABRIC SHARD INTEGRITY VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Shards Found: {results['shards_found']}")
    print(f"Total Records: {results['total_records']:,}")
    print(f"Unique Records: {results['unique_records']:,}")
    print()
    
    print("SHARD DISTRIBUTION:")
    for db_path, count in results['shard_distribution'].items():
        shard_name = os.path.basename(db_path)
        print(f"  {shard_name}: {count:,} records")
    print()
    
    print("INTEGRITY CHECKS:")
    print(f"  Status: {results['integrity_status']}")
    print(f"  Distribution Balance: {results['distribution_balance']:.1f}%")
    print(f"  Max Deviation: {results['max_deviation']:.1f}%")
    print()
    
    if results['errors']:
        print("ERRORS:")
        for error in results['errors']:
            print(f"  ❌ {error}")
        print()
    
    # Overall status
    if results['integrity_status'] == "PASS" and results['max_deviation'] <= 5.0:
        print("✅ VERIFICATION PASSED")
        print("   - All records unique")
        print("   - Distribution balanced")
    else:
        print("❌ VERIFICATION FAILED")
        print("   - Check errors above")

if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "./artifacts/memory/"
    
    print(f"Verifying shard integrity in: {data_dir}")
    results = verify_shard_integrity(data_dir)
    print_verification_report(results)
    
    # Write results to file
    with open("shard_integrity_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed report saved to: shard_integrity_report.json")
    
    # Exit with appropriate code
    if results['integrity_status'] == "PASS" and results['max_deviation'] <= 5.0:
        sys.exit(0)
    else:
        sys.exit(1)

