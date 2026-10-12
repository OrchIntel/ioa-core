# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Session Evidence Receipt tests. Synthetic keys and synthetic text only."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ioa_core.cli import app
from ioa_core.evidence import (
    EvidenceBundle,
    EvidenceSigningError,
    SessionReceiptError,
    create_session_receipt,
    receipt_json_bytes,
    verify_session_receipt,
    verify_session_receipt_from_registry,
)
from ioa_core.evidence import session_receipt as module
from ioa_core.health import ContentGateEvaluator, sha256_text

SYNTHETIC_OUTPUT = "SYNTHETIC: reported suicidal ideation without a plan. Protective factors: supportive aunt."
SYNTHETIC_INPUT = "SYNTHETIC input [NAME_1] low mood two weeks"


def _keypair():
    key = Ed25519PrivateKey.generate()
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private_pem, public_pem


def _gate_report(text: str = SYNTHETIC_OUTPUT):
    return ContentGateEvaluator.for_profile("youth_mental_health_nz").evaluate(
        output_text=text
    )


def _inputs(report=None, **overrides):
    report = report or _gate_report()
    fired = [result.gate for result in report.fired_gates()]
    values = {
        "session": {
            "evidence_bundle_id": "evb-synthetic-1",
            "evidence_chain_id": "chain-synthetic-1",
            "workflow_key": "clinical_reasoning_review",
            "care_setting": "youth_mental_health",
            "profile_id": "youth_mental_health_nz",
            "jurisdiction": "NZ",
            "provider": "synthetic",
            "model": "synthetic-model",
        },
        "model_input": {
            "sha256": sha256_text(SYNTHETIC_INPUT),
            "length": len(SYNTHETIC_INPUT),
            "deidentification": {
                "mode": "pseudonymize",
                "engine": "presidio+regex",
                "detections": 1,
                "uncertain_hits": 0,
                "changed": True,
            },
        },
        "model_output": {
            "sha256": report.output_sha256,
            "length": len(SYNTHETIC_OUTPUT),
        },
        "content_gates": report.to_dict(),
        "acknowledgement": {
            "review_event_id": "42",
            "role": "supervisor",
            "acknowledged_at": "2026-10-13T01:00:00Z",
            "checklist_items_count": 6,
            "acknowledged_gates": fired,
        },
        "escalation_follow_up": (
            {
                "required": True,
                "obligation_id": "ob-synthetic-1",
                "gate": "crisis_risk_to_self",
                "severity": "escalate",
                "created_at": "2026-10-13T01:00:00Z",
                "deadline_at": "2026-10-14T01:00:00Z",
                "deadline_hours": 24,
                "status": "open",
                "closed_at": None,
                "closed_by_role": None,
                "closure_review_event_id": None,
                "alert": None,
            }
            if fired
            else None
        ),
        "software": {"ioa_core_version": "synthetic", "console_version": "synthetic"},
    }
    values.update(overrides)
    return values


def _flatten(value, found=None):
    found = found if found is not None else set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key).lower())
            _flatten(child, found)
    elif isinstance(value, list):
        for child in value:
            _flatten(child, found)
    return found


def test_receipt_is_signed_hash_only_and_verifies_offline(tmp_path: Path):
    private_pem, public_pem = _keypair()
    receipt = create_session_receipt(**_inputs(), private_key_pem=private_pem)

    assert receipt["framework"] == module.RECEIPT_FRAMEWORK
    assert receipt["bundle_id"].startswith(module.RECEIPT_ID_PREFIX)
    assert receipt["signature"]["sig_version"] == "ed25519-v1"
    assert receipt["signature_status"] == "signed"
    metadata = receipt["metadata"]
    assert metadata["schema"] == module.RECEIPT_SCHEMA
    assert metadata["disclaimers"] == {
        "no_diagnosis": True,
        "no_efficacy_claim": True,
        "not_youth_facing": True,
        "content_included": False,
    }
    assert metadata["model_input"]["sha256"] == sha256_text(SYNTHETIC_INPUT)
    assert metadata["content_gates"]["overall_action"] == "escalate"
    assert metadata["acknowledgement"]["role"] == "supervisor"
    assert metadata["acknowledgement"]["name_included"] is False
    assert metadata["escalation_follow_up"]["status"] == "open"
    assert metadata["software"]["product"] == "QiXMind"
    assert metadata["software"]["lexicon_versions"]

    serialized = receipt_json_bytes(receipt).decode("utf-8")
    assert "suicidal" not in serialized
    assert "[NAME_1]" not in serialized
    assert not (_flatten(receipt) & module._CONTENT_KEYS)

    public_path = tmp_path / "pub.pem"
    public_path.write_bytes(public_pem)
    assert verify_session_receipt(receipt, public_path) is True
    restored = EvidenceBundle.from_dict(json.loads(json.dumps(receipt)))
    assert restored.verify_signature(str(public_path)) is True


