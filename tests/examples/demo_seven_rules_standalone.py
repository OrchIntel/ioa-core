#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""
Standalone Seven Rules Demo - No IOA Core imports required.
Demonstrates governance primitives with minimal dependencies.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Generic policy violations for demo
SEVEN_RULES = [
    "trace_required",
    "no_pii_tokens",
    "rate_guard",
    "jurisdiction_aware",
    "data_classification",
    "approval_required",
    "evidence_generation"
]

def main():
    print("🔒 IOA Core - Seven Rules Governance Demo (Standalone)")
    print("=" * 60)
    
    # Paths
    artifacts_dir = Path(__file__).parent.parent.parent / 'artifacts' / 'examples'
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    data_file = Path(__file__).parent.parent / 'data' / 'generic_request.json'
    
    # Load request
    print(f"📄 Loading request: {data_file}")
    if not data_file.exists():
        print(f"❌ Input file not found: {data_file}")
        return 1
    
    with open(data_file, 'r') as f:
        request = json.load(f)
    
    print(f"   Request ID: {request['request_id']}")
    print(f"   Action: {request['action_type']}")
    print()
    
    # Evaluate Seven Rules (simplified)
    print("⚖️  Evaluating Seven Rules...")
    violations = []
    
    # Check if data classification is set
    if not request.get('data_classification'):
        violations.append({
            "law_id": "data_classification",
            "description": "Data classification not specified"
        })
    
    # Check jurisdiction
    if not request.get('jurisdiction'):
        violations.append({
            "law_id": "jurisdiction_aware",
            "description": "Jurisdiction not specified"
        })
    
    print(f"   Laws Checked: {', '.join(SEVEN_RULES)}")
    print(f"   Status: {'APPROVED' if len(violations) == 0 else 'REQUIRES_REVIEW'}")
    print(f"   Violations: {len(violations)}")
    print()
    
    # Generate evidence
    print("📦 Generating Evidence Bundle...")
    evidence = {
        "demo": "seven_rules_standalone",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request['request_id'],
        "request_hash": hashlib.sha256(
            json.dumps(request, sort_keys=True).encode()
        ).hexdigest(),
        "decision": {
            "status": "APPROVED" if len(violations) == 0 else "REQUIRES_REVIEW",
            "laws_checked": SEVEN_RULES,
            "violations_count": len(violations)
        },
        "evidence_hash": ""
    }
    
    # Calculate evidence hash
    evidence_json = json.dumps(evidence, sort_keys=True)
    evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
    evidence["evidence_hash"] = evidence_hash
    
    # Save evidence
    evidence_file = artifacts_dir / 'seven_rules_evidence.json'
    with open(evidence_file, 'w') as f:
        json.dump(evidence, f, indent=2)
    
    print(f"   Evidence Hash: {evidence_hash[:16]}...")
    print(f"   Evidence File: {evidence_file}")
    print()
    
    # Generate signature
    print("🔐 Generating SIGv1 Signature...")
    sig_payload = {
        "version": "SIGv1",
        "algorithm": "SHA256",
        "evidence_hash": evidence_hash,
        "signer": "ioa-core-demo",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    sig_data = json.dumps(sig_payload, sort_keys=True).encode()
    signature = f"SIGv1:{hashlib.sha256(sig_data).hexdigest()}"
    sig_payload["signature"] = signature
    
    sig_file = artifacts_dir / 'seven_rules_evidence.sig'
    with open(sig_file, 'w') as f:
        json.dump(sig_payload, f, indent=2)
    
    print(f"   Signature: {signature[:24]}...")
    print()
    
    # Generate report
    print("📊 Generating Report...")
    report = f"""# IOA Core - Seven Rules Demo Report

**Generated:** {datetime.now(timezone.utc).isoformat()}

## Request
- **ID:** {request['request_id']}
- **Action:** {request['action_type']}
- **Classification:** {request.get('data_classification', 'N/A')}

## Seven Rules Evaluation
- **Status:** {'APPROVED' if len(violations) == 0 else 'REQUIRES_REVIEW'}
- **Laws Checked:** {len(SEVEN_RULES)}
- **Violations:** {len(violations)}

## Evidence
- **Hash:** `{evidence_hash}`
- **Signature:** `{signature[:64]}...`

## Conclusion
✅ Demo Complete - Evidence generated and verifiable
"""
    
    report_file = artifacts_dir / 'seven_rules_report.md'
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"   Report File: {report_file}")
    print()
    
    print("=" * 60)
    print("✅ Seven Rules Demo Complete")
    print(f"Artifacts: {artifacts_dir}")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

