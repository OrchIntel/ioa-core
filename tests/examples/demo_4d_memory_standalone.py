#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""
Standalone 4D Memory Demo - No IOA Core imports required.
Demonstrates memory tiering with minimal dependencies.
"""

import hashlib
import json
import random
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

def main():
    print("💾 IOA Core - 4D MemoryFabric Demo (Standalone)")
    print("=" * 60)
    
    # Paths
    artifacts_dir = Path(__file__).parent.parent.parent / 'artifacts' / 'examples'
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    num_records = 100
    print(f"Records to generate: {num_records}")
    print()
    
    # Generate synthetic records
    print(f"📝 Generating {num_records} synthetic records...")
    templates = [
        "How do I configure IOA logging?",
        "What are system requirements?",
        "Container deployment guide",
        "Enable debug mode",
        "Monitor performance"
    ]
    
    records = []
    tier_counts = {"hot": 0, "warm": 0, "cold": 0, "archive": 0}
    
    for i in range(num_records):
        age_days = random.randint(0, 120)
        created_at = datetime.now(timezone.utc) - timedelta(days=age_days)
        
        # Determine tier
        if age_days < 7:
            tier = "hot"
        elif age_days < 30:
            tier = "warm"
        elif age_days < 90:
            tier = "cold"
        else:
            tier = "archive"
        
        tier_counts[tier] += 1
        
        records.append({
            "id": f"ticket-{i+1:04d}",
            "created_at": created_at.isoformat(),
            "age_days": age_days,
            "query": random.choice(templates),
            "tier": tier
        })
    
    print(f"   ✅ Generated {len(records)} records")
    print(f"   Tier distribution:")
    for tier, count in tier_counts.items():
        pct = (count / len(records)) * 100
        print(f"      - {tier.capitalize()}: {count} ({pct:.1f}%)")
    print()
    
    # Simulate retrieval
    print("🔍 Performing retrieval query...")
    retrieval = {
        "query": "How do I configure IOA logging?",
        "results_count": random.randint(5, 15),
        "latency_ms": round(random.uniform(10, 50), 2),
        "tiers_searched": ["hot", "warm"]
    }
    
    print(f"   Query: \"{retrieval['query']}\"")
    print(f"   Results: {retrieval['results_count']}")
    print(f"   Latency: {retrieval['latency_ms']}ms")
    print()
    
    # Generate evidence
    print("📦 Generating Evidence Bundle...")
    evidence = {
        "demo": "4d_memory_standalone",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operations": {
            "ingest": {
                "records_count": len(records),
                "tier_distribution": tier_counts
            },
            "retrieval": retrieval
        },
        "evidence_hash": ""
    }
    
    evidence_json = json.dumps(evidence, sort_keys=True)
    evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
    evidence["evidence_hash"] = evidence_hash
    
    evidence_file = artifacts_dir / 'memory_evidence.json'
    with open(evidence_file, 'w') as f:
        json.dump(evidence, f, indent=2)
    
    print(f"   Evidence Hash: {evidence_hash[:16]}...")
    print()
    
    # Generate signature
    print("🔐 Generating SIGv1 Signature...")
    sig_payload = {
        "version": "SIGv1",
        "algorithm": "SHA256",
        "evidence_hash": evidence_hash,
        "signer": "ioa-core-memory-demo",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    sig_data = json.dumps(sig_payload, sort_keys=True).encode()
    signature = f"SIGv1:{hashlib.sha256(sig_data).hexdigest()}"
    sig_payload["signature"] = signature
    
    sig_file = artifacts_dir / 'memory_evidence.sig'
    with open(sig_file, 'w') as f:
        json.dump(sig_payload, f, indent=2)
    
    print(f"   Signature: {signature[:24]}...")
    print()
    
    # Generate metrics
    print("📊 Generating Metrics...")
    metrics = {
        "demo": "4d_memory_standalone",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ingest_metrics": {
            "total_records": len(records),
            "tier_distribution": tier_counts
        },
        "retrieval_metrics": retrieval
    }
    
    metrics_file = artifacts_dir / 'memory_metrics.json'
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"   Metrics File: {metrics_file}")
    print()
    
    print("=" * 60)
    print("✅ 4D Memory Demo Complete")
    print(f"Records Processed: {len(records)}")
    print(f"Artifacts: {artifacts_dir}")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