def test_cli_verifies_receipt_and_rejects_tampering(tmp_path: Path):
    private_pem, public_pem = _keypair()
    receipt = create_session_receipt(**_inputs(), private_key_pem=private_pem)
    receipt_path = tmp_path / "receipt.json"
    public_path = tmp_path / "pub.pem"
    receipt_path.write_bytes(receipt_json_bytes(receipt))
    public_path.write_bytes(public_pem)

    runner = CliRunner()
    result = runner.invoke(app, ["verify", str(receipt_path), str(public_path)])
    assert result.exit_code == 0, result.output
    assert "PASS" in result.output

    tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
    tampered["metadata"]["acknowledgement"]["role"] = "clinician"
    receipt_path.write_text(json.dumps(tampered), encoding="utf-8")
    result = runner.invoke(app, ["verify", str(receipt_path), str(public_path)])
    assert result.exit_code != 0
    assert "FAIL" in result.output


def test_missing_key_fails_closed_and_emits_nothing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("IOA_EVIDENCE_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.delenv("IOA_EVIDENCE_PRIVATE_KEY_B64", raising=False)
    with pytest.raises(EvidenceSigningError):
        create_session_receipt(**_inputs())


def test_fired_gate_must_be_acknowledged():
    private_pem, _ = _keypair()
    inputs = _inputs()
    inputs["acknowledgement"]["acknowledged_gates"] = []
    with pytest.raises(SessionReceiptError, match="acknowledged"):
        create_session_receipt(**inputs, private_key_pem=private_pem)


def test_escalation_requires_follow_up_block():
    private_pem, _ = _keypair()
    with pytest.raises(SessionReceiptError, match="escalation_follow_up"):
        create_session_receipt(
            **_inputs(escalation_follow_up=None), private_key_pem=private_pem
        )


def test_clean_session_needs_no_follow_up_block():
    private_pem, public_pem = _keypair()
    report = _gate_report("SYNTHETIC: sleep hygiene discussed, review in two weeks.")
    receipt = create_session_receipt(
        **_inputs(report=report), private_key_pem=private_pem
    )
    assert receipt["metadata"]["escalation_follow_up"] == {"required": False}
    assert receipt["metadata"]["content_gates"]["overall_action"] == "pass"


def test_content_fields_and_long_strings_are_rejected():
    private_pem, _ = _keypair()
    inputs = _inputs()
    inputs["session"] = dict(inputs["session"], patient_name="Synthetic Person")
    with pytest.raises(SessionReceiptError, match="content"):
        create_session_receipt(**inputs, private_key_pem=private_pem)
    inputs = _inputs()
    inputs["content_gates"]["results"][0]["matched_text"] = "x"
    with pytest.raises(SessionReceiptError, match="content|unexpected keys"):
        create_session_receipt(**inputs, private_key_pem=private_pem)
    inputs = _inputs()
    inputs["content_gates"]["results"][0]["offset"] = 12
    with pytest.raises(SessionReceiptError, match="unexpected keys"):
        create_session_receipt(**inputs, private_key_pem=private_pem)
    inputs = _inputs()
    inputs["software"]["console_version"] = "v" * 401
    with pytest.raises(SessionReceiptError, match="too long"):
        create_session_receipt(**inputs, private_key_pem=private_pem)


def test_bad_hash_and_held_output_are_rejected():
    private_pem, _ = _keypair()
    inputs = _inputs()
    inputs["model_input"]["sha256"] = "not-a-hash"
    with pytest.raises(SessionReceiptError, match="SHA-256"):
        create_session_receipt(**inputs, private_key_pem=private_pem)
    inputs = _inputs()
    inputs["model_output"]["held"] = True
    with pytest.raises(SessionReceiptError, match="held"):
        create_session_receipt(**inputs, private_key_pem=private_pem)


def test_unavailable_detector_must_hold():
    private_pem, _ = _keypair()
    inputs = _inputs()
    inputs["content_gates"]["detector_status"] = "unavailable"
    inputs["content_gates"]["overall_action"] = "pass"
    with pytest.raises(SessionReceiptError, match="hold"):
        create_session_receipt(**inputs, private_key_pem=private_pem)


def test_registry_keeps_rotated_key_for_old_receipts():
    old_private, old_public = _keypair()
    new_private, new_public = _keypair()
    old_receipt = create_session_receipt(**_inputs(), private_key_pem=old_private)
    new_receipt = create_session_receipt(**_inputs(), private_key_pem=new_private)
    registry = {
        "schema": module.KEY_REGISTRY_SCHEMA,
        "current_public_key_id": module.public_key_id_from_pem(new_public),
        "keys": [
            {
                "public_key_id": module.public_key_id_from_pem(old_public),
                "public_key_pem": old_public.decode("ascii"),
                "valid_from": "2026-10-13",
                "valid_to": "2026-12-31",
            },
            {
                "public_key_id": module.public_key_id_from_pem(new_public),
                "public_key_pem": new_public.decode("ascii"),
                "valid_from": "2027-01-01",
                "valid_to": None,
            },
        ],
    }
    assert verify_session_receipt_from_registry(old_receipt, registry) is True
    assert verify_session_receipt_from_registry(new_receipt, registry) is True
    stranger_receipt = create_session_receipt(
        **_inputs(), private_key_pem=_keypair()[0]
    )
    assert verify_session_receipt_from_registry(stranger_receipt, registry) is False
    normalized = json.loads(module.public_key_registry_json_bytes(registry))
    assert normalized["framework"] == module.RECEIPT_FRAMEWORK
    assert len(normalized["keys"]) == 2


def test_registry_rejects_mismatched_key_id():
    _, public = _keypair()
    registry = {
        "schema": module.KEY_REGISTRY_SCHEMA,
        "current_public_key_id": "0000000000000000",
        "keys": [
            {
                "public_key_id": "0000000000000000",
                "public_key_pem": public.decode("ascii"),
                "valid_from": "2026-10-13",
            }
        ],
    }
    with pytest.raises(SessionReceiptError, match="does not match"):
        module._normalize_key_registry(registry)


def test_configured_registry_from_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    private_pem, public_pem = _keypair()
    for name in (
        module.ENV_PUBLIC_KEY_REGISTRY_PATH,
        module.ENV_PUBLIC_KEY_REGISTRY_B64,
        module.ENV_PUBLIC_KEY_B64,
    ):
        monkeypatch.delenv(name, raising=False)
    public_path = tmp_path / "pub.pem"
    public_path.write_bytes(public_pem)
    monkeypatch.setenv(module.ENV_PUBLIC_KEY_PATH, str(public_path))
    monkeypatch.setenv(module.ENV_PUBLIC_KEY_VALID_FROM, "2026-10-13")
    registry = module.configured_public_key_registry()
    assert registry["current_public_key_id"] == module.public_key_id_from_pem(
        public_pem
    )
    assert module.configured_public_key_pem() == public_pem
    receipt = create_session_receipt(**_inputs(), private_key_pem=private_pem)
    assert verify_session_receipt_from_registry(receipt, registry) is True

    monkeypatch.delenv(module.ENV_PRIVATE_KEY_B64, raising=False)
    monkeypatch.delenv(module.ENV_PRIVATE_KEY_PATH, raising=False)
    with pytest.raises(SessionReceiptError, match="signing key"):
        module.configured_private_key_pem()


def test_non_receipt_bundles_are_not_verified_as_receipts(tmp_path: Path):
    private_pem, public_pem = _keypair()
    bundle = EvidenceBundle(bundle_id="other-synthetic")
    bundle.generate_signature(private_key_pem=private_pem)
    public_path = tmp_path / "pub.pem"
    public_path.write_bytes(public_pem)
    assert verify_session_receipt(bundle.to_dict(), public_path) is False
