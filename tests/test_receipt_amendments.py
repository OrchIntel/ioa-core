# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""QiXMind receipt amendments and acknowledgement role source (2.18.0).

Synthetic keys and synthetic identifiers only.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_session_receipt import _inputs, _keypair  # noqa: E402

from ioa_core.cli import app  # noqa: E402
from ioa_core.evidence import (  # noqa: E402
    SessionReceiptError,
    amend_session_receipt,
    create_session_receipt,
    describe_amendment,
    receipt_json_bytes,
    receipt_sha256,
    verify_amendment_link,
    verify_session_receipt,
    verify_session_receipt_from_registry,
)
from ioa_core.evidence import session_receipt as module  # noqa: E402

SUPERVISOR = {
    "role": "supervisor",
    "role_source": "self_declared",
    "authority": "supervising_role",
}
SIGNER = {
    "role": "clinician",
    "role_source": "clerk_org_role",
    "authority": "original_signer",
}
SOFTWARE = {"ioa_core_version": "synthetic-2.18", "console_version": "synthetic"}


def _registry(public_pem: bytes) -> dict:
    key_id = module.public_key_id_from_pem(public_pem)
    return {
        "schema": module.KEY_REGISTRY_SCHEMA,
        "current_public_key_id": key_id,
        "keys": [
            {
                "public_key_id": key_id,
                "public_key_pem": public_pem.decode("ascii"),
                "valid_from": "2026-10-13",
                "valid_to": None,
            }
        ],
    }


def _original(private_pem: bytes, **overrides):
    inputs = _inputs(
        episode={"episode_id": "SYN-EPISODE-0001"},
        care_event={"type": "escalation", "source_role": "supervisor"},
        **overrides,
    )
    return create_session_receipt(**inputs, private_key_pem=private_pem)


def test_role_source_is_optional_and_absent_receipts_are_unchanged():
    private_pem, _ = _keypair()
    plain = create_session_receipt(**_inputs(), private_key_pem=private_pem)
    assert "role_source" not in plain["metadata"]["acknowledgement"]
    assert "amendment" not in plain["metadata"]

    inputs = _inputs()
    inputs["acknowledgement"] = {
        **inputs["acknowledgement"],
        "role_source": "self_declared",
    }
    with_source = create_session_receipt(**inputs, private_key_pem=private_pem)
    assert with_source["metadata"]["acknowledgement"]["role_source"] == "self_declared"


def test_role_source_is_a_closed_enumeration():
    private_pem, _ = _keypair()
    inputs = _inputs()
    inputs["acknowledgement"] = {**inputs["acknowledgement"], "role_source": "trust me"}
    with pytest.raises(SessionReceiptError, match="role_source"):
        create_session_receipt(**inputs, private_key_pem=private_pem)


def test_amendment_links_original_and_both_verify(tmp_path: Path):
    private_pem, public_pem = _keypair()
    registry = _registry(public_pem)
    original = _original(private_pem)
    frozen = copy.deepcopy(original)

    amended = amend_session_receipt(
        original,
        reason_code="episode_reference_corrected",
        corrections={"episode.episode_id": "SYN-EPISODE-0002"},
        amended_by=SUPERVISOR,
        reason_sha256=hashlib.sha256(b"synthetic reason").hexdigest(),
        software=SOFTWARE,
        registry=registry,
        private_key_pem=private_pem,
    )

    assert original == frozen, "the original receipt object is never modified"
    public_path = tmp_path / "pub.pem"
    public_path.write_bytes(public_pem)
    assert verify_session_receipt(original, public_path) is True
    assert verify_session_receipt(amended, public_path) is True
    assert verify_session_receipt_from_registry(amended, registry) is True

    metadata = amended["metadata"]
    block = metadata["amendment"]
    assert block["schema"] == module.AMENDMENT_SCHEMA
    assert block["amends_receipt_id"] == original["bundle_id"]
    assert block["amends_receipt_sha256"] == receipt_sha256(original)
    assert (
        block["amends_receipt_sha256"]
        == "sha256:" + hashlib.sha256(receipt_json_bytes(original)).hexdigest()
    )
    assert block["corrected_fields"] == ["episode.episode_id"]
    assert block["amended_by"] == {**SUPERVISOR, "name_included": False}
    assert block["original_preserved"] is True
    assert block["reason_sha256"].startswith("sha256:")
    assert metadata["supersedes_receipt_id"] == original["bundle_id"]
    assert metadata["episode"]["episode_id"] == "SYN-EPISODE-0002"
    assert original["metadata"]["episode"]["episode_id"] == "SYN-EPISODE-0001"
    # Evidence of what happened is carried unchanged.
    for key in (
        "session",
        "model_input",
        "model_output",
        "content_gates",
        "acknowledgement",
    ):
        assert metadata[key] == original["metadata"][key]
    assert amended["bundle_id"] != original["bundle_id"]
    assert verify_amendment_link(amended, original) is True
    assert describe_amendment(original) is None
    assert describe_amendment(amended)["reason_code"] == "episode_reference_corrected"


