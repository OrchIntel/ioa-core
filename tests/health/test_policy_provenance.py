# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""Action policies and session provenance (evaluation only). Synthetic text only."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from ioa_core.evidence import (
    SessionReceiptError,
    create_session_receipt,
    verify_session_receipt,
)
from ioa_core.health import (
    PolicyError,
    capture_session_provenance,
    detect_findings,
    load_packaged_policy,
    policy_from_mapping,
    require_live_approval,
)
from ioa_core.health.registry import profile_definition_fingerprint

_RECEIPT_TESTS = Path(__file__).resolve().parents[1] / "test_session_receipt.py"
_spec = importlib.util.spec_from_file_location("_receipt_helpers", _RECEIPT_TESTS)
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)

YOUTH = "youth_mental_health_au"
MIXED_INPUT = "SYNTHETIC. Denies suicidal ideation. Self-harm last week. Thinking about ending their life."


def _report(input_text=MIXED_INPUT, output_text="SYNTHETIC. Risk: suicidal thoughts."):
    return detect_findings(
        profile_id=YOUTH, input_text=input_text, output_text=output_text
    )


def _definition():
    return copy.deepcopy(load_packaged_policy().definition)


# --- findings keep distinct concerns -------------------------------------------


def test_occurrences_keep_every_source_and_context():
    finding = _report().finding("crisis_risk_to_self")
    groups = {(item.source, item.context) for item in finding.occurrences}
    assert ("input", "negated") in groups
    assert ("input", "affirmed") in groups
    assert ("output", "affirmed") in groups
    # Entry ids name rules, never text.
    for item in finding.occurrences:
        assert item.entry.startswith("crisis_risk_to_self@")
        assert "ending" not in item.entry


def test_findings_report_carries_a_ruleset_fingerprint():
    first = _report()
    second = _report()
    assert first.ruleset_sha256 and first.ruleset_sha256.startswith("sha256:")
    assert first.ruleset_sha256 == second.ruleset_sha256


# --- policy -------------------------------------------------------------------


def test_packaged_policy_is_a_draft_and_refused_for_live_use():
    policy = load_packaged_policy()
    assert policy.status == "draft"
    assert policy.approval is None
    with pytest.raises(PolicyError):
        require_live_approval(policy)


def test_required_actions_cover_every_occurrence_group():
    policy = load_packaged_policy()
    report = _report()
    actions = policy.required_actions(report)
    groups = sum(len(item.occurrences) for item in report.findings)
    assert len(actions) == groups
    by_context = {(item.source, item.context): item for item in actions}
    assert by_context[("input", "negated")].action == "disposition_required"
    assert by_context[("input", "affirmed")].action == "escalate_with_follow_up"
    assert by_context[("input", "affirmed")].dismissal_allowed is False
    summary = policy.summary_by_gate(report)["crisis_risk_to_self"]
    assert summary == {
        "action": "escalate_with_follow_up",
        "follow_up_hours": 24,
        "dismissal_allowed": False,
    }


def test_input_only_finding_is_not_downgraded():
    policy = load_packaged_policy()
    input_only = policy.required_actions(
        _report(
            input_text="SYNTHETIC. Thinking about ending their life.",
            output_text="SYNTHETIC. Low mood.",
        )
    )
    output_only = policy.required_actions(
        _report(
            input_text="SYNTHETIC. Low mood.",
            output_text="SYNTHETIC. Thinking about ending their life.",
        )
    )
    assert (
        {item.action for item in input_only}
        == {item.action for item in output_only}
        == {"escalate_with_follow_up"}
    )


def test_fingerprint_ignores_approval_but_not_rules():
    draft = load_packaged_policy()
    approved_def = _definition()
    approved_def["status"] = "approved"
    approved_def["approval"] = {
        "approved_by_role": "clinical_lead",
        "approved_at": "2026-11-01T00:00:00Z",
    }
    approved = policy_from_mapping(approved_def)
    assert approved.fingerprint == draft.fingerprint
    assert require_live_approval(approved) is approved
    changed = _definition()
    changed["rules"][0]["follow_up_hours"] = 12
    assert policy_from_mapping(changed).fingerprint != draft.fingerprint


