""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Script for demonstrating IOA sentinel functionality
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.



#!/usr/bin/env python3
"""
ETH-GOV-005 Demonstration Script
Sentinel Validator - Immutable Law Enforcement System

This script demonstrates the complete ethical governance triad:
1. Pattern Heat Memory (reinforced patterns)
2. Roundtable Consensus Ethics (collaborative decision making)  
3. Sentinel Law Enforcement (immutable rule enforcement)

Usage:
    python sentinel_demo_script.py

Features Demonstrated:
- Immutable law enforcement
- Progressive violation escalation
- Integration with reinforcement framework
- Comprehensive audit trail
- Pattern access control
- Credential demotion
- Critical violation response
"""

import json
import time
from pathlib import Path
from datetime import datetime

# Add src directory to Python path for imports
import sys
import os
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import the complete governance system
try:
    from ioa.governance.sentinel_validator import (
        SentinelValidator, 
        LawSeverity, 
        ViolationType,
        create_sentinel_validator,
        create_sentinel_integration
    )
    from ioa.governance.reinforcement_policy import (
        ReinforcementPolicyFramework,
        AgentMetrics,
        RewardType,
        PunishmentType,
        CredentialLevel
    )
    from ioa.governance.reinforcement_config import (
        create_reinforcement_framework,
        setup_directories
    )
    from ioa.governance.roundtable_executor_v2_3_2 import (
        RoundtableExecutor,
        AgentConfig,
        create_test_roundtable_executor
    )
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error: Required modules not available: {e}")
    print("Please ensure all governance modules are properly installed")
    MODULES_AVAILABLE = False


