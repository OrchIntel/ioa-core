""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CertificationStatus(Enum):
    """Executive certification status."""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    MISSING = "missing"


@dataclass
class ExecutiveCert:
    """Executive certification data."""
    certifier_id: str
    certifier_name: str
    certifier_title: str
    certification_date: datetime
    expiration_date: datetime
    section_302_compliant: bool
    section_906_compliant: bool
    digital_signature: Optional[str] = None
    evidence: Dict[str, Any] = None


@dataclass
class CertValidation:
    """Result of executive certification validation."""
    certifier_id: str
    status: CertificationStatus
    section_302_valid: bool
    section_906_valid: bool
    deficiencies: List[str]
    recommendations: List[str]
    evidence: Dict[str, Any]
    validated_at: datetime


class ExecutiveCertificationValidator:
    """
    SOX executive certification validator.
    
    Validates executive certifications required by SOX Sections 302 and 906.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize executive certification validator."""
        self.config = config
        self.enabled = config.get("enabled", True)
        
        # Load certification requirements
        self._load_certification_requirements()
        
        logger.info(f"ExecutiveCertificationValidator initialized: enabled={self.enabled}")
    
    def _load_certification_requirements(self):
        """Load SOX executive certification requirements."""
        self.certification_requirements = {
            "section_302": {
                "ceo_certification": [
                    "reviewed_financial_statements",
                    "no_material_misstatements",
                    "no_material_omissions",
                    "fair_presentation",
                    "disclosure_controls_effective",
                    "internal_controls_effective",
                    "fraud_disclosed",
                    "material_changes_disclosed"
                ],
                "cfo_certification": [
                    "reviewed_financial_statements",
                    "no_material_misstatements",
                    "no_material_omissions",
                    "fair_presentation",
                    "disclosure_controls_effective",
                    "internal_controls_effective",
                    "fraud_disclosed",
                    "material_changes_disclosed"
                ]
            },
            "section_906": {
                "periodic_certification": [
                    "accuracy_verification",
                    "completeness_verification",
                    "fair_presentation",
                    "compliance_verification",
                    "no_false_statements",
                    "no_material_omissions"
                ]
            }
        }
    
    def validate_executive_certification(self, cert: ExecutiveCert) -> CertValidation:
        """
        Validate an executive certification.
        
        Args:
            cert: Executive certification to validate
            
        Returns:
            CertValidation with validation results
        """
        deficiencies = []
        recommendations = []
        section_302_valid = True
        section_906_valid = True
        
        # Check if certification is current
        current_time = datetime.now(timezone.utc)
        if cert.expiration_date < current_time:
            deficiencies.append("Executive certification has expired")
            status = CertificationStatus.EXPIRED
            section_302_valid = False
            section_906_valid = False
            recommendations.append("Obtain current executive certification")
        else:
            status = CertificationStatus.VALID
        
        # Validate Section 302 requirements
        if cert.section_302_compliant:
            # Check specific requirements based on certifier title
            if cert.certifier_title.lower() in ["ceo", "chief executive officer"]:
                requirements = self.certification_requirements["section_302"]["ceo_certification"]
            elif cert.certifier_title.lower() in ["cfo", "chief financial officer"]:
                requirements = self.certification_requirements["section_302"]["cfo_certification"]
            else:
                requirements = []
                deficiencies.append("Invalid certifier title for Section 302")
                section_302_valid = False
            
            # Validate each requirement
            for requirement in requirements:
                if not cert.evidence.get(requirement):
                    deficiencies.append(f"Missing Section 302 requirement: {requirement}")
                    section_302_valid = False
                    recommendations.append(f"Ensure {requirement} is documented")
        else:
            deficiencies.append("Section 302 compliance not declared")
            section_302_valid = False
            recommendations.append("Ensure Section 302 compliance is properly declared")
        
        # Validate Section 906 requirements
        if cert.section_906_compliant:
            requirements = self.certification_requirements["section_906"]["periodic_certification"]
            
            # Validate each requirement
            for requirement in requirements:
                if not cert.evidence.get(requirement):
                    deficiencies.append(f"Missing Section 906 requirement: {requirement}")
                    section_906_valid = False
                    recommendations.append(f"Ensure {requirement} is documented")
        else:
            deficiencies.append("Section 906 compliance not declared")
            section_906_valid = False
            recommendations.append("Ensure Section 906 compliance is properly declared")
        
        # Check digital signature
        if not cert.digital_signature:
            deficiencies.append("Digital signature not provided")
            recommendations.append("Implement digital signature for executive certifications")
        
        # Determine overall status
        if not section_302_valid or not section_906_valid:
            if status == CertificationStatus.VALID:
                status = CertificationStatus.INVALID
        
        return CertValidation(
            certifier_id=cert.certifier_id,
            status=status,
            section_302_valid=section_302_valid,
            section_906_valid=section_906_valid,
            deficiencies=deficiencies,
            recommendations=recommendations,
            evidence=cert.evidence or {},
            validated_at=datetime.now(timezone.utc)
        )
    
    def validate_ceo_certification(self, cert: ExecutiveCert) -> CertValidation:
        """Validate CEO certification specifically."""
        if cert.certifier_title.lower() not in ["ceo", "chief executive officer"]:
            return CertValidation(
                certifier_id=cert.certifier_id,
                status=CertificationStatus.INVALID,
                section_302_valid=False,
                section_906_valid=False,
                deficiencies=["Invalid certifier title for CEO certification"],
                recommendations=["Ensure certifier is CEO or Chief Executive Officer"],
                evidence=cert.evidence or {},
                validated_at=datetime.now(timezone.utc)
            )
        
        return self.validate_executive_certification(cert)
    
    def validate_cfo_certification(self, cert: ExecutiveCert) -> CertValidation:
        """Validate CFO certification specifically."""
        if cert.certifier_title.lower() not in ["cfo", "chief financial officer"]:
            return CertValidation(
                certifier_id=cert.certifier_id,
                status=CertificationStatus.INVALID,
                section_302_valid=False,
                section_906_valid=False,
                deficiencies=["Invalid certifier title for CFO certification"],
                recommendations=["Ensure certifier is CFO or Chief Financial Officer"],
                evidence=cert.evidence or {},
                validated_at=datetime.now(timezone.utc)
            )
        
        return self.validate_executive_certification(cert)
    
    def validate_all_certifications(self, certifications: List[ExecutiveCert]) -> List[CertValidation]:
        """Validate all executive certifications."""
        validations = []
        
        for cert in certifications:
            validation = self.validate_executive_certification(cert)
            validations.append(validation)
        
        return validations
    
    def generate_certification_report(self, validations: List[CertValidation]) -> Dict[str, Any]:
        """Generate a comprehensive certification report."""
        total_certifications = len(validations)
        valid_certifications = len([v for v in validations if v.status == CertificationStatus.VALID])
        expired_certifications = len([v for v in validations if v.status == CertificationStatus.EXPIRED])
        invalid_certifications = len([v for v in validations if v.status == CertificationStatus.INVALID])
        missing_certifications = len([v for v in validations if v.status == CertificationStatus.MISSING])
        
        section_302_valid = len([v for v in validations if v.section_302_valid])
        section_906_valid = len([v for v in validations if v.section_906_valid])
        
        all_deficiencies = []
        all_recommendations = []
        
        for validation in validations:
            all_deficiencies.extend(validation.deficiencies)
            all_recommendations.extend(validation.recommendations)
        
        return {
            "report_type": "Executive_Certification_Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_certifications": total_certifications,
                "valid_certifications": valid_certifications,
                "expired_certifications": expired_certifications,
                "invalid_certifications": invalid_certifications,
                "missing_certifications": missing_certifications,
                "section_302_compliant": section_302_valid,
                "section_906_compliant": section_906_valid
            },
            "compliance_status": {
                "overall_compliant": valid_certifications == total_certifications and section_302_valid == total_certifications and section_906_valid == total_certifications,
                "section_302_compliant": section_302_valid == total_certifications,
                "section_906_compliant": section_906_valid == total_certifications
            },
            "deficiencies": all_deficiencies,
            "recommendations": all_recommendations,
            "detailed_validations": [
                {
                    "certifier_id": v.certifier_id,
                    "status": v.status.value,
                    "section_302_valid": v.section_302_valid,
                    "section_906_valid": v.section_906_valid,
                    "deficiencies": v.deficiencies,
                    "recommendations": v.recommendations
                }
                for v in validations
            ]
        }
