# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""Source-aware findings (evaluation only). Synthetic text only."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ioa_core.health import ContentGateEvaluator, detect_findings

YOUTH = "youth_mental_health_au"
ADULT = "mental_health_nz"
ROOT = Path(__file__).resolve().parents[2]


def _gate(report, gate):
    finding = report.finding(gate)
    assert finding is not None, f"{gate} not found"
    return finding


@pytest.mark.parametrize(
    "text,context",
    [
        ("SYNTHETIC. Client reports suicidal ideation with a plan.", "affirmed"),
        ("SYNTHETIC. Denies suicidal ideation.", "negated"),
        ("SYNTHETIC. Suicidal ideation was denied at assessment.", "negated"),
        ("SYNTHETIC. History of self-harm in 2019, none since.", "historical"),
        ("SYNTHETIC. Her friend died by suicide last month.", "third_person"),
        ("SYNTHETIC. Family history of suicide.", "third_person"),
        ("SYNTHETIC. Possible suicidal thoughts? Unclear.", "uncertain"),
        ("SYNTHETIC. Mum reports that he has been cutting himself.", "affirmed"),
        ("SYNTHETIC. Texted a friend 'kms tbh'.", "affirmed"),
        ("SYNTHETIC. Says he does not want to be here anymore.", "affirmed"),
    ],
)
def test_context_of_risk_to_self(text, context):
    report = detect_findings(profile_id=ADULT, input_text=text, output_text=None)
    assert _gate(report, "crisis_risk_to_self").context == context


def test_affirmed_match_outweighs_a_negated_one():
    report = detect_findings(
        profile_id=ADULT,
        input_text="SYNTHETIC. Denies current suicidal ideation. Self-harm last week by cutting himself.",
        output_text=None,
    )
    finding = _gate(report, "crisis_risk_to_self")
    assert finding.context == "affirmed"
    assert set(finding.contexts_observed) == {"affirmed", "negated"}


def test_sources_are_merged_into_one_finding_per_gate():
    report = detect_findings(
        profile_id=YOUTH,
        input_text="SYNTHETIC. Thinking about ending their life.",
        output_text="SYNTHETIC. Risk: the client describes suicidal thoughts.",
    )
    risk = [item for item in report.findings if item.gate == "crisis_risk_to_self"]
    assert len(risk) == 1
    assert risk[0].sources == ("input", "output")
    assert risk[0].omitted_in_output is False


def test_input_finding_kept_when_output_omits_it():
    report = detect_findings(
        profile_id=YOUTH,
        input_text="SYNTHETIC. Thinking about ending their life and does not feel safe at home.",
        output_text="SYNTHETIC. Presenting concern: low mood. Next steps: sleep hygiene.",
    )
    for gate in ("crisis_risk_to_self", "child_protection"):
        finding = _gate(report, gate)
        assert finding.sources == ("input",)
        assert finding.omitted_in_output is True


def test_refused_output_still_reports_input_findings():
    report = detect_findings(
        profile_id=YOUTH,
        input_text="SYNTHETIC. Thinking about ending their life.",
        output_text="I am unable to help with this request.",
    )
    assert report.review_output["status"] == "refused"
    finding = _gate(report, "crisis_risk_to_self")
    assert finding.sources == ("input",)
    assert finding.omitted_in_output is True


def test_not_omitted_when_there_is_no_output():
    report = detect_findings(
        profile_id=YOUTH,
        input_text="SYNTHETIC. Thinking about ending their life.",
        output_text=None,
    )
    assert _gate(report, "crisis_risk_to_self").omitted_in_output is False
    assert report.review_output is None


def test_negated_signal_is_a_finding_not_cleared():
    report = detect_findings(
        profile_id=ADULT,
        input_text="SYNTHETIC. No homicidal ideation.",
        output_text=None,
    )
    finding = _gate(report, "risk_to_others")
    assert finding.context == "negated"
    assert finding.default_severity == "escalate"


def test_child_protection_only_on_profiles_that_declare_it():
    text = "SYNTHETIC. Disclosed physical abuse by stepfather."
    assert detect_findings(profile_id=YOUTH, input_text=text, output_text=None).finding(
        "child_protection"
    )
    assert (
        detect_findings(
            profile_id="mental_health_au", input_text=text, output_text=None
        ).finding("child_protection")
        is None
    )


def test_report_carries_no_case_text_and_is_marked_evaluation_only():
    secret = "SYNTHETIC-MARKER-7f3a"
    report = detect_findings(
        profile_id=YOUTH,
        input_text=f"{secret} thinking about ending their life",
        output_text=f"{secret} Risk: suicidal thoughts.",
    )
    serialized = json.dumps(report.to_dict())
    assert secret not in serialized
    assert "ending their life" not in serialized
    assert report.status == "evaluation_only"
    assert report.lexicon_versions["crisis_risk_to_self"].endswith("-eval")


def test_live_gates_do_not_use_the_evaluation_lexicons():
    # "unalive" is only in the evaluation additions; the live gate must not fire.
    report = ContentGateEvaluator.for_profile(YOUTH).evaluate(
        output_text="SYNTHETIC. wants to unalive myself"
    )
    assert report.overall_action == "pass"
    assert report.lexicon_versions["crisis_risk_to_self"] == "2026.10.1"


def test_evaluation_harness_runs_and_writes_no_case_text(tmp_path):
    out = tmp_path / "report.md"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "eval_gates.py"), "--out", str(out)],
        check=True,
        capture_output=True,
    )
    text = out.read_text(encoding="utf-8")
    assert "Concern caught, by detector" in text
    cases = json.loads(
        (
            ROOT / "tests" / "health" / "fixtures" / "gate_eval" / "cases.json"
        ).read_text()
    )["cases"]
    for case in cases:
        body = (case["input"] or "").replace("SYNTHETIC. ", "")
        assert body not in text
