# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Sandbox Evaluation Receipt tests. Synthetic keys and synthetic text only."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ioa_core.cli import app
from ioa_core.evidence import (
    SANDBOX_NOTICE,
    SandboxReceiptError,
    check_sandbox_receipt,
    create_sandbox_receipt,
    create_session_receipt,
    sign_bundle,
    verify_sandbox_receipt,
    verify_sandbox_receipt_from_registry,
    verify_session_receipt,
    verify_session_receipt_from_registry,
)
from ioa_core.evidence import sandbox_receipt as sbx
from ioa_core.evidence import session_receipt as prod
from ioa_core.evidence.session_receipt import public_key_id_from_pem
from ioa_core.health import (
    ContentGateEvaluator,
    capture_session_provenance,
    detect_findings,
    load_packaged_policy,
    sha256_text,
)

PROFILE = "youth_mental_health_au"
SYNTHETIC_INPUT = (
    "SYNTHETIC FIXTURE. Fictional young person. Says they want to end their life. "
    "No plan described."
)
SYNTHETIC_OUTPUT = (
    "SYNTHETIC FIXTURE.\nSummary: The young person reports suicidal thoughts and says "
    "they want to end their life. No plan was described.\nNext steps: clinician to "
    "escalate under the service procedure."
)


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


def _registry(public_pem: bytes, schema: str = sbx.SANDBOX_KEY_REGISTRY_SCHEMA):
    key_id = public_key_id_from_pem(public_pem)
    return {
        "schema": schema,
        "current_public_key_id": key_id,
        "keys": [
            {
                "public_key_id": key_id,
                "public_key_pem": public_pem.decode("ascii"),
                "valid_from": "2026-10-15",
            }
        ],
    }


def _computed():
    report = ContentGateEvaluator.for_profile(PROFILE).evaluate(
        output_text=SYNTHETIC_OUTPUT,
        input_text=SYNTHETIC_INPUT,
        profile_id=PROFILE,
        require_review_output=True,
    )
    findings = detect_findings(
        profile_id=PROFILE, input_text=SYNTHETIC_INPUT, output_text=SYNTHETIC_OUTPUT
    )
    policy = load_packaged_policy("qixmind_default_draft")
    actions = []
    for item in policy.required_actions(findings):
        entry = item.to_dict()
        entry["occurrence_key"] = "|".join(
            str(entry.get(k) or "") for k in ("gate", "source", "context", "entry")
        )
        actions.append(entry)
    gate_dict = report.to_dict()
    return (
        {
            "fixtures": {
                "label": "SYNTHETIC",
                "fixture_set_version": "2026.10.1",
                "input_fixture_id": "sbx-in-test",
                "output_fixture_id": "sbx-out-test-a",
                "profile_id": PROFILE,
                "jurisdiction": "AU-NSW",
            },
            "model_input": {
                "sha256": sha256_text(SYNTHETIC_INPUT),
                "length": len(SYNTHETIC_INPUT),
            },
            "model_output": {
                "sha256": sha256_text(SYNTHETIC_OUTPUT),
                "length": len(SYNTHETIC_OUTPUT),
                "held": report.is_held(),
            },
            "content_gates": gate_dict,
            "review_output": dict(gate_dict["review_output"]),
            "findings": findings.to_dict(),
            "required_actions": {"policy": policy.provenance(), "actions": actions},
            "provenance": capture_session_provenance(
                profile_id=PROFILE, policy=policy, findings_report=findings
            ),
        },
        [r.gate for r in report.fired_gates()],
        actions,
    )


def _assertions(fired, actions, **overrides):
    values = {
        "model": "partner-model-1.2",
        "provider": "partner-ai",
        "clinician_role": "clinician",
        "partner_timestamps": {"generated_at": "2026-10-15T03:00:00Z"},
        "acknowledged_gates": list(fired),
        "dispositions": [
            {"occurrence_key": a["occurrence_key"], "disposition": "escalated"}
            for a in actions
        ],
    }
    values.update(overrides)
    return values


def _receipt(private_pem, **kwargs):
    computed, fired, actions = _computed()
    return create_sandbox_receipt(
        sandbox={
            "tenant_id": "sbx-0123456789abcdef",
            "evaluation_id": "sbxe-0123456789abcdef",
        },
        computed=kwargs.pop("computed", computed),
        assertions=kwargs.pop("assertions", _assertions(fired, actions)),
        software={"ioa_core_version": "test", "console_version": "test"},
        private_key_pem=private_pem,
        **kwargs,
    )


