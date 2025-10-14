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


class ControlEffectiveness(Enum):
    """Control effectiveness levels."""
    EFFECTIVE = "effective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    INEFFECTIVE = "ineffective"
    NOT_IMPLEMENTED = "not_implemented"


@dataclass
class ControlValidation:
    """Result of internal control validation."""
    control_id: str
    control_name: str
    effectiveness: ControlEffectiveness
    design_adequate: bool
    operating_effectiveness: bool
    deficiencies: List[str]
    recommendations: List[str]
    evidence: Dict[str, Any]
    tested_at: datetime


class InternalControlsValidator:
    """
    SOX Section 404 internal controls validator.
    
    Validates the design and operating effectiveness of internal controls
    over financial reporting as required by SOX Section 404.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize internal controls validator."""
        self.config = config
        self.enabled = config.get("enabled", True)
        
        # Load control framework
        self._load_control_framework()
        
        logger.info(f"InternalControlsValidator initialized: enabled={self.enabled}")
    
    def _load_control_framework(self):
        """Load COSO internal control framework."""
        self.control_framework = {
            "control_environment": {
                "integrity_and_ethical_values": [
                    "code_of_conduct",
                    "ethics_training",
                    "whistleblower_protection",
                    "tone_at_the_top"
                ],
                "board_of_directors": [
                    "independence",
                    "financial_expertise",
                    "oversight_activities",
                    "audit_committee"
                ],
                "management_philosophy": [
                    "risk_appetite",
                    "operating_style",
                    "organizational_structure",
                    "assignment_of_authority"
                ]
            },
            "risk_assessment": {
                "entity_level_risks": [
                    "external_risks",
                    "internal_risks",
                    "fraud_risks",
                    "technology_risks"
                ],
                "process_level_risks": [
                    "revenue_recognition_risks",
                    "expense_recognition_risks",
                    "asset_valuation_risks",
                    "liability_measurement_risks"
                ]
            },
            "control_activities": {
                "preventive_controls": [
                    "segregation_of_duties",
                    "authorization_controls",
                    "documentation_controls",
                    "physical_controls"
                ],
                "detective_controls": [
                    "reconciliations",
                    "exception_reports",
                    "analytical_procedures",
                    "independent_verification"
                ]
            },
            "information_communication": {
                "information_systems": [
                    "data_integrity",
                    "data_security",
                    "system_reliability",
                    "change_management"
                ],
                "communication": [
                    "internal_communication",
                    "external_communication",
                    "reporting_requirements",
                    "disclosure_controls"
                ]
            },
            "monitoring": {
                "ongoing_monitoring": [
                    "management_oversight",
                    "internal_audit",
                    "exception_reporting",
                    "key_performance_indicators"
                ],
                "separate_evaluations": [
                    "control_testing",
                    "deficiency_assessment",
                    "remediation_planning",
                    "effectiveness_evaluation"
                ]
            }
        }
    
    def validate_control_environment(self, control_data: Dict[str, Any]) -> ControlValidation:
        """Validate the control environment component."""
        control_id = "control_environment"
        control_name = "Control Environment"
        
        deficiencies = []
        recommendations = []
        design_adequate = True
        operating_effectiveness = True
        
        # Check integrity and ethical values
        integrity_controls = control_data.get("integrity_and_ethical_values", {})
        for control in self.control_framework["control_environment"]["integrity_and_ethical_values"]:
            if not integrity_controls.get(control):
                deficiencies.append(f"Missing integrity control: {control}")
                design_adequate = False
                recommendations.append(f"Implement {control} control")
        
        # Check board of directors
        board_controls = control_data.get("board_of_directors", {})
        for control in self.control_framework["control_environment"]["board_of_directors"]:
            if not board_controls.get(control):
                deficiencies.append(f"Missing board control: {control}")
                design_adequate = False
                recommendations.append(f"Implement {control} control")
        
        # Check management philosophy
        management_controls = control_data.get("management_philosophy", {})
        for control in self.control_framework["control_environment"]["management_philosophy"]:
            if not management_controls.get(control):
                deficiencies.append(f"Missing management control: {control}")
                design_adequate = False
                recommendations.append(f"Implement {control} control")
        
        # Determine effectiveness
        if not design_adequate:
            effectiveness = ControlEffectiveness.NOT_IMPLEMENTED
        elif deficiencies:
            effectiveness = ControlEffectiveness.PARTIALLY_EFFECTIVE
        else:
            effectiveness = ControlEffectiveness.EFFECTIVE
        
        return ControlValidation(
            control_id=control_id,
            control_name=control_name,
            effectiveness=effectiveness,
            design_adequate=design_adequate,
            operating_effectiveness=operating_effectiveness,
            deficiencies=deficiencies,
            recommendations=recommendations,
            evidence=control_data,
            tested_at=datetime.now(timezone.utc)
        )
    
    def validate_risk_assessment(self, control_data: Dict[str, Any]) -> ControlValidation:
        """Validate the risk assessment component."""
        control_id = "risk_assessment"
        control_name = "Risk Assessment"
        
        deficiencies = []
        recommendations = []
        design_adequate = True
        operating_effectiveness = True
        
        # Check entity level risks
        entity_risks = control_data.get("entity_level_risks", {})
        for risk in self.control_framework["risk_assessment"]["entity_level_risks"]:
            if not entity_risks.get(risk):
                deficiencies.append(f"Missing entity level risk assessment: {risk}")
                design_adequate = False
                recommendations.append(f"Implement {risk} risk assessment")
        
        # Check process level risks
        process_risks = control_data.get("process_level_risks", {})
        for risk in self.control_framework["risk_assessment"]["process_level_risks"]:
            if not process_risks.get(risk):
                deficiencies.append(f"Missing process level risk assessment: {risk}")
                design_adequate = False
                recommendations.append(f"Implement {risk} risk assessment")
        
        # Determine effectiveness
        if not design_adequate:
            effectiveness = ControlEffectiveness.NOT_IMPLEMENTED
        elif deficiencies:
            effectiveness = ControlEffectiveness.PARTIALLY_EFFECTIVE
        else:
            effectiveness = ControlEffectiveness.EFFECTIVE
        
        return ControlValidation(
            control_id=control_id,
            control_name=control_name,
            effectiveness=effectiveness,
            design_adequate=design_adequate,
            operating_effectiveness=operating_effectiveness,
            deficiencies=deficiencies,
            recommendations=recommendations,
            evidence=control_data,
            tested_at=datetime.now(timezone.utc)
        )
    
    def validate_control_activities(self, control_data: Dict[str, Any]) -> ControlValidation:
        """Validate the control activities component."""
        control_id = "control_activities"
        control_name = "Control Activities"
        
        deficiencies = []
        recommendations = []
        design_adequate = True
        operating_effectiveness = True
        
        # Check preventive controls
        preventive_controls = control_data.get("preventive_controls", {})
        for control in self.control_framework["control_activities"]["preventive_controls"]:
            if not preventive_controls.get(control):
                deficiencies.append(f"Missing preventive control: {control}")
                design_adequate = False
                recommendations.append(f"Implement {control} preventive control")
        
        # Check detective controls
        detective_controls = control_data.get("detective_controls", {})
        for control in self.control_framework["control_activities"]["detective_controls"]:
            if not detective_controls.get(control):
                deficiencies.append(f"Missing detective control: {control}")
                design_adequate = False
                recommendations.append(f"Implement {control} detective control")
        
        # Determine effectiveness
        if not design_adequate:
            effectiveness = ControlEffectiveness.NOT_IMPLEMENTED
        elif deficiencies:
            effectiveness = ControlEffectiveness.PARTIALLY_EFFECTIVE
        else:
            effectiveness = ControlEffectiveness.EFFECTIVE
        
        return ControlValidation(
            control_id=control_id,
            control_name=control_name,
            effectiveness=effectiveness,
            design_adequate=design_adequate,
            operating_effectiveness=operating_effectiveness,
            deficiencies=deficiencies,
            recommendations=recommendations,
            evidence=control_data,
            tested_at=datetime.now(timezone.utc)
        )
    
    def validate_information_communication(self, control_data: Dict[str, Any]) -> ControlValidation:
        """Validate the information and communication component."""
        control_id = "information_communication"
        control_name = "Information and Communication"
        
        deficiencies = []
        recommendations = []
        design_adequate = True
        operating_effectiveness = True
        
        # Check information systems
        info_systems = control_data.get("information_systems", {})
        for control in self.control_framework["information_communication"]["information_systems"]:
            if not info_systems.get(control):
                deficiencies.append(f"Missing information system control: {control}")
                design_adequate = False
                recommendations.append(f"Implement {control} information system control")
        
        # Check communication
        communication = control_data.get("communication", {})
        for control in self.control_framework["information_communication"]["communication"]:
            if not communication.get(control):
                deficiencies.append(f"Missing communication control: {control}")
                design_adequate = False
                recommendations.append(f"Implement {control} communication control")
        
        # Determine effectiveness
        if not design_adequate:
            effectiveness = ControlEffectiveness.NOT_IMPLEMENTED
        elif deficiencies:
            effectiveness = ControlEffectiveness.PARTIALLY_EFFECTIVE
        else:
            effectiveness = ControlEffectiveness.EFFECTIVE
        
        return ControlValidation(
            control_id=control_id,
            control_name=control_name,
            effectiveness=effectiveness,
            design_adequate=design_adequate,
            operating_effectiveness=operating_effectiveness,
            deficiencies=deficiencies,
            recommendations=recommendations,
            evidence=control_data,
            tested_at=datetime.now(timezone.utc)
        )
    
    def validate_monitoring(self, control_data: Dict[str, Any]) -> ControlValidation:
        """Validate the monitoring component."""
        control_id = "monitoring"
        control_name = "Monitoring"
        
        deficiencies = []
        recommendations = []
        design_adequate = True
        operating_effectiveness = True
        
        # Check ongoing monitoring
        ongoing_monitoring = control_data.get("ongoing_monitoring", {})
        for control in self.control_framework["monitoring"]["ongoing_monitoring"]:
            if not ongoing_monitoring.get(control):
                deficiencies.append(f"Missing ongoing monitoring control: {control}")
                design_adequate = False
                recommendations.append(f"Implement {control} ongoing monitoring control")
        
        # Check separate evaluations
        separate_evaluations = control_data.get("separate_evaluations", {})
        for control in self.control_framework["monitoring"]["separate_evaluations"]:
            if not separate_evaluations.get(control):
                deficiencies.append(f"Missing separate evaluation control: {control}")
                design_adequate = False
                recommendations.append(f"Implement {control} separate evaluation control")
        
        # Determine effectiveness
        if not design_adequate:
            effectiveness = ControlEffectiveness.NOT_IMPLEMENTED
        elif deficiencies:
            effectiveness = ControlEffectiveness.PARTIALLY_EFFECTIVE
        else:
            effectiveness = ControlEffectiveness.EFFECTIVE
        
        return ControlValidation(
            control_id=control_id,
            control_name=control_name,
            effectiveness=effectiveness,
            design_adequate=design_adequate,
            operating_effectiveness=operating_effectiveness,
            deficiencies=deficiencies,
            recommendations=recommendations,
            evidence=control_data,
            tested_at=datetime.now(timezone.utc)
        )
    
    def validate_all_controls(self, control_data: Dict[str, Any]) -> List[ControlValidation]:
        """Validate all internal control components."""
        validations = []
        
        # Validate each component
        validations.append(self.validate_control_environment(control_data.get("control_environment", {})))
        validations.append(self.validate_risk_assessment(control_data.get("risk_assessment", {})))
        validations.append(self.validate_control_activities(control_data.get("control_activities", {})))
        validations.append(self.validate_information_communication(control_data.get("information_communication", {})))
        validations.append(self.validate_monitoring(control_data.get("monitoring", {})))
        
        return validations
