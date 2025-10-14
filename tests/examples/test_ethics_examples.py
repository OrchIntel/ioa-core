#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# Part of IOA Core (Open Source Edition).

"""
Test suite for ethics examples (Aletheia-inspired).

This test suite verifies that the ethics examples work correctly and
generate proper evidence bundles and governance decisions.

NOTE: Inspired by Aletheia v2.0 (CC BY-ND 4.0) but NOT a derivative.
This test uses IOA-original test cases and validation logic.

Attribution: Aletheia Framework v2.0 by Rolls-Royce Civil Aerospace (CC BY-ND 4.0)
Reference: https://www.rolls-royce.com/innovation/the-aletheia-framework.aspx
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add IOA Core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from examples.ethics.boroscope_inspired import IndustrialInspectionEthics, run_boroscope_example
from examples.ethics.oncology_inspired import MedicalAIEthics, run_oncology_example


class TestEthicsExamples:
    """Test suite for ethics examples."""
    
    def test_boroscope_ethics_basic_functionality(self):
        """Test basic functionality of boroscope ethics system."""
        ethics = IndustrialInspectionEthics()
        
        # Test valid inspection request
        valid_request = {
            "type": "visual",
            "equipment_type": "pressure_vessel",
            "equipment_id": "PV-001",
            "data_points": ["crack_detection", "corrosion_assessment"],
            "authorization": ["inspector_certification", "safety_clearance", "supervisor_approval"],
            "documentation": {
                "inspection_protocol": "standard_visual_inspection_v2.1",
                "data_usage_policy": "inspection_data_retention_policy",
                "retention_schedule": "7_years_archival"
            },
            "criteria": {
                "crack_threshold": "0.1mm",
                "corrosion_level": "moderate"
            }
        }
        
        decision = ethics.validate_inspection_request(valid_request)
        
        # Should be approved
        assert decision.allow is True
        assert len(decision.reasons) == 0
        assert decision.confidence >= 0.5
        assert "inspection_type" in decision.metadata
        assert decision.metadata["inspection_type"] == "visual"
    
    def test_boroscope_ethics_violation_detection(self):
        """Test violation detection in boroscope ethics system."""
        ethics = IndustrialInspectionEthics()
        
        # Test request with violations
        invalid_request = {
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
                "tolerance": "±0.05mm"
            }
        }
        
        decision = ethics.validate_inspection_request(invalid_request)
        
        # Should be rejected
        assert decision.allow is False
        assert len(decision.reasons) > 0
        assert decision.confidence < 0.5
    
    def test_boroscope_ethics_report_generation(self):
        """Test ethics report generation for boroscope system."""
        ethics = IndustrialInspectionEthics()
        
        # Process some requests
        test_requests = [
            {
                "type": "visual",
                "equipment_type": "pressure_vessel",
                "equipment_id": "PV-001",
                "data_points": ["crack_detection"],
                "authorization": ["inspector_certification", "safety_clearance", "supervisor_approval"],
                "documentation": {
                    "inspection_protocol": "standard_visual_inspection_v2.1",
                    "data_usage_policy": "inspection_data_retention_policy",
                    "retention_schedule": "7_years_archival"
                },
                "criteria": {"crack_threshold": "0.1mm"}
            },
            {
                "type": "dimensional",
                "equipment_type": "turbine_blade",
                "equipment_id": "TB-002",
                "data_points": [f"measurement_{i}" for i in range(60)],
                "authorization": ["inspector_certification"],
                "documentation": {"inspection_protocol": "dimensional_measurement_v1.5"},
                "criteria": {"tolerance": "±0.05mm"}
            }
        ]
        
        for request in test_requests:
            ethics.validate_inspection_request(request)
        
        # Generate report
        report = ethics.generate_ethics_report()
        
        # Verify report structure
        assert "report_timestamp" in report
        assert "total_inspections" in report
        assert "ethics_violations" in report
        assert "compliance_rate" in report
        assert "violation_breakdown" in report
        assert "recommendations" in report
        
        # Verify report content
        assert report["total_inspections"] == 2
        assert report["ethics_violations"] >= 0
        assert 0 <= report["compliance_rate"] <= 1
        assert isinstance(report["recommendations"], list)
    
    def test_medical_ethics_basic_functionality(self):
        """Test basic functionality of medical ethics system."""
        ethics = MedicalAIEthics()
        
        # Test valid medical request
        valid_request = {
            "analysis_type": "tumor_detection",
            "patient_id": "P001",
            "data_collected": ["imaging_data", "patient_age", "medical_history"],
            "consent": {
                "explicit_consent": True,
                "informed_consent": True,
                "scope": ["tumor_detection"]
            },
            "analysis_parameters": {
                "demographic_filters": {"age_bias": False, "gender_bias": False, "ethnicity_bias": False}
            },
            "training_data_info": {"demographic_imbalance": False},
            "algorithm_info": {"bias_mitigation": "adversarial_debiasing"},
            "transparency": {
                "algorithm_explanation": "CNN-based tumor detection",
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
        }
        
        decision = ethics.validate_medical_request(valid_request)
        
        # Should be approved
        assert decision.allow is True
        assert len(decision.reasons) == 0
        assert decision.confidence >= 0.5
        assert "analysis_type" in decision.metadata
        assert decision.metadata["analysis_type"] == "tumor_detection"
    
    def test_medical_ethics_violation_detection(self):
        """Test violation detection in medical ethics system."""
        ethics = MedicalAIEthics()
        
        # Test request with violations
        invalid_request = {
            "analysis_type": "treatment_recommendation",
            "patient_id": "P002",
            "data_collected": ["imaging_data", "lab_results", "patient_age", "medical_history", "genetic_markers", "family_history", "lifestyle_data"],
            "consent": {
                "explicit_consent": True,
                "informed_consent": False,  # Missing informed consent
                "scope": ["treatment_recommendation"]
            },
            "analysis_parameters": {
                "demographic_filters": {"age_bias": True, "gender_bias": False, "ethnicity_bias": False}
            },
            "training_data_info": {"demographic_imbalance": True},
            "algorithm_info": {"bias_mitigation": "none"},
            "transparency": {
                "algorithm_explanation": "Treatment recommendation algorithm",
                "confidence_scores": True
                # Missing other transparency requirements
            },
            "fairness_analysis": {
                "demographic_parity": 0.75,
                "equalized_odds": 0.65,
                "calibration": 0.55
            },
            "accuracy_metrics": {
                "accuracy": 0.88,
                "precision": 0.85,
                "recall": 0.87
            }
        }
        
        decision = ethics.validate_medical_request(invalid_request)
        
        # Should be rejected
        assert decision.allow is False
        assert len(decision.reasons) > 0
        assert decision.confidence < 0.5
    
    def test_medical_ethics_report_generation(self):
        """Test ethics report generation for medical system."""
        ethics = MedicalAIEthics()
        
        # Process some requests
        test_requests = [
            {
                "analysis_type": "tumor_detection",
                "patient_id": "P001",
                "data_collected": ["imaging_data", "patient_age", "medical_history"],
                "consent": {
                    "explicit_consent": True,
                    "informed_consent": True,
                    "scope": ["tumor_detection"]
                },
                "analysis_parameters": {"demographic_filters": {"age_bias": False, "gender_bias": False, "ethnicity_bias": False}},
                "training_data_info": {"demographic_imbalance": False},
                "algorithm_info": {"bias_mitigation": "adversarial_debiasing"},
                "transparency": {
                    "algorithm_explanation": "CNN-based tumor detection",
                    "confidence_scores": True,
                    "decision_rationale": "Tumor probability based on imaging features",
                    "data_sources": "CT scans, MRI images",
                    "limitations": "Limited to specific tumor types"
                },
                "fairness_analysis": {"demographic_parity": 0.92, "equalized_odds": 0.88, "calibration": 0.85},
                "accuracy_metrics": {"accuracy": 0.96, "precision": 0.94, "recall": 0.93}
            },
            {
                "analysis_type": "treatment_recommendation",
                "patient_id": "P002",
                "data_collected": ["imaging_data", "lab_results", "patient_age", "medical_history", "genetic_markers", "family_history", "lifestyle_data"],
                "consent": {"explicit_consent": True, "informed_consent": False, "scope": ["treatment_recommendation"]},
                "analysis_parameters": {"demographic_filters": {"age_bias": True, "gender_bias": False, "ethnicity_bias": False}},
                "training_data_info": {"demographic_imbalance": True},
                "algorithm_info": {"bias_mitigation": "none"},
                "transparency": {"algorithm_explanation": "Treatment recommendation algorithm", "confidence_scores": True},
                "fairness_analysis": {"demographic_parity": 0.75, "equalized_odds": 0.65, "calibration": 0.55},
                "accuracy_metrics": {"accuracy": 0.88, "precision": 0.85, "recall": 0.87}
            }
        ]
        
        for request in test_requests:
            ethics.validate_medical_request(request)
        
        # Generate report
        report = ethics.generate_medical_ethics_report()
        
        # Verify report structure
        assert "report_timestamp" in report
        assert "total_medical_requests" in report
        assert "ethics_violations" in report
        assert "compliance_rate" in report
        assert "violation_breakdown" in report
        assert "recommendations" in report
        assert "patient_privacy_score" in report
        
        # Verify report content
        assert report["total_medical_requests"] == 2
        assert report["ethics_violations"] >= 0
        assert 0 <= report["compliance_rate"] <= 1
        assert 0 <= report["patient_privacy_score"] <= 1
        assert isinstance(report["recommendations"], list)
    
    def test_evidence_bundle_generation(self):
        """Test that examples generate proper evidence bundles."""
        # Test boroscope evidence bundle
        ethics = IndustrialInspectionEthics()
        
        request = {
            "type": "visual",
            "equipment_type": "pressure_vessel",
            "equipment_id": "PV-001",
            "data_points": ["crack_detection"],
            "authorization": ["inspector_certification", "safety_clearance", "supervisor_approval"],
            "documentation": {
                "inspection_protocol": "standard_visual_inspection_v2.1",
                "data_usage_policy": "inspection_data_retention_policy",
                "retention_schedule": "7_years_archival"
            },
            "criteria": {"crack_threshold": "0.1mm"}
        }
        
        decision = ethics.validate_inspection_request(request)
        
        # Verify evidence bundle structure
        assert hasattr(decision, 'metadata')
        assert "timestamp" in decision.metadata
        assert "ethics_checks" in decision.metadata
        assert isinstance(decision.metadata["ethics_checks"], list)
        
        # Verify governance decision is present
        assert hasattr(decision, 'allow')
        assert hasattr(decision, 'reasons')
        assert hasattr(decision, 'confidence')
        assert isinstance(decision.allow, bool)
        assert isinstance(decision.reasons, list)
        assert isinstance(decision.confidence, float)
    
    def test_governance_decisions_present(self):
        """Test that governance decisions are properly recorded."""
        # Test medical governance decisions
        ethics = MedicalAIEthics()
        
        request = {
            "analysis_type": "tumor_detection",
            "patient_id": "P001",
            "data_collected": ["imaging_data", "patient_age", "medical_history"],
            "consent": {"explicit_consent": True, "informed_consent": True, "scope": ["tumor_detection"]},
            "analysis_parameters": {"demographic_filters": {"age_bias": False, "gender_bias": False, "ethnicity_bias": False}},
            "training_data_info": {"demographic_imbalance": False},
            "algorithm_info": {"bias_mitigation": "adversarial_debiasing"},
            "transparency": {
                "algorithm_explanation": "CNN-based tumor detection",
                "confidence_scores": True,
                "decision_rationale": "Tumor probability based on imaging features",
                "data_sources": "CT scans, MRI images",
                "limitations": "Limited to specific tumor types"
            },
            "fairness_analysis": {"demographic_parity": 0.92, "equalized_odds": 0.88, "calibration": 0.85},
            "accuracy_metrics": {"accuracy": 0.96, "precision": 0.94, "recall": 0.93}
        }
        
        decision = ethics.validate_medical_request(request)
        
        # Verify governance decision structure
        assert hasattr(decision, 'allow')
        assert hasattr(decision, 'reasons')
        assert hasattr(decision, 'confidence')
        assert hasattr(decision, 'metadata')
        
        # Verify decision is logged
        assert len(ethics.medical_requests) == 1
        logged_request = ethics.medical_requests[0]
        assert "request" in logged_request
        assert "decision" in logged_request
        assert "timestamp" in logged_request
    
    def test_example_scripts_execution(self):
        """Test that example scripts can be executed without errors."""
        # Test boroscope example
        try:
            report = run_boroscope_example()
            assert isinstance(report, dict)
            assert "total_inspections" in report
        except Exception as e:
            assert False, f"Boroscope example failed: {e}"
        
        # Test oncology example
        try:
            report = run_oncology_example()
            assert isinstance(report, dict)
            assert "total_medical_requests" in report
        except Exception as e:
            assert False, f"Oncology example failed: {e}"


def run_tests():
    """Run all tests."""
    test_instance = TestEthicsExamples()
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    total_tests = 0
    passed_tests = 0
    
    for method_name in test_methods:
        total_tests += 1
        try:
            method = getattr(test_instance, method_name)
            method()
            print(f"✅ {method_name}")
            passed_tests += 1
        except Exception as e:
            print(f"❌ {method_name}: {e}")
    
    print(f"\n=== Test Summary ===")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
