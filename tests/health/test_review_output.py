# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""A refused or empty output is never a review that passed its checks."""

from __future__ import annotations

import pytest

from ioa_core.health import ContentGateEvaluator, assess_review_output

# Synthetic outputs only. The refusal is the wording a model returned in the
# 13 October 2026 acceptance test on a synthetic case.
REFUSAL = (
    "I'm unable to create or interact with clinical workflows directly or provide "
    "specific clinical reasoning reviews based on detailed case notes. However, if "
    "you have general questions about clinical reasoning processes or need guidance "
    "on structuring clinical notes, feel free to ask."
)
REVIEW_WITH_DISCLAIMER = """Presenting concern:
Low mood for six weeks, poor sleep and withdrawal from school (synthetic case).

Risk, safety and escalation considerations:
The client described thoughts of ending their life. Immediate clinician review.

Care coordination and next steps:
Consider a safety plan and family involvement with consent.

Review notes:
I cannot provide a diagnosis; this is advisory and needs clinician review.
"""


@pytest.mark.parametrize(
    "text,status",
    [
        (REFUSAL, "refused"),
        ("I'm sorry, but I can't help with that.", "refused"),
        ("I cannot assist with this request as an AI language model.", "refused"),
        ("", "empty"),
        ("   \n\t ", "empty"),
        (None, "empty"),
        ("OK.", "empty"),
        (REVIEW_WITH_DISCLAIMER, "produced"),
    ],
)
def test_assess_review_output(text, status):
    assessment = assess_review_output(text)
    assert assessment.status == status
    assert assessment.produced is (status == "produced")
    # Never carries any of the output text.
    assert set(assessment.to_dict()) == {"status", "reason_code", "detector_version"}


@pytest.mark.parametrize("profile_id", ["youth_mental_health_au", "mental_health_nz"])
def test_refusal_is_held_and_every_gate_still_recorded(profile_id):
    evaluator = ContentGateEvaluator.for_profile(profile_id)
    report = evaluator.evaluate(
        output_text=REFUSAL, input_text="synthetic input", require_review_output=True
    )
    assert report.overall_action == "hold"
    assert report.is_held()
    assert report.detector_status == "ok"
    assert report.review_output["status"] == "refused"
    assert report.review_output["reason_code"] == "refusal_language"
    assert all(result.evaluated for result in report.results)
    assert report.to_dict()["review_output"]["status"] == "refused"


def test_empty_output_is_held():
    evaluator = ContentGateEvaluator.for_profile("youth_mental_health_nz")
    report = evaluator.evaluate(output_text="", require_review_output=True)
    assert report.overall_action == "hold"
    assert report.review_output["status"] == "empty"


def test_produced_review_keeps_its_gate_outcome():
    evaluator = ContentGateEvaluator.for_profile("youth_mental_health_au")
    report = evaluator.evaluate(
        output_text=REVIEW_WITH_DISCLAIMER, require_review_output=True
    )
    assert report.review_output["status"] == "produced"
    assert report.overall_action != "hold"


def test_check_is_off_unless_requested():
    evaluator = ContentGateEvaluator.for_profile("youth_mental_health_au")
    report = evaluator.evaluate(output_text=REFUSAL)
    assert report.review_output is None
    assert report.overall_action == "pass"
