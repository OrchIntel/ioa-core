# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

from ioa_core.governance.healthcare_taxonomy import (
    consent_required_for_risk,
    infer_risk_from_resource_type,
    infer_risk_from_text,
    normalize_risk_class,
    resolve_effective_risk_class,
)


def test_normalize_risk_class_rejects_unknown() -> None:
    try:
        normalize_risk_class("unknown")
    except ValueError as exc:
        assert "Unsupported clinical_risk_class" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown risk class")


def test_infer_risk_from_text_treatment_recommendation() -> None:
    risk = infer_risk_from_text("Please prescribe medication with dosage guidance.")
    assert risk == "treatment_recommendation"


def test_infer_risk_from_resource_type_medication_request() -> None:
    risk = infer_risk_from_resource_type("MedicationRequest")
    assert risk == "treatment_recommendation"


def test_resolve_effective_risk_class_prefers_explicit_requested() -> None:
    risk = resolve_effective_risk_class(
        "documentation",
        text="Please prescribe medication",
    )
    assert risk == "documentation"


def test_consent_required_for_risk() -> None:
    assert consent_required_for_risk("clinical_advice")
    assert not consent_required_for_risk("documentation")
