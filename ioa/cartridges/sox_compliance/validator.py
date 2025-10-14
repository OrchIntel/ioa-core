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


class SOXComplianceStatus(Enum):
    """SOX compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REMEDIATION = "requires_remediation"
    PARTIAL = "partial"


class FinancialDataClassification(Enum):
    """Financial data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class SOXComplianceResult:
    """Result of SOX compliance validation."""
    status: SOXComplianceStatus
    section_404_compliant: bool
    section_302_compliant: bool
    section_906_compliant: bool
    internal_controls_adequate: bool
    audit_trail_complete: bool
    executive_certification_valid: bool
    whistleblower_protection_active: bool
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    audit_evidence: Dict[str, Any]
    timestamp: datetime
    system_id: str


@dataclass
class SOXAuditTrail:
    """SOX-compliant audit trail entry."""
    transaction_id: str
    timestamp: datetime
    user_id: str
    action: str
    financial_data_classification: FinancialDataClassification
    amount: Optional[float] = None
    account: Optional[str] = None
    approval_required: bool = False
    approval_received: bool = False
    approver_id: Optional[str] = None
    evidence: Dict[str, Any] = None


class SOXValidator:
    """
    SOX compliance validator for financial services.
    
    Implements comprehensive validation for:
    - Section 404: Internal controls over financial reporting
    - Section 302: Corporate responsibility for financial reports
    - Section 906: Corporate responsibility for financial reports
    - Executive certification requirements
    - Whistleblower protection mechanisms
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize SOX validator."""
        self.config = config
        self.enabled = config.get("enabled", True)
        self.mode = config.get("mode", "monitor")
        
        # Load SOX requirements
        self._load_sox_requirements()
        
        logger.info(f"SOXValidator initialized: enabled={self.enabled}, mode={self.mode}")
    
    def _load_sox_requirements(self):
        """Load SOX compliance requirements."""
        self.requirements = {
            "section_404": {
                "internal_controls": [
                    "control_environment",
                    "risk_assessment",
                    "control_activities",
                    "information_communication",
                    "monitoring"
                ],
                "financial_reporting": [
                    "revenue_recognition",
                    "expense_management",
                    "asset_valuation",
                    "liability_management",
                    "equity_tracking"
                ],
                "it_controls": [
                    "access_controls",
                    "change_management",
                    "data_integrity",
                    "backup_recovery",
                    "security_monitoring"
                ]
            },
            "section_302": {
                "executive_responsibility": [
                    "ceo_cfo_certification",
                    "disclosure_controls",
                    "internal_control_evaluation",
                    "fraud_detection",
                    "material_changes"
                ]
            },
            "section_906": {
                "certification_requirements": [
                    "periodic_certification",
                    "accuracy_verification",
                    "completeness_verification",
                    "fair_presentation",
                    "compliance_verification"
                ]
            },
            "whistleblower_protection": [
                "confidential_reporting",
                "retaliation_protection",
                "investigation_procedures",
                "remedial_actions",
                "documentation_requirements"
            ]
        }
    
    def validate_system(self, system_context: Dict[str, Any]) -> SOXComplianceResult:
        """
        Validate a financial system against SOX requirements.
        
        Args:
            system_context: System context including financial data, controls, etc.
            
        Returns:
            SOXComplianceResult with validation details
        """
        if not self.enabled:
            return SOXComplianceResult(
                status=SOXComplianceStatus.COMPLIANT,
                section_404_compliant=True,
                section_302_compliant=True,
                section_906_compliant=True,
                internal_controls_adequate=True,
                audit_trail_complete=True,
                executive_certification_valid=True,
                whistleblower_protection_active=True,
                violations=[],
                recommendations=[],
                audit_evidence={},
                timestamp=datetime.now(timezone.utc),
                system_id=system_context.get("system_id", "unknown")
            )
        
        system_id = system_context.get("system_id", "unknown")
        violations = []
        recommendations = []
        
        # Validate Section 404 (Internal Controls)
        section_404_result = self._validate_section_404(system_context)
        violations.extend(section_404_result["violations"])
        recommendations.extend(section_404_result["recommendations"])
        
        # Validate Section 302 (Corporate Responsibility)
        section_302_result = self._validate_section_302(system_context)
        violations.extend(section_302_result["violations"])
        recommendations.extend(section_302_result["recommendations"])
        
        # Validate Section 906 (Certification)
        section_906_result = self._validate_section_906(system_context)
        violations.extend(section_906_result["violations"])
        recommendations.extend(section_906_result["recommendations"])
        
        # Validate Whistleblower Protection
        whistleblower_result = self._validate_whistleblower_protection(system_context)
        violations.extend(whistleblower_result["violations"])
        recommendations.extend(whistleblower_result["recommendations"])
        
        # Determine overall compliance status
        status = self._determine_compliance_status(violations, section_404_result, section_302_result, section_906_result)
        
        return SOXComplianceResult(
            status=status,
            section_404_compliant=section_404_result["compliant"],
            section_302_compliant=section_302_result["compliant"],
            section_906_compliant=section_906_result["compliant"],
            internal_controls_adequate=section_404_result["internal_controls_adequate"],
            audit_trail_complete=section_404_result["audit_trail_complete"],
            executive_certification_valid=section_302_result["executive_certification_valid"],
            whistleblower_protection_active=whistleblower_result["active"],
            violations=violations,
            recommendations=recommendations,
            audit_evidence=system_context,
            timestamp=datetime.now(timezone.utc),
            system_id=system_id
        )
    
    def _validate_section_404(self, system_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Section 404 - Internal Controls over Financial Reporting."""
        violations = []
        recommendations = []
        
        # Check internal controls framework
        internal_controls = system_context.get("internal_controls", {})
        controls_adequate = True
        
        for control_area in self.requirements["section_404"]["internal_controls"]:
            if not internal_controls.get(control_area):
                violations.append({
                    "type": "internal_controls",
                    "section": "404",
                    "description": f"Missing internal control: {control_area}",
                    "severity": "high"
                })
                controls_adequate = False
                recommendations.append(f"Implement {control_area} internal controls")
        
        # Check financial reporting controls
        financial_controls = system_context.get("financial_controls", {})
        for control in self.requirements["section_404"]["financial_reporting"]:
            if not financial_controls.get(control):
                violations.append({
                    "type": "financial_controls",
                    "section": "404",
                    "description": f"Missing financial control: {control}",
                    "severity": "high"
                })
                controls_adequate = False
                recommendations.append(f"Implement {control} financial controls")
        
        # Check IT controls
        it_controls = system_context.get("it_controls", {})
        for control in self.requirements["section_404"]["it_controls"]:
            if not it_controls.get(control):
                violations.append({
                    "type": "it_controls",
                    "section": "404",
                    "description": f"Missing IT control: {control}",
                    "severity": "medium"
                })
                recommendations.append(f"Implement {control} IT controls")
        
        # Check audit trail completeness
        audit_trail = system_context.get("audit_trail", {})
        audit_trail_complete = audit_trail.get("complete", False)
        if not audit_trail_complete:
            violations.append({
                "type": "audit_trail",
                "section": "404",
                "description": "Incomplete audit trail for financial transactions",
                "severity": "high"
            })
            recommendations.append("Implement complete audit trail for all financial transactions")
        
        return {
            "compliant": len(violations) == 0,
            "internal_controls_adequate": controls_adequate,
            "audit_trail_complete": audit_trail_complete,
            "violations": violations,
            "recommendations": recommendations
        }
    
    def _validate_section_302(self, system_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Section 302 - Corporate Responsibility for Financial Reports."""
        violations = []
        recommendations = []
        
        # Check executive responsibility
        executive_responsibility = system_context.get("executive_responsibility", {})
        certification_valid = True
        
        for requirement in self.requirements["section_302"]["executive_responsibility"]:
            if not executive_responsibility.get(requirement):
                violations.append({
                    "type": "executive_responsibility",
                    "section": "302",
                    "description": f"Missing executive responsibility: {requirement}",
                    "severity": "high"
                })
                certification_valid = False
                recommendations.append(f"Implement {requirement} executive responsibility")
        
        # Check CEO/CFO certification
        ceo_cfo_cert = system_context.get("ceo_cfo_certification", {})
        if not ceo_cfo_cert.get("current"):
            violations.append({
                "type": "executive_certification",
                "section": "302",
                "description": "Current CEO/CFO certification not found",
                "severity": "critical"
            })
            certification_valid = False
            recommendations.append("Obtain current CEO/CFO certification")
        
        return {
            "compliant": len(violations) == 0,
            "executive_certification_valid": certification_valid,
            "violations": violations,
            "recommendations": recommendations
        }
    
    def _validate_section_906(self, system_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Section 906 - Corporate Responsibility for Financial Reports."""
        violations = []
        recommendations = []
        
        # Check certification requirements
        certification_requirements = system_context.get("certification_requirements", {})
        
        for requirement in self.requirements["section_906"]["certification_requirements"]:
            if not certification_requirements.get(requirement):
                violations.append({
                    "type": "certification_requirements",
                    "section": "906",
                    "description": f"Missing certification requirement: {requirement}",
                    "severity": "high"
                })
                recommendations.append(f"Implement {requirement} certification requirement")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "recommendations": recommendations
        }
    
    def _validate_whistleblower_protection(self, system_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate whistleblower protection mechanisms."""
        violations = []
        recommendations = []
        
        # Check whistleblower protection
        whistleblower_protection = system_context.get("whistleblower_protection", {})
        protection_active = True
        
        for requirement in self.requirements["whistleblower_protection"]:
            if not whistleblower_protection.get(requirement):
                violations.append({
                    "type": "whistleblower_protection",
                    "description": f"Missing whistleblower protection: {requirement}",
                    "severity": "medium"
                })
                protection_active = False
                recommendations.append(f"Implement {requirement} whistleblower protection")
        
        return {
            "active": protection_active,
            "violations": violations,
            "recommendations": recommendations
        }
    
    def _determine_compliance_status(self, violations: List[Dict[str, Any]], 
                                   section_404_result: Dict[str, Any],
                                   section_302_result: Dict[str, Any],
                                   section_906_result: Dict[str, Any]) -> SOXComplianceStatus:
        """Determine overall SOX compliance status."""
        if not violations:
            return SOXComplianceStatus.COMPLIANT
        
        # Check for critical violations
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        if critical_violations:
            return SOXComplianceStatus.NON_COMPLIANT
        
        # Check for high severity violations
        high_violations = [v for v in violations if v.get("severity") == "high"]
        if high_violations:
            return SOXComplianceStatus.REQUIRES_REMEDIATION
        
        return SOXComplianceStatus.PARTIAL
    
    def create_audit_trail_entry(self, transaction: Dict[str, Any]) -> SOXAuditTrail:
        """Create a SOX-compliant audit trail entry."""
        return SOXAuditTrail(
            transaction_id=transaction.get("transaction_id", "unknown"),
            timestamp=datetime.now(timezone.utc),
            user_id=transaction.get("user_id", "system"),
            action=transaction.get("action", "unknown"),
            financial_data_classification=FinancialDataClassification(
                transaction.get("data_classification", "internal")
            ),
            amount=transaction.get("amount"),
            account=transaction.get("account"),
            approval_required=transaction.get("approval_required", False),
            approval_received=transaction.get("approval_received", False),
            approver_id=transaction.get("approver_id"),
            evidence=transaction.get("evidence", {})
        )
    
    def generate_sox_report(self, system_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive SOX compliance report."""
        compliance_result = self.validate_system(system_context)
        
        return {
            "report_type": "SOX_Compliance_Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "system_id": system_context.get("system_id", "unknown"),
            "compliance_status": compliance_result.status.value,
            "sections": {
                "404_internal_controls": {
                    "compliant": compliance_result.section_404_compliant,
                    "internal_controls_adequate": compliance_result.internal_controls_adequate,
                    "audit_trail_complete": compliance_result.audit_trail_complete
                },
                "302_corporate_responsibility": {
                    "compliant": compliance_result.section_302_compliant,
                    "executive_certification_valid": compliance_result.executive_certification_valid
                },
                "906_certification": {
                    "compliant": compliance_result.section_906_compliant
                },
                "whistleblower_protection": {
                    "active": compliance_result.whistleblower_protection_active
                }
            },
            "violations": compliance_result.violations,
            "recommendations": compliance_result.recommendations,
            "summary": {
                "total_violations": len(compliance_result.violations),
                "critical_violations": len([v for v in compliance_result.violations if v.get("severity") == "critical"]),
                "high_violations": len([v for v in compliance_result.violations if v.get("severity") == "high"]),
                "medium_violations": len([v for v in compliance_result.violations if v.get("severity") == "medium"]),
                "total_recommendations": len(compliance_result.recommendations)
            }
        }
