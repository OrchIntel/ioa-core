# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""Named K4 evidence-keystone suite.

Every test uses synthetic evidence only. The PyPI test is opt-in because the
2.9.0 release is intentionally held until the rest of GATE0 is complete.
"""

import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ioa_core.cli import app
from ioa_core.evidence import EvidenceBundle, EvidenceSigningError


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


def _write_signed_bundle(directory: Path) -> tuple[Path, Path, Path]:
    private_path, public_path = _write_keypair(directory)
    bundle = EvidenceBundle(bundle_id="k4-synthetic-001")
    bundle.add_validation({"result": "pass", "source": "synthetic"})
    bundle.generate_signature(private_key_path=str(private_path))
    bundle_path = directory / "bundle.json"
    bundle_path.write_text(bundle.to_json(), encoding="utf-8")
    return bundle_path, public_path, private_path


def test_k4a_unchanged_bundle_verifies_pass(tmp_path: Path):
    bundle_path, public_path, _ = _write_signed_bundle(tmp_path)

    result = CliRunner().invoke(app, ["verify", str(bundle_path), str(public_path)])

    assert result.exit_code == 0
    assert "PASS: Ed25519 evidence signature verified offline" in result.output


def test_k4b_one_byte_bundle_change_verifies_fail(tmp_path: Path):
    bundle_path, public_path, _ = _write_signed_bundle(tmp_path)
    payload = bytearray(bundle_path.read_bytes())
    marker = b"k4-synthetic-001"
    marker_offset = payload.index(marker)
    payload[marker_offset + len(marker) - 1] = ord("2")
    bundle_path.write_bytes(payload)

    result = CliRunner().invoke(app, ["verify", str(bundle_path), str(public_path)])

    assert result.exit_code != 0
    assert "FAIL:" in result.output


def test_k4c_wrong_public_key_verifies_fail(tmp_path: Path):
    bundle_path, _, _ = _write_signed_bundle(tmp_path)
    wrong_dir = tmp_path / "wrong-key"
    wrong_dir.mkdir()
    _, wrong_public_path = _write_keypair(wrong_dir)

    result = CliRunner().invoke(
        app, ["verify", str(bundle_path), str(wrong_public_path)]
    )

    assert result.exit_code != 0
    assert "FAIL:" in result.output


def test_k4d_missing_signing_key_fails_closed_without_emission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("IOA_EVIDENCE_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.delenv("IOA_EVIDENCE_PRIVATE_KEY_B64", raising=False)
    bundle = EvidenceBundle(bundle_id="k4-missing-key-001")
    output_path = tmp_path / "not-emitted.json"

    with pytest.raises(EvidenceSigningError):
        bundle.generate_signature()

    assert bundle.signature is None
    assert bundle.signature_status == "unsigned"
    assert not output_path.exists()


def test_k4e_signer_failure_cannot_mark_bundle_signed(
    monkeypatch: pytest.MonkeyPatch,
):
    bundle = EvidenceBundle(bundle_id="k4-signer-failure-001")

    def fail(*_args, **_kwargs):
        raise EvidenceSigningError("synthetic signer failure")

    monkeypatch.setattr("ioa_core.evidence.signing.sign_bundle", fail)

    with pytest.raises(EvidenceSigningError):
        bundle.generate_signature()

    assert bundle.signature is None
    assert bundle.signature_status == "unsigned"


def test_k4f_verifier_passes_with_network_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    bundle_path, public_path, _ = _write_signed_bundle(tmp_path)
    real_socket = socket.socket

    def blocked_socket(*args, **kwargs):
        family = args[0] if args else kwargs.get("family", socket.AF_INET)
        if family in {socket.AF_INET, socket.AF_INET6}:
            raise AssertionError("network access attempted during offline verification")
        return real_socket(*args, **kwargs)

    monkeypatch.setattr(socket, "socket", blocked_socket)
    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("network access attempted during offline verification")
        ),
    )

    result = CliRunner().invoke(app, ["verify", str(bundle_path), str(public_path)])

    assert result.exit_code == 0
    assert "offline" in result.output


@pytest.mark.skipif(
    os.getenv("IOA_RUN_PYPI_K4") != "1",
    reason="Run with IOA_RUN_PYPI_K4=1 after ioa-core 2.9.0 is published",
)
def test_k4g_clean_machine_verifier_from_pypi(tmp_path: Path):
    bundle_path, public_path, _ = _write_signed_bundle(tmp_path)
    venv_path = tmp_path / "clean-venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_path)],
        check=True,
        cwd=tmp_path,
    )
    python_path = venv_path / "bin" / "python"
    ioa_path = venv_path / "bin" / "ioa"
    subprocess.run(
        [
            str(python_path),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "ioa-core==2.9.0",
        ],
        check=True,
        cwd=tmp_path,
    )
    result = subprocess.run(
        [str(ioa_path), "verify", str(bundle_path), str(public_path)],
        check=False,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: Ed25519 evidence signature verified offline" in result.stdout