def _production_receipt(private_pem):
    report = ContentGateEvaluator.for_profile(PROFILE).evaluate(
        output_text=SYNTHETIC_OUTPUT
    )
    fired = [r.gate for r in report.fired_gates()]
    return create_session_receipt(
        session={
            "evidence_bundle_id": "evb-synthetic-1",
            "workflow_key": "clinical_reasoning_review",
            "care_setting": "youth_mental_health",
            "profile_id": PROFILE,
        },
        model_input={
            "sha256": sha256_text(SYNTHETIC_INPUT),
            "deidentification": {"mode": "pseudonymize"},
        },
        model_output={"sha256": report.output_sha256},
        content_gates=report.to_dict(),
        acknowledgement={
            "review_event_id": "1",
            "role": "clinician",
            "acknowledged_at": "2026-10-15T03:00:00Z",
            "acknowledged_gates": fired,
        },
        escalation_follow_up={
            "required": True,
            "obligation_id": "1",
            "deadline_at": "2026-10-16T03:00:00Z",
            "status": "open",
        },
        software={"ioa_core_version": "test"},
        private_key_pem=private_pem,
    )


def test_sandbox_receipt_is_designated_labelled_and_verifies(tmp_path: Path):
    private_pem, public_pem = _keypair()
    receipt = _receipt(private_pem)
    meta = receipt["metadata"]
    assert receipt["framework"] == "QIXMIND_SANDBOX_EVALUATION_RECEIPT"
    assert receipt["bundle_id"].startswith("qixmind-sbx-")
    assert meta["environment"] == "sandbox_evaluation"
    assert meta["not_for_clinical_use"] is True
    assert meta["notice"] == SANDBOX_NOTICE
    for block in meta["computed"].values():
        assert block["computed_by"] == "qixmind" and "asserted_by" not in block
    for block in meta["assertions"].values():
        assert block["asserted_by"] == "partner" and "computed_by" not in block
    assert set(meta["assertions"]) == {
        "model",
        "provider",
        "clinician_role",
        "partner_timestamps",
        "acknowledged_gates",
        "dispositions",
    }
    assert meta["computed"]["findings"]["status"] == "evaluation_only"
    assert meta["computed"]["required_actions"]["label"] == "draft"
    assert meta["computed"]["sign_off_checks"]["all_fired_gates_acknowledged"] is True
    pub = tmp_path / "sandbox.pem"
    pub.write_bytes(public_pem)
    assert verify_sandbox_receipt(receipt, pub)
    result = check_sandbox_receipt(receipt, _registry(public_pem))
    assert list(result)[0] == "notice" and result["notice"] == SANDBOX_NOTICE
    assert result["valid"] is True and result["reason"] is None


def test_sandbox_receipt_fails_production_verification(tmp_path: Path):
    private_pem, public_pem = _keypair()
    receipt = _receipt(private_pem)
    pub = tmp_path / "k.pem"
    pub.write_bytes(public_pem)
    # Even with the very key that signed it, production verification refuses.
    assert verify_session_receipt(receipt, pub) is False
    assert verify_session_receipt_from_registry(receipt, _registry(public_pem)) is False
    production_shaped = _registry(public_pem, schema=prod.KEY_REGISTRY_SCHEMA)
    assert verify_session_receipt_from_registry(receipt, production_shaped) is False
    # Relabelling the framework breaks the signature and is still refused.
    forged = copy.deepcopy(receipt)
    forged["framework"] = prod.RECEIPT_FRAMEWORK
    forged["metadata"]["schema"] = prod.RECEIPT_SCHEMA
    assert verify_session_receipt(forged, pub) is False


def test_production_receipt_fails_sandbox_verification(tmp_path: Path):
    private_pem, public_pem = _keypair()
    receipt = _production_receipt(private_pem)
    pub = tmp_path / "k.pem"
    pub.write_bytes(public_pem)
    assert verify_session_receipt(receipt, pub) is True
    assert verify_sandbox_receipt(receipt, pub) is False
    result = check_sandbox_receipt(receipt, _registry(public_pem))
    assert result["valid"] is False and result["reason"] == "not_a_sandbox_receipt"
    assert result["notice"] == SANDBOX_NOTICE
    with pytest.raises(SandboxReceiptError):
        verify_sandbox_receipt_from_registry(
            _receipt(_keypair()[0]),
            _registry(public_pem, schema=prod.KEY_REGISTRY_SCHEMA),
        )


