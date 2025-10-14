#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# Part of IOA Core (Open Source Edition).

"""
Oncology-Inspired Ethics Example (IOA Original)

This example demonstrates ethics governance for AI systems in medical/oncology
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


class MedicalAIEthics:
    """
    Ethics governance for AI-powered medical systems.
    
    This class demonstrates how IOA Core can enforce ethical principles
    in medical AI applications, inspired by Aletheia Framework use cases
    but using IOA-original implementation.
    """
    
    def __init__(self):
        self.medical_requests = []
        self.ethics_violations = []
        self.patient_consent_log = []
    
    def validate_medical_request(self, request: Dict[str, Any]) -> EthicsDecision:
        """
        Validate a medical AI request against ethics principles.
        
        Args:
            request: Medical request containing patient data, analysis type, etc.
            
        Returns:
            EthicsDecision with allow/reject decision and reasoning
        """
        # IOA-original ethics checks for medical AI
        reasons = []
        confidence = 1.0
        
        # Check for patient consent
        if not self._has_valid_consent(request):
            reasons.append("Valid patient consent required for medical data processing")
            confidence *= 0.2
        
        # Check for data minimization in medical context
        if self._exceeds_medical_data_minimization(request):
            reasons.append("Medical data collection exceeds necessary scope")
            confidence *= 0.4
        
        # Check for bias in medical algorithms
        if self._contains_medical_bias(request):
            reasons.append("Medical analysis may contain algorithmic bias")
            confidence *= 0.3
        
        # Check for transparency in medical decisions
        if not self._meets_medical_transparency(request):
            reasons.append("Medical AI decisions require full transparency")
            confidence *= 0.5
        
        # Check for fairness across patient populations
        if self._violates_fairness_principles(request):
            reasons.append("Medical analysis violates fairness principles")
            confidence *= 0.4
        
        # Check for accuracy requirements
        if not self._meets_accuracy_standards(request):
            reasons.append("Medical AI must meet high accuracy standards")
            confidence *= 0.6
        
        # Determine final decision
        allow = confidence >= 0.5 and len(reasons) == 0
        
        decision = EthicsDecision(
            allow=allow,
            reasons=reasons,
            confidence=confidence,
            metadata={
                "analysis_type": request.get("analysis_type", "unknown"),
                "patient_id": request.get("patient_id", "anonymous"),
                "timestamp": datetime.utcnow().isoformat(),
                "ethics_checks": [
                    "patient_consent",
                    "data_minimization",
                    "bias_detection",
                    "transparency_standards",
                    "fairness_principles",
                    "accuracy_requirements"
                ]
            }
        )
        
        # Log the decision
        self.medical_requests.append({
            "request": request,
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if not allow:
            self.ethics_violations.append(decision)
        
        return decision
    
    def _has_valid_consent(self, request: Dict[str, Any]) -> bool:
        """Check if request has valid patient consent."""
        consent_info = request.get("consent", {})
        
        # Check for explicit consent
        if not consent_info.get("explicit_consent", False):
            return False
        
        # Check for informed consent
        if not consent_info.get("informed_consent", False):
            return False
        
        # Check for consent scope
        analysis_type = request.get("analysis_type", "")
        consent_scope = consent_info.get("scope", [])
        
        return analysis_type in consent_scope
    
    def _exceeds_medical_data_minimization(self, request: Dict[str, Any]) -> bool:
        """Check if medical data collection exceeds minimization principles."""
        analysis_type = request.get("analysis_type", "")
        data_collected = request.get("data_collected", [])
        
        # Define minimal data requirements for different analysis types
        minimal_requirements = {
            "tumor_detection": ["imaging_data", "patient_age", "medical_history"],
            "treatment_recommendation": ["imaging_data", "lab_results", "patient_age", "medical_history", "genetic_markers"],
            "prognosis_analysis": ["imaging_data", "lab_results", "patient_age", "medical_history", "treatment_history"],
            "drug_interaction": ["current_medications", "lab_results", "genetic_markers"]
        }
        
        required_data = minimal_requirements.get(analysis_type, [])
        collected_set = set(data_collected)
        required_set = set(required_data)
        
        # Check if collecting more than necessary
        extra_data = collected_set - required_set
        return len(extra_data) > 2  # Allow some flexibility
    
    def _contains_medical_bias(self, request: Dict[str, Any]) -> bool:
        """Check if medical analysis contains bias."""
        analysis_params = request.get("analysis_parameters", {})
        
        # Check for demographic bias
        if "demographic_filters" in analysis_params:
            filters = analysis_params["demographic_filters"]
            if any(filters.get(key, False) for key in ["age_bias", "gender_bias", "ethnicity_bias"]):
                return True
        
        # Check for training data bias indicators
        training_info = request.get("training_data_info", {})
        if training_info.get("demographic_imbalance", False):
            return True
        
        # Check for algorithm bias indicators
        algorithm_info = request.get("algorithm_info", {})
        if algorithm_info.get("bias_mitigation", "none") == "none":
            return True
        
        return False
    
    def _meets_medical_transparency(self, request: Dict[str, Any]) -> bool:
        """Check if medical AI meets transparency requirements."""
        transparency_requirements = [
            "algorithm_explanation",
            "confidence_scores",
            "decision_rationale",
            "data_sources",
            "limitations"
        ]
        
        transparency_info = request.get("transparency", {})
        return all(req in transparency_info for req in transparency_requirements)
    
    def _violates_fairness_principles(self, request: Dict[str, Any]) -> bool:
        """Check if medical analysis violates fairness principles."""
        fairness_info = request.get("fairness_analysis", {})
        
        # Check for equal treatment across demographics
        if fairness_info.get("demographic_parity", 0) < 0.8:
            return True
        
        # Check for equalized odds
        if fairness_info.get("equalized_odds", 0) < 0.7:
            return True
        
        # Check for calibration across groups
        if fairness_info.get("calibration", 0) < 0.6:
            return True
        
        return False
    
    def _meets_accuracy_standards(self, request: Dict[str, Any]) -> bool:
        """Check if medical AI meets accuracy standards."""
        accuracy_info = request.get("accuracy_metrics", {})
        
        # High accuracy requirements for medical AI
        min_accuracy = 0.95
        min_precision = 0.90
        min_recall = 0.90
        
        return (
            accuracy_info.get("accuracy", 0) >= min_accuracy and
            accuracy_info.get("precision", 0) >= min_precision and
            accuracy_info.get("recall", 0) >= min_recall
        )
    
    def generate_medical_ethics_report(self) -> Dict[str, Any]:
        """Generate a medical ethics compliance report."""
        total_requests = len(self.medical_requests)
        violations = len(self.ethics_violations)
        compliance_rate = (total_requests - violations) / total_requests if total_requests > 0 else 1.0
        
        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "total_medical_requests": total_requests,
            "ethics_violations": violations,
            "compliance_rate": compliance_rate,
            "violation_breakdown": self._analyze_medical_violations(),
            "recommendations": self._generate_medical_recommendations(),
            "patient_privacy_score": self._calculate_privacy_score()
        }
    
    def _analyze_medical_violations(self) -> Dict[str, int]:
        """Analyze medical violation patterns."""
        breakdown = {}
        for violation in self.ethics_violations:
            for reason in violation.reasons:
                breakdown[reason] = breakdown.get(reason, 0) + 1
        return breakdown
    
    def _generate_medical_recommendations(self) -> List[str]:
        """Generate medical-specific recommendations."""
        recommendations = []
        
        if not self.ethics_violations:
            recommendations.append("No medical ethics violations detected. Continue current practices.")
        else:
            if any("consent" in v.reasons for v in self.ethics_violations):
                recommendations.append("Implement stricter patient consent verification")
            
            if any("data_minimization" in v.reasons for v in self.ethics_violations):
                recommendations.append("Review medical data collection for minimization compliance")
            
            if any("bias" in v.reasons for v in self.ethics_violations):
                recommendations.append("Implement bias detection and mitigation in medical algorithms")
            
            if any("transparency" in v.reasons for v in self.ethics_violations):
                recommendations.append("Enhance medical AI transparency and explainability")
            
            if any("fairness" in v.reasons for v in self.ethics_violations):
                recommendations.append("Implement fairness testing across patient demographics")
            
            if any("accuracy" in v.reasons for v in self.ethics_violations):
                recommendations.append("Improve medical AI accuracy and validation processes")
        
        return recommendations
    
    def _calculate_privacy_score(self) -> float:
        """Calculate patient privacy protection score."""
        if not self.medical_requests:
            return 1.0
        
        privacy_violations = 0
        for request_data in self.medical_requests:
            request = request_data["request"]
            if not self._has_valid_consent(request) or self._exceeds_medical_data_minimization(request):
                privacy_violations += 1
        
        return 1.0 - (privacy_violations / len(self.medical_requests))


def run_oncology_example():
    """Run the oncology-inspired ethics example."""
    print("🏥 Medical AI Ethics Example (Aletheia-inspired)")
    print("=" * 60)
    
    # Initialize ethics system
    ethics = MedicalAIEthics()
    
    # Example medical AI requests
    test_requests = [
        {
            "analysis_type": "tumor_detection",
            "patient_id": "P001",
            "data_collected": ["imaging_data", "patient_age", "medical_history"],
            "consent": {
                "explicit_consent": True,
                "informed_consent": True,
                "scope": ["tumor_detection", "imaging_analysis"]
            },
            "analysis_parameters": {
                "demographic_filters": {"age_bias": False, "gender_bias": False, "ethnicity_bias": False}
            },
            "training_data_info": {
                "demographic_imbalance": False
            },
            "algorithm_info": {
                "bias_mitigation": "adversarial_debiasing"
            },
            "transparency": {
                "algorithm_explanation": "CNN-based tumor detection with attention maps",
                "confidence_scores": True,
                "decision_rationale": "Tumor probability based on imaging features",
                "data_sources": "CT scans, MRI images",
                "limitations": "Limited to specific tumor types"
            },
            "fairness_analysis": {
                "demographic_parity": 0.92,
                "equalized_odds": 0.88,
                "calibration": 0.85
            },
            "accuracy_metrics": {
                "accuracy": 0.96,
                "precision": 0.94,
                "recall": 0.93
            }
        },
        {
            "analysis_type": "treatment_recommendation",
            "patient_id": "P002",
            "data_collected": ["imaging_data", "lab_results", "patient_age", "medical_history", "genetic_markers", "family_history", "lifestyle_data"],  # Exceeds minimization
            "consent": {
                "explicit_consent": True,
                "informed_consent": False,  # Missing informed consent
                "scope": ["treatment_recommendation"]
            },
            "analysis_parameters": {
                "demographic_filters": {"age_bias": True, "gender_bias": False, "ethnicity_bias": False}  # Age bias
            },
            "training_data_info": {
                "demographic_imbalance": True  # Training data imbalance
            },
            "algorithm_info": {
                "bias_mitigation": "none"  # No bias mitigation
            },
            "transparency": {
                "algorithm_explanation": "Treatment recommendation algorithm",
                "confidence_scores": True
                # Missing other transparency requirements
            },
            "fairness_analysis": {
                "demographic_parity": 0.75,  # Below threshold
                "equalized_odds": 0.65,  # Below threshold
                "calibration": 0.55  # Below threshold
            },
            "accuracy_metrics": {
                "accuracy": 0.88,  # Below medical standards
                "precision": 0.85,  # Below medical standards
                "recall": 0.87  # Below medical standards
            }
        },
        {
            "analysis_type": "prognosis_analysis",
            "patient_id": "P003",
            "data_collected": ["imaging_data", "lab_results", "patient_age", "medical_history", "treatment_history"],
            "consent": {
                "explicit_consent": True,
                "informed_consent": True,
                "scope": ["prognosis_analysis", "survival_prediction"]
            },
            "analysis_parameters": {
                "demographic_filters": {"age_bias": False, "gender_bias": False, "ethnicity_bias": False}
            },
            "training_data_info": {
                "demographic_imbalance": False
            },
            "algorithm_info": {
                "bias_mitigation": "fairness_constraints"
            },
            "transparency": {
                "algorithm_explanation": "Survival analysis using Cox proportional hazards model",
                "confidence_scores": True,
                "decision_rationale": "Prognosis based on clinical and imaging features",
                "data_sources": "Clinical records, imaging data, lab results",
                "limitations": "Based on historical data, individual outcomes may vary"
            },
            "fairness_analysis": {
                "demographic_parity": 0.95,
                "equalized_odds": 0.92,
                "calibration": 0.90
            },
            "accuracy_metrics": {
                "accuracy": 0.97,
                "precision": 0.95,
                "recall": 0.96
            }
        }
    ]
    
    # Process each request
    for i, request in enumerate(test_requests, 1):
        print(f"\n📋 Processing Medical AI Request {i}")
        print(f"Analysis: {request['analysis_type']}")
        print(f"Patient: {request['patient_id']}")
        
        decision = ethics.validate_medical_request(request)
        
        if decision.allow:
            print("✅ APPROVED - Request meets medical ethics standards")
        else:
            print("❌ REJECTED - Medical ethics violations detected")
            for reason in decision.reasons:
                print(f"   • {reason}")
        
        print(f"Confidence: {decision.confidence:.2f}")
    
    # Generate medical ethics report
    print("\n📊 Medical Ethics Compliance Report")
    print("=" * 45)
    
    report = ethics.generate_medical_ethics_report()
    print(f"Total Medical Requests: {report['total_medical_requests']}")
    print(f"Violations: {report['ethics_violations']}")
    print(f"Compliance Rate: {report['compliance_rate']:.1%}")
    print(f"Patient Privacy Score: {report['patient_privacy_score']:.1%}")
    
    if report['violation_breakdown']:
        print("\nViolation Breakdown:")
        for reason, count in report['violation_breakdown'].items():
            print(f"  • {reason}: {count}")
    
    print("\nMedical Recommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    print("\n🎯 Example Complete - Medical AI ethics governance demonstrated")
    return report


if __name__ == "__main__":
    run_oncology_example()
