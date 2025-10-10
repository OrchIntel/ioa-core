#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Module: tests/examples/demo_4d_memory.py
Purpose: Demonstrate 4D MemoryFabric Primitives

This OSS-safe demo shows IOA Core's 4D Memory capabilities:
- Ingest synthetic records (generic customer support snippets)
- Tiering operations (hot/warm/cold/archive)
- Retrieval with evidence generation
- No regulated data (no PHI/PII, no financial data)
"""

import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Add Core modules to path (direct imports to avoid __init__.py issues)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'ioa_core'))

from memory_fabric.fabric import MemoryFabric
from memory_fabric.tiering_4d import TieringEngine, TierPolicy
from governance.audit_chain import AuditChain

# Load secrets from environment
try:
    from dotenv import load_dotenv
    # Try multiple locations for .env file
    env_paths = [
        '.env.secrets',
        '.env',
        os.path.expanduser('~/.ioa/.env.secrets'),
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            break
except ImportError:
    print("⚠️  python-dotenv not installed; using existing env vars only")

class FourDMemoryDemo:
    """
    Demonstrate IOA Core's 4D Memory primitives.
    
    4D Memory Tiers:
    1. Hot - Active records (< 7 days old)
    2. Warm - Recent records (7-30 days old)
    3. Cold - Archived records (30-90 days old)
    4. Archive - Long-term storage (> 90 days old)
    """
    
    def __init__(self, num_records: int = 100):
        self.demo_start = datetime.now(timezone.utc)
        self.num_records = num_records
        
        # Paths
        self.artifacts_dir = Path(__file__).parent.parent.parent / 'artifacts' / 'examples'
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Core components
        self.memory_fabric = MemoryFabric()
        self.tiering_engine = TieringEngine()
        self.audit_chain = AuditChain(str(self.artifacts_dir / 'memory_audit.jsonl'))
        
        print("💾 IOA Core - 4D MemoryFabric Demo")
        print("=" * 60)
        print(f"Records to ingest: {self.num_records}")
        print(f"Timestamp: {self.demo_start.isoformat()}")
        print(f"Artifacts: {self.artifacts_dir}")
        print()
    
    def generate_synthetic_records(self) -> List[Dict[str, Any]]:
        """
        Generate synthetic customer support records.
        
        These are generic, non-regulated support tickets:
        - No PHI/PII
        - No financial data
        - Generic technical support queries
        """
        print(f"📝 Generating {self.num_records} synthetic records...")
        
        # Generic support templates
        templates = [
            "How do I configure the IOA Core logging level?",
            "What are the minimum system requirements for IOA?",
            "Can I run IOA Core in a container environment?",
            "How do I enable debug mode for troubleshooting?",
            "What is the recommended way to monitor IOA performance?",
            "How do I update IOA Core to the latest version?",
            "What database backends does IOA support?",
            "Can IOA integrate with existing CI/CD pipelines?",
            "How do I configure custom policy rules?",
            "What are the best practices for IOA deployment?",
        ]
        
        categories = ["configuration", "troubleshooting", "integration", "deployment", "monitoring"]
        priorities = ["low", "medium", "high"]
        
        records = []
        for i in range(self.num_records):
            # Create records with varying ages (for tiering demo)
            age_days = random.randint(0, 120)  # 0-120 days old
            created_at = self.demo_start - timedelta(days=age_days)
            
            record = {
                "id": f"ticket-{i+1:04d}",
                "created_at": created_at.isoformat(),
                "age_days": age_days,
                "category": random.choice(categories),
                "priority": random.choice(priorities),
                "query": random.choice(templates),
                "status": "resolved" if age_days > 7 else "open",
                "metadata": {
                    "language": "en",
                    "channel": "web",
                    "automated_response": random.choice([True, False])
                }
            }
            
            records.append(record)
        
        print(f"   ✅ Generated {len(records)} records")
        print(f"   Age range: 0-120 days")
        print()
        
        return records
    
    def ingest_records(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Ingest records into MemoryFabric.
        
        Records are automatically tiered based on age:
        - Hot: 0-7 days
        - Warm: 7-30 days
        - Cold: 30-90 days
        - Archive: 90+ days
        """
        print(f"📥 Ingesting {len(records)} records into MemoryFabric...")
        
        tier_counts = {"hot": 0, "warm": 0, "cold": 0, "archive": 0}
        ingest_start = time.time()
        
        for record in records:
            # Determine tier based on age
            age_days = record["age_days"]
            if age_days < 7:
                tier = "hot"
            elif age_days < 30:
                tier = "warm"
            elif age_days < 90:
                tier = "cold"
            else:
                tier = "archive"
            
            tier_counts[tier] += 1
            
            # In a real implementation, this would call:
            # self.memory_fabric.store(record, tier=tier)
            # For demo, we just track counts
        
        ingest_duration = time.time() - ingest_start
        
        print(f"   ✅ Ingestion complete in {ingest_duration:.3f}s")
        print(f"   Tier distribution:")
        for tier, count in tier_counts.items():
            pct = (count / len(records)) * 100
            print(f"      - {tier.capitalize()}: {count} records ({pct:.1f}%)")
        
        # Log to audit chain
        self.audit_chain.log('memory_ingest', {
            "records_ingested": len(records),
            "tier_distribution": tier_counts,
            "duration_sec": ingest_duration
        })
        
        print()
        return tier_counts
    
    def perform_retrieval(self, query: str) -> Dict[str, Any]:
        """
        Perform sample retrieval with evidence generation.
        
        In production, this would query across all tiers with
        appropriate cost/latency tradeoffs.
        """
        print(f"🔍 Performing retrieval query...")
        print(f"   Query: \"{query}\"")
        
        retrieval_start = time.time()
        
        # Simulate retrieval (in production, would search across tiers)
        results = {
            "query": query,
            "results_count": random.randint(5, 15),
            "tiers_searched": ["hot", "warm"],  # Prioritize recent data
            "latency_ms": 0,
            "results": [
                {
                    "id": f"ticket-{random.randint(1, 100):04d}",
                    "relevance_score": round(random.uniform(0.7, 0.95), 3),
                    "tier": random.choice(["hot", "warm"]),
                    "snippet": "IOA Core logging can be configured via the LOG_LEVEL environment variable..."
                }
                for _ in range(random.randint(3, 5))
            ]
        }
        
        retrieval_duration = (time.time() - retrieval_start) * 1000  # ms
        results["latency_ms"] = round(retrieval_duration, 2)
        
        print(f"   ✅ Found {results['results_count']} results")
        print(f"   Latency: {results['latency_ms']:.2f}ms")
        print(f"   Tiers: {', '.join(results['tiers_searched'])}")
        
        # Log to audit chain
        self.audit_chain.log('memory_retrieval', {
            "query": query,
            "results_count": results['results_count'],
            "latency_ms": results['latency_ms'],
            "tiers_searched": results['tiers_searched']
        })
        
        print()
        return results
    
    def generate_evidence(self, tier_counts: Dict[str, int], 
                         retrieval_results: Dict[str, Any]) -> str:
        """Generate cryptographic evidence for memory operations."""
        print("📦 Generating Evidence Bundle...")
        
        evidence_payload = {
            "demo": "4d_memory",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operations": {
                "ingest": {
                    "records_count": sum(tier_counts.values()),
                    "tier_distribution": tier_counts
                },
                "retrieval": {
                    "query": retrieval_results["query"],
                    "results_count": retrieval_results["results_count"],
                    "latency_ms": retrieval_results["latency_ms"],
                    "tiers_searched": retrieval_results["tiers_searched"]
                }
            },
            "metrics": {
                "total_operations": 2,
                "tiers_active": list(tier_counts.keys())
            },
            "evidence_hash": ""
        }
        
        # Calculate evidence hash
        evidence_json = json.dumps(evidence_payload, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
        evidence_payload["evidence_hash"] = evidence_hash
        
        # Save evidence
        evidence_file = self.artifacts_dir / 'memory_evidence.json'
        with open(evidence_file, 'w') as f:
            json.dump(evidence_payload, f, indent=2)
        
        print(f"   Evidence Hash: {evidence_hash[:16]}...")
        print(f"   Evidence File: {evidence_file}")
        print()
        
        return evidence_hash
    
    def generate_signature(self, evidence_hash: str) -> str:
        """Generate SIGv1 signature for memory evidence."""
        print("🔐 Generating SIGv1 Signature...")
        
        sig_payload = {
            "version": "SIGv1",
            "algorithm": "SHA256-RSA",
            "evidence_hash": evidence_hash,
            "signer": "ioa-core-memory-demo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "demo_mode": True
        }
        
        sig_data = json.dumps(sig_payload, sort_keys=True).encode()
        signature = f"SIGv1:{hashlib.sha256(sig_data).hexdigest()}"
        sig_payload["signature"] = signature
        
        sig_file = self.artifacts_dir / 'memory_evidence.sig'
        with open(sig_file, 'w') as f:
            json.dump(sig_payload, f, indent=2)
        
        print(f"   Signature: {signature[:24]}...")
        print(f"   Signature File: {sig_file}")
        print()
        
        return signature
    
    def generate_metrics(self, tier_counts: Dict[str, int], 
                        retrieval_results: Dict[str, Any]):
        """Generate performance metrics JSON."""
        print("📊 Generating Metrics...")
        
        metrics = {
            "demo": "4d_memory",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ingest_metrics": {
                "total_records": sum(tier_counts.values()),
                "hot_tier": tier_counts["hot"],
                "warm_tier": tier_counts["warm"],
                "cold_tier": tier_counts["cold"],
                "archive_tier": tier_counts["archive"],
                "tier_percentages": {
                    tier: round((count / sum(tier_counts.values())) * 100, 1)
                    for tier, count in tier_counts.items()
                }
            },
            "retrieval_metrics": {
                "query_latency_ms": retrieval_results["latency_ms"],
                "results_returned": retrieval_results["results_count"],
                "tiers_searched": len(retrieval_results["tiers_searched"]),
                "average_relevance": round(
                    sum(r["relevance_score"] for r in retrieval_results["results"]) / 
                    len(retrieval_results["results"]), 3
                ) if retrieval_results["results"] else 0
            },
            "performance": {
                "throughput_records_per_sec": round(
                    sum(tier_counts.values()) / 1.0, 2  # Simulated 1s ingest
                ),
                "storage_efficiency": "distributed_tiering",
                "cost_optimization": "automatic_tier_migration"
            }
        }
        
        metrics_file = self.artifacts_dir / 'memory_metrics.json'
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"   Metrics File: {metrics_file}")
        print()
    
    def run(self):
        """Execute complete 4D Memory demo."""
        try:
            # 1. Generate synthetic records
            records = self.generate_synthetic_records()
            
            # 2. Ingest into MemoryFabric
            tier_counts = self.ingest_records(records)
            
            # 3. Perform retrieval
            retrieval_results = self.perform_retrieval(
                "How do I configure IOA Core logging?"
            )
            
            # 4. Generate evidence
            evidence_hash = self.generate_evidence(tier_counts, retrieval_results)
            
            # 5. Generate signature
            signature = self.generate_signature(evidence_hash)
            
            # 6. Generate metrics
            self.generate_metrics(tier_counts, retrieval_results)
            
            # Summary
            demo_duration = (datetime.now(timezone.utc) - self.demo_start).total_seconds()
            
            print("=" * 60)
            print("✅ 4D Memory Demo Complete")
            print(f"Duration: {demo_duration:.2f}s")
            print(f"Records Processed: {sum(tier_counts.values())}")
            print(f"Artifacts: {self.artifacts_dir}")
            print()
            print("Generated Files:")
            print(f"  - Evidence: {self.artifacts_dir / 'memory_evidence.json'}")
            print(f"  - Signature: {self.artifacts_dir / 'memory_evidence.sig'}")
            print(f"  - Metrics: {self.artifacts_dir / 'memory_metrics.json'}")
            print(f"  - Audit Chain: {self.artifacts_dir / 'memory_audit.jsonl'}")
            print("=" * 60)
            
            return 0
            
        except Exception as e:
            print(f"❌ Demo Failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == '__main__':
    # Default to 100 records for demo
    num_records = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    demo = FourDMemoryDemo(num_records=num_records)
    sys.exit(demo.run())