def test_link_fails_for_a_different_or_altered_original():
    private_pem, _ = _keypair()
    original = _original(private_pem)
    other = _original(private_pem)
    amended = amend_session_receipt(
        original,
        reason_code="administrative_correction",
        amended_by=SIGNER,
        software=SOFTWARE,
        private_key_pem=private_pem,
    )
    assert verify_amendment_link(amended, original) is True
    assert verify_amendment_link(amended, other) is False
    altered = copy.deepcopy(original)
    altered["metadata"]["acknowledgement"]["role"] = "clinician"
    assert verify_amendment_link(amended, altered) is False
    assert verify_amendment_link(original, amended) is False


def test_altering_the_amendment_block_breaks_the_signature(tmp_path: Path):
    private_pem, public_pem = _keypair()
    original = _original(private_pem)
    amended = amend_session_receipt(
        original,
        reason_code="care_event_type_corrected",
        corrections={"care_event.type": "clinician_review"},
        amended_by=SIGNER,
        software=SOFTWARE,
        private_key_pem=private_pem,
    )
    assert amended["metadata"]["care_event"] == {
        "type": "clinician_review",
        "signal_type": None,
        "source_role": "supervisor",
    }
    public_path = tmp_path / "pub.pem"
    public_path.write_bytes(public_pem)
    tampered = copy.deepcopy(amended)
    tampered["metadata"]["amendment"]["amended_by"]["role"] = "clinician_lead"
    assert verify_session_receipt(tampered, public_path) is False
    tampered = copy.deepcopy(amended)
    tampered["metadata"]["amendment"]["amends_receipt_id"] = "qixmind-ser-" + "0" * 16
    assert verify_session_receipt(tampered, public_path) is False


@pytest.mark.parametrize(
    ("reason_code", "corrections"),
    [
        ("episode_reference_corrected", {}),
        ("episode_reference_corrected", {"care_event.type": "clinician_review"}),
        ("administrative_correction", {"episode.episode_id": "SYN-EPISODE-0009"}),
        ("not_a_reason", {}),
    ],
)
def test_reason_code_must_match_corrected_fields(reason_code, corrections):
    private_pem, _ = _keypair()
    original = _original(private_pem)
    with pytest.raises(SessionReceiptError):
        amend_session_receipt(
            original,
            reason_code=reason_code,
            corrections=corrections,
            amended_by=SUPERVISOR,
            software=SOFTWARE,
            private_key_pem=private_pem,
        )


@pytest.mark.parametrize(
    "corrections",
    [
        {"acknowledgement.role": "clinician"},
        {"content_gates.overall_action": "pass"},
        {"model_output.sha256": "0" * 64},
    ],
)
def test_evidence_fields_are_never_amendable(corrections):
    private_pem, _ = _keypair()
    with pytest.raises(SessionReceiptError, match="corrections may name only"):
        amend_session_receipt(
            _original(private_pem),
            reason_code="administrative_correction",
            corrections=corrections,
            amended_by=SUPERVISOR,
            software=SOFTWARE,
            private_key_pem=private_pem,
        )


