#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# Part of IOA Core (Open Source Edition).

"""
Boroscope-Inspired Ethics Example (IOA Original)

This example demonstrates ethics governance for AI systems in industrial inspection
contexts, inspired by the Aletheia Framework v2.0 use cases but using IOA-original
criteria and prompts.

NOTE: Inspired by Aletheia v2.0 (CC BY-ND 4.0) but NOT a derivative.
This example uses IOA-original prompts and criteria names.

Attribution: Aletheia Framework v2.0 by Rolls-Royce Civil Aerospace (CC BY-ND 4.0)
Reference: https://www.rolls-royce.com/innovation/the-aletheia-framework.aspx
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Add IOA Core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cartridges.ethics.policy_ethics import precheck, EthicsDecision


class IndustrialInspectionEthics:
    """
    Ethics governance for AI-powered industrial inspection systems.
    
    This class demonstrates how IOA Core can enforce ethical principles
    in industrial AI applications, inspired by Aletheia Framework use cases
    but using IOA-original implementation.
    """
    
    def __init__(self):
        self.inspection_history = []
        self.ethics_violations = []
    
    def validate_inspection_request(self, request: Dict[str, Any]) -> EthicsDecision:
        """
        Validate an industrial inspection request against ethics principles.
        
        Args:
            request: Inspection request containing equipment details, location, etc.
            
        Returns:
            EthicsDecision with allow/reject decision and reasoning
        """
        # IOA-original ethics checks for industrial inspection
        reasons = []
        confidence = 1.0
        
        # Check for safety-critical equipment
        if self._is_safety_critical_equipment(request):
            if not self._has_proper_authorization(request):
                reasons.append("Safety-critical equipment requires proper authorization")
                confidence *= 0.3
        
        # Check for data minimization
        if self._exceeds_data_minimization(request):
            reasons.append("Inspection request exceeds necessary data collection")
            confidence *= 0.7
        
        # Check for transparency requirements
        if not self._meets_transparency_standards(request):
            reasons.append("Inspection lacks required transparency documentation")
            confidence *= 0.6
        
        # Check for bias in inspection criteria
        if self._contains_biased_criteria(request):
            reasons.append("Inspection criteria may contain bias")
            confidence *= 0.5
        
        # Determine final decision
        allow = confidence >= 0.5 and len(reasons) == 0
        
        decision = EthicsDecision(
            allow=allow,
            reasons=reasons,
            confidence=confidence,
            metadata={
                "inspection_type": request.get("type", "unknown"),
                "equipment_id": request.get("equipment_id", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
                "ethics_checks": [
                    "safety_authorization",
                    "data_minimization", 
                    "transparency_standards",
                    "bias_detection"
                ]
            }
        )
        
        # Log the decision
        self.inspection_history.append({
            "request": request,
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if not allow:
            self.ethics_violations.append(decision)
        
        return decision
    
    def _is_safety_critical_equipment(self, request: Dict[str, Any]) -> bool:
        """Check if equipment is safety-critical."""
        safety_critical_types = [
            "pressure_vessel", "turbine_blade", "fuel_system", 
            "brake_system", "structural_component"
        ]
        return request.get("equipment_type", "").lower() in safety_critical_types
    
    def _has_proper_authorization(self, request: Dict[str, Any]) -> bool:
        """Check if request has proper authorization."""
        required_auth = ["inspector_certification", "safety_clearance", "supervisor_approval"]
        return all(auth in request.get("authorization", []) for auth in required_auth)
    
    def _exceeds_data_minimization(self, request: Dict[str, Any]) -> bool:
        """Check if request exceeds data minimization principles."""
        # Simple check: if collecting more data than necessary for inspection type
        inspection_type = request.get("type", "")
        data_points = request.get("data_points", [])
        
        if inspection_type == "visual" and len(data_points) > 10:
            return True
        elif inspection_type == "dimensional" and len(data_points) > 50:
            return True
        elif inspection_type == "material" and len(data_points) > 20:
            return True
        
        return False
    
    def _meets_transparency_standards(self, request: Dict[str, Any]) -> bool:
        """Check if request meets transparency standards."""
        required_docs = ["inspection_protocol", "data_usage_policy", "retention_schedule"]
        return all(doc in request.get("documentation", {}) for doc in required_docs)
    
    def _contains_biased_criteria(self, request: Dict[str, Any]) -> bool:
        """Check if inspection criteria contain bias."""
        criteria = request.get("criteria", {})
        
        # Check for discriminatory language
        biased_terms = ["prefer", "avoid", "typically", "usually", "generally"]
        criteria_text = str(criteria).lower()
        
        return any(term in criteria_text for term in biased_terms)
    
    def generate_ethics_report(self) -> Dict[str, Any]:
        """Generate an ethics compliance report."""
        total_inspections = len(self.inspection_history)
        violations = len(self.ethics_violations)
        compliance_rate = (total_inspections - violations) / total_inspections if total_inspections > 0 else 1.0
        
        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "total_inspections": total_inspections,
            "ethics_violations": violations,
            "compliance_rate": compliance_rate,
            "violation_breakdown": self._analyze_violations(),
            "recommendations": self._generate_recommendations()
        }
    
    def _analyze_violations(self) -> Dict[str, int]:
        """Analyze violation patterns."""
        breakdown = {}
        for violation in self.ethics_violations:
            for reason in violation.reasons:
                breakdown[reason] = breakdown.get(reason, 0) + 1
        return breakdown
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on violation patterns."""
        recommendations = []
        
        if not self.ethics_violations:
            recommendations.append("No ethics violations detected. Continue current practices.")
        else:
            if any("authorization" in v.reasons for v in self.ethics_violations):
                recommendations.append("Implement stricter authorization requirements for safety-critical equipment")
            
            if any("data_minimization" in v.reasons for v in self.ethics_violations):
                recommendations.append("Review data collection practices to ensure minimization principles")
            
            if any("transparency" in v.reasons for v in self.ethics_violations):
                recommendations.append("Enhance documentation and transparency standards")
            
            if any("bias" in v.reasons for v in self.ethics_violations):
                recommendations.append("Review inspection criteria for potential bias")
        
        return recommendations


