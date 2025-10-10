#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntelWorkspace Ltd.

"""
Standalone Round-Table Demo - No IOA Core imports required.
Demonstrates orchestration with minimal dependencies.
"""

import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

def main():
    print("🤝 IOA Core - Orchestration Demo (Standalone)")
    print("=" * 60)
    
    # Paths
    artifacts_dir = Path(__file__).parent.parent.parent / 'artifacts' / 'examples'
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Simulate 2 providers
    prompt = "Summarize IOA Core features for developers (no marketing, no PII)"
    print(f"🎯 Prompt: \"{prompt[:60]}...\"")
    print()
    
    # Simulate provider responses
    print("📡 Querying Providers...")
    responses = [
        {
            "provider": "MockProvider1",
            "model": "mock-v1",
            "response": "IOA Core provides multi-provider orchestration, governance, and evidence generation.",
            "response_time_ms": round(random.uniform(100, 300), 2),
            "compliant": True,
            "violations": []
        },
        {
            "provider": "MockProvider2",
            "model": "mock-v2",
            "response": "IOA Core offers governance enforcement and 4D memory tiering capabilities.",
            "response_time_ms": round(random.uniform(100, 300), 2),
            "compliant": True,
            "violations": []
        }
    ]
    
    for r in responses:
        print(f"   ✓ {r['provider']} ({r['response_time_ms']:.0f}ms) - Compliant")
    print()
    
    # Calculate consensus
    print("📊 Calculating Consensus...")
    compliant_count = sum(1 for r in responses if r['compliant'])
    consensus_pct = (compliant_count / len(responses)) * 100
    consensus_achieved = consensus_pct > 50
    
    print(f"   Compliant: {compliant_count}/{len(responses)} ({consensus_pct:.1f}%)")
    print(f"   Consensus: {'✅ Achieved' if consensus_achieved else '❌ Not Achieved'}")
    print()
    
    # Generate evidence
    print("📦 Generating Evidence Bundle...")
    evidence = {
        "demo": "round_table_standalone",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "orchestration": {
            "prompt": prompt,
            "providers_queried": [r['provider'] for r in responses],
            "total_providers": len(responses)
        },
        "consensus": {
            "total_providers": len(responses),
            "compliant_providers": compliant_count,
            "consensus_percentage": consensus_pct,
            "consensus_achieved": consensus_achieved
        },
        "responses": responses,
        "evidence_hash": ""
    }
    
    evidence_json = json.dumps(evidence, sort_keys=True)
    evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
    evidence["evidence_hash"] = evidence_hash
    
    evidence_file = artifacts_dir / 'rt_core_results.json'
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
        "signer": "ioa-core-orchestration-demo",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    sig_data = json.dumps(sig_payload, sort_keys=True).encode()
    signature = f"SIGv1:{hashlib.sha256(sig_data).hexdigest()}"
    sig_payload["signature"] = signature
    
    sig_file = artifacts_dir / 'rt_core_evidence.sig'
    with open(sig_file, 'w') as f:
        json.dump(sig_payload, f, indent=2)
    
    print(f"   Signature: {signature[:24]}...")
    print()
    
    # Generate report
    print("📊 Generating Report...")
    report = f"""# IOA Core - Orchestration Demo Report

**Generated:** {datetime.now(timezone.utc).isoformat()}

## Orchestration
- **Prompt:** {prompt}
- **Providers:** {len(responses)}

## Results
| Provider | Model | Time (ms) | Compliant |
|----------|-------|-----------|-----------|
"""
    
    for r in responses:
        report += f"| {r['provider']} | {r['model']} | {r['response_time_ms']:.0f} | {'✅' if r['compliant'] else '❌'} |\n"
    
    report += f"""
## Consensus
- **Compliant:** {compliant_count}/{len(responses)}
- **Percentage:** {consensus_pct:.1f}%
- **Result:** {'✅ Achieved' if consensus_achieved else '❌ Not Achieved'}

## Evidence
- **Hash:** `{evidence_hash}`
- **Signature:** `{signature[:64]}...`

## Conclusion
✅ Orchestration Demo Complete
"""
    
    report_file = artifacts_dir / 'rt_core_report.md'
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"   Report File: {report_file}")
    print()
    
    print("=" * 60)
    print("✅ Orchestration Demo Complete")
    print(f"Consensus: {consensus_pct:.1f}%")
    print(f"Artifacts: {artifacts_dir}")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