def test_unchanged_correction_and_bad_actor_are_refused():
    private_pem, _ = _keypair()
    original = _original(private_pem)
    with pytest.raises(SessionReceiptError, match="unchanged"):
        amend_session_receipt(
            original,
            reason_code="episode_reference_corrected",
            corrections={"episode.episode_id": "SYN-EPISODE-0001"},
            amended_by=SUPERVISOR,
            software=SOFTWARE,
            private_key_pem=private_pem,
        )
    for actor in (
        {
            "role": "Supervisor Jane",
            "role_source": "self_declared",
            "authority": "supervising_role",
        },
        {
            "role": "supervisor",
            "role_source": "said_so",
            "authority": "supervising_role",
        },
        {"role": "supervisor", "role_source": "self_declared", "authority": "anyone"},
        {
            "role": "supervisor",
            "role_source": "self_declared",
            "authority": "supervising_role",
            "name": "x",
        },
    ):
        with pytest.raises(SessionReceiptError):
            amend_session_receipt(
                original,
                reason_code="administrative_correction",
                amended_by=actor,
                software=SOFTWARE,
                private_key_pem=private_pem,
            )


def test_episode_correction_follows_episode_rules():
    private_pem, _ = _keypair()
    with pytest.raises(SessionReceiptError, match="episode"):
        amend_session_receipt(
            _original(private_pem),
            reason_code="episode_reference_corrected",
            corrections={"episode.episode_id": "ABC1234"},
            amended_by=SUPERVISOR,
            software=SOFTWARE,
            private_key_pem=private_pem,
        )


def test_original_must_verify_when_a_registry_is_given():
    private_pem, public_pem = _keypair()
    stranger_private, _ = _keypair()
    original = _original(stranger_private)
    with pytest.raises(SessionReceiptError, match="does not verify"):
        amend_session_receipt(
            original,
            reason_code="administrative_correction",
            amended_by=SUPERVISOR,
            software=SOFTWARE,
            registry=_registry(public_pem),
            private_key_pem=private_pem,
        )


def test_sandbox_or_foreign_bundles_cannot_be_amended():
    private_pem, _ = _keypair()
    original = _original(private_pem)
    sandboxish = copy.deepcopy(original)
    sandboxish["metadata"]["environment"] = "sandbox_evaluation"
    for candidate in (sandboxish, {"framework": "OTHER", "metadata": {}}):
        with pytest.raises(SessionReceiptError, match="only a QiXMind session receipt"):
            amend_session_receipt(
                candidate,
                reason_code="administrative_correction",
                amended_by=SUPERVISOR,
                software=SOFTWARE,
                private_key_pem=private_pem,
            )


def test_amendment_must_supersede_what_it_amends():
    private_pem, _ = _keypair()
    original = _original(private_pem)
    inputs = _inputs()
    with pytest.raises(SessionReceiptError, match="supersedes exactly"):
        create_session_receipt(
            **inputs,
            supersedes_receipt_id="qixmind-ser-" + "1" * 16,
            amendment={
                "amends_receipt_id": original["bundle_id"],
                "amends_receipt_sha256": receipt_sha256(original),
                "reason_code": "administrative_correction",
                "corrected_fields": [],
                "amended_by": SUPERVISOR,
                "amended_at": "2026-10-15T10:00:00Z",
            },
            private_key_pem=private_pem,
        )