@pytest.mark.parametrize(
    "mutate,message",
    [
        (lambda d: d.update(status="approved"), "approval record"),
        (lambda d: d.update(approval={"approved_by_role": "x"}), "draft policy cannot"),
        (lambda d: d["rules"][0].update(action="ignore"), "unknown action"),
        (lambda d: d["rules"][0].update(contexts=["safe"]), "unknown values"),
        (
            lambda d: d["rules"][0].update(follow_up_hours=None),
            "positive follow_up_hours",
        ),
        (
            lambda d: d["rules"][1].update(follow_up_hours=24),
            "follow_up_hours applies only",
        ),
        (lambda d: d.update(schema="other"), "schema"),
    ],
)
def test_malformed_policies_are_rejected(mutate, message):
    definition = _definition()
    mutate(definition)
    with pytest.raises(PolicyError, match=message):
        policy_from_mapping(definition)


def test_policy_scoped_to_its_profiles():
    definition = _definition()
    definition["profile_ids"] = ["mental_health_nz"]
    with pytest.raises(PolicyError):
        policy_from_mapping(definition).required_actions(_report())


# --- provenance and receipts ----------------------------------------------------


def test_provenance_without_a_policy_says_none_was_applied():
    record = capture_session_provenance(profile_id=YOUTH)
    assert record["source"] == "runtime"
    assert record["action_policy"] == {
        "applied": False,
        "basis": "profile_gate_severities",
    }
    assert record["profile"]["fingerprint"] == profile_definition_fingerprint(YOUTH)
    assert record["profile"]["fingerprint"] != profile_definition_fingerprint(
        "mental_health_au"
    )
    assert "findings" not in record


def test_provenance_with_a_draft_policy_records_draft():
    record = capture_session_provenance(
        profile_id=YOUTH, policy=load_packaged_policy(), findings_report=_report()
    )
    assert record["action_policy"]["status"] == "draft"
    assert record["findings"]["status"] == "evaluation_only"


def test_receipt_with_provenance_signs_and_verifies(tmp_path: Path):
    private_pem, public_pem = _helpers._keypair()
    key_path = tmp_path / "pub.pem"
    key_path.write_bytes(public_pem)
    provenance = capture_session_provenance(profile_id="youth_mental_health_nz")
    receipt = create_session_receipt(
        **_helpers._inputs(), private_key_pem=private_pem, provenance=provenance
    )
    block = receipt["metadata"]["provenance"]
    assert block["action_policy"] == {
        "applied": False,
        "basis": "profile_gate_severities",
    }
    assert block["profile"]["fingerprint"].startswith("sha256:")
    assert verify_session_receipt(receipt, key_path)
    tampered = json.loads(json.dumps(receipt))
    tampered["metadata"]["provenance"]["action_policy"] = {
        "applied": True,
        "policy_id": "qixmind_default",
        "version": "x",
        "status": "approved",
        "fingerprint": "sha256:" + "0" * 64,
    }
    assert not verify_session_receipt(tampered, key_path)


def test_receipt_without_provenance_is_unchanged():
    private_pem, _ = _helpers._keypair()
    receipt = create_session_receipt(**_helpers._inputs(), private_key_pem=private_pem)
    assert "provenance" not in receipt["metadata"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(source="console"),
        lambda p: p.update(schema="other"),
        lambda p: p["profile"].update(fingerprint="not-a-hash"),
        lambda p: p["action_policy"].update(applied="yes"),
    ],
)
def test_receipt_rejects_bad_provenance(mutate):
    private_pem, _ = _helpers._keypair()
    provenance = capture_session_provenance(profile_id="youth_mental_health_nz")
    mutate(provenance)
    with pytest.raises(SessionReceiptError):
        create_session_receipt(
            **_helpers._inputs(), private_key_pem=private_pem, provenance=provenance
        )


def test_frozen_detector_matches_the_freeze_record():
    # Changing any rule or lexicon after the freeze must be a deliberate act:
    # update FREEZE.json and treat the held-out set as development data.
    from ioa_core.health.findings import (
        DETECTOR_VERSION,
        FROZEN_FOR_HELDOUT,
        ruleset_fingerprint,
    )

    freeze = json.loads(
        (Path(__file__).parent / "fixtures" / "gate_eval" / "FREEZE.json").read_text()
    )
    assert FROZEN_FOR_HELDOUT is True
    assert freeze["detector_version"] == DETECTOR_VERSION
    assert freeze["findings_ruleset_sha256"] == ruleset_fingerprint()
