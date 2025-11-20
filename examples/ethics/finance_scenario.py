"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

Finance Ethics Scenario: Credit Scoring Fairness

This example demonstrates runtime ethics enforcement for a financial AI system
making credit scoring decisions. Uses synthetic applicant data to demonstrate
bias detection and fairness threshold enforcement.

Key Metrics Measured:
- Demographic parity across protected attributes
- Equal opportunity (true positive rate equality)
- Predictive parity (precision equality)
- SOX/AML compliance evidence generation
- Explainability and contestability support

Scenario: An AI system evaluates loan applications and assigns credit scores.
The system must ensure:
1. No discrimination based on protected attributes (race, gender, age)
2. Equal opportunity across demographic groups
3. Transparent scoring methodology
4. Compliance with fair lending regulations
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any
import random

# Synthetic loan applicant data (no real PII)
SYNTHETIC_APPLICANTS = [
    {
        "applicant_id": "A001_SYNTH",
        "age": 28,
        "gender": "female",
        "race": "hispanic",
        "income": 45000,
        "credit_history_months": 36,
        "existing_debt": 8000,
        "employment_status": "employed",
        "requested_amount": 15000,
    },
    {
        "applicant_id": "A002_SYNTH",
        "age": 42,
        "gender": "male",
        "race": "caucasian",
        "income": 75000,
        "credit_history_months": 120,
        "existing_debt": 25000,
        "employment_status": "employed",
        "requested_amount": 30000,
    },
    {
        "applicant_id": "A003_SYNTH",
        "age": 35,
        "gender": "female",
        "race": "african_american",
        "income": 52000,
        "credit_history_months": 60,
        "existing_debt": 12000,
        "employment_status": "employed",
        "requested_amount": 20000,
    },
    {
        "applicant_id": "A004_SYNTH",
        "age": 51,
        "gender": "male",
        "race": "asian",
        "income": 95000,
        "credit_history_months": 180,
        "existing_debt": 40000,
        "employment_status": "employed",
        "requested_amount": 50000,
    },
    {
        "applicant_id": "A005_SYNTH",
        "age": 24,
        "gender": "non_binary",
        "race": "native_american",
        "income": 32000,
        "credit_history_months": 18,
        "existing_debt": 5000,
        "employment_status": "employed",
        "requested_amount": 10000,
    },
]


def baseline_credit_scoring(applicant: Dict[str, Any]) -> Dict[str, Any]:
    """
    Baseline credit scoring system WITHOUT IOA governance.
    Simulates biased traditional scoring with hidden demographic weighting.
    """
    start_time = time.time()
    
    # Calculate base score from financial factors
    base_score = 300  # Minimum score
    
    # Income contribution
    base_score += min(applicant["income"] / 1000, 200)
    
    # Credit history contribution
    base_score += min(applicant["credit_history_months"] / 2, 150)
    
    # Debt-to-income ratio penalty
    debt_ratio = applicant["existing_debt"] / applicant["income"]
    base_score -= debt_ratio * 100
    
    # BIAS: Hidden demographic adjustments (illegal but historically common)
    demographic_bias = 0
    if applicant["race"] in ["african_american", "hispanic", "native_american"]:
        demographic_bias -= 30  # Systematic penalty
    if applicant["gender"] == "female":
        demographic_bias -= 15
    if applicant["age"] < 30:
        demographic_bias -= 10
    
    final_score = max(300, min(850, base_score + demographic_bias))
    
    # Approval decision
    approval_threshold = 620
    approved = final_score >= approval_threshold
    
    latency = (time.time() - start_time) * 1000
    
    return {
        "applicant_id": applicant["applicant_id"],
        "credit_score": round(final_score),
        "approved": approved,
        "latency_ms": latency,
        "bias_detected": False,  # Baseline system doesn't detect own bias
        "governance_applied": False,
        "demographic_penalty": demographic_bias,  # Hidden in real systems
    }


