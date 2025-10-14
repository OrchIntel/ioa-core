"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class WhistleblowerStatus(Enum):
    """Whistleblower protection status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"


@dataclass
class WhistleblowerReport:
    """Whistleblower report data."""
    report_id: str
    reporter_id: Optional[str]
    report_type: str
    description: str
    reported_at: datetime
    confidentiality_level: str
    investigation_status: str
    resolution_status: str
    retaliation_claimed: bool
    evidence: Dict[str, Any] = None


@dataclass
class WhistleblowerValidation:
    """Result of whistleblower protection validation."""
    protection_status: WhistleblowerStatus
    confidential_reporting_available: bool
    retaliation_protection_active: bool
    investigation_procedures_adequate: bool
    remedial_actions_available: bool
    documentation_complete: bool
    deficiencies: List[str]
    recommendations: List[str]
    evidence: Dict[str, Any]
    validated_at: datetime


class WhistleblowerProtectionValidator:
    """
    SOX whistleblower protection validator.
    
    Validates whistleblower protection mechanisms required by SOX.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize whistleblower protection validator."""
        self.config = config
        self.enabled = config.get("enabled", True)
        
        # Load whistleblower protection requirements
        self._load_whistleblower_requirements()
        
        logger.info(f"WhistleblowerProtectionValidator initialized: enabled={self.enabled}")
    
    def _load_whistleblower_requirements(self):
        """Load SOX whistleblower protection requirements."""
        self.whistleblower_requirements = {
            "confidential_reporting": [
                "hotline_available",
                "anonymous_reporting",
                "multiple_channels",
                "24_7_availability",
                "secure_communication",
                "report_tracking"
            ],
            "retaliation_protection": [
                "anti_retaliation_policy",
                "retaliation_detection",
                "investigation_procedures",
                "remedial_actions",
                "legal_protection",
                "employee_education"
            ],
            "investigation_procedures": [
                "investigation_team",
                "investigation_timeline",
                "evidence_collection",
                "witness_protection",
                "reporting_requirements",
                "resolution_process"
            ],
            "remedial_actions": [
                "disciplinary_actions",
                "corrective_measures",
                "system_improvements",
                "training_programs",
                "policy_updates",
                "monitoring_enhancements"
            ],
            "documentation_requirements": [
                "report_logging",
                "investigation_documentation",
                "resolution_tracking",
                "audit_trail",
                "retention_policies",
                "confidentiality_protection"
            ]
        }
    
    def validate_whistleblower_protection(self, protection_data: Dict[str, Any]) -> WhistleblowerValidation:
        """
        Validate whistleblower protection mechanisms.
        
        Args:
            protection_data: Whistleblower protection system data
            
        Returns:
            WhistleblowerValidation with validation results
        """
        deficiencies = []
        recommendations = []
        
        # Check confidential reporting
        confidential_reporting = protection_data.get("confidential_reporting", {})
        confidential_available = True
        
        for requirement in self.whistleblower_requirements["confidential_reporting"]:
            if not confidential_reporting.get(requirement):
                deficiencies.append(f"Missing confidential reporting requirement: {requirement}")
                confidential_available = False
                recommendations.append(f"Implement {requirement} for confidential reporting")
        
        # Check retaliation protection
        retaliation_protection = protection_data.get("retaliation_protection", {})
        retaliation_active = True
        
        for requirement in self.whistleblower_requirements["retaliation_protection"]:
            if not retaliation_protection.get(requirement):
                deficiencies.append(f"Missing retaliation protection requirement: {requirement}")
                retaliation_active = False
                recommendations.append(f"Implement {requirement} for retaliation protection")
        
        # Check investigation procedures
        investigation_procedures = protection_data.get("investigation_procedures", {})
        investigation_adequate = True
        
        for requirement in self.whistleblower_requirements["investigation_procedures"]:
            if not investigation_procedures.get(requirement):
                deficiencies.append(f"Missing investigation procedure: {requirement}")
                investigation_adequate = False
                recommendations.append(f"Implement {requirement} for investigation procedures")
        
        # Check remedial actions
        remedial_actions = protection_data.get("remedial_actions", {})
        remedial_available = True
        
        for requirement in self.whistleblower_requirements["remedial_actions"]:
            if not remedial_actions.get(requirement):
                deficiencies.append(f"Missing remedial action: {requirement}")
                remedial_available = False
                recommendations.append(f"Implement {requirement} for remedial actions")
        
        # Check documentation requirements
        documentation = protection_data.get("documentation_requirements", {})
        documentation_complete = True
        
        for requirement in self.whistleblower_requirements["documentation_requirements"]:
            if not documentation.get(requirement):
                deficiencies.append(f"Missing documentation requirement: {requirement}")
                documentation_complete = False
                recommendations.append(f"Implement {requirement} for documentation")
        
        # Determine overall protection status
        if not confidential_available or not retaliation_active or not investigation_adequate:
            protection_status = WhistleblowerStatus.NON_COMPLIANT
        elif not remedial_available or not documentation_complete:
            protection_status = WhistleblowerStatus.PARTIAL
        elif deficiencies:
            protection_status = WhistleblowerStatus.INACTIVE
        else:
            protection_status = WhistleblowerStatus.ACTIVE
        
        return WhistleblowerValidation(
            protection_status=protection_status,
            confidential_reporting_available=confidential_available,
            retaliation_protection_active=retaliation_active,
            investigation_procedures_adequate=investigation_adequate,
            remedial_actions_available=remedial_available,
            documentation_complete=documentation_complete,
            deficiencies=deficiencies,
            recommendations=recommendations,
            evidence=protection_data,
            validated_at=datetime.now(timezone.utc)
        )
    
    def validate_whistleblower_report(self, report: WhistleblowerReport) -> Dict[str, Any]:
        """
        Validate a whistleblower report.
        
        Args:
            report: Whistleblower report to validate
            
        Returns:
            Validation result for the report
        """
        validation_result = {
            "report_id": report.report_id,
            "valid": True,
            "issues": [],
            "recommendations": []
        }
        
        # Check if report has required information
        if not report.description or len(report.description.strip()) < 10:
            validation_result["valid"] = False
            validation_result["issues"].append("Report description is too short or missing")
            validation_result["recommendations"].append("Provide detailed description of the issue")
        
        # Check confidentiality level
        valid_confidentiality_levels = ["public", "confidential", "anonymous"]
        if report.confidentiality_level not in valid_confidentiality_levels:
            validation_result["valid"] = False
            validation_result["issues"].append("Invalid confidentiality level")
            validation_result["recommendations"].append("Use valid confidentiality level")
        
        # Check if reporter ID is provided for non-anonymous reports
        if report.confidentiality_level != "anonymous" and not report.reporter_id:
            validation_result["valid"] = False
            validation_result["issues"].append("Reporter ID required for non-anonymous reports")
            validation_result["recommendations"].append("Provide reporter ID or mark as anonymous")
        
        # Check investigation status
        valid_investigation_statuses = ["pending", "in_progress", "completed", "closed"]
        if report.investigation_status not in valid_investigation_statuses:
            validation_result["valid"] = False
            validation_result["issues"].append("Invalid investigation status")
            validation_result["recommendations"].append("Use valid investigation status")
        
        # Check resolution status
        valid_resolution_statuses = ["pending", "resolved", "unresolved", "dismissed"]
        if report.resolution_status not in valid_resolution_statuses:
            validation_result["valid"] = False
            validation_result["issues"].append("Invalid resolution status")
            validation_result["recommendations"].append("Use valid resolution status")
        
        return validation_result
    
    def generate_whistleblower_report(self, protection_data: Dict[str, Any], 
                                    reports: List[WhistleblowerReport]) -> Dict[str, Any]:
        """Generate a comprehensive whistleblower protection report."""
        validation = self.validate_whistleblower_protection(protection_data)
        
        # Analyze reports
        total_reports = len(reports)
        anonymous_reports = len([r for r in reports if r.confidentiality_level == "anonymous"])
        retaliation_claims = len([r for r in reports if r.retaliation_claimed])
        resolved_reports = len([r for r in reports if r.resolution_status == "resolved"])
        
        return {
            "report_type": "Whistleblower_Protection_Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "protection_status": validation.protection_status.value,
            "compliance_summary": {
                "confidential_reporting_available": validation.confidential_reporting_available,
                "retaliation_protection_active": validation.retaliation_protection_active,
                "investigation_procedures_adequate": validation.investigation_procedures_adequate,
                "remedial_actions_available": validation.remedial_actions_available,
                "documentation_complete": validation.documentation_complete
            },
            "report_analysis": {
                "total_reports": total_reports,
                "anonymous_reports": anonymous_reports,
                "retaliation_claims": retaliation_claims,
                "resolved_reports": resolved_reports,
                "resolution_rate": resolved_reports / total_reports if total_reports > 0 else 0
            },
            "deficiencies": validation.deficiencies,
            "recommendations": validation.recommendations,
            "compliance_status": {
                "overall_compliant": validation.protection_status == WhistleblowerStatus.ACTIVE,
                "requires_improvement": validation.protection_status in [WhistleblowerStatus.PARTIAL, WhistleblowerStatus.INACTIVE],
                "non_compliant": validation.protection_status == WhistleblowerStatus.NON_COMPLIANT
            }
        }