def test_sandbox_verifier_refuses_production_keys():
    private_pem, public_pem = _keypair()
    receipt = _receipt(private_pem)
    sandbox_registry = _registry(public_pem)
    production_registry = _registry(public_pem, schema=prod.KEY_REGISTRY_SCHEMA)
    result = check_sandbox_receipt(
        receipt, sandbox_registry, production_registry=production_registry
    )
    assert (
        result["valid"] is False and result["reason"] == "production_key_not_accepted"
    )
    with pytest.raises(SandboxReceiptError):
        sbx.assert_registries_disjoint(sandbox_registry, production_registry)
    with pytest.raises(SandboxReceiptError, match="production key"):
        _receipt(private_pem, production_registry=production_registry)
    other_public = _keypair()[1]
    sbx.assert_registries_disjoint(
        sandbox_registry, _registry(other_public, schema=prod.KEY_REGISTRY_SCHEMA)
    )
    result = check_sandbox_receipt(receipt, _registry(other_public))
    assert result["reason"] == "key_not_in_sandbox_registry"


@pytest.mark.parametrize(
    "path,value",
    [
        (("environment",), "production"),
        (("not_for_clinical_use",), False),
        (("notice",), "Clinical record"),
        (("assertions", "clinician_role", "asserted_by"), "qixmind"),
        (("computed", "content_gates", "computed_by"), "partner"),
    ],
)
def test_environment_and_labels_are_signed(tmp_path: Path, path, value):
    private_pem, public_pem = _keypair()
    receipt = _receipt(private_pem)
    target = receipt["metadata"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    pub = tmp_path / "k.pem"
    pub.write_bytes(public_pem)
    assert verify_sandbox_receipt(receipt, pub) is False
    assert check_sandbox_receipt(receipt, _registry(public_pem))["valid"] is False


@pytest.mark.parametrize("drop", ["environment", "not_for_clinical_use"])
def test_environment_fields_are_required_even_when_signed(tmp_path: Path, drop):
    """A correctly signed bundle without the designation is still refused."""
    private_pem, public_pem = _keypair()
    receipt = _receipt(private_pem)
    receipt["metadata"].pop(drop)
    receipt.pop("signature")
    receipt["signature"] = sign_bundle(receipt, private_key_pem=private_pem)
    pub = tmp_path / "k.pem"
    pub.write_bytes(public_pem)
    assert verify_sandbox_receipt(receipt, pub) is False
    assert (
        check_sandbox_receipt(receipt, _registry(public_pem))["reason"]
        == "environment_missing"
    )


def test_resigned_receipt_with_relabelled_assertion_is_refused(tmp_path: Path):
    private_pem, public_pem = _keypair()
    receipt = _receipt(private_pem)
    model = receipt["metadata"]["assertions"].pop("model")
    receipt["metadata"]["computed"]["model"] = {
        "computed_by": "qixmind",
        "value": model["value"],
    }
    receipt.pop("signature")
    receipt["signature"] = sign_bundle(receipt, private_key_pem=private_pem)
    assert (
        check_sandbox_receipt(receipt, _registry(public_pem))["reason"]
        == "labels_invalid"
    )


@pytest.mark.parametrize("field", list(sbx.PARTNER_ASSERTED_FIELDS))
def test_partner_asserted_fields_cannot_be_marked_computed(field):
    private_pem, _ = _keypair()
    computed, fired, actions = _computed()
    computed[field] = {"value": "x"}
    with pytest.raises(SandboxReceiptError, match="cannot be marked as computed"):
        _receipt(private_pem, computed=computed)


def test_assertion_labelled_computed_is_refused():
    private_pem, _ = _keypair()
    computed, fired, actions = _computed()
    assertions = _assertions(
        fired, actions, model={"value": "m-1", "computed_by": "qixmind"}
    )
    with pytest.raises(SandboxReceiptError, match="cannot be marked as computed"):
        _receipt(private_pem, assertions=assertions)


@pytest.mark.parametrize("field", ["content_gates", "findings", "required_actions"])
def test_computed_fields_cannot_be_asserted(field):
    private_pem, _ = _keypair()
    computed, fired, actions = _computed()
    assertions = _assertions(fired, actions, **{field: {"fired": []}})
    with pytest.raises(SandboxReceiptError, match="computed by QiXMind"):
        _receipt(private_pem, assertions=assertions)


@pytest.mark.parametrize(
    "override",
    [
        {"model": "a model with spaces"},
        {"provider": "x" * 200},
        {"clinician_role": "Senior Clinician"},
        {"partner_timestamps": {"generated_at": "yesterday afternoon"}},
        {"partner_timestamps": {"submitted_on": "2026-10-15T00:00:00Z"}},
        {"acknowledged_gates": ["crisis risk to self"]},
    ],
)
def test_assertions_are_identifiers_never_free_text(override):
    private_pem, _ = _keypair()
    computed, fired, actions = _computed()
    with pytest.raises(SandboxReceiptError):
        _receipt(private_pem, assertions=_assertions(fired, actions, **override))


def test_sign_off_rules_are_checked_by_qixmind():
    private_pem, _ = _keypair()
    computed, fired, actions = _computed()
    assert fired and actions
    with pytest.raises(SandboxReceiptError, match="acknowledged"):
        _receipt(
            private_pem, assertions=_assertions(fired, actions, acknowledged_gates=[])
        )
    with pytest.raises(SandboxReceiptError, match="disposition"):
        _receipt(private_pem, assertions=_assertions(fired, actions, dispositions=[]))
    escalation = next(a for a in actions if not a["dismissal_allowed"])
    dismissed = [
        (
            {
                "occurrence_key": a["occurrence_key"],
                "disposition": "not_applicable_with_reason",
                "reason_code": "negated_in_source",
            }
            if a is escalation
            else {"occurrence_key": a["occurrence_key"], "disposition": "escalated"}
        )
        for a in actions
    ]
    with pytest.raises(SandboxReceiptError, match="not applicable"):
        _receipt(
            private_pem, assertions=_assertions(fired, actions, dispositions=dismissed)
        )
    held = copy.deepcopy(computed)
    held["model_output"]["held"] = True
    with pytest.raises(SandboxReceiptError, match="held"):
        _receipt(private_pem, computed=held)


def test_content_fields_are_rejected():
    private_pem, _ = _keypair()
    computed, fired, actions = _computed()
    computed["model_output"]["text"] = SYNTHETIC_OUTPUT
    with pytest.raises(prod.SessionReceiptError):
        _receipt(private_pem, computed=computed)


def test_fixture_label_must_be_synthetic():
    private_pem, _ = _keypair()
    computed, fired, actions = _computed()
    computed["fixtures"]["label"] = "REAL"
    with pytest.raises(SandboxReceiptError, match="SYNTHETIC"):
        _receipt(private_pem, computed=computed)


def test_registry_schemas_are_separate():
    _, public_pem = _keypair()
    with pytest.raises(SandboxReceiptError):
        sbx.normalize_sandbox_key_registry(
            _registry(public_pem, schema=prod.KEY_REGISTRY_SCHEMA)
        )
    with pytest.raises(prod.SessionReceiptError):
        prod.public_key_registry_json_bytes(_registry(public_pem))
    body = json.loads(sbx.sandbox_key_registry_json_bytes(_registry(public_pem)))
    assert (
        body["environment"] == "sandbox_evaluation" and body["notice"] == SANDBOX_NOTICE
    )


def test_sandbox_key_environment_is_separate(monkeypatch: pytest.MonkeyPatch):
    import base64

    private_pem, _ = _keypair()
    for name in (
        sbx.ENV_SANDBOX_PRIVATE_KEY_B64,
        sbx.ENV_SANDBOX_PRIVATE_KEY_PATH,
        "QIXMIND_EVIDENCE_PRIVATE_KEY_B64",
        "QIXMIND_EVIDENCE_PRIVATE_KEY_PATH",
    ):
        monkeypatch.delenv(name, raising=False)
    # The production key variable alone never configures sandbox signing.
    monkeypatch.setenv(
        "QIXMIND_EVIDENCE_PRIVATE_KEY_B64", base64.b64encode(private_pem).decode()
    )
    with pytest.raises(SandboxReceiptError, match="not configured"):
        sbx.configured_sandbox_private_key_pem()
    monkeypatch.setenv(
        sbx.ENV_SANDBOX_PRIVATE_KEY_B64, base64.b64encode(private_pem).decode()
    )
    with pytest.raises(SandboxReceiptError, match="production key"):
        sbx.configured_sandbox_private_key_pem()
    other, _ = _keypair()
    monkeypatch.setenv(
        sbx.ENV_SANDBOX_PRIVATE_KEY_B64, base64.b64encode(other).decode()
    )
    assert sbx.configured_sandbox_private_key_pem() == other


def test_cli_shows_sandbox_notice_first(tmp_path: Path):
    private_pem, public_pem = _keypair()
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(_receipt(private_pem)), encoding="utf-8")
    pub = tmp_path / "k.pem"
    pub.write_bytes(public_pem)
    result = CliRunner().invoke(app, ["verify", str(receipt_path), str(pub)])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[0] == SANDBOX_NOTICE
