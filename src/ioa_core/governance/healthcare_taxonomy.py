# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""Healthcare clinical risk taxonomy helpers used by governed runtimes."""

from __future__ import annotations

from typing import Final, Optional, Set

CLINICAL_RISK_CLASSES: Final[Set[str]] = {
    "administrative",
    "documentation",
    "clinical_advice",
    "diagnostic_support",
    "treatment_recommendation",
}

CONSENT_REQUIRED_RISK_CLASSES: Final[Set[str]] = {
    "clinical_advice",
    "treatment_recommendation",
}

FHIR_RESOURCE_RISK_DEFAULTS: Final[dict[str, str]] = {
    "MedicationRequest": "treatment_recommendation",
    "Procedure": "treatment_recommendation",
    "DiagnosticReport": "diagnostic_support",
    "Condition": "diagnostic_support",
    "Observation": "documentation",
    "Encounter": "documentation",
    "Patient": "documentation",
    "AllergyIntolerance": "documentation",
}


def normalize_risk_class(risk: str) -> str:
    """Normalize and validate a clinical risk class."""
    normalized = (risk or "").strip().lower()
    if normalized not in CLINICAL_RISK_CLASSES:
        raise ValueError(f"Unsupported clinical_risk_class: {normalized}")
    return normalized


def infer_risk_from_text(text: str, default: str = "documentation") -> str:
    """Infer a deterministic clinical risk class from free text input."""
    lowered = (text or "").strip().lower()
    if not lowered:
        return normalize_risk_class(default)

    treatment_markers = ("prescribe", "dosage", "dose", "medication plan", "treatment plan", "start taking")
    advice_markers = ("should i", "what should", "recommend", "advice", "is it safe", "can i take")
    diagnostic_markers = ("diagnose", "differential", "interpret labs", "interpret results", "symptoms suggest")
    admin_markers = ("billing", "invoice", "appointment", "schedule", "admin")

    if any(marker in lowered for marker in treatment_markers):
        return "treatment_recommendation"
    if any(marker in lowered for marker in advice_markers):
        return "clinical_advice"
    if any(marker in lowered for marker in diagnostic_markers):
        return "diagnostic_support"
    if any(marker in lowered for marker in admin_markers):
        return "administrative"
    return normalize_risk_class(default)


def infer_risk_from_resource_type(resource_type: str, default: str = "documentation") -> str:
    """Infer deterministic risk from an incoming FHIR resource type."""
    inferred = FHIR_RESOURCE_RISK_DEFAULTS.get(resource_type, default)
    return normalize_risk_class(inferred)


def resolve_effective_risk_class(
    requested: Optional[str],
    *,
    default: str = "documentation",
    text: Optional[str] = None,
    resource_type: Optional[str] = None,
) -> str:
    """Resolve effective risk class from explicit input or deterministic inference."""
    if requested:
        return normalize_risk_class(requested)
    if text is not None:
        return infer_risk_from_text(text, default=default)
    if resource_type is not None:
        return infer_risk_from_resource_type(resource_type, default=default)
    return normalize_risk_class(default)


def consent_required_for_risk(risk_class: str) -> bool:
    """Return whether the risk class requires consent proof at runtime."""
    return normalize_risk_class(risk_class) in CONSENT_REQUIRED_RISK_CLASSES
