"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """EU AI Act risk levels."""
    PROHIBITED = "prohibited"
    HIGH_RISK = "high_risk"
    LIMITED = "limited"
    MINIMAL = "minimal"


class ComplianceStatus(Enum):
    """Compliance validation status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"
    PARTIAL = "partial"


@dataclass
class ComplianceResult:
    """Result of EU AI Act compliance validation."""
    status: ComplianceStatus
    risk_level: RiskLevel
    violations: List[Dict[str, Any]]
    requirements_met: List[str]
    requirements_missing: List[str]
    human_oversight_required: bool
    transparency_obligations: List[str]
    data_governance_requirements: List[str]
    robustness_requirements: List[str]
    timestamp: datetime
    system_id: str
    evidence: Dict[str, Any]


@dataclass
class TransparencyReport:
    """EU AI Act transparency report."""
    system_id: str
    system_name: str
    provider: str
    risk_level: RiskLevel
    capabilities: List[str]
    limitations: List[str]
    data_sources: List[str]
    training_data_info: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    human_oversight: Dict[str, Any]
    generated_at: datetime


class EUAIActValidator:
    """
    EU AI Act compliance validator for high-risk AI systems.
    
    Implements comprehensive validation for:
    - Risk classification
    - High-risk AI system requirements
    - Transparency and documentation obligations
    - Human oversight requirements
    - Data governance and quality management
    - Accuracy, robustness, and cybersecurity requirements
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize EU AI Act validator."""
        self.config = config
        self.enabled = config.get("enabled", True)
        self.mode = config.get("scope", {}).get("default_mode", "monitor")
        
        # Load EU AI Act requirements
        self._load_requirements()
        
        logger.info(f"EUAIActValidator initialized: enabled={self.enabled}, mode={self.mode}")
    
    def _load_requirements(self):
        """Load EU AI Act requirements from configuration."""
        self.requirements = {
            "high_risk": {
                "risk_management": [
                    "risk_management_system",
                    "risk_assessment_documentation",
                    "risk_mitigation_measures",
                    "ongoing_monitoring"
                ],
                "data_governance": [
                    "data_quality_management",
                    "data_provenance_tracking",
                    "data_retention_policies",
                    "data_protection_compliance"
                ],
                "technical_documentation": [
                    "system_architecture_documentation",
                    "training_data_documentation",
                    "model_performance_metrics",
                    "testing_procedures"
                ],
                "record_keeping": [
                    "audit_trail_maintenance",
                    "decision_logging",
                    "model_versioning",
                    "performance_monitoring"
                ],
                "transparency": [
                    "user_information_provision",
                    "system_capability_disclosure",
                    "limitation_communication",
                    "human_oversight_indicators"
                ],
                "human_oversight": [
                    "human_in_loop_mechanisms",
                    "override_capabilities",
                    "escalation_procedures",
                    "decision_explanation"
                ],
                "accuracy_robustness": [
                    "performance_validation",
                    "bias_detection",
                    "adversarial_testing",
                    "robustness_verification"
                ],
                "cybersecurity": [
                    "security_by_design",
                    "vulnerability_assessment",
                    "incident_response_plan",
                    "access_controls"
                ]
            },
            "prohibited": [
                "subliminal_manipulation",
                "social_scoring",
                "biometric_categorization_sensitive",
                "real_time_biometric_identification",
                "emotion_recognition_workplace",
                "predictive_policing_profiling"
            ]
        }
    
    def validate_system(self, system_context: Dict[str, Any]) -> ComplianceResult:
        """
        Validate an AI system against EU AI Act requirements.
        
        Args:
            system_context: System context including risk level, capabilities, etc.
            
        Returns:
            ComplianceResult with validation details
        """
        if not self.enabled:
            return ComplianceResult(
                status=ComplianceStatus.COMPLIANT,
                risk_level=RiskLevel.MINIMAL,
                violations=[],
                requirements_met=[],
                requirements_missing=[],
                human_oversight_required=False,
                transparency_obligations=[],
                data_governance_requirements=[],
                robustness_requirements=[],
                timestamp=datetime.now(timezone.utc),
                system_id=system_context.get("system_id", "unknown"),
                evidence={}
            )
        
        system_id = system_context.get("system_id", "unknown")
        risk_level = self._classify_risk_level(system_context)
        
        violations = []
        requirements_met = []
        requirements_missing = []
        human_oversight_required = False
        transparency_obligations = []
        data_governance_requirements = []
        robustness_requirements = []
        
        # Validate based on risk level
        if risk_level == RiskLevel.PROHIBITED:
            violations.append({
                "type": "prohibited_use",
                "description": "System falls under prohibited AI practices",
                "severity": "critical"
            })
            status = ComplianceStatus.NON_COMPLIANT
        
        elif risk_level == RiskLevel.HIGH_RISK:
            # Validate high-risk requirements
            high_risk_validation = self._validate_high_risk_requirements(system_context)
            violations.extend(high_risk_validation["violations"])
            requirements_met.extend(high_risk_validation["requirements_met"])
            requirements_missing.extend(high_risk_validation["requirements_missing"])
            human_oversight_required = True
            transparency_obligations = high_risk_validation["transparency_obligations"]
            data_governance_requirements = high_risk_validation["data_governance_requirements"]
            robustness_requirements = high_risk_validation["robustness_requirements"]
            
            if violations:
                status = ComplianceStatus.NON_COMPLIANT
            elif requirements_missing:
                status = ComplianceStatus.REQUIRES_REVIEW
            else:
                status = ComplianceStatus.COMPLIANT
        
        else:
            # Limited or minimal risk - basic compliance
            status = ComplianceStatus.COMPLIANT
            requirements_met = ["basic_compliance"]
        
        return ComplianceResult(
            status=status,
            risk_level=risk_level,
            violations=violations,
            requirements_met=requirements_met,
            requirements_missing=requirements_missing,
            human_oversight_required=human_oversight_required,
            transparency_obligations=transparency_obligations,
            data_governance_requirements=data_governance_requirements,
            robustness_requirements=robustness_requirements,
            timestamp=datetime.now(timezone.utc),
            system_id=system_id,
            evidence=system_context
        )
    
    def _classify_risk_level(self, system_context: Dict[str, Any]) -> RiskLevel:
        """Classify the risk level of the AI system."""
        use_case = system_context.get("use_case", "").lower()
        capabilities = system_context.get("capabilities", [])
        
        # Check for prohibited practices
        for prohibited in self.requirements["prohibited"]:
            if prohibited in use_case or any(prohibited in cap.lower() for cap in capabilities):
                return RiskLevel.PROHIBITED
        
        # Check for high-risk indicators
        high_risk_indicators = [
            "biometric_identification",
            "employment_hr",
            "critical_infrastructure",
            "education",
            "healthcare",
            "law_enforcement",
            "migration_asylum",
            "justice_democracy"
        ]
        
        for indicator in high_risk_indicators:
            if indicator in use_case or any(indicator in cap.lower() for cap in capabilities):
                return RiskLevel.HIGH_RISK
        
        # Check for limited risk indicators
        limited_risk_indicators = [
            "content_moderation",
            "recommendation_system",
            "synthetic_media",
            "emotion_recognition"
        ]
        
        for indicator in limited_risk_indicators:
            if indicator in use_case or any(indicator in cap.lower() for cap in capabilities):
                return RiskLevel.LIMITED
        
        return RiskLevel.MINIMAL
    
    def _validate_high_risk_requirements(self, system_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate high-risk AI system requirements."""
        violations = []
        requirements_met = []
        requirements_missing = []
        transparency_obligations = []
        data_governance_requirements = []
        robustness_requirements = []
        
        # Check risk management requirements
        if not system_context.get("risk_management_system"):
            violations.append({
                "type": "risk_management",
                "description": "Risk management system not implemented",
                "severity": "high"
            })
            requirements_missing.append("risk_management_system")
        else:
            requirements_met.append("risk_management_system")
        
        # Check data governance requirements
        data_governance = system_context.get("data_governance", {})
        for req in self.requirements["high_risk"]["data_governance"]:
            if not data_governance.get(req.replace("_", " ")):
                violations.append({
                    "type": "data_governance",
                    "description": f"Data governance requirement not met: {req}",
                    "severity": "medium"
                })
                requirements_missing.append(req)
                data_governance_requirements.append(req)
            else:
                requirements_met.append(req)
        
        # Check transparency requirements
        transparency = system_context.get("transparency", {})
        for req in self.requirements["high_risk"]["transparency"]:
            if not transparency.get(req.replace("_", " ")):
                violations.append({
                    "type": "transparency",
                    "description": f"Transparency requirement not met: {req}",
                    "severity": "medium"
                })
                requirements_missing.append(req)
                transparency_obligations.append(req)
            else:
                requirements_met.append(req)
        
        # Check human oversight requirements
        human_oversight = system_context.get("human_oversight", {})
        for req in self.requirements["high_risk"]["human_oversight"]:
            if not human_oversight.get(req.replace("_", " ")):
                violations.append({
                    "type": "human_oversight",
                    "description": f"Human oversight requirement not met: {req}",
                    "severity": "high"
                })
                requirements_missing.append(req)
            else:
                requirements_met.append(req)
        
        # Check accuracy and robustness requirements
        robustness = system_context.get("robustness", {})
        for req in self.requirements["high_risk"]["accuracy_robustness"]:
            if not robustness.get(req.replace("_", " ")):
                violations.append({
                    "type": "robustness",
                    "description": f"Robustness requirement not met: {req}",
                    "severity": "medium"
                })
                requirements_missing.append(req)
                robustness_requirements.append(req)
            else:
                requirements_met.append(req)
        
        return {
            "violations": violations,
            "requirements_met": requirements_met,
            "requirements_missing": requirements_missing,
            "transparency_obligations": transparency_obligations,
            "data_governance_requirements": data_governance_requirements,
            "robustness_requirements": robustness_requirements
        }
    
    def generate_transparency_report(self, system_context: Dict[str, Any]) -> TransparencyReport:
        """Generate EU AI Act transparency report."""
        return TransparencyReport(
            system_id=system_context.get("system_id", "unknown"),
            system_name=system_context.get("system_name", "AI System"),
            provider=system_context.get("provider", "Unknown"),
            risk_level=self._classify_risk_level(system_context),
            capabilities=system_context.get("capabilities", []),
            limitations=system_context.get("limitations", []),
            data_sources=system_context.get("data_sources", []),
            training_data_info=system_context.get("training_data_info", {}),
            performance_metrics=system_context.get("performance_metrics", {}),
            human_oversight=system_context.get("human_oversight", {}),
            generated_at=datetime.now(timezone.utc)
        )
    
    def enforce_human_oversight(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce human oversight requirements for AI decisions."""
        risk_level = self._classify_risk_level(decision_context)
        
        if risk_level == RiskLevel.HIGH_RISK:
            return {
                "human_oversight_required": True,
                "oversight_type": "mandatory",
                "escalation_required": True,
                "decision_explanation_required": True,
                "override_capabilities": True
            }
        elif risk_level == RiskLevel.LIMITED:
            return {
                "human_oversight_required": True,
                "oversight_type": "recommended",
                "escalation_required": False,
                "decision_explanation_required": True,
                "override_capabilities": True
            }
        else:
            return {
                "human_oversight_required": False,
                "oversight_type": "optional",
                "escalation_required": False,
                "decision_explanation_required": False,
                "override_capabilities": False
            }