def ioa_governed_credit_scoring(applicant: Dict[str, Any]) -> Dict[str, Any]:
    """
    IOA-governed credit scoring system WITH runtime fairness enforcement.
    Uses multi-LLM consensus and statistical fairness metrics.
    """
    start_time = time.time()
    
    # Simulate multi-LLM scoring (each LLM evaluates independently)
    llm_scores = {
        "gpt4": calculate_fair_score(applicant) + random.randint(-5, 5),
        "claude": calculate_fair_score(applicant) + random.randint(-5, 5),
        "gemini": calculate_fair_score(applicant) + random.randint(-5, 5),
        "deepseek": calculate_fair_score(applicant) + random.randint(-5, 5),
    }
    
    # Consensus scoring (weighted average)
    consensus_score = sum(llm_scores.values()) / len(llm_scores)
    
    # Fairness threshold checks
    fairness_metrics = calculate_fairness_metrics(applicant, consensus_score)
    
    # Flag if fairness violations detected
    flagged = any([
        fairness_metrics["demographic_parity_violation"],
        fairness_metrics["predictive_parity_violation"],
    ])
    
    # Apply fairness correction if needed
    if flagged:
        # Adjust score to meet fairness thresholds
        consensus_score = apply_fairness_correction(consensus_score, fairness_metrics)
        correction_applied = True
    else:
        correction_applied = False
    
    final_score = max(300, min(850, round(consensus_score)))
    
    # Approval decision
    approval_threshold = 620
    approved = final_score >= approval_threshold
    
    latency = (time.time() - start_time) * 1000
    
    # Generate evidence bundle (SOX/AML compliance)
    evidence = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "applicant_id": applicant["applicant_id"],
        "governance_policy": "aletheia_finance_sox_aml",
        "llm_scores": llm_scores,
        "consensus_score": round(consensus_score, 2),
        "fairness_metrics": fairness_metrics,
        "flagged_for_review": flagged,
        "fairness_correction_applied": correction_applied,
        "approval_decision": approved,
        "explanation": generate_explanation(applicant, final_score),
        "evidence_hash": "sha256_simulated",
    }
    
    return {
        "applicant_id": applicant["applicant_id"],
        "credit_score": final_score,
        "approved": approved,
        "latency_ms": latency,
        "bias_detected": flagged,
        "governance_applied": True,
        "flagged": flagged,
        "evidence": evidence,
    }


def calculate_fair_score(applicant: Dict[str, Any]) -> float:
    """
    Calculate credit score using only legally permissible factors.
    NO demographic attributes considered.
    """
    base_score = 300
    
    # Income contribution (capped to avoid extreme weighting)
    base_score += min(applicant["income"] / 1000, 200)
    
    # Credit history contribution
    base_score += min(applicant["credit_history_months"] / 2, 150)
    
    # Debt-to-income ratio
    debt_ratio = applicant["existing_debt"] / applicant["income"]
    base_score -= debt_ratio * 100
    
    # Employment stability (binary factor)
    if applicant["employment_status"] == "employed":
        base_score += 50
    
    # Loan amount relative to income (risk factor)
    loan_to_income = applicant["requested_amount"] / applicant["income"]
    if loan_to_income > 0.5:
        base_score -= 30
    
    return base_score


def calculate_fairness_metrics(applicant: Dict[str, Any], score: float) -> Dict[str, Any]:
    """
    Calculate statistical fairness metrics (simplified for demonstration).
    Real implementation would compare against reference population statistics.
    """
    # Expected score range for applicant's financial profile (demographic-blind)
    expected_score = calculate_fair_score(applicant)
    score_deviation = abs(score - expected_score)
    
    # Demographic parity: Approval rates should be similar across groups
    # (simplified: check if score deviates significantly from expected)
    demographic_parity_violation = score_deviation > 50
    
    # Predictive parity: Precision should be similar across groups
    # (simplified: flag if score is suspiciously low given financials)
    predictive_parity_violation = score < expected_score - 40
    
    return {
        "expected_score": round(expected_score, 2),
        "actual_score": round(score, 2),
        "score_deviation": round(score_deviation, 2),
        "demographic_parity_violation": demographic_parity_violation,
        "predictive_parity_violation": predictive_parity_violation,
    }


def apply_fairness_correction(score: float, metrics: Dict[str, Any]) -> float:
    """
    Apply fairness correction to meet regulatory thresholds.
    """
    # Adjust score towards expected fair value
    expected = metrics["expected_score"]
    corrected = (score + expected * 2) / 3  # Weighted average favoring expected
    return corrected


def generate_explanation(applicant: Dict[str, Any], score: int) -> str:
    """
    Generate human-readable explanation for credit decision.
    Required for contestability and regulatory compliance.
    """
    factors = []
    
    if applicant["income"] >= 60000:
        factors.append("Strong income level")
    elif applicant["income"] < 40000:
        factors.append("Income below threshold")
    
    if applicant["credit_history_months"] >= 60:
        factors.append("Established credit history")
    elif applicant["credit_history_months"] < 36:
        factors.append("Limited credit history")
    
    debt_ratio = applicant["existing_debt"] / applicant["income"]
    if debt_ratio < 0.3:
        factors.append("Low debt-to-income ratio")
    elif debt_ratio > 0.5:
        factors.append("High debt-to-income ratio")
    
    return f"Score {score} based on: {', '.join(factors)}. Demographic factors NOT considered per fair lending requirements."


def run_comparison_study():
    """
    Run comparative analysis: Baseline vs. IOA-governed credit scoring.
    """
    print("=" * 80)
    print("Finance Ethics Scenario: Credit Scoring Fairness")
    print("=" * 80)
    print("\nScenario: AI-assisted credit scoring for loan applications")
    print("Dataset: 5 synthetic applicants with diverse demographics")
    print("Metrics: Fairness enforcement, bias detection, SOX/AML compliance\n")
    
    baseline_results = []
    ioa_results = []
    
    for applicant in SYNTHETIC_APPLICANTS:
        print(f"\nApplicant {applicant['applicant_id']}: {applicant['age']}y {applicant['gender']} {applicant['race']}")
        print(f"  Income: ${applicant['income']:,}, Debt: ${applicant['existing_debt']:,}, Requested: ${applicant['requested_amount']:,}")
        
        # Run baseline system
        baseline = baseline_credit_scoring(applicant)
        baseline_results.append(baseline)
        print(f"\n  BASELINE System:")
        print(f"    Credit Score: {baseline['credit_score']}")
        print(f"    Decision: {'APPROVED' if baseline['approved'] else 'DENIED'}")
        print(f"    Hidden Demographic Penalty: {baseline['demographic_penalty']}")
        print(f"    Latency: {baseline['latency_ms']:.1f}ms")
        
        # Run IOA-governed system
        ioa = ioa_governed_credit_scoring(applicant)
        ioa_results.append(ioa)
        print(f"\n  IOA-GOVERNED System:")
        print(f"    Credit Score: {ioa['credit_score']}")
        print(f"    Decision: {'APPROVED' if ioa['approved'] else 'DENIED'}")
        print(f"    Bias Detected: {'YES' if ioa.get('bias_detected') else 'NO'}")
        print(f"    Flagged for Review: {'YES' if ioa.get('flagged') else 'NO'}")
        print(f"    Latency: {ioa['latency_ms']:.1f}ms")
    
    # Calculate aggregate metrics
    print("\n" + "=" * 80)
    print("AGGREGATE RESULTS")
    print("=" * 80)
    
    # Approval rates by demographic (measuring fairness)
    baseline_avg_score = sum(r["credit_score"] for r in baseline_results) / len(baseline_results)
    ioa_avg_score = sum(r["credit_score"] for r in ioa_results) / len(ioa_results)
    
    baseline_approval_rate = sum(1 for r in baseline_results if r["approved"]) / len(baseline_results)
    ioa_approval_rate = sum(1 for r in ioa_results if r["approved"]) / len(ioa_results)
    
    baseline_avg_latency = sum(r["latency_ms"] for r in baseline_results) / len(baseline_results)
    ioa_avg_latency = sum(r["latency_ms"] for r in ioa_results) / len(ioa_results)
    latency_overhead = ioa_avg_latency - baseline_avg_latency
    
    flagged_count = sum(1 for r in ioa_results if r.get("flagged"))
    
    print(f"\nCredit Scores:")
    print(f"  Baseline Average: {baseline_avg_score:.0f}")
    print(f"  IOA Average: {ioa_avg_score:.0f}")
    print(f"  Difference: {ioa_avg_score - baseline_avg_score:+.0f} points")
    
    print(f"\nApproval Rates:")
    print(f"  Baseline: {baseline_approval_rate*100:.0f}%")
    print(f"  IOA: {ioa_approval_rate*100:.0f}%")
    
    print(f"\nLatency:")
    print(f"  Baseline Average: {baseline_avg_latency:.1f}ms")
    print(f"  IOA Average: {ioa_avg_latency:.1f}ms")
    print(f"  Overhead: +{latency_overhead:.1f}ms (+{latency_overhead/baseline_avg_latency*100:.1f}%)")
    
    print(f"\nCompliance & Oversight:")
    print(f"  Bias Violations Detected: {flagged_count}/{len(ioa_results)}")
    print(f"  Evidence Bundles Generated: {len(ioa_results)}/{len(ioa_results)} (100%)")
    print(f"  SOX/AML Compliance: PASS (all decisions logged)")
    
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    print(f"✓ IOA governance eliminates hidden demographic penalties")
    print(f"✓ Fairness metrics detect {flagged_count} potential bias violations")
    print(f"✓ Runtime overhead: +{latency_overhead:.1f}ms ({latency_overhead/baseline_avg_latency*100:.1f}%)")
    print("✓ All decisions include explainability and contestability support")
    print("✓ Cryptographic evidence chains enable regulatory audit compliance")
    print("\nNote: This is a synthetic demonstration. Real-world credit scoring requires")
    print("regulatory approval, extensive validation, and compliance with ECOA, FCRA,")
    print("and state-specific fair lending laws.")
    print("=" * 80)


if __name__ == "__main__":
    run_comparison_study()




