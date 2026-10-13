# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Content gate evaluator tests. Synthetic fixtures only; no real case material."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ioa_core.health import (
    GATE_DEFINITIONS,
    SEVERITY_ORDER,
    ContentGateError,
    ContentGateEvaluator,
    GateDefinition,
    fail_closed_report,
    sha256_text,
)
from ioa_core.health import content_gates as module

FIXTURES = Path(__file__).parent / "fixtures"
RISK_FIXTURE = (FIXTURES / "synthetic_youth_mh_01.txt").read_text(encoding="utf-8")
CLEAN_FIXTURE = (FIXTURES / "synthetic_youth_mh_02.txt").read_text(encoding="utf-8")
FORBIDDEN_RESULT_KEYS = {"matched_text", "pattern", "start", "end", "text", "snippet"}


def _flatten_keys(value, found=None):
    found = found if found is not None else set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            _flatten_keys(child, found)
    elif isinstance(value, list):
        for child in value:
            _flatten_keys(child, found)
    return found


def test_youth_profile_resolves_four_escalate_gates_in_profile_order():
    evaluator = ContentGateEvaluator.for_profile("youth_mental_health_nz")
    assert evaluator.gates == [
        "crisis_risk_to_self",
        "risk_to_others",
        "child_protection",
        "crisis_mandatory_reporting",
    ]
    assert evaluator.unimplemented_gates == []
    report = evaluator.evaluate(output_text=CLEAN_FIXTURE)
    assert [result.gate for result in report.results] == evaluator.gates
    assert all(result.severity == "escalate" for result in report.results)
    assert report.detector_status == "ok"


def test_risk_fixture_fires_self_harm_and_child_protection_gates():
    report = ContentGateEvaluator.for_profile("youth_mental_health_nz").evaluate(
        output_text=RISK_FIXTURE
    )
    fired = {result.gate for result in report.fired_gates()}
    assert "crisis_risk_to_self" in fired
    assert "child_protection" in fired
    assert "risk_to_others" not in fired
    assert report.overall_action == "escalate"
    assert report.requires_follow_up() is True
    assert report.is_held() is False
    by_gate = {result.gate: result for result in report.results}
    assert by_gate["crisis_risk_to_self"].matched_category == "risk_to_self"
    assert by_gate["child_protection"].matched_category == "child_protection"
    assert by_gate["risk_to_others"].matched_category is None


def test_adult_profile_fires_risk_to_self_without_child_protection():
    report = ContentGateEvaluator.for_profile("mental_health_au").evaluate(
        output_text=RISK_FIXTURE
    )
    fired = {result.gate for result in report.fired_gates()}
    assert "crisis_risk_to_self" in fired
    assert "child_protection" not in {result.gate for result in report.results}
    assert report.overall_action == "escalate"
    assert report.requires_follow_up() is True


def test_clean_fixture_passes_and_requires_no_follow_up():
    report = ContentGateEvaluator.for_profile("youth_mental_health_nz").evaluate(
        output_text=CLEAN_FIXTURE
    )
    assert report.overall_action == "pass"
    assert report.fired_gates() == []
    assert report.requires_follow_up() is False


@pytest.mark.parametrize(
    "gate, phrase",
    [
        ("crisis_risk_to_self", "SYNTHETIC: expressed thoughts of ending their life."),
        ("crisis_risk_to_self", "SYNTHETIC: plan to end his life disclosed."),
        (
            "risk_to_others",
            "SYNTHETIC: threatened to hurt a classmate and has access to a knife.",
        ),
        ("risk_to_others", "SYNTHETIC: homicidal ideation towards a named peer."),
        (
            "child_protection",
            "SYNTHETIC: afraid to go home; unexplained bruising noted.",
        ),
        ("child_protection", "SYNTHETIC: disclosed abuse by a caregiver."),
        (
            "crisis_mandatory_reporting",
            "SYNTHETIC: serious and imminent risk; crisis team contacted.",
        ),
        ("crisis_mandatory_reporting", "SYNTHETIC: requires urgent assessment today."),
    ],
)
def test_each_gate_fires_on_its_own_synthetic_phrase(gate: str, phrase: str):
    evaluator = ContentGateEvaluator([gate], {gate: "escalate"}, profile_id="synthetic")
    report = evaluator.evaluate(output_text=phrase)
    assert [result.gate for result in report.fired_gates()] == [gate]