def run_boroscope_example():
    """Run the boroscope-inspired ethics example."""
    print("🔍 Industrial Inspection Ethics Example (Aletheia-inspired)")
    print("=" * 60)
    
    # Initialize ethics system
    ethics = IndustrialInspectionEthics()
    
    # Example inspection requests
    test_requests = [
        {
            "type": "visual",
            "equipment_type": "pressure_vessel",
            "equipment_id": "PV-001",
            "data_points": ["crack_detection", "corrosion_assessment", "weld_integrity"],
            "authorization": ["inspector_certification", "safety_clearance", "supervisor_approval"],
            "documentation": {
                "inspection_protocol": "standard_visual_inspection_v2.1",
                "data_usage_policy": "inspection_data_retention_policy",
                "retention_schedule": "7_years_archival"
            },
            "criteria": {
                "crack_threshold": "0.1mm",
                "corrosion_level": "moderate",
                "weld_quality": "acceptable"
            }
        },
        {
            "type": "dimensional",
            "equipment_type": "turbine_blade",
            "equipment_id": "TB-002",
            "data_points": [f"measurement_{i}" for i in range(60)],  # Exceeds minimization
            "authorization": ["inspector_certification"],  # Missing safety clearance
            "documentation": {
                "inspection_protocol": "dimensional_measurement_v1.5"
                # Missing other required docs
            },
            "criteria": {
                "tolerance": "±0.05mm",
                "surface_finish": "Ra 0.8"
            }
        },
        {
            "type": "material",
            "equipment_type": "structural_component",
            "equipment_id": "SC-003",
            "data_points": ["composition", "hardness", "tensile_strength"],
            "authorization": ["inspector_certification", "safety_clearance", "supervisor_approval"],
            "documentation": {
                "inspection_protocol": "material_analysis_v3.0",
                "data_usage_policy": "material_data_retention",
                "retention_schedule": "10_years_archival"
            },
            "criteria": {
                "composition_analysis": "full_spectrum",
                "hardness_range": "prefer_higher_values",  # Potential bias
                "strength_requirements": "typically_met"
            }
        }
    ]
    
    # Process each request
    for i, request in enumerate(test_requests, 1):
        print(f"\n📋 Processing Inspection Request {i}")
        print(f"Equipment: {request['equipment_type']} ({request['equipment_id']})")
        print(f"Type: {request['type']}")
        
        decision = ethics.validate_inspection_request(request)
        
        if decision.allow:
            print("✅ APPROVED - Request meets ethics standards")
        else:
            print("❌ REJECTED - Ethics violations detected")
            for reason in decision.reasons:
                print(f"   • {reason}")
        
        print(f"Confidence: {decision.confidence:.2f}")
    
    # Generate ethics report
    print("\n📊 Ethics Compliance Report")
    print("=" * 40)
    
    report = ethics.generate_ethics_report()
    print(f"Total Inspections: {report['total_inspections']}")
    print(f"Violations: {report['ethics_violations']}")
    print(f"Compliance Rate: {report['compliance_rate']:.1%}")
    
    if report['violation_breakdown']:
        print("\nViolation Breakdown:")
        for reason, count in report['violation_breakdown'].items():
            print(f"  • {reason}: {count}")
    
    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    print("\n🎯 Example Complete - Ethics governance demonstrated")
    return report


if __name__ == "__main__":
    run_boroscope_example()
