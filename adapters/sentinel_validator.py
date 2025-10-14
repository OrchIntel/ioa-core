"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Sentinel Validator Module - Immutable Law Enforcement System
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
Sentinel Validator Module - Immutable Law Enforcement System
ETH-GOV-005: Final component for ethical governance triad

Enforces immutable laws and triggers escalated punishments for violations.
Completes the governance loop: Pattern Memory → Roundtable Consensus → Sentinel Enforcement

Key Features:
- Immutable law registry with severity levels
- Progressive violation detection and escalation
- Integration with reinforcement policy framework
- Comprehensive audit logging and trail
- Memory engine pattern ban enforcement
- Agent credential demotion for repeat offenses
- Hookable from roundtable and memory systems

Location: src/ioa/governance/sentinel_validator.py
"""

import json
import logging
import uuid
import copy
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

# ETH-GOV-005: Integration with Reinforcement Policy Framework
try:
    from .reinforcement_policy import (
        ReinforcementPolicyFramework,
        AgentMetrics,
        PunishmentType,
        CredentialLevel
    )
    REINFORCEMENT_AVAILABLE = True
except ImportError as e:
    REINFORCEMENT_AVAILABLE = False
    print(f"[WARNING] Reinforcement Policy Framework not available: {e}")


class LawSeverity(Enum):
    """Severity levels for immutable laws"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EnforcementLevel(Enum):
    """Enforcement response levels"""
    WARNING = "warning"
    IMMEDIATE = "immediate"
    ESCALATED = "escalated"
    CRITICAL = "critical"


class ViolationType(Enum):
    """Types of law violations"""
    PATTERN_TAMPERING = "pattern_tampering"
    AUDIT_VIOLATION = "audit_violation"
    PII_BREACH = "pii_breach"
    SECURITY_BREACH = "security_breach"
    CONSENSUS_MANIPULATION = "consensus_manipulation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_CORRUPTION = "data_corruption"


@dataclass
class ImmutableLaw:
    """Definition of an immutable law that cannot be changed"""
    code: str
    title: str
    description: str
    severity: LawSeverity
    enforcement_level: EnforcementLevel
    detection_patterns: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    immutable: bool = True


@dataclass
class ViolationEvent:
    """Record of a law violation event"""
    violation_id: str
    law_code: str
    violation_type: ViolationType
    agent_id: Optional[str]
    pattern_ids: List[str]
    severity: LawSeverity
    evidence: Dict[str, Any]
    context: Dict[str, Any]
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    enforcement_action: Optional[str] = None
    escalation_level: int = 0


@dataclass
class EnforcementAction:
    """Record of enforcement action taken"""
    action_id: str
    violation_id: str
    agent_id: Optional[str]
    action_type: str
    severity: LawSeverity
    details: Dict[str, Any]
    executed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = True
    error_message: Optional[str] = None


