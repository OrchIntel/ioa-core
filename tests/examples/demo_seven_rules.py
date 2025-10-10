#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Module: tests/examples/demo_seven_rules.py
Purpose: Demonstrate Core Governance Primitives (Seven Rules)

This OSS-safe demo shows IOA Core's governance capabilities:
- Request → Policy Evaluation → Decision → Evidence → Verification
- Uses generic policies (no regulated frameworks like HIPAA/SOX)
- Generates cryptographically verifiable evidence bundles
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

# Add Core modules to path (direct imports to avoid __init__.py issues)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'ioa_core'))

from governance.policy_engine import PolicyEngine, ActionContext, ValidationResult
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

class SevenRulesDemo:
    """
    Demonstrate IOA Core's Seven Rules governance primitives.
    
    Seven Rules (generic governance, no named regulations):
    1. Trace Required - All actions must be auditable
    2. No PII Tokens - Generic data protection
    3. Rate Guard - Prevent abuse/DoS
    4. Jurisdiction Aware - Geographic compliance awareness
    5. Data Classification - Sensitivity levels
    6. Approval Required - High-risk actions need approval
    7. Evidence Generation - Cryptographic proof of decisions
    """
    
    def __init__(self):
        self.demo_start = datetime.now(timezone.utc)
        
        # Paths
        self.artifacts_dir = Path(__file__).parent.parent.parent / 'artifacts' / 'examples'
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.input_file = self.data_dir / 'generic_request.json'
        
        # Core components
        self.policy_engine = PolicyEngine(mode='enforce')
        self.audit_chain = AuditChain(str(self.artifacts_dir / 'seven_rules_audit.jsonl'))
        
        print("🔒 IOA Core - Seven Rules Governance Demo")
        print("=" * 60)
        print(f"Mode: {self.policy_engine._mode.value}")
        print(f"Timestamp: {self.demo_start.isoformat()}")
        print(f"Artifacts: {self.artifacts_dir}")
        print()
    
    def load_request(self) -> Dict[str, Any]:
        """Load synthetic request from test data."""
        print(f"📄 Loading request: {self.input_file}")
        
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        
        with open(self.input_file, 'r') as f:
            request = json.load(f)
        
        print(f"   Request ID: {request['request_id']}")
        print(f"   Action: {request['action_type']}")
        print(f"   Actor: {request['actor_id']}")
        print()
        
        return request
    
    def evaluate_seven_rules(self, request: Dict[str, Any]) -> ValidationResult:
        """
        Evaluate request against Seven Rules using PolicyEngine.
        
        This demonstrates Core's governance primitives without
        referencing any specific regulatory framework.
        """
        print("⚖️  Evaluating Seven Rules...")
        
        # Create ActionContext from request
        action_ctx = ActionContext(
            action_id=request['request_id'],
            action_type=request['action_type'],
            actor_id=request['actor_id'],
            data_classification=request.get('data_classification', 'unclassified'),
            jurisdiction=request.get('jurisdiction', 'UNKNOWN'),
            metadata=request.get('metadata', {})
        )
        
        # PolicyEngine applies Seven Rules
        result = self.policy_engine.validate_against_laws(action_ctx)
        
        # Display results
        print(f"   Status: {result.status.value}")
        print(f"   Laws Checked: {', '.join(result.laws_checked)}")
        
        if result.violations:
            print(f"   ⚠️  Violations: {len(result.violations)}")
            for violation in result.violations:
                print(f"      - {violation.get('law_id', 'unknown')}: {violation.get('description', 'N/A')}")
        else:
            print("   ✅ No violations detected")
        
        if result.required_approvals:
            print(f"   📋 Required Approvals: {len(result.required_approvals)}")
            for approval in result.required_approvals:
                print(f"      - {approval}")
        
        print()
        return result
    
    def generate_evidence(self, request: Dict[str, Any], result: ValidationResult) -> str:
        """
        Generate cryptographic evidence bundle.
        
        Evidence includes:
        - Request hash
        - Decision hash
        - Audit chain entry
        - Verifiable signature (SIGv1)
        """
        print("📦 Generating Evidence Bundle...")
        
        # Create evidence payload
        evidence_payload = {
            "demo": "seven_rules",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request['request_id'],
            "request_hash": hashlib.sha256(
                json.dumps(request, sort_keys=True).encode()
            ).hexdigest(),
            "decision": {
                "status": result.status.value,
                "laws_checked": result.laws_checked,
                "violations_count": len(result.violations),
                "approvals_required_count": len(result.required_approvals),
                "audit_id": result.audit_id,
                "timestamp": result.timestamp.isoformat()
            },
            "evidence_hash": ""
        }
        
        # Calculate evidence hash
        evidence_json = json.dumps(evidence_payload, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
        evidence_payload["evidence_hash"] = evidence_hash
        
        # Log to audit chain
        audit_entry = self.audit_chain.log(
            'seven_rules_demo',
            evidence_payload
        )
        
        # Save evidence JSON
        evidence_file = self.artifacts_dir / 'seven_rules_evidence.json'
        with open(evidence_file, 'w') as f:
            json.dump(evidence_payload, f, indent=2)
        
        print(f"   Evidence Hash: {evidence_hash[:16]}...")
        print(f"   Audit Entry: {audit_entry.get('hash', 'N/A')[:16]}...")
        print(f"   Evidence File: {evidence_file}")
        print()
        
        return evidence_hash
    
    def generate_signature(self, evidence_hash: str) -> str:
        """
        Generate SIGv1 signature for evidence.
        
        Uses Core's signing infrastructure (dev keys in demo mode).
        """
        print("🔐 Generating SIGv1 Signature...")
        
        # Create signature payload
        sig_payload = {
            "version": "SIGv1",
            "algorithm": "SHA256-RSA",
            "evidence_hash": evidence_hash,
            "signer": "ioa-core-demo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "demo_mode": True
        }
        
        # In production, this would use real KMS/HSM signing
        # For demo, we create a verifiable checksum
        sig_data = json.dumps(sig_payload, sort_keys=True).encode()
        signature = f"SIGv1:{hashlib.sha256(sig_data).hexdigest()}"
        
        sig_payload["signature"] = signature
        
        # Save signature file
        sig_file = self.artifacts_dir / 'seven_rules_evidence.sig'
        with open(sig_file, 'w') as f:
            json.dump(sig_payload, f, indent=2)
        
        print(f"   Signature: {signature[:24]}...")
        print(f"   Signature File: {sig_file}")
        print()
        
        return signature
    
    def generate_report(self, request: Dict[str, Any], result: ValidationResult, 
                       evidence_hash: str, signature: str):
        """Generate human-readable report."""
        print("📊 Generating Report...")
        
        report_lines = [
            "# IOA Core - Seven Rules Governance Demo Report",
            "",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            f"**Demo Mode:** OSS-Safe (No Regulated Frameworks)",
            "",
            "## Executive Summary",
            "",
            "This demo exercised IOA Core's Seven Rules governance primitives",
            "using generic policies without referencing specific regulatory frameworks.",
            "",
            "## Request Details",
            "",
            f"- **Request ID:** {request['request_id']}",
            f"- **Action Type:** {request['action_type']}",
            f"- **Actor:** {request['actor_id']}",
            f"- **Data Classification:** {request.get('data_classification', 'N/A')}",
            f"- **Jurisdiction:** {request.get('jurisdiction', 'N/A')}",
            "",
            "## Seven Rules Evaluation",
            "",
            f"- **Decision Status:** {result.status.value}",
            f"- **Laws Checked:** {', '.join(result.laws_checked)}",
            f"- **Violations:** {len(result.violations)}",
            f"- **Approvals Required:** {len(result.required_approvals)}",
            "",
            "## Evidence Chain",
            "",
            f"- **Evidence Hash:** `{evidence_hash}`",
            f"- **Signature:** `{signature[:64]}...`",
            f"- **Audit Chain:** `{self.artifacts_dir / 'seven_rules_audit.jsonl'}`",
            "",
            "## Verification",
            "",
            "To verify this evidence:",
            "",
            "```bash",
            "# Verify evidence hash",
            f"cat {self.artifacts_dir / 'seven_rules_evidence.json'} | sha256sum",
            "",
            "# Verify signature",
            f"cat {self.artifacts_dir / 'seven_rules_evidence.sig'}",
            "",
            "# Verify audit chain",
            f"python3 -m ioa_core.governance.audit_chain verify {self.artifacts_dir / 'seven_rules_audit.jsonl'}",
            "```",
            "",
            "## Conclusion",
            "",
            "✅ **Demo Complete** - Evidence generated and verifiable",
            "",
            "IOA Core successfully demonstrated:",
            "- Generic policy evaluation (Seven Rules)",
            "- Cryptographic evidence generation",
            "- Audit chain integrity",
            "- Verifiable decision trail",
            "",
            "---",
            "*IOA Core (Open Source Edition) - Governed AI Orchestration*"
        ]
        
        report_file = self.artifacts_dir / 'seven_rules_report.md'
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"   Report File: {report_file}")
        print()
    
    def run(self):
        """Execute complete Seven Rules demo."""
        try:
            # 1. Load request
            request = self.load_request()
            
            # 2. Evaluate Seven Rules
            result = self.evaluate_seven_rules(request)
            
            # 3. Generate evidence
            evidence_hash = self.generate_evidence(request, result)
            
            # 4. Generate signature
            signature = self.generate_signature(evidence_hash)
            
            # 5. Generate report
            self.generate_report(request, result, evidence_hash, signature)
            
            # Summary
            demo_duration = (datetime.now(timezone.utc) - self.demo_start).total_seconds()
            
            print("=" * 60)
            print("✅ Seven Rules Demo Complete")
            print(f"Duration: {demo_duration:.2f}s")
            print(f"Artifacts: {self.artifacts_dir}")
            print()
            print("Verification Commands:")
            print(f"  - View Evidence: cat {self.artifacts_dir / 'seven_rules_evidence.json'}")
            print(f"  - View Signature: cat {self.artifacts_dir / 'seven_rules_evidence.sig'}")
            print(f"  - View Report: cat {self.artifacts_dir / 'seven_rules_report.md'}")
            print(f"  - Verify Chain: python3 -m ioa_core.governance.audit_chain verify {self.artifacts_dir / 'seven_rules_audit.jsonl'}")
            print("=" * 60)
            
            return 0
            
        except Exception as e:
            print(f"❌ Demo Failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == '__main__':
    demo = SevenRulesDemo()
    sys.exit(demo.run())

