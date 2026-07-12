# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""K2 evidence signing tests using synthetic bundles only."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ioa_core.cli import app
from ioa_core.evidence import EvidenceBundle, EvidenceSigningError
from ioa_core.governance.audit_chain import AuditChain


def _write_keypair(directory: Path) -> tuple[Path, Path]:
    private_key = Ed25519PrivateKey.generate()
    private_path = directory / "synthetic-private.pem"
    public_path = directory / "synthetic-public.pem"
    private_path.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return private_path, public_path


def _bundle() -> EvidenceBundle:
    bundle = EvidenceBundle(bundle_id="bundle-synthetic-001")
    bundle.add_validation({"result": "pass", "source": "synthetic"})
    return bundle


def test_missing_signing_key_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("IOA_EVIDENCE_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.delenv("IOA_EVIDENCE_PRIVATE_KEY_B64", raising=False)

    with pytest.raises(EvidenceSigningError):
        _bundle().generate_signature()


def test_signing_failure_never_marks_bundle_signed(monkeypatch: pytest.MonkeyPatch):
    bundle = _bundle()

    def fail(*_args, **_kwargs):
        raise EvidenceSigningError("synthetic signer failure")

    monkeypatch.setattr("ioa_core.evidence.signing.sign_bundle", fail)

    with pytest.raises(EvidenceSigningError):
        bundle.generate_signature()

    assert bundle.signature is None
    assert bundle.signature_status == "unsigned"


def test_ed25519_sign_and_verify(tmp_path: Path):
    private_path, public_path = _write_keypair(tmp_path)
    bundle = _bundle()

    envelope = bundle.generate_signature(private_key_path=str(private_path))

    assert envelope["sig_version"] == "ed25519-v1"
    assert envelope["algo"] == "Ed25519"
    assert bundle.signature_status == "signed"
    assert bundle.verify_signature(str(public_path)) is True
    assert bundle.signature_status == "signed"


def test_tampered_bundle_fails_verification(tmp_path: Path):
    private_path, public_path = _write_keypair(tmp_path)
    bundle = _bundle()
    bundle.generate_signature(private_key_path=str(private_path))
    tampered = bundle.to_dict()
    tampered["metadata"]["changed"] = True

    restored = EvidenceBundle.from_dict(tampered)

    assert restored.verify_signature(str(public_path)) is False
    assert restored.signature_status == "invalid"


def test_wrong_public_key_fails_verification(tmp_path: Path):
    private_path, _ = _write_keypair(tmp_path)
    wrong_dir = tmp_path / "wrong-key"
    wrong_dir.mkdir()
    _, wrong_public_path = _write_keypair(wrong_dir)
    bundle = _bundle()
    bundle.generate_signature(private_key_path=str(private_path))

    assert bundle.verify_signature(str(wrong_public_path)) is False


def test_mutating_a_signed_bundle_invalidates_signature(tmp_path: Path):
    private_path, _ = _write_keypair(tmp_path)
    bundle = _bundle()
    bundle.generate_signature(private_key_path=str(private_path))

    bundle.add_metadata("changed", True)

    assert bundle.signature is None
    assert bundle.signature_status == "unsigned"


def test_legacy_signature_is_explicitly_unsigned():
    legacy = EvidenceBundle.from_dict(
        {
            "bundle_id": "legacy-synthetic-001",
            "signature": "SIGv1:deadbeef",
        }
    )

    assert legacy.signature_status == "unsigned_legacy"
    assert legacy.verify_signature() is False
    assert legacy.signature_status == "unsigned_legacy"


def test_cli_verifies_good_bundle_and_rejects_tampering(tmp_path: Path):
    private_path, public_path = _write_keypair(tmp_path)
    bundle = _bundle()
    bundle.generate_signature(private_key_path=str(private_path))
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(bundle.to_json(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["verify", str(bundle_path), str(public_path)])
    assert result.exit_code == 0
    assert "PASS" in result.output

    tampered = json.loads(bundle_path.read_text(encoding="utf-8"))
    tampered["bundle_id"] = "tampered"
    bundle_path.write_text(json.dumps(tampered), encoding="utf-8")
    result = runner.invoke(app, ["verify", str(bundle_path), str(public_path)])
    assert result.exit_code != 0
    assert "FAIL" in result.output


def test_signed_bundle_is_added_to_and_verified_in_audit_chain(tmp_path: Path):
    private_path, public_path = _write_keypair(tmp_path)
    bundle = _bundle()
    bundle.generate_signature(private_key_path=str(private_path))
    chain_path = tmp_path / "audit-chain.jsonl"
    chain = AuditChain(str(chain_path), disable_rotation=True)

    chain.log_evidence_bundle(bundle.to_dict())
    chain.flush()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(bundle.to_json(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "verify",
            "--chain",
            "--chain-path",
            str(chain_path),
            str(bundle_path),
            str(public_path),
        ],
    )

    assert result.exit_code == 0
    assert "audit chain verified" in result.output

    lines = chain_path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[0])
    tampered["data"]["bundle_id"] = "tampered"
    chain_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
    assert chain.verify_chain(bundle_id=bundle.bundle_id)["valid"] is False