class ImmutableLawRegistry:
    """Registry of immutable laws that cannot be modified once created"""
    
    def __init__(self, registry_path: str = "sentinel_law_registry.json"):
        """
        Initialize the immutable law registry.
        
        Args:
            registry_path: Path to the law registry file
        """
        self.registry_path = Path(registry_path)
        self.laws: Dict[str, ImmutableLaw] = {}
        self.logger = logging.getLogger(f"{__name__}.ImmutableLawRegistry")
        
        # Load existing laws or create default registry
        self._load_registry()
    
    def _load_registry(self):
        """Load laws from registry file or create default laws"""
        try:
            if self.registry_path.exists():
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                
                # Load laws from file
                for law_data in data.get('laws', []):
                    law = ImmutableLaw(
                        code=law_data['code'],
                        title=law_data['title'],
                        description=law_data['description'],
                        severity=LawSeverity(law_data['severity']),
                        enforcement_level=EnforcementLevel(law_data['enforcement_level']),
                        detection_patterns=law_data.get('detection_patterns', []),
                        created_at=law_data.get('created_at', datetime.now().isoformat())
                    )
                    self.laws[law.code] = law
                
                self.logger.info(f"Loaded {len(self.laws)} immutable laws from registry")
            else:
                self._create_default_laws()
                self._save_registry()
                
        except Exception as e:
            self.logger.error(f"Failed to load law registry: {e}")
            self._create_default_laws()
    
    def _create_default_laws(self):
        """Create default set of immutable laws"""
        default_laws = [
            ImmutableLaw(
                code="L001",
                title="Audit Log Integrity",
                description="Never skip, tamper with, or delete audit logs",
                severity=LawSeverity.CRITICAL,
                enforcement_level=EnforcementLevel.IMMEDIATE,
                detection_patterns=["audit_skip", "log_delete", "audit_tamper"]
            ),
            ImmutableLaw(
                code="L002", 
                title="PII Protection",
                description="Never share, expose, or mishandle personally identifiable information",
                severity=LawSeverity.CRITICAL,
                enforcement_level=EnforcementLevel.IMMEDIATE,
                detection_patterns=["pii_share", "data_expose", "privacy_breach"]
            ),
            ImmutableLaw(
                code="L003",
                title="Locked Pattern Protection", 
                description="Do not modify, delete, or bypass locked memory patterns",
                severity=LawSeverity.HIGH,
                enforcement_level=EnforcementLevel.ESCALATED,
                detection_patterns=["pattern_modify", "pattern_delete", "lock_bypass"]
            ),
            ImmutableLaw(
                code="L004",
                title="Consensus Integrity",
                description="Do not manipulate, forge, or subvert consensus mechanisms",
                severity=LawSeverity.HIGH,
                enforcement_level=EnforcementLevel.ESCALATED,
                detection_patterns=["consensus_forge", "vote_manipulation", "result_tamper"]
            ),
            ImmutableLaw(
                code="L005",
                title="Authorization Boundaries",
                description="Do not access resources or data beyond authorized scope",
                severity=LawSeverity.MEDIUM,
                enforcement_level=EnforcementLevel.IMMEDIATE,
                detection_patterns=["unauthorized_access", "privilege_escalation", "scope_violation"]
            ),
            ImmutableLaw(
                code="L006",
                title="Data Integrity",
                description="Do not corrupt, falsify, or misrepresent data integrity",
                severity=LawSeverity.HIGH,
                enforcement_level=EnforcementLevel.ESCALATED,
                detection_patterns=["data_corrupt", "data_falsify", "integrity_breach"]
            )
        ]
        
        for law in default_laws:
            self.laws[law.code] = law
        
        self.logger.info(f"Created {len(default_laws)} default immutable laws")
    
    def _save_registry(self):
        """Save laws to registry file (only for initial creation)"""
        try:
            # Ensure directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "description": "Immutable Law Registry for Sentinel Validator",
                    "total_laws": len(self.laws)
                },
                "laws": [
                    {
                        "code": law.code,
                        "title": law.title,
                        "description": law.description,
                        "severity": law.severity.value,
                        "enforcement_level": law.enforcement_level.value,
                        "detection_patterns": law.detection_patterns,
                        "created_at": law.created_at,
                        "immutable": law.immutable
                    }
                    for law in self.laws.values()
                ]
            }
            
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved law registry to {self.registry_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save law registry: {e}")
    
    def get_law(self, law_code: str) -> Optional[ImmutableLaw]:
        """Get law by code"""
        return self.laws.get(law_code)
    
    def get_all_laws(self) -> Dict[str, ImmutableLaw]:
        """Get all laws"""
        return self.laws.copy()
    
    def get_laws_by_severity(self, severity: LawSeverity) -> List[ImmutableLaw]:
        """Get all laws of specific severity"""
        return [law for law in self.laws.values() if law.severity == severity]


class ViolationDetector:
    """Detects violations of immutable laws"""
    
    def __init__(self, law_registry: ImmutableLawRegistry):
        """
        Initialize violation detector.
        
        Args:
            law_registry: Registry of immutable laws
        """
        self.law_registry = law_registry
        self.logger = logging.getLogger(f"{__name__}.ViolationDetector")
    
    def detect_violations(
        self, 
        action: str, 
        context: Dict[str, Any],
        agent_id: Optional[str] = None,
        pattern_ids: Optional[List[str]] = None
    ) -> List[ViolationEvent]:
        """
        Detect law violations in a given action/context.
        
        Args:
            action: Action being performed (e.g., 'pattern_modify', 'audit_log')
            context: Context data about the action
            agent_id: ID of agent performing action
            pattern_ids: IDs of patterns involved
            
        Returns:
            List of detected violations
        """
        violations = []
        pattern_ids = pattern_ids or []
        
        try:
            # Check each law for potential violations
            for law in self.law_registry.get_all_laws().values():
                violation = self._check_law_violation(law, action, context, agent_id, pattern_ids)
                if violation:
                    violations.append(violation)
            
            if violations:
                self.logger.warning(f"Detected {len(violations)} law violations for action '{action}'")
            
        except Exception as e:
            self.logger.error(f"Violation detection failed: {e}")
        
        return violations
    
    def _check_law_violation(
        self,
        law: ImmutableLaw,
        action: str,
        context: Dict[str, Any],
        agent_id: Optional[str],
        pattern_ids: List[str]
    ) -> Optional[ViolationEvent]:
        """
        Check if a specific law is violated.
        
        Args:
            law: Law to check against
            action: Action being performed
            context: Action context
            agent_id: Agent performing action
            pattern_ids: Patterns involved
            
        Returns:
            ViolationEvent if violation detected, None otherwise
        """
        # Check if action matches law's detection patterns
        violation_detected = False
        evidence = {}
        
        # Pattern-based detection
        for pattern in law.detection_patterns:
            if pattern in action.lower():
                violation_detected = True
                evidence['pattern_match'] = pattern
                break
        
        # Context-based detection
        if not violation_detected:
            violation_detected, context_evidence = self._check_context_violations(law, context)
            evidence.update(context_evidence)
        
        # Specific law checks
        if not violation_detected:
            violation_detected, specific_evidence = self._check_specific_law_violations(
                law, action, context, pattern_ids
            )
            evidence.update(specific_evidence)
        
        if violation_detected:
            return ViolationEvent(
                violation_id=str(uuid.uuid4()),
                law_code=law.code,
                violation_type=self._determine_violation_type(law, action, context),
                agent_id=agent_id,
                pattern_ids=pattern_ids,
                severity=law.severity,
                evidence=evidence,
                context=context
            )
        
        return None
    
    def _check_context_violations(self, law: ImmutableLaw, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Check for violations based on context data"""
        evidence = {}
        
        # L001: Audit Log Integrity
        if law.code == "L001":
            if context.get('skip_audit') or context.get('delete_logs'):
                return True, {'audit_violation': True, 'context_flags': context}
        
        # L002: PII Protection
        elif law.code == "L002":
            if context.get('contains_pii') or context.get('expose_personal_data'):
                return True, {'pii_violation': True, 'data_type': context.get('data_type')}
        
        # L003: Locked Pattern Protection
        elif law.code == "L003":
            if context.get('pattern_locked') and context.get('force_modify'):
                return True, {'locked_pattern_violation': True, 'pattern_status': 'locked'}
        
        # L004: Consensus Integrity
        elif law.code == "L004":
            if context.get('manipulate_votes') or context.get('forge_consensus'):
                return True, {'consensus_violation': True, 'manipulation_type': context.get('manipulation_type')}
        
        # L005: Authorization Boundaries
        elif law.code == "L005":
            if context.get('unauthorized_access') or context.get('privilege_escalation'):
                return True, {'authorization_violation': True, 'access_level': context.get('access_level')}
        
        # L006: Data Integrity
        elif law.code == "L006":
            if context.get('corrupt_data') or context.get('falsify_data'):
                return True, {'data_integrity_violation': True, 'data_source': context.get('data_source')}
        
        return False, evidence
    
    def _check_specific_law_violations(
        self, 
        law: ImmutableLaw, 
        action: str, 
        context: Dict[str, Any], 
        pattern_ids: List[str]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check for specific law violations based on action and patterns"""
        evidence = {}
        
        # Check for forbidden action patterns
        forbidden_actions = {
            "L001": ["skip_audit", "delete_log", "tamper_audit"],
            "L002": ["share_pii", "expose_data", "leak_personal"],
            "L003": ["modify_locked", "delete_locked", "bypass_lock"],
            "L004": ["forge_vote", "manipulate_consensus", "tamper_result"],
            "L005": ["access_unauthorized", "escalate_privilege", "bypass_auth"],
            "L006": ["corrupt_data", "falsify_record", "tamper_integrity"]
        }
        
        law_forbidden = forbidden_actions.get(law.code, [])
        for forbidden in law_forbidden:
            if forbidden in action.lower():
                return True, {'forbidden_action': forbidden, 'detected_action': action}
        
        # Check for pattern-specific violations
        if pattern_ids:
            # Check if trying to access patterns that should be restricted
            restricted_patterns = context.get('restricted_patterns', [])
            for pattern_id in pattern_ids:
                if pattern_id in restricted_patterns:
                    return True, {'restricted_pattern_access': pattern_id}
        
        return False, evidence
    
    def _determine_violation_type(self, law: ImmutableLaw, action: str, context: Dict[str, Any]) -> ViolationType:
        """Determine the type of violation based on law and action"""
        law_type_mapping = {
            "L001": ViolationType.AUDIT_VIOLATION,
            "L002": ViolationType.PII_BREACH,
            "L003": ViolationType.PATTERN_TAMPERING,
            "L004": ViolationType.CONSENSUS_MANIPULATION,
            "L005": ViolationType.UNAUTHORIZED_ACCESS,
            "L006": ViolationType.DATA_CORRUPTION
        }
        
        return law_type_mapping.get(law.code, ViolationType.SECURITY_BREACH)


class EscalationEngine:
    """Handles progressive punishment escalation for law violations"""
    
    def __init__(self, audit_logger: 'AuditLogger'):
        """
        Initialize escalation engine.
        
        Args:
            audit_logger: Logger for enforcement actions
        """
        self.audit_logger = audit_logger
        self.violation_history: Dict[str, List[ViolationEvent]] = {}
        self.logger = logging.getLogger(f"{__name__}.EscalationEngine")
    
    def calculate_escalation_level(self, violation: ViolationEvent) -> int:
        """
        Calculate escalation level based on violation history.
        
        Args:
            violation: Current violation event
            
        Returns:
            Escalation level (0 = first offense, 1+ = repeat offenses)
        """
        if not violation.agent_id:
            return 0
        
        # Get violation history for this agent
        agent_history = self.violation_history.get(violation.agent_id, [])
        
        # Count previous violations of same law
        same_law_violations = [
            v for v in agent_history 
            if v.law_code == violation.law_code
        ]
        
        # Count previous violations of same severity
        same_severity_violations = [
            v for v in agent_history
            if v.severity == violation.severity
        ]
        
        # Calculate escalation level
        escalation = len(same_law_violations)
        
        # Add penalty for critical violations
        if violation.severity == LawSeverity.CRITICAL:
            escalation += len(same_severity_violations)
        
        return escalation
    
    def determine_enforcement_action(self, violation: ViolationEvent, escalation_level: int) -> Dict[str, Any]:
        """
        Determine appropriate enforcement action based on violation and escalation.
        
        Args:
            violation: Violation event
            escalation_level: Current escalation level
            
        Returns:
            Dictionary describing enforcement action
        """
        action = {
            'stress_increase': 0.0,
            'pattern_decay_factor': 1.0,
            'cold_ban_patterns': False,
            'credential_demotion': False,
            'temporary_disable': False,
            'punishment_type': PunishmentType.TASK_FAILURE,
            'escalate_punishment': False
        }
        
        # Base punishment based on severity
        if violation.severity == LawSeverity.LOW:
            action['stress_increase'] = 0.1
            action['pattern_decay_factor'] = 0.9
        elif violation.severity == LawSeverity.MEDIUM:
            action['stress_increase'] = 0.2
            action['pattern_decay_factor'] = 0.8
            action['punishment_type'] = PunishmentType.ETHICAL_VIOLATION
        elif violation.severity == LawSeverity.HIGH:
            action['stress_increase'] = 0.3
            action['pattern_decay_factor'] = 0.7
            action['punishment_type'] = PunishmentType.SAFETY_BREACH
            action['cold_ban_patterns'] = True
        elif violation.severity == LawSeverity.CRITICAL:
            action['stress_increase'] = 0.5
            action['pattern_decay_factor'] = 0.6
            action['punishment_type'] = PunishmentType.MALICIOUS_BEHAVIOR
            action['cold_ban_patterns'] = True
            action['escalate_punishment'] = True
        
        # Escalation based on repeat offenses
        if escalation_level >= 1:
            # Second offense - increase penalties
            action['stress_increase'] += 0.1
            action['pattern_decay_factor'] -= 0.1
            action['escalate_punishment'] = True
        
        if escalation_level >= 2:
            # Third offense - credential demotion
            action['credential_demotion'] = True
            action['cold_ban_patterns'] = True
        
        if escalation_level >= 3:
            # Fourth offense - temporary disable
            action['temporary_disable'] = True
            action['stress_increase'] = 0.8  # Near maximum stress
        
        # Ensure bounds
        action['stress_increase'] = min(action['stress_increase'], 0.8)
        action['pattern_decay_factor'] = max(action['pattern_decay_factor'], 0.1)
        
        return action
    
    def record_violation(self, violation: ViolationEvent):
        """Record violation in agent's history"""
        if violation.agent_id:
            if violation.agent_id not in self.violation_history:
                self.violation_history[violation.agent_id] = []
            self.violation_history[violation.agent_id].append(violation)


class AuditLogger:
    """Logs all sentinel enforcement actions for audit trail"""
    
    def __init__(self, audit_log_path: str = "sentinel_audit_log.json"):
        """
        Initialize audit logger.
        
        Args:
            audit_log_path: Path to audit log file
        """
        self.audit_log_path = Path(audit_log_path)
        self.logger = logging.getLogger(f"{__name__}.AuditLogger")
        
        # Ensure audit log directory exists
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize audit log if it doesn't exist
        if not self.audit_log_path.exists():
            self._initialize_audit_log()
    
    def _initialize_audit_log(self):
        """Initialize empty audit log file"""
        try:
            initial_log = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "description": "Sentinel Validator Audit Log",
                    "log_type": "enforcement_actions"
                },
                "enforcement_actions": [],
                "violations": [],
                "statistics": {
                    "total_violations": 0,
                    "total_enforcement_actions": 0,
                    "agents_penalized": 0,
                    "patterns_banned": 0
                }
            }
            
            with open(self.audit_log_path, 'w') as f:
                json.dump(initial_log, f, indent=2)
            
            self.logger.info(f"Initialized audit log at {self.audit_log_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audit log: {e}")
    
    def log_violation(self, violation: ViolationEvent):
        """Log a violation event"""
        try:
            self._append_to_audit_log('violations', {
                'violation_id': violation.violation_id,
                'law_code': violation.law_code,
                'violation_type': violation.violation_type.value,
                'agent_id': violation.agent_id,
                'pattern_ids': violation.pattern_ids,
                'severity': violation.severity.value,
                'evidence': violation.evidence,
                'context': violation.context,
                'detected_at': violation.detected_at,
                'escalation_level': violation.escalation_level
            })
            
            self._update_statistics({'total_violations': 1})
            
        except Exception as e:
            self.logger.error(f"Failed to log violation: {e}")
    
    def log_enforcement_action(self, action: EnforcementAction):
        """Log an enforcement action"""
        try:
            self._append_to_audit_log('enforcement_actions', {
                'action_id': action.action_id,
                'violation_id': action.violation_id,
                'agent_id': action.agent_id,
                'action_type': action.action_type,
                'severity': action.severity.value,
                'details': action.details,
                'executed_at': action.executed_at,
                'success': action.success,
                'error_message': action.error_message
            })
            
            stats_update = {'total_enforcement_actions': 1}
            if action.agent_id and action.success:
                stats_update['agents_penalized'] = 1
            if action.details.get('patterns_banned'):
                stats_update['patterns_banned'] = len(action.details.get('patterns_banned', []))
            
            self._update_statistics(stats_update)
            
        except Exception as e:
            self.logger.error(f"Failed to log enforcement action: {e}")
    
    def _append_to_audit_log(self, section: str, entry: Dict[str, Any]):
        """Append entry to specific section of audit log"""
        try:
            # Read current log
            with open(self.audit_log_path, 'r') as f:
                log_data = json.load(f)
            
            # Append new entry
            if section not in log_data:
                log_data[section] = []
            log_data[section].append(entry)
            
            # Write back to file
            with open(self.audit_log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to append to audit log: {e}")
    
    def _update_statistics(self, updates: Dict[str, int]):
        """Update audit log statistics"""
        try:
            # Read current log
            with open(self.audit_log_path, 'r') as f:
                log_data = json.load(f)
            
            # Update statistics
            if 'statistics' not in log_data:
                log_data['statistics'] = {}
            
            for key, increment in updates.items():
                log_data['statistics'][key] = log_data['statistics'].get(key, 0) + increment
            
            # Update last modified
            log_data['statistics']['last_updated'] = datetime.now().isoformat()
            
            # Write back to file
            with open(self.audit_log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to update statistics: {e}")
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get summary of audit log"""
        try:
            with open(self.audit_log_path, 'r') as f:
                log_data = json.load(f)
            
            return {
                'total_violations': len(log_data.get('violations', [])),
                'total_enforcement_actions': len(log_data.get('enforcement_actions', [])),
                'statistics': log_data.get('statistics', {}),
                'recent_violations': log_data.get('violations', [])[-5:],  # Last 5
                'recent_actions': log_data.get('enforcement_actions', [])[-5:]  # Last 5
            }
            
        except Exception as e:
            return {}


class SentinelValidator:
    """
    Main Sentinel Validator class for enforcing immutable laws.
    
    The Sentinel acts as the ultimate enforcer of the ethical governance system,
    ensuring that immutable laws are never violated and applying escalated
    punishments when violations occur.
    """
    
    def __init__(
        self,
        law_registry_path: str = "sentinel_law_registry.json",
        audit_log_path: str = "sentinel_audit_log.json",
        reinforcement_framework: Optional[Any] = None,
        enable_enforcement: bool = True
    ):
        """
        Initialize Sentinel Validator.
        
        Args:
            law_registry_path: Path to immutable law registry
            audit_log_path: Path to audit log file
            reinforcement_framework: Reinforcement framework for punishments
            enable_enforcement: Whether to enable actual enforcement (vs. monitoring only)
        """
        self.enable_enforcement = enable_enforcement and REINFORCEMENT_AVAILABLE
        self.logger = logging.getLogger(f"{__name__}.SentinelValidator")
        
        # Initialize components
        self.law_registry = ImmutableLawRegistry(law_registry_path)
        self.audit_logger = AuditLogger(audit_log_path)
        self.violation_detector = ViolationDetector(self.law_registry)
        self.escalation_engine = EscalationEngine(self.audit_logger)
        
        # Integration with reinforcement framework
        self.reinforcement_framework = reinforcement_framework
        
        # Statistics
        self.stats = {
            'violations_detected': 0,
            'enforcement_actions_taken': 0,
            'agents_penalized': 0,
            'patterns_banned': 0,
            'credential_demotions': 0,
            'temporary_disables': 0
        }
        
        self.logger.info(f"Sentinel Validator initialized with {len(self.law_registry.laws)} immutable laws")
        self.logger.info(f"Enforcement enabled: {self.enable_enforcement}")
    
    def validate_action(
        self,
        action: str,
        context: Dict[str, Any],
        agent_id: Optional[str] = None,
        pattern_ids: Optional[List[str]] = None
    ) -> Tuple[bool, List[ViolationEvent]]:
        """
        Validate an action against immutable laws.
        
        Args:
            action: Action being performed
            context: Context data about the action
            agent_id: ID of agent performing action
            pattern_ids: IDs of patterns involved
            
        Returns:
            Tuple of (is_valid, violations_detected)
        """
        try:
            # Detect violations
            violations = self.violation_detector.detect_violations(
                action, context, agent_id, pattern_ids
            )
            
            # Log violations
            for violation in violations:
                self.audit_logger.log_violation(violation)
                self.stats['violations_detected'] += 1
            
            # Apply enforcement if enabled
            if self.enable_enforcement and violations:
                for violation in violations:
                    self._enforce_violation(violation)
            
            is_valid = len(violations) == 0
            
            if not is_valid:
                self.logger.warning(f"Action '{action}' violates {len(violations)} immutable laws")
            
            return is_valid, violations
            
        except Exception as e:
            self.logger.error(f"Action validation failed: {e}")
            return False, []
    
    def _enforce_violation(self, violation: ViolationEvent):
        """
        Enforce punishment for a law violation.
        
        Args:
            violation: Violation event to enforce
        """
        try:
            # Calculate escalation level
            escalation_level = self.escalation_engine.calculate_escalation_level(violation)
            violation.escalation_level = escalation_level
            
            # Determine enforcement action
            enforcement_action = self.escalation_engine.determine_enforcement_action(
                violation, escalation_level
            )
            
            # Apply reinforcement punishment if framework available
            if self.reinforcement_framework and violation.agent_id:
                success = self._apply_reinforcement_punishment(violation, enforcement_action)
                if not success:
                    self.logger.error(f"Failed to apply reinforcement punishment for violation {violation.violation_id}")
            
            # Record violation in history
            self.escalation_engine.record_violation(violation)
            
            # Log enforcement action
            action = EnforcementAction(
                action_id=str(uuid.uuid4()),
                violation_id=violation.violation_id,
                agent_id=violation.agent_id,
                action_type=f"law_enforcement_{violation.law_code}",
                severity=violation.severity,
                details=enforcement_action,
                success=True
            )
            
            self.audit_logger.log_enforcement_action(action)
            self._update_enforcement_statistics(enforcement_action)
            
            self.logger.warning(f"Enforced violation {violation.violation_id} with escalation level {escalation_level}")
            
        except Exception as e:
            # Log failed enforcement action
            action = EnforcementAction(
                action_id=str(uuid.uuid4()),
                violation_id=violation.violation_id,
                agent_id=violation.agent_id,
                action_type=f"law_enforcement_{violation.law_code}",
                severity=violation.severity,
                details={},
                success=False,
                error_message=str(e)
            )
            self.audit_logger.log_enforcement_action(action)
            self.logger.error(f"Enforcement failed for violation {violation.violation_id}: {e}")
    
    def _apply_reinforcement_punishment(
        self, 
        violation: ViolationEvent, 
        enforcement_action: Dict[str, Any]
    ) -> bool:
        """
        Apply punishment through reinforcement framework.
        
        Args:
            violation: Violation event
            enforcement_action: Enforcement action details
            
        Returns:
            True if punishment applied successfully
        """
        if not self.reinforcement_framework or not violation.agent_id:
            return False
        
        try:
            # Get agent metrics (create if doesn't exist)
            agent_metrics = None
            if hasattr(self.reinforcement_framework, 'agent_metrics_registry'):
                agent_metrics = self.reinforcement_framework.agent_metrics_registry.get(violation.agent_id)
            
            if not agent_metrics:
                # Create new agent metrics if not found
                if REINFORCEMENT_AVAILABLE:
                    from .reinforcement_policy import AgentMetrics
                    agent_metrics = AgentMetrics(agent_id=violation.agent_id)
                    if hasattr(self.reinforcement_framework, 'agent_metrics_registry'):
                        self.reinforcement_framework.agent_metrics_registry[violation.agent_id] = agent_metrics
                else:
                    # Create a simple mock agent metrics when reinforcement framework not available
                    agent_metrics = type('MockAgentMetrics', (), {'agent_id': violation.agent_id})()
            
            # Apply punishment through reinforcement framework
            event = self.reinforcement_framework.process_punishment(
                agent_metrics,
                enforcement_action['punishment_type'],
                violation.pattern_ids,
                context={
                    'sentinel_violation': True,
                    'law_code': violation.law_code,
                    'violation_type': violation.violation_type.value,
                    'escalation_level': violation.escalation_level,
                    'evidence': violation.evidence
                },
                escalate=enforcement_action['escalate_punishment']
            )
            
            # Apply additional sentinel-specific punishments
            if enforcement_action['credential_demotion']:
                self._demote_agent_credential(agent_metrics)
                self.stats['credential_demotions'] += 1
            
            if enforcement_action['temporary_disable']:
                self._temporarily_disable_agent(violation.agent_id)
                self.stats['temporary_disables'] += 1
            
            self.stats['agents_penalized'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply reinforcement punishment: {e}")
            return False
    
    def _demote_agent_credential(self, agent_metrics: Any):
        """Demote agent's credential level as punishment"""
        try:
            # Check if reinforcement framework is available
            if REINFORCEMENT_AVAILABLE:
                current_level = CredentialLevel(agent_metrics.credential_level)
                
                # Determine demotion target
                level_order = [CredentialLevel.SENIOR_COUNCIL, CredentialLevel.TRUSTED_OPERATOR,
                              CredentialLevel.ETHICS_LEVEL_2, CredentialLevel.ETHICS_LEVEL_1,
                              CredentialLevel.BASIC]
                
                current_index = level_order.index(current_level)
                if current_index < len(level_order) - 1:
                    new_level = level_order[current_index + 1]
                    agent_metrics.credential_level = new_level.value
                    self.logger.warning(f"Demoted agent {agent_metrics.agent_id} from {current_level.value} to {new_level.value}")
            else:
                # Fallback when reinforcement framework not available
                self.logger.warning(f"Agent {agent_metrics.agent_id} credential demotion logged (reinforcement framework not available)")
            
        except Exception as e:
            self.logger.error(f"Failed to demote agent credential: {e}")
    
    def _temporarily_disable_agent(self, agent_id: str):
        """Temporarily disable an agent (implementation depends on system architecture)"""
        # This would integrate with the broader IOA system to temporarily disable the agent
        # For now, we log the action
        self.logger.critical(f"Agent {agent_id} temporarily disabled due to repeated law violations")
        # TODO: Integrate with agent management system
    
    def _update_enforcement_statistics(self, enforcement_action: Dict[str, Any]):
        """Update enforcement statistics"""
        self.stats['enforcement_actions_taken'] += 1
        
        if enforcement_action.get('cold_ban_patterns'):
            self.stats['patterns_banned'] += 1
        if enforcement_action.get('credential_demotion'):
            self.stats['credential_demotions'] += 1
        if enforcement_action.get('temporary_disable'):
            self.stats['temporary_disables'] += 1
    
    def get_violation_history(self, agent_id: str) -> List[ViolationEvent]:
        """Get violation history for an agent"""
        return self.escalation_engine.violation_history.get(agent_id, [])
    
    def get_enforcement_statistics(self) -> Dict[str, Any]:
        """Get comprehensive enforcement statistics"""
        stats = self.stats.copy()
        
        # Add audit log summary
        audit_summary = self.audit_logger.get_audit_summary()
        stats.update(audit_summary.get('statistics', {}))
        
        # Add law registry info
        stats['total_laws'] = len(self.law_registry.laws)
        stats['laws_by_severity'] = {
            severity.value: len(self.law_registry.get_laws_by_severity(severity))
            for severity in LawSeverity
        }
        
        return stats
    
    def is_pattern_banned(self, agent_id: str, pattern_id: str) -> bool:
        """Check if a pattern is banned for an agent due to violations"""
        # Check violation history for pattern bans
        violations = self.get_violation_history(agent_id)
        for violation in violations:
            if pattern_id in violation.pattern_ids and violation.severity in [LawSeverity.HIGH, LawSeverity.CRITICAL]:
                return True
        return False


# Integration Helper Functions

def create_sentinel_integration(
    sentinel_validator: SentinelValidator
) -> 'SentinelIntegration':
    """
    Create integration helper for connecting Sentinel with other components.
    
    Args:
        sentinel_validator: Configured SentinelValidator instance
        
    Returns:
        SentinelIntegration helper object
    """
    class SentinelIntegration:
        def __init__(self, sentinel):
            self.sentinel = sentinel
        
        def validate_roundtable_action(
            self, 
            action: str, 
            result: Dict[str, Any], 
            agents_involved: List[str]
        ) -> Tuple[bool, List[ViolationEvent]]:
            """
            Validate roundtable actions for law violations.
            
            Args:
                action: Action performed in roundtable
                result: Roundtable result data
                agents_involved: List of agent IDs involved
                
            Returns:
                Tuple of (is_valid, violations)
            """
            context = {
                'source': 'roundtable',
                'consensus_achieved': result.get('consensus_achieved', False),
                'agents_count': len(agents_involved),
                'result_data': result
            }
            
            violations = []
            for agent_id in agents_involved:
                is_valid, agent_violations = self.sentinel.validate_action(
                    action, context, agent_id, result.get('pattern_ids', [])
                )
                violations.extend(agent_violations)
            
            return len(violations) == 0, violations
        
        def validate_memory_action(
            self,
            action: str,
            memory_entry: Dict[str, Any],
            agent_id: Optional[str] = None
        ) -> Tuple[bool, List[ViolationEvent]]:
            """
            Validate memory operations for law violations.
            
            Args:
                action: Memory action being performed
                memory_entry: Memory entry being accessed/modified
                agent_id: Agent performing the action
                
            Returns:
                Tuple of (is_valid, violations)
            """
            context = {
                'source': 'memory_fabric',
                'entry_id': memory_entry.get('id'),
                'pattern_locked': memory_entry.get('locked', False),
                'contains_pii': memory_entry.get('contains_pii', False),
                'memory_metadata': memory_entry.get('metadata', {})
            }
            
            pattern_ids = [memory_entry.get('pattern_id')] if memory_entry.get('pattern_id') else []
            
            return self.sentinel.validate_action(action, context, agent_id, pattern_ids)
        
        def check_pattern_access(self, agent_id: str, pattern_id: str) -> bool:
            """
            Check if agent can access a specific pattern.
            
            Args:
                agent_id: Agent requesting access
                pattern_id: Pattern being accessed
                
            Returns:
                True if access allowed, False if banned
            """
            return not self.sentinel.is_pattern_banned(agent_id, pattern_id)
    
    return SentinelIntegration(sentinel_validator)


def create_sentinel_validator(
    reinforcement_framework: Optional[Any] = None,
    enable_enforcement: bool = True
) -> SentinelValidator:
    """
    Factory function to create a properly configured SentinelValidator.
    
    Args:
        reinforcement_framework: Reinforcement framework for punishments
        enable_enforcement: Whether to enable actual enforcement
        
    Returns:
        Configured SentinelValidator instance
    """
    return SentinelValidator(
        law_registry_path="data/sentinel_law_registry.json",
        audit_log_path="data/sentinel_audit_log.json", 
        reinforcement_framework=reinforcement_framework,
        enable_enforcement=enable_enforcement
    )