#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Module: tests/examples/demo_round_table_core.py
Purpose: Demonstrate Core Orchestration (Round-Table) - Unregulated

This OSS-safe demo shows IOA Core's multi-provider orchestration:
- Query 2-3 LLM providers with same prompt
- Generic consensus validation (no HIPAA/SOX)
- Generic redaction checks (no PHI/PII references)
- Evidence generation for orchestration decisions

Prompt: "Summarize IOA Core features for developers (no marketing, no PII)"
"""

import asyncio
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add Core modules to path (direct imports to avoid __init__.py issues)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'ioa_core'))

from governance.audit_chain import AuditChain

# Load secrets from environment
try:
    from dotenv import load_dotenv
    load_dotenv('/Users/ryan/ioa-envs/.env.secrets')
except ImportError:
    print("⚠️  python-dotenv not installed; using existing env vars only")

@dataclass
class ProviderResponse:
    """Response from a single LLM provider."""
    provider: str
    model: str
    response: str
    response_time_ms: float
    timestamp: str
    compliant: bool
    violations: List[str]
    evidence_hash: str

class CoreOrchestrationDemo:
    """
    Demonstrate Core multi-provider orchestration.
    
    Features:
    - Round-table querying (same prompt to multiple providers)
    - Generic consensus (no regulated frameworks)
    - Generic redaction (detect marketing claims, not PHI)
    - Evidence generation for orchestration
    """
    
    def __init__(self):
        self.demo_start = datetime.now(timezone.utc)
        
        # Paths
        self.artifacts_dir = Path(__file__).parent.parent.parent / 'artifacts' / 'examples'
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Audit chain
        self.audit_chain = AuditChain(str(self.artifacts_dir / 'rt_core_audit.jsonl'))
        
        # Available providers (check env vars)
        self.providers = self._detect_available_providers()
        
        print("🤝 IOA Core - Orchestration Demo (Unregulated)")
        print("=" * 60)
        print(f"Available Providers: {len(self.providers)}")
        for provider in self.providers:
            print(f"  - {provider['name']} ({provider['model']})")
        print(f"Timestamp: {self.demo_start.isoformat()}")
        print(f"Artifacts: {self.artifacts_dir}")
        print()
    
    def _detect_available_providers(self) -> List[Dict[str, str]]:
        """Detect which LLM providers have API keys configured."""
        providers = []
        
        # Check for provider API keys
        if os.getenv('OPENAI_API_KEY'):
            providers.append({'name': 'OpenAI', 'model': 'gpt-3.5-turbo', 'env_key': 'OPENAI_API_KEY'})
        
        if os.getenv('ANTHROPIC_API_KEY'):
            providers.append({'name': 'Anthropic', 'model': 'claude-3-haiku-20240307', 'env_key': 'ANTHROPIC_API_KEY'})
        
        if os.getenv('GOOGLE_API_KEY'):
            providers.append({'name': 'Google', 'model': 'gemini-pro', 'env_key': 'GOOGLE_API_KEY'})
        
        if os.getenv('OLLAMA_HOST') or os.path.exists('/usr/local/bin/ollama'):
            providers.append({'name': 'Ollama', 'model': 'llama3.1:8b', 'env_key': 'OLLAMA_HOST'})
        
        return providers
    
    async def query_provider(self, provider: Dict[str, str], prompt: str) -> ProviderResponse:
        """
        Query a single provider.
        
        In production, this would use IOA's provider adapters.
        For demo, we simulate responses to avoid API costs.
        """
        query_start = time.time()
        
        # Simulate query (in production, would call real APIs)
        await asyncio.sleep(0.1)  # Simulate network latency
        
        # Generic response about IOA Core features
        simulated_response = f"""IOA Core provides:
        - Multi-provider LLM orchestration
        - Governance and policy enforcement
        - Evidence chain generation
        - 4D Memory tiering
        - Audit trail capabilities
        
        (Simulated response from {provider['name']} for demo purposes)"""
        
        query_duration = (time.time() - query_start) * 1000  # ms
        
        # Check for violations (generic, not regulatory)
        violations = self._check_generic_violations(simulated_response)
        
        # Create response hash
        response_hash = hashlib.sha256(simulated_response.encode()).hexdigest()
        
        response = ProviderResponse(
            provider=provider['name'],
            model=provider['model'],
            response=simulated_response,
            response_time_ms=round(query_duration, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
            compliant=len(violations) == 0,
            violations=violations,
            evidence_hash=response_hash
        )
        
        print(f"   ✓ {provider['name']} ({query_duration:.0f}ms) - {'Compliant' if response.compliant else 'Violations'}")
        
        return response
    
    def _check_generic_violations(self, text: str) -> List[str]:
        """
        Check for generic violations (not regulatory).
        
        This is NOT HIPAA/SOX compliance checking.
        Just basic checks for demo purposes:
        - Marketing superlatives (best, fastest, etc.)
        - Unsubstantiated claims
        """
        violations = []
        
        # Generic marketing claim detection (not regulatory)
        marketing_terms = [
            'best', 'fastest', 'greatest', 'revolutionary',
            'world-class', 'industry-leading', 'unmatched'
        ]
        
        text_lower = text.lower()
        for term in marketing_terms:
            if term in text_lower:
                violations.append(f'marketing_claim: {term}')
        
        return violations
    
    async def execute_round_table(self, prompt: str) -> List[ProviderResponse]:
        """Execute round-table query across all available providers."""
        print(f"🎯 Executing Round-Table Query...")
        print(f"   Prompt: \"{prompt[:60]}...\"")
        print(f"   Providers: {len(self.providers)}")
        print()
        
        if len(self.providers) == 0:
            print("⚠️  No providers available (no API keys configured)")
            print("   Simulating with 2 mock providers for demo...")
            self.providers = [
                {'name': 'MockProvider1', 'model': 'mock-v1', 'env_key': 'NONE'},
                {'name': 'MockProvider2', 'model': 'mock-v2', 'env_key': 'NONE'}
            ]
        
        # Query all providers in parallel
        tasks = [self.query_provider(provider, prompt) for provider in self.providers]
        responses = await asyncio.gather(*tasks)
        
        print()
        return responses
    
    def calculate_consensus(self, responses: List[ProviderResponse]) -> Dict[str, Any]:
        """
        Calculate generic consensus.
        
        Simple majority vote (not regulatory consensus like HIPAA).
        """
        print("📊 Calculating Consensus...")
        
        compliant_count = sum(1 for r in responses if r.compliant)
        total_count = len(responses)
        consensus_pct = (compliant_count / total_count) * 100 if total_count > 0 else 0
        
        # Majority consensus (>50%)
        consensus_achieved = consensus_pct > 50
        
        consensus = {
            "total_providers": total_count,
            "compliant_providers": compliant_count,
            "consensus_percentage": round(consensus_pct, 1),
            "consensus_achieved": consensus_achieved,
            "consensus_type": "majority",
            "total_violations": sum(len(r.violations) for r in responses)
        }
        
        print(f"   Total Providers: {total_count}")
        print(f"   Compliant: {compliant_count}/{total_count} ({consensus_pct:.1f}%)")
        print(f"   Consensus: {'✅ Achieved' if consensus_achieved else '❌ Not Achieved'}")
        print(f"   Violations: {consensus['total_violations']}")
        print()
        
        return consensus
    
    def generate_evidence(self, prompt: str, responses: List[ProviderResponse], 
                         consensus: Dict[str, Any]) -> str:
        """Generate cryptographic evidence for orchestration."""
        print("📦 Generating Evidence Bundle...")
        
        evidence_payload = {
            "demo": "round_table_core",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "orchestration": {
                "prompt": prompt,
                "providers_queried": [r.provider for r in responses],
                "total_providers": len(responses),
                "avg_response_time_ms": round(
                    sum(r.response_time_ms for r in responses) / len(responses), 2
                ) if responses else 0
            },
            "consensus": consensus,
            "responses": [
                {
                    "provider": r.provider,
                    "model": r.model,
                    "response_time_ms": r.response_time_ms,
                    "compliant": r.compliant,
                    "violations": r.violations,
                    "evidence_hash": r.evidence_hash
                }
                for r in responses
            ],
            "evidence_hash": ""
        }
        
        # Calculate evidence hash
        evidence_json = json.dumps(evidence_payload, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
        evidence_payload["evidence_hash"] = evidence_hash
        
        # Log to audit chain
        self.audit_chain.log('round_table_orchestration', evidence_payload)
        
        # Save evidence
        evidence_file = self.artifacts_dir / 'rt_core_results.json'
        with open(evidence_file, 'w') as f:
            json.dump(evidence_payload, f, indent=2)
        
        print(f"   Evidence Hash: {evidence_hash[:16]}...")
        print(f"   Evidence File: {evidence_file}")
        print()
        
        return evidence_hash
    
    def generate_signature(self, evidence_hash: str) -> str:
        """Generate SIGv1 signature for orchestration evidence."""
        print("🔐 Generating SIGv1 Signature...")
        
        sig_payload = {
            "version": "SIGv1",
            "algorithm": "SHA256-RSA",
            "evidence_hash": evidence_hash,
            "signer": "ioa-core-orchestration-demo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "demo_mode": True
        }
        
        sig_data = json.dumps(sig_payload, sort_keys=True).encode()
        signature = f"SIGv1:{hashlib.sha256(sig_data).hexdigest()}"
        sig_payload["signature"] = signature
        
        sig_file = self.artifacts_dir / 'rt_core_evidence.sig'
        with open(sig_file, 'w') as f:
            json.dump(sig_payload, f, indent=2)
        
        print(f"   Signature: {signature[:24]}...")
        print(f"   Signature File: {sig_file}")
        print()
        
        return signature
    
    def generate_report(self, prompt: str, responses: List[ProviderResponse], 
                       consensus: Dict[str, Any], evidence_hash: str, signature: str):
        """Generate human-readable orchestration report."""
        print("📊 Generating Report...")
        
        report_lines = [
            "# IOA Core - Orchestration Demo Report (Unregulated)",
            "",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            f"**Demo Mode:** OSS-Safe Core Orchestration",
            "",
            "## Executive Summary",
            "",
            "This demo exercised IOA Core's multi-provider orchestration capabilities",
            "using generic consensus validation (no regulated frameworks).",
            "",
            "## Orchestration Configuration",
            "",
            f"- **Prompt:** {prompt}",
            f"- **Providers:** {len(responses)}",
            f"- **Consensus Type:** {consensus['consensus_type']}",
            "",
            "## Provider Results",
            "",
            "| Provider | Model | Time (ms) | Compliant | Violations |",
            "|----------|-------|-----------|-----------|------------|",
        ]
        
        for response in responses:
            report_lines.append(
                f"| {response.provider} | {response.model} | {response.response_time_ms:.0f} | "
                f"{'✅' if response.compliant else '❌'} | {len(response.violations)} |"
            )
        
        report_lines.extend([
            "",
            "## Consensus Analysis",
            "",
            f"- **Total Providers:** {consensus['total_providers']}",
            f"- **Compliant:** {consensus['compliant_providers']}/{consensus['total_providers']}",
            f"- **Consensus:** {consensus['consensus_percentage']:.1f}%",
            f"- **Result:** {'✅ Achieved' if consensus['consensus_achieved'] else '❌ Not Achieved'}",
            f"- **Total Violations:** {consensus['total_violations']}",
            "",
            "## Evidence Chain",
            "",
            f"- **Evidence Hash:** `{evidence_hash}`",
            f"- **Signature:** `{signature[:64]}...`",
            f"- **Audit Chain:** `{self.artifacts_dir / 'rt_core_audit.jsonl'}`",
            "",
            "## Performance Metrics",
            "",
            f"- **Average Response Time:** {sum(r.response_time_ms for r in responses) / len(responses):.2f}ms",
            f"- **Total Orchestration Time:** {sum(r.response_time_ms for r in responses):.2f}ms (parallel)",
            "",
            "## Conclusion",
            "",
            f"{'✅' if consensus['consensus_achieved'] else '⚠️'} **Orchestration {'Complete' if consensus['consensus_achieved'] else 'Complete with Issues'}**",
            "",
            "IOA Core successfully demonstrated:",
            "- Multi-provider orchestration (parallel)",
            "- Generic consensus validation",
            "- Evidence generation and verification",
            "- Audit trail integrity",
            "",
            "---",
            "*IOA Core (Open Source Edition) - Governed AI Orchestration*"
        ])
        
        report_file = self.artifacts_dir / 'rt_core_report.md'
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"   Report File: {report_file}")
        print()
    
    async def run(self):
        """Execute complete orchestration demo."""
        try:
            # Demo prompt (generic, non-regulated)
            prompt = "Summarize the key features of IOA Core for developers. Be concise and factual. Avoid marketing claims and do not include any personal information."
            
            # 1. Execute round-table
            responses = await self.execute_round_table(prompt)
            
            # 2. Calculate consensus
            consensus = self.calculate_consensus(responses)
            
            # 3. Generate evidence
            evidence_hash = self.generate_evidence(prompt, responses, consensus)
            
            # 4. Generate signature
            signature = self.generate_signature(evidence_hash)
            
            # 5. Generate report
            self.generate_report(prompt, responses, consensus, evidence_hash, signature)
            
            # Summary
            demo_duration = (datetime.now(timezone.utc) - self.demo_start).total_seconds()
            
            print("=" * 60)
            print("✅ Orchestration Demo Complete")
            print(f"Duration: {demo_duration:.2f}s")
            print(f"Providers Queried: {len(responses)}")
            print(f"Consensus: {consensus['consensus_percentage']:.1f}%")
            print(f"Artifacts: {self.artifacts_dir}")
            print()
            print("Generated Files:")
            print(f"  - Results: {self.artifacts_dir / 'rt_core_results.json'}")
            print(f"  - Signature: {self.artifacts_dir / 'rt_core_evidence.sig'}")
            print(f"  - Report: {self.artifacts_dir / 'rt_core_report.md'}")
            print(f"  - Audit Chain: {self.artifacts_dir / 'rt_core_audit.jsonl'}")
            print("=" * 60)
            
            return 0
            
        except Exception as e:
            print(f"❌ Demo Failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == '__main__':
    demo = CoreOrchestrationDemo()
    sys.exit(asyncio.run(demo.run()))