def test_chained_amendment_names_only_its_direct_predecessor():
    private_pem, _ = _keypair()
    first = _original(private_pem)
    second = amend_session_receipt(
        first,
        reason_code="episode_reference_corrected",
        corrections={"episode.episode_id": "SYN-EPISODE-0002"},
        amended_by=SUPERVISOR,
        software=SOFTWARE,
        private_key_pem=private_pem,
    )
    third = amend_session_receipt(
        second,
        reason_code="care_event_type_corrected",
        corrections={"care_event.type": "service_review"},
        amended_by=SIGNER,
        software=SOFTWARE,
        private_key_pem=private_pem,
    )
    assert third["metadata"]["amendment"]["amends_receipt_id"] == second["bundle_id"]
    assert third["metadata"]["episode"]["episode_id"] == "SYN-EPISODE-0002"
    assert verify_amendment_link(third, second) is True
    assert verify_amendment_link(third, first) is False


def test_follow_up_state_can_be_refreshed_in_an_amendment():
    private_pem, _ = _keypair()
    original = _original(private_pem)
    follow_up = dict(original["metadata"]["escalation_follow_up"])
    follow_up.update(
        {
            "status": "closed",
            "closed_at": "2026-10-13T05:00:00Z",
            "closed_by_role": "clinician",
            "owner_role": "clinician",
            "backup_role": "supervisor",
            "closure_outcome_code": "follow_up_completed",
        }
    )
    amended = amend_session_receipt(
        original,
        reason_code="administrative_correction",
        amended_by=SUPERVISOR,
        software=SOFTWARE,
        escalation_follow_up=follow_up,
        review_state={"service_level": "closed", "reviewed_by_role": "supervisor"},
        private_key_pem=private_pem,
    )
    assert amended["metadata"]["escalation_follow_up"]["status"] == "closed"
    assert amended["metadata"]["escalation_follow_up"]["owner_role"] == "clinician"
    assert amended["metadata"]["review_state"]["service_level"] == "closed"


def test_cli_names_the_amended_receipt_and_checks_the_link(tmp_path: Path):
    private_pem, public_pem = _keypair()
    original = _original(private_pem)
    amended = amend_session_receipt(
        original,
        reason_code="episode_reference_corrected",
        corrections={"episode.episode_id": "SYN-EPISODE-0003"},
        amended_by=SUPERVISOR,
        software=SOFTWARE,
        private_key_pem=private_pem,
    )
    original_path = tmp_path / "original.json"
    amended_path = tmp_path / "amended.json"
    other_path = tmp_path / "other.json"
    public_path = tmp_path / "pub.pem"
    original_path.write_bytes(receipt_json_bytes(original))
    amended_path.write_bytes(receipt_json_bytes(amended))
    other_path.write_bytes(receipt_json_bytes(_original(private_pem)))
    public_path.write_bytes(public_pem)
    runner = CliRunner()

    result = runner.invoke(app, ["verify", str(original_path), str(public_path)])
    assert result.exit_code == 0, result.output
    assert "AMENDS" not in result.output

    result = runner.invoke(app, ["verify", str(amended_path), str(public_path)])
    assert result.exit_code == 0, result.output
    assert f"AMENDS: {original['bundle_id']}" in result.output

    result = runner.invoke(
        app,
        ["verify", str(amended_path), str(public_path), "--amends", str(original_path)],
    )
    assert result.exit_code == 0, result.output
    assert "amendment link (id and SHA-256) matches" in result.output

    result = runner.invoke(
        app,
        ["verify", str(amended_path), str(public_path), "--amends", str(other_path)],
    )
    assert result.exit_code != 0
    assert "does not match" in result.output

    result = runner.invoke(
        app,
        ["verify", str(original_path), str(public_path), "--amends", str(other_path)],
    )
    assert result.exit_code != 0
    assert "amends nothing" in result.output


def test_amended_receipt_verifies_with_the_2_16_rules(tmp_path: Path):
    """An older verifier checks framework, schema, content keys and signature only."""
    private_pem, public_pem = _keypair()
    amended = amend_session_receipt(
        _original(private_pem),
        reason_code="administrative_correction",
        amended_by=SUPERVISOR,
        software=SOFTWARE,
        private_key_pem=private_pem,
    )
    module._reject_content_fields(amended)
    serialized = json.dumps(amended)
    for forbidden in ('"name"', '"text"', '"notes"', '"reason"'):
        assert forbidden not in serialized