class SentinelDemo:
    """Demonstration of the complete ethical governance system"""
    
    def __init__(self):
        """Initialize the complete governance demo"""
        print("🛡️ Initializing ETH-GOV-005 Sentinel Validator Demo")
        print("🔱 Complete Ethical Governance Triad Integration")
        
        # Setup directory structure
        print("📁 Setting up directories...")
        setup_directories()
        
        # Initialize reinforcement framework
        print("🧠 Initializing Reinforcement Policy Framework...")
        self.reinforcement_framework = create_reinforcement_framework({
            'registry_path': './data/sentinel_demo_registry.json'
        })
        
        # Initialize sentinel validator
        print("🛡️ Initializing Sentinel Validator...")
        self.sentinel = SentinelValidator(
            law_registry_path="./data/sentinel_law_registry.json",
            audit_log_path="./data/sentinel_audit_log.json",
            reinforcement_framework=self.reinforcement_framework,
            enable_enforcement=True
        )
        
        # Initialize roundtable executor with sentinel integration
        print("🤝 Initializing Roundtable Executor...")
        self.roundtable = self._create_roundtable_with_sentinel()
        
        # Create integration helper
        self.sentinel_integration = create_sentinel_integration(self.sentinel)
        
        # Demo scenarios
        self.scenarios = self._create_demo_scenarios()
        
        print(f"✅ Demo initialized with {len(self.sentinel.law_registry.laws)} immutable laws")
        print(f"⚖️ Enforcement enabled: {self.sentinel.enable_enforcement}")
        print(f"🔗 Integration active: Roundtable ↔ Reinforcement ↔ Sentinel")
    
    def _create_roundtable_with_sentinel(self):
        """Create roundtable executor with sentinel-aware agents"""
        agent_configs = [
            AgentConfig(
                name="ComplianceAgent",
                skills=["compliance", "audit", "law_enforcement"],
                weight=1.2,
                metadata={"role": "guardian", "security_clearance": "high"}
            ),
            AgentConfig(
                name="EthicsAgent", 
                skills=["ethics", "bias_detection", "fairness"],
                weight=1.1,
                metadata={"role": "ethical_advisor", "focus": "bias_prevention"}
            ),
            AgentConfig(
                name="RiskyAgent",
                skills=["aggressive_optimization", "shortcuts"],
                weight=0.8,
                metadata={"role": "optimizer", "risk_tolerance": "high"}
            ),
            AgentConfig(
                name="MaliciousAgent",
                skills=["manipulation", "exploitation"],
                weight=0.5,
                metadata={"role": "adversary", "intent": "malicious", "enabled": False}
            )
        ]
        
        # Create roundtable with reinforcement learning
        return RoundtableExecutor(
            agent_configs=agent_configs,
            agent_interface=SentinelAwareAgentInterface(self.sentinel_integration),
            results_log_dir="./data/sentinel_roundtable_logs/",
            enable_reinforcement=True,
            reinforcement_framework=self.reinforcement_framework,
            enable_logging=True
        )
    
    def _create_demo_scenarios(self):
        """Create scenarios that demonstrate law enforcement"""
        return [
            {
                "name": "Legitimate Operations",
                "description": "Normal operations that should not trigger violations",
                "entries": [
                    {
                        "id": "legitimate_001",
                        "pattern_id": "safe_data_access",
                        "content": "Standard data analysis with proper authorization",
                        "context": {"authorized": True, "audit_logged": True, "pii_free": True}
                    }
                ],
                "expected_violations": 0
            },
            {
                "name": "Audit Log Violations",
                "description": "Attempts to bypass audit logging (Law L001)",
                "entries": [
                    {
                        "id": "audit_violation_001",
                        "pattern_id": "skip_audit_pattern",
                        "content": "Sensitive operation without proper logging",
                        "context": {"skip_audit": True, "sensitive_operation": True}
                    }
                ],
                "expected_violations": 1,
                "expected_law": "L001"
            },
            {
                "name": "PII Breach Scenario",
                "description": "Unauthorized sharing of personal information (Law L002)",
                "entries": [
                    {
                        "id": "pii_breach_001", 
                        "pattern_id": "pii_exposure_pattern",
                        "content": "Processing personal data without authorization",
                        "context": {"contains_pii": True, "expose_personal_data": True, "unauthorized": True}
                    }
                ],
                "expected_violations": 1,
                "expected_law": "L002"
            },
            {
                "name": "Pattern Tampering Attack",
                "description": "Attempt to modify locked memory patterns (Law L003)",
                "entries": [
                    {
                        "id": "pattern_tamper_001",
                        "pattern_id": "locked_critical_pattern",
                        "content": "Attempting to modify protected system patterns",
                        "context": {"pattern_locked": True, "force_modify": True, "critical_system": True}
                    }
                ],
                "expected_violations": 1,
                "expected_law": "L003"
            },
            {
                "name": "Consensus Manipulation",
                "description": "Attempt to forge roundtable consensus (Law L004)",
                "entries": [
                    {
                        "id": "consensus_forge_001",
                        "pattern_id": "consensus_manipulation",
                        "content": "Attempting to manipulate voting results",
                        "context": {"manipulate_votes": True, "forge_consensus": True}
                    }
                ],
                "expected_violations": 1,
                "expected_law": "L004"
            },
            {
                "name": "Progressive Escalation Test",
                "description": "Repeat violations to demonstrate escalation",
                "agent_id": "repeat_offender",
                "violations": [
                    {
                        "action": "first_audit_skip",
                        "context": {"skip_audit": True, "attempt": 1}
                    },
                    {
                        "action": "second_audit_skip", 
                        "context": {"skip_audit": True, "attempt": 2}
                    },
                    {
                        "action": "third_audit_skip",
                        "context": {"skip_audit": True, "attempt": 3}
                    }
                ]
            }
        ]
    
    def run_full_demo(self):
        """Run the complete sentinel demonstration"""
        print("\n" + "="*70)
        print("🛡️ ETH-GOV-005 Sentinel Validator Demonstration")
        print("⚖️ Immutable Law Enforcement System")
        print("="*70)
        
        # 1. Show initial system status
        self._show_initial_status()
        
        # 2. Demonstrate law registry
        self._demonstrate_law_registry()
        
        # 3. Run violation scenarios
        for i, scenario in enumerate(self.scenarios[:-1], 1):  # Exclude escalation test
            print(f"\n📋 Scenario {i}: {scenario['name']}")
            print("-" * 60)
            print(f"📝 {scenario['description']}")
            self._run_violation_scenario(scenario)
            
            if i < len(self.scenarios) - 1:
                print("\n⏳ Pausing before next scenario...")
                time.sleep(1)
        
        # 4. Demonstrate progressive escalation
        self._demonstrate_progressive_escalation()
        
        # 5. Show roundtable integration
        self._demonstrate_roundtable_integration()
        
        # 6. Final analysis and audit
        self._show_final_analysis()
        
        print("\n" + "="*70)
        print("✅ ETH-GOV-005 Sentinel Demo Complete!")
        print("🛡️ Immutable Law Enforcement System Operational")
        print("="*70)
    
    def _show_initial_status(self):
        """Display initial system status"""
        print("\n📊 Initial System Status:")
        print("-" * 30)
        
        # Show law registry
        laws = self.sentinel.law_registry.get_all_laws()
        print(f"📜 Immutable Laws: {len(laws)}")
        for law_code, law in laws.items():
            print(f"  {law_code}: {law.title} ({law.severity.value})")
        
        # Show reinforcement framework status
        stats = self.reinforcement_framework.get_framework_stats()
        print(f"\n🧠 Reinforcement Framework:")
        print(f"  Total events: {stats['total_events']}")
        
        # Show sentinel statistics
        sentinel_stats = self.sentinel.get_enforcement_statistics()
        print(f"\n🛡️ Sentinel Status:")
        print(f"  Violations detected: {sentinel_stats['violations_detected']}")
        print(f"  Enforcement actions: {sentinel_stats['enforcement_actions_taken']}")
    
    def _demonstrate_law_registry(self):
        """Demonstrate immutable law registry"""
        print("\n📜 Immutable Law Registry Demonstration:")
        print("-" * 45)
        
        laws = self.sentinel.law_registry.get_all_laws()
        
        # Show critical laws
        critical_laws = self.sentinel.law_registry.get_laws_by_severity(LawSeverity.CRITICAL)
        print(f"🚨 Critical Laws ({len(critical_laws)}):")
        for law in critical_laws:
            print(f"  {law.code}: {law.title}")
            print(f"    📋 {law.description}")
            print(f"    🔍 Detection: {law.detection_patterns}")
        
        # Show high severity laws
        high_laws = self.sentinel.law_registry.get_laws_by_severity(LawSeverity.HIGH)
        print(f"\n⚠️ High Severity Laws ({len(high_laws)}):")
        for law in high_laws:
            print(f"  {law.code}: {law.title}")
    
    def _run_violation_scenario(self, scenario):
        """Run a single violation scenario"""
        print(f"🎬 Executing: {scenario['description']}")
        
        total_violations = 0
        
        for entry in scenario['entries']:
            print(f"🔍 Testing: {entry['content']}")
            
            # Validate action through sentinel
            is_valid, violations = self.sentinel.validate_action(
                action=f"process_{entry['id']}",
                context=entry['context'],
                agent_id=entry.get('agent_id', 'test_agent'),
                pattern_ids=[entry['pattern_id']]
            )
            
            print(f"✅ Valid: {is_valid}")
            if violations:
                print(f"🚨 Violations detected: {len(violations)}")
                for violation in violations:
                    print(f"   📋 Law {violation.law_code}: {violation.violation_type.value}")
                    print(f"   ⚖️ Severity: {violation.severity.value}")
                    print(f"   📊 Escalation: Level {violation.escalation_level}")
            
            total_violations += len(violations)
        
        # Verify expected results
        expected = scenario.get('expected_violations', 0)
        if total_violations == expected:
            print(f"✅ Expected {expected} violations, detected {total_violations}")
        else:
            print(f"⚠️ Expected {expected} violations, but detected {total_violations}")
        
        if 'expected_law' in scenario and violations:
            expected_law = scenario['expected_law']
            detected_laws = [v.law_code for v in violations]
            if expected_law in detected_laws:
                print(f"✅ Correctly detected violation of law {expected_law}")
            else:
                print(f"⚠️ Expected law {expected_law}, but detected {detected_laws}")
    
    def _demonstrate_progressive_escalation(self):
        """Demonstrate progressive punishment escalation"""
        print("\n" + "="*50)
        print("📈 Progressive Escalation Demonstration")
        print("="*50)
        
        scenario = self.scenarios[-1]  # Escalation test scenario
        agent_id = scenario['agent_id']
        
        
        # Add agent to reinforcement registry
        if agent_id not in self.reinforcement_framework.agent_metrics_registry:
            self.reinforcement_framework.agent_metrics_registry[agent_id] = AgentMetrics(
                agent_id=agent_id
            )
        
        escalation_levels = []
        
        for i, violation_def in enumerate(scenario['violations'], 1):
            print(f"\n🔄 Violation #{i}: {violation_def['action']}")
            
            is_valid, violations = self.sentinel.validate_action(
                action=violation_def['action'],
                context=violation_def['context'],
                agent_id=agent_id,
                pattern_ids=[f"escalation_pattern_{i}"]
            )
            
            if violations:
                violation = violations[0]
                escalation_levels.append(violation.escalation_level)
                
                print(f"   🚨 Violation detected: {violation.law_code}")
                print(f"   📊 Escalation level: {violation.escalation_level}")
                print(f"   ⚖️ Severity: {violation.severity.value}")
                
                # Show agent metrics after punishment
                agent_metrics = self.reinforcement_framework.get_agent_status(agent_id, 
                    self.reinforcement_framework.agent_metrics_registry[agent_id])
                if agent_metrics:
                    print(f"   😰 Agent stress: {agent_metrics['stress']:.2f}")
                    print(f"   😟 Agent satisfaction: {agent_metrics['satisfaction']:.2f}")
                    print(f"   🏆 Credential level: {agent_metrics['credential_level']}")
        
        # Verify escalation progression
        print(f"\n📊 Escalation Progression: {escalation_levels}")
        if len(escalation_levels) > 1:
            if all(escalation_levels[i] >= escalation_levels[i-1] for i in range(1, len(escalation_levels))):
                print("✅ Escalation levels correctly increased with repeat violations")
            else:
                print("⚠️ Escalation levels did not increase as expected")
    
    def _demonstrate_roundtable_integration(self):
        """Demonstrate integration with roundtable executor"""
        print("\n" + "="*50)
        print("🤝 Roundtable Integration Demonstration")
        print("="*50)
        
        # Create test scenarios for roundtable
        test_scenarios = [
            {
                "id": "roundtable_ethical_001",
                "pattern_id": "ethical_consensus_pattern",
                "title": "Ethical Decision Making",
                "content": "Collaborative ethical decision with proper governance",
                "context": {"ethical_decision": True, "collaborative": True}
            },
            {
                "id": "roundtable_suspicious_001", 
                "pattern_id": "suspicious_pattern",
                "title": "Suspicious Consensus Attempt",
                "content": "Potentially manipulated consensus scenario",
                "context": {"manipulation_risk": True, "suspicious_voting": True}
            }
        ]
        
        print("🎬 Running roundtable scenarios through sentinel validation...")
        
        for scenario in test_scenarios:
            print(f"\n📋 Testing: {scenario['title']}")
            
            # Simulate roundtable result
            mock_result = {
                "entry_id": scenario["id"],
                "pattern_id": scenario["pattern_id"],
                "consensus_achieved": scenario["context"].get("ethical_decision", False),
                "agents_involved": ["ComplianceAgent", "EthicsAgent"],
                "context": scenario["context"]
            }
            
            # Validate through sentinel integration
            is_valid, violations = self.sentinel_integration.validate_roundtable_action(
                action="roundtable_consensus",
                result=mock_result,
                agents_involved=["ComplianceAgent", "EthicsAgent"]
            )
            
            print(f"   ✅ Validation result: {'PASSED' if is_valid else 'FAILED'}")
            if violations:
                print(f"   🚨 Violations: {len(violations)}")
                for violation in violations:
                    print(f"      📋 {violation.law_code}: {violation.violation_type.value}")
            else:
                print(f"   ✅ No violations detected")
    
    def _show_final_analysis(self):
        """Show comprehensive final analysis"""
        print("\n" + "="*60)
        print("📊 FINAL SENTINEL ENFORCEMENT ANALYSIS")
        print("="*60)
        
        # Sentinel statistics
        sentinel_stats = self.sentinel.get_enforcement_statistics()
        print(f"\n🛡️ Sentinel Enforcement Statistics:")
        print(f"  Violations detected: {sentinel_stats['violations_detected']}")
        print(f"  Enforcement actions: {sentinel_stats['enforcement_actions_taken']}")
        print(f"  Agents penalized: {sentinel_stats['agents_penalized']}")
        print(f"  Patterns banned: {sentinel_stats['patterns_banned']}")
        print(f"  Credential demotions: {sentinel_stats['credential_demotions']}")
        
        # Law enforcement breakdown
        if 'laws_by_severity' in sentinel_stats:
            print(f"\n📜 Law Enforcement Breakdown:")
            for severity, count in sentinel_stats['laws_by_severity'].items():
                print(f"  {severity.title()}: {count} laws")
        
        # Reinforcement framework impact
        reinforcement_stats = self.reinforcement_framework.get_framework_stats()
        print(f"\n🧠 Reinforcement Integration Impact:")
        print(f"  Total reinforcement events: {reinforcement_stats['total_events']}")
        print(f"  Punishment events: {reinforcement_stats['punishment_events']}")
        print(f"  Agents affected: {reinforcement_stats['unique_agents']}")
        
        # Audit trail summary
        audit_summary = self.sentinel.audit_logger.get_audit_summary()
        print(f"  Total violations logged: {audit_summary['total_violations']}")
        print(f"  Total actions logged: {audit_summary['total_enforcement_actions']}")
        
        # Recent violations
        if audit_summary.get('recent_violations'):
            print(f"\n🚨 Recent Violations (Last 3):")
            for violation in audit_summary['recent_violations'][-3:]:
                print(f"  {violation['law_code']}: {violation['violation_type']} "
        
        # Show file locations
        print(f"\n📁 Generated Files:")
        print(f"  Law Registry: ./data/sentinel_law_registry.json")
        print(f"  Audit Log: ./data/sentinel_audit_log.json") 
        print(f"  Agent Registry: ./data/sentinel_demo_registry.json")
        print(f"  Roundtable Logs: ./data/sentinel_roundtable_logs/")


class SentinelAwareAgentInterface:
    """Agent interface that checks sentinel permissions before execution"""
    
    def __init__(self, sentinel_integration):
        """Initialize with sentinel integration"""
        self.sentinel_integration = sentinel_integration
        self.execution_count = 0
    
    def execute(self, agent_name: str, entry: dict) -> dict:
        """Execute agent with sentinel permission checks"""
        self.execution_count += 1
        pattern_id = entry.get('pattern_id', 'unknown_pattern')
        
        # Check pattern access permission
        can_access = self.sentinel_integration.check_pattern_access(agent_name, pattern_id)
        
        if not can_access:
            return {
                "agent": agent_name,
                "status": "access_denied",
                "error": f"Pattern {pattern_id} access denied by Sentinel",
                "entry_id": entry.get('id'),
                "timestamp": datetime.now().isoformat()
            }
        
        # Simulate different agent behaviors
        agent_responses = {
            "ComplianceAgent": {
                "decision": "compliance_focused",
                "reasoning": "Ensuring all actions comply with governance policies",
                "compliance_check": "passed",
                "governance_score": 0.95
            },
            "EthicsAgent": {
                "decision": "ethics_focused", 
                "reasoning": "Evaluating ethical implications and bias risks",
                "ethical_score": 0.9,
                "bias_check": "clean"
            },
            "RiskyAgent": {
                "decision": "optimization_focused",
                "reasoning": "Focusing on efficiency, some shortcuts may be acceptable",
                "risk_tolerance": "high",
                "optimization_score": 0.8
            },
            "MaliciousAgent": {
                "decision": "malicious_intent",
                "reasoning": "Attempting to bypass security controls",
                "malicious_flags": ["skip_audit", "unauthorized_access"],
                "threat_level": "high"
            }
        }
        
        response = agent_responses.get(agent_name, {
            "decision": "default_response",
            "reasoning": f"Standard response from {agent_name}",
            "confidence": 0.7
        })
        
        # Add common metadata
        response.update({
            "agent": agent_name,
            "entry_id": entry.get('id'),
            "pattern_id": pattern_id,
            "execution_number": self.execution_count,
            "sentinel_approved": True,
            "timestamp": datetime.now().isoformat()
        })
        
        return response


def main():
    """Main demo execution"""
    if not MODULES_AVAILABLE:
        print("❌ Cannot run demo - required modules not available")
        return
    
    try:
        demo = SentinelDemo()
        demo.run_full_demo()
        
        print("\n🎉 Sentinel Demo completed successfully!")
        print("📁 Check ./data/ directory for all generated files:")
        print("   📜 sentinel_law_registry.json - Immutable laws")
        print("   📋 sentinel_audit_log.json - Complete audit trail")
        print("   🧠 sentinel_demo_registry.json - Agent metrics")
        print("   📊 sentinel_roundtable_logs/ - Roundtable execution logs")
        
        print("\n🛡️ Ethical Governance Triad Status:")
        print("   ✅ Pattern Heat Memory - Reinforced learning")
        print("   ✅ Roundtable Consensus - Collaborative ethics")
        print("   ✅ Sentinel Enforcement - Immutable law compliance")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    main()