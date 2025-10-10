""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from typing import Optional, Dict, Any


class SystemLawsError(Exception):
    """Base exception for System Laws violations and errors."""
    
    def __init__(self, message: str, law_id: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.law_id = law_id
        self.context = context or {}
        super().__init__(self.message)


class SystemIntegrityError(SystemLawsError):
    """Raised when System Laws manifest integrity is compromised."""
    
    def __init__(self, message: str, manifest_path: Optional[str] = None):
        super().__init__(message, context={"manifest_path": manifest_path})


class LawViolationError(SystemLawsError):
    """Raised when a specific law is violated."""
    
    def __init__(self, law_id: str, violation_details: str, 
                 action_context: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Law violation: {law_id} - {violation_details}",
            law_id=law_id,
            context={"violation_details": violation_details, "action_context": action_context}
        )


class SignatureVerificationError(SystemLawsError):
    """Raised when manifest signature verification fails."""
    
    def __init__(self, message: str, signature_alg: Optional[str] = None,
                 key_id: Optional[str] = None):
        super().__init__(message, context={
            "signature_alg": signature_alg,
            "key_id": key_id
        })


class PolicyConflictError(SystemLawsError):
    """Raised when policy conflicts cannot be resolved."""
    
    def __init__(self, conflicting_laws: list, resolution_attempt: str):
        super().__init__(
            f"Policy conflict between laws: {conflicting_laws}",
            context={
                "conflicting_laws": conflicting_laws,
                "resolution_attempt": resolution_attempt
            }
        )


class FairnessViolationError(SystemLawsError):
    """Raised when fairness thresholds are exceeded."""
    
    def __init__(self, fairness_score: float, threshold: float, 
                 metrics: Optional[Dict[str, float]] = None):
        super().__init__(
            f"Fairness violation: score {fairness_score} exceeds threshold {threshold}",
            law_id="law5",
            context={
                "fairness_score": fairness_score,
                "threshold": threshold,
                "metrics": metrics or {}
            }
        )


class HumanApprovalRequiredError(SystemLawsError):
    """Raised when human approval is required for an action."""
    
    def __init__(self, action_description: str, risk_level: str,
                 required_approval_type: str):
        super().__init__(
            f"Human approval required: {action_description}",
            law_id="law6",
            context={
                "action_description": action_description,
                "risk_level": risk_level,
                "required_approval_type": required_approval_type
            }
        )


class AuditTrailError(SystemLawsError):
    """Raised when audit trail requirements are not met."""
    
    def __init__(self, missing_audit_id: bool, context_required: list):
        super().__init__(
            "Audit trail requirements not met",
            law_id="law3",
            context={
                "missing_audit_id": missing_audit_id,
                "context_required": context_required
            }
        )


class SustainabilityViolationError(SystemLawsError):
    """Raised when sustainability budget limits are exceeded."""
    
    def __init__(self, budget_type: str, current_usage_kwh: float, budget_limit_kwh: float,
                 action_context: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Sustainability violation: {budget_type} budget exceeded "
            f"({current_usage_kwh:.3f} kWh > {budget_limit_kwh:.3f} kWh)",
            law_id="law7",
            context={
                "budget_type": budget_type,
                "current_usage_kwh": current_usage_kwh,
                "budget_limit_kwh": budget_limit_kwh,
                "action_context": action_context
            }
        )


class EnergyBudgetExceededError(SystemLawsError):
    """Raised when energy budget limits are exceeded without HITL override."""
    
    def __init__(self, budget_context: str, projected_kwh: float, limit_kwh: float,
                 override_available: bool = False):
        super().__init__(
            f"Energy budget exceeded: {budget_context} "
            f"({projected_kwh:.3f} kWh > {limit_kwh:.3f} kWh)",
            law_id="law7",
            context={
                "budget_context": budget_context,
                "projected_kwh": projected_kwh,
                "limit_kwh": limit_kwh,
                "override_available": override_available
            }
        )