@pytest.mark.parametrize(
    "phrase",
    [
        "SYNTHETIC: cutting back on screen time; dying to see the new film.",
        "SYNTHETIC: reviewed sleep hygiene and school supports; no concerns raised.",
        "SYNTHETIC: angry at a sibling after an argument about chores.",
    ],
)
def test_ambiguous_everyday_language_does_not_fire(phrase: str):
    report = ContentGateEvaluator.for_profile("youth_mental_health_nz").evaluate(
        output_text=phrase
    )
    assert report.fired_gates() == []


def test_results_never_carry_matched_text_or_patterns():
    report = ContentGateEvaluator.for_profile("youth_mental_health_nz").evaluate(
        output_text=RISK_FIXTURE, input_text="SYNTHETIC input [NAME_1]"
    )
    keys = _flatten_keys(report.to_dict())
    assert not (keys & FORBIDDEN_RESULT_KEYS)
    serialized = json.dumps(report.to_dict())
    assert "stepfather" not in serialized
    assert "[NAME_1]" not in serialized
    assert report.output_sha256 == sha256_text(RISK_FIXTURE)
    assert report.input_sha256 == sha256_text("SYNTHETIC input [NAME_1]")


def test_missing_lexicon_fails_closed_at_construction(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setitem(
        GATE_DEFINITIONS,
        "synthetic_missing_gate",
        GateDefinition(
            name="synthetic_missing_gate",
            lexicon="does_not_exist_synthetic",
            category="synthetic",
            default_severity="escalate",
            applies_to=("output",),
            description="test only",
        ),
    )
    with pytest.raises(ContentGateError):
        ContentGateEvaluator(["synthetic_missing_gate"], {})


def test_malformed_lexicon_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps({"version": "1", "category": "c", "words": [], "patterns": []})
    )

    class _Files:
        def joinpath(self, _name):
            return bad

    monkeypatch.setattr(module.resources, "files", lambda _pkg: _Files())
    module._load_lexicon.cache_clear()
    try:
        with pytest.raises(ContentGateError):
            module._load_lexicon("anything")
    finally:
        module._load_lexicon.cache_clear()


def test_fail_closed_report_holds_and_sanitises_reason():
    report = fail_closed_report(
        "youth_mental_health_nz",
        "Lexicon Unavailable: patient said something",
        output_text="SYNTHETIC output",
    )
    assert report.overall_action == "hold"
    assert report.detector_status == "unavailable"
    assert report.results == []
    assert report.requires_follow_up() is True
    assert report.is_held() is True
    assert report.unavailable_reason == "lexicon_unavailable_patient_said_something"
    assert report.output_sha256 == sha256_text("SYNTHETIC output")


def test_profiles_without_gates_pass_everything():
    evaluator = ContentGateEvaluator.for_profile("gp_nz")
    assert evaluator.gates == []
    report = evaluator.evaluate(output_text=RISK_FIXTURE)
    assert report.overall_action == "pass"
    assert report.results == []


def test_declared_but_unimplemented_gates_are_reported_not_hidden():
    evaluator = ContentGateEvaluator.for_profile("aged_care_au_nz")
    assert "mandatory_reporting_gate" in evaluator.unimplemented_gates
    report = evaluator.evaluate(output_text="SYNTHETIC text")
    assert report.detector_status == "partial"
    unevaluated = [result for result in report.results if not result.evaluated]
    assert unevaluated
    assert all(result.fired is False for result in unevaluated)


def test_severity_policy_controls_overall_action():
    evaluator = ContentGateEvaluator(
        ["crisis_risk_to_self"],
        {"crisis_risk_to_self": "acknowledge"},
        profile_id="synthetic",
    )
    report = evaluator.evaluate(output_text="SYNTHETIC: suicidal ideation noted.")
    assert report.overall_action == "acknowledge"
    assert report.requires_follow_up() is False
    held = ContentGateEvaluator(
        ["crisis_risk_to_self"], {"crisis_risk_to_self": "hold"}, profile_id="synthetic"
    ).evaluate(output_text="SYNTHETIC: suicidal ideation noted.")
    assert held.is_held() is True


def test_unknown_severity_is_rejected():
    with pytest.raises(ContentGateError):
        ContentGateEvaluator(["crisis_risk_to_self"], {"crisis_risk_to_self": "loud"})
    assert "escalate" in SEVERITY_ORDER


def test_lexicon_versions_are_recorded_for_auditability():
    report = ContentGateEvaluator.for_profile("youth_mental_health_nz").evaluate(
        output_text=CLEAN_FIXTURE
    )
    assert set(report.lexicon_versions) == set(GATE_DEFINITIONS)
    assert all(result.lexicon_version for result in report.results)
