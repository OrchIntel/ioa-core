# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Signed Session Evidence Receipts (QiXMind).

A Session Evidence Receipt is an IOA Core evidence bundle that answers four
questions about one governed AI session, in a form an outside party can verify
offline with ``ioa verify receipt.json pubkey.pem``:

1. What did the model actually see? (hash of the de-identified payload)
2. Which safety gates fired, in what order, with what result?
3. Who (by role, never by name) acknowledged the output before it was committed?
4. When an escalation was promised, was follow-up confirmed by the deadline,
   or did an alert fire?

The receipt stores hashes, identifiers, roles and timestamps. It never stores
clinical content, names or matched text, and it is never emitted unsigned.
It follows the QiXCite Filing Integrity Certificate pattern.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from base64 import b64decode
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .evidence_bundle import EvidenceBundle
from .signing import load_public_key, public_key_id, verify_bundle

RECEIPT_SCHEMA = "qixmind.session-evidence-receipt.v1"
RECEIPT_FRAMEWORK = "QIXMIND_SESSION_EVIDENCE_RECEIPT"
KEY_REGISTRY_SCHEMA = "qixmind.session-evidence-key-registry.v1"
RECEIPT_ID_PREFIX = "qixmind-ser-"

_SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{64}$")
_MAX_STRING_LEN = 400
# Keys that would indicate clinical content, identity or matched text. Any of
# these anywhere in the receipt is a defect, so creation and export reject them.
_CONTENT_KEYS = {
    "address",
    "content",
    "dob",
    "date_of_birth",
    "document_text",
    "email",
    "encounter_summary",
    "full_text",
    "instruction",
    "matched_text",
    "message",
    "name",
    "nhi",
    "notes",
    "note_text",
    "pattern",
    "patient_name",
    "phone",
    "prompt",
    "raw_text",
    "response",
    "response_text",
    "text",
    "transcript",
}
_GATE_RESULT_KEYS = {
    "order",
    "gate",
    "evaluated",
    "fired",
    "severity",
    "matched_category",
    "lexicon_version",
    "applies_to",
}
_OVERALL_ACTIONS = {"pass", "acknowledge", "escalate", "hold"}
_FOLLOW_UP_REQUIRED_ACTIONS = {"escalate", "hold"}
_DEID_KEYS = ("mode", "engine", "detections", "uncertain_hits", "changed")

# Environment names are QiXMind-specific so the generic IOA_EVIDENCE_* names used
# by other products can never be picked up by accident.
ENV_PRIVATE_KEY_B64 = "QIXMIND_EVIDENCE_PRIVATE_KEY_B64"
ENV_PRIVATE_KEY_PATH = "QIXMIND_EVIDENCE_PRIVATE_KEY_PATH"
ENV_PUBLIC_KEY_REGISTRY_PATH = "QIXMIND_EVIDENCE_PUBLIC_KEY_REGISTRY_PATH"
ENV_PUBLIC_KEY_REGISTRY_B64 = "QIXMIND_EVIDENCE_PUBLIC_KEY_REGISTRY_B64"
ENV_PUBLIC_KEY_PATH = "QIXMIND_EVIDENCE_PUBLIC_KEY_PATH"
ENV_PUBLIC_KEY_B64 = "QIXMIND_EVIDENCE_PUBLIC_KEY_B64"
ENV_PUBLIC_KEY_VALID_FROM = "QIXMIND_EVIDENCE_PUBLIC_KEY_VALID_FROM"
ENV_PUBLIC_KEY_VALID_TO = "QIXMIND_EVIDENCE_PUBLIC_KEY_VALID_TO"


class SessionReceiptError(ValueError):
    """Raised when a receipt cannot be created or verified safely."""


def normalize_sha256(value: Any, field_name: str) -> str:
    text = str(value or "").strip().lower()
    if not _SHA256_RE.fullmatch(text):
        raise SessionReceiptError(f"{field_name} must be a 64-character SHA-256 value")
    return f"sha256:{text.removeprefix('sha256:')}"


def _reject_content_fields(value: Any, path: str = "receipt") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in _CONTENT_KEYS:
                raise SessionReceiptError(
                    f"receipt cannot contain content at {path}.{key}"
                )
            _reject_content_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_content_fields(child, f"{path}[{index}]")
    elif isinstance(value, str) and len(value) > _MAX_STRING_LEN:
        raise SessionReceiptError(f"receipt string too long at {path}")


def _timestamp(value: Optional[str]) -> str:
    if value:
        return str(value).strip()
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _required_str(mapping: Mapping[str, Any], key: str, section: str) -> str:
    value = str(mapping.get(key, "") or "").strip()
    if not value:
        raise SessionReceiptError(f"{section}.{key} is required")
    return value


def _optional_str(mapping: Mapping[str, Any], key: str) -> Optional[str]:
    value = mapping.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise SessionReceiptError("expected an integer") from exc


def _normalize_session(session: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "evidence_bundle_id": _required_str(session, "evidence_bundle_id", "session"),
        "evidence_chain_id": _optional_str(session, "evidence_chain_id"),
        "workflow_key": _required_str(session, "workflow_key", "session"),
        "care_setting": _required_str(session, "care_setting", "session"),
        "profile_id": _required_str(session, "profile_id", "session"),
        "jurisdiction": _optional_str(session, "jurisdiction"),
        "runtime_service": str(session.get("runtime_service") or "qixhealth").strip(),
        "provider": _optional_str(session, "provider"),
        "model": _optional_str(session, "model"),
    }


def _normalize_model_input(model_input: Mapping[str, Any]) -> Dict[str, Any]:
    deid_raw = model_input.get("deidentification")
    deid: Dict[str, Any] = {}
    if isinstance(deid_raw, Mapping):
        for key in _DEID_KEYS:
            if key in deid_raw:
                deid[key] = deid_raw[key]
    if "mode" not in deid:
        raise SessionReceiptError("model_input.deidentification.mode is required")
    return {
        "sha256": normalize_sha256(model_input.get("sha256"), "model_input.sha256"),
        "length": _optional_int(model_input.get("length")),
        "scope": str(model_input.get("scope") or "user_turn_message_for_model").strip(),
        "deidentification": deid,
        "content_included": False,
    }


def _normalize_model_output(model_output: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "sha256": normalize_sha256(model_output.get("sha256"), "model_output.sha256"),
        "length": _optional_int(model_output.get("length")),
        "held": bool(model_output.get("held", False)),
        "content_included": False,
    }


def _normalize_gate_result(entry: Any, index: int) -> Dict[str, Any]:
    if not isinstance(entry, Mapping):
        raise SessionReceiptError(f"content_gates.results[{index}] must be an object")
    extra = set(str(key) for key in entry.keys()) - _GATE_RESULT_KEYS
    if extra:
        raise SessionReceiptError(
            f"content_gates.results[{index}] has unexpected keys: {', '.join(sorted(extra))}"
        )
    gate = _required_str(entry, "gate", f"content_gates.results[{index}]")
    severity = _required_str(entry, "severity", f"content_gates.results[{index}]")
    return {
        "order": int(entry.get("order", index)),
        "gate": gate,
        "evaluated": bool(entry.get("evaluated", True)),
        "fired": bool(entry.get("fired", False)),
        "severity": severity,
        "matched_category": _optional_str(entry, "matched_category"),
        "lexicon_version": _optional_str(entry, "lexicon_version"),
        "applies_to": str(entry.get("applies_to") or "output").strip(),
    }


def _normalize_content_gates(content_gates: Mapping[str, Any]) -> Dict[str, Any]:
    overall = _required_str(content_gates, "overall_action", "content_gates").lower()
    if overall not in _OVERALL_ACTIONS:
        raise SessionReceiptError("content_gates.overall_action is not recognised")
    status = _required_str(content_gates, "detector_status", "content_gates").lower()
    results_raw = content_gates.get("results")
    if not isinstance(results_raw, list):
        raise SessionReceiptError("content_gates.results must be a list")
    results = [
        _normalize_gate_result(entry, index) for index, entry in enumerate(results_raw)
    ]
    if status == "unavailable" and overall != "hold":
        raise SessionReceiptError("an unavailable detector must hold the output")
    lexicon_versions_raw = content_gates.get("lexicon_versions")
    lexicon_versions = (
        {str(k): str(v) for k, v in lexicon_versions_raw.items()}
        if isinstance(lexicon_versions_raw, Mapping)
        else {}
    )
    return {
        "detector": _required_str(content_gates, "detector", "content_gates"),
        "detector_version": _required_str(
            content_gates, "detector_version", "content_gates"
        ),
        "detector_status": status,
        "unavailable_reason": _optional_str(content_gates, "unavailable_reason"),
        "evaluated_at": _required_str(content_gates, "evaluated_at", "content_gates"),
        "overall_action": overall,
        "results": results,
        "lexicon_versions": lexicon_versions,
    }


def _normalize_acknowledgement(
    acknowledgement: Mapping[str, Any], gate_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    fired = [result for result in gate_results if result["fired"]]
    acknowledged_gates = acknowledgement.get("acknowledged_gates")
    acknowledged = (
        [str(item).strip() for item in acknowledged_gates if str(item).strip()]
        if isinstance(acknowledged_gates, list)
        else []
    )
    missing = [result["gate"] for result in fired if result["gate"] not in acknowledged]
    if missing:
        raise SessionReceiptError(
            "every fired gate must be acknowledged before a receipt is issued: "
            + ", ".join(missing)
        )
    return {
        "required": True,
        "review_event_id": _required_str(
            acknowledgement, "review_event_id", "acknowledgement"
        ),
        "role": _required_str(acknowledgement, "role", "acknowledgement"),
        "action": str(acknowledgement.get("action") or "signed_off").strip(),
        "acknowledged_at": _required_str(
            acknowledgement, "acknowledged_at", "acknowledgement"
        ),
        "checklist_items_count": _optional_int(
            acknowledgement.get("checklist_items_count")
        ),
        "acknowledged_gates": acknowledged,
        "name_included": False,
    }


def _normalize_follow_up(
    escalation_follow_up: Optional[Mapping[str, Any]], overall_action: str
) -> Dict[str, Any]:
    if escalation_follow_up is None or not escalation_follow_up.get("required", False):
        if overall_action in _FOLLOW_UP_REQUIRED_ACTIONS:
            raise SessionReceiptError(
                "escalation_follow_up is required when the overall action is "
                f"{overall_action}"
            )
        return {"required": False}
    block = dict(escalation_follow_up)
    block["required"] = True
    _required_str(block, "obligation_id", "escalation_follow_up")
    _required_str(block, "deadline_at", "escalation_follow_up")
    status = _required_str(block, "status", "escalation_follow_up")
    if status not in {"open", "closed", "overdue"}:
        raise SessionReceiptError("escalation_follow_up.status is not recognised")
    block.setdefault("alert", None)
    block.setdefault("alert_evaluation", "read_time_and_daily_sweep")
    return block


def _normalize_software(
    software: Mapping[str, Any], lexicon_versions: Dict[str, str]
) -> Dict[str, Any]:
    # "name" is a banned key everywhere in a receipt (it exists to catch person
    # names), so the product identity is recorded as "product".
    return {
        "product": "QiXMind",
        "ioa_core_version": _required_str(software, "ioa_core_version", "software"),
        "console_version": _optional_str(software, "console_version"),
        "runtime_version": _optional_str(software, "runtime_version"),
        "lexicon_versions": dict(lexicon_versions),
    }


def create_session_receipt(
    *,
    session: Mapping[str, Any],
    model_input: Mapping[str, Any],
    model_output: Mapping[str, Any],
    content_gates: Mapping[str, Any],
    acknowledgement: Mapping[str, Any],
    escalation_follow_up: Optional[Mapping[str, Any]],
    software: Mapping[str, Any],
    issued_at: Optional[str] = None,
    supersedes_receipt_id: Optional[str] = None,
    private_key_path: Optional[str] = None,
    private_key_pem: Optional[bytes] = None,
) -> Dict[str, Any]:
    """Create and sign a Session Evidence Receipt.

    Every section is validated and reduced to hashes, identifiers, roles and
    timestamps. Signing uses the operator key supplied by path or PEM bytes;
    no key is generated here and signing errors propagate, so an unsigned
    receipt can never be returned.
    """
    # Inputs are screened before normalisation so that a caller passing content
    # or identity fields fails loudly instead of having them silently dropped.
    for section_name, section in (
        ("session", session),
        ("model_input", model_input),
        ("model_output", model_output),
        ("content_gates", content_gates),
        ("acknowledgement", acknowledgement),
        ("escalation_follow_up", escalation_follow_up),
        ("software", software),
    ):
        if section is not None:
            _reject_content_fields(section, section_name)
    normalized_gates = _normalize_content_gates(content_gates)
    payload: Dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "issued_at": _timestamp(issued_at),
        "disclaimers": {
            "no_diagnosis": True,
            "no_efficacy_claim": True,
            "not_youth_facing": True,
            "content_included": False,
        },
        "session": _normalize_session(session),
        "model_input": _normalize_model_input(model_input),
        "model_output": _normalize_model_output(model_output),
        "content_gates": normalized_gates,
        "acknowledgement": _normalize_acknowledgement(
            acknowledgement, normalized_gates["results"]
        ),
        "escalation_follow_up": _normalize_follow_up(
            escalation_follow_up, normalized_gates["overall_action"]
        ),
        "software": _normalize_software(software, normalized_gates["lexicon_versions"]),
    }
    if payload["model_output"]["held"]:
        raise SessionReceiptError("a held output cannot be issued a receipt")
    if supersedes_receipt_id:
        payload["supersedes_receipt_id"] = str(supersedes_receipt_id).strip()
    _reject_content_fields(payload)

    bundle = EvidenceBundle(
        bundle_id=f"{RECEIPT_ID_PREFIX}{uuid.uuid4().hex[:16]}",
        version="1.0.0",
        framework=RECEIPT_FRAMEWORK,
        generated_at=payload["issued_at"],
        validations=list(normalized_gates["results"]),
        metadata=payload,
        evidence_chain_id=payload["session"]["evidence_chain_id"]
        or f"chain-{uuid.uuid4()}",
        related_bundle_ids=[payload["session"]["evidence_bundle_id"]],
    )
    # Signing is allowed to fail. An unsigned receipt would undermine the
    # verifiability claim and must never be emitted.
    bundle.generate_signature(
        private_key_path=private_key_path, private_key_pem=private_key_pem
    )
    receipt = bundle.to_dict()
    _reject_content_fields(receipt)
    return receipt


def receipt_json_bytes(receipt: Mapping[str, Any]) -> bytes:
    """Return deterministic UTF-8 JSON for export and hashing."""
    _reject_content_fields(receipt)
    return (
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")


def _is_receipt(receipt: Mapping[str, Any]) -> bool:
    metadata = receipt.get("metadata")
    return (
        receipt.get("framework") == RECEIPT_FRAMEWORK
        and isinstance(metadata, Mapping)
        and metadata.get("schema") == RECEIPT_SCHEMA
    )


def verify_session_receipt(
    receipt: Mapping[str, Any], public_key_path: str | Path
) -> bool:
    """Verify a receipt offline with the canonical IOA Core verifier."""
    if not _is_receipt(receipt):
        return False
    try:
        _reject_content_fields(receipt)
    except SessionReceiptError:
        return False
    return verify_bundle(receipt, load_public_key(public_key_path))


def _configured_registry_bytes() -> Optional[bytes]:
    path = os.getenv(ENV_PUBLIC_KEY_REGISTRY_PATH, "").strip()
    if path:
        return Path(path).read_bytes()
    encoded = os.getenv(ENV_PUBLIC_KEY_REGISTRY_B64, "").strip()
    if encoded:
        return b64decode(encoded, validate=True)
    return None


def _configured_public_key_pem() -> bytes:
    path = os.getenv(ENV_PUBLIC_KEY_PATH, "").strip()
    if path:
        return Path(path).read_bytes()
    encoded = os.getenv(ENV_PUBLIC_KEY_B64, "").strip()
    if encoded:
        return b64decode(encoded, validate=True)
    raise SessionReceiptError("public verification key is not configured")


def configured_private_key_pem() -> bytes:
    """Return the signing key PEM from the QiXMind-specific environment, or fail."""
    path = os.getenv(ENV_PRIVATE_KEY_PATH, "").strip()
    if path:
        return Path(path).read_bytes()
    encoded = os.getenv(ENV_PRIVATE_KEY_B64, "").strip()
    if encoded:
        return b64decode(encoded, validate=True)
    raise SessionReceiptError("receipt signing key is not configured")


def _load_public_key_pem(public_key_pem: bytes) -> Ed25519PublicKey:
    try:
        key = serialization.load_pem_public_key(public_key_pem)
    except (ValueError, TypeError) as exc:
        raise SessionReceiptError("public verification key is not valid PEM") from exc
    if not isinstance(key, Ed25519PublicKey):
        raise SessionReceiptError("public verification key must be Ed25519")
    return key


def public_key_id_from_pem(public_key_pem: bytes) -> str:
    return public_key_id(_load_public_key_pem(public_key_pem))


def _normalize_key_registry(registry: Mapping[str, Any]) -> Dict[str, Any]:
    if registry.get("schema") != KEY_REGISTRY_SCHEMA:
        raise SessionReceiptError("public key registry schema is unsupported")
    entries = registry.get("keys")
    current_id = str(registry.get("current_public_key_id", "")).strip()
    if not isinstance(entries, list) or not entries:
        raise SessionReceiptError("public key registry must contain keys")
    if not current_id:
        raise SessionReceiptError("public key registry must identify the current key")
    normalized: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise SessionReceiptError("public key registry entries must be objects")
        key_id = str(entry.get("public_key_id", "")).strip()
        pem_value = entry.get("public_key_pem", "")
        valid_from = str(entry.get("valid_from", "")).strip()
        valid_to = str(entry.get("valid_to", "")).strip() or None
        if not isinstance(pem_value, str) or not key_id or not valid_from:
            raise SessionReceiptError(
                "public key registry entries require id, PEM, and valid_from"
            )
        if key_id in seen:
            raise SessionReceiptError(f"duplicate public key id: {key_id}")
        if public_key_id_from_pem(pem_value.encode("ascii", "strict")) != key_id:
            raise SessionReceiptError(f"public key id does not match PEM: {key_id}")
        seen.add(key_id)
        normalized.append(
            {
                "public_key_id": key_id,
                "public_key_pem": pem_value,
                "valid_from": valid_from,
                "valid_to": valid_to,
            }
        )
    if current_id not in seen:
        raise SessionReceiptError("current public key id is absent from registry")
    return {
        "schema": KEY_REGISTRY_SCHEMA,
        "framework": RECEIPT_FRAMEWORK,
        "current_public_key_id": current_id,
        "keys": normalized,
    }


def configured_public_key_registry() -> Dict[str, Any]:
    """Load the public registry, or derive one from the configured current key."""
    registry_bytes = _configured_registry_bytes()
    if registry_bytes is not None:
        try:
            registry = json.loads(registry_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SessionReceiptError("public key registry is not valid JSON") from exc
        return _normalize_key_registry(registry)
    pem = _configured_public_key_pem()
    valid_from = os.getenv(ENV_PUBLIC_KEY_VALID_FROM, "").strip()
    valid_to = os.getenv(ENV_PUBLIC_KEY_VALID_TO, "").strip() or None
    if not valid_from:
        raise SessionReceiptError("public key registry is not configured")
    key_id = public_key_id_from_pem(pem)
    return _normalize_key_registry(
        {
            "schema": KEY_REGISTRY_SCHEMA,
            "current_public_key_id": key_id,
            "keys": [
                {
                    "public_key_id": key_id,
                    "public_key_pem": pem.decode("ascii"),
                    "valid_from": valid_from,
                    "valid_to": valid_to,
                }
            ],
        }
    )


def configured_public_key_pem() -> bytes:
    """Return the current public key without exposing any private material."""
    if _configured_registry_bytes() is None:
        return _configured_public_key_pem()
    registry = configured_public_key_registry()
    current_id = registry["current_public_key_id"]
    entry = next(
        item for item in registry["keys"] if item["public_key_id"] == current_id
    )
    return entry["public_key_pem"].encode("ascii")


def public_key_registry_json_bytes(registry: Mapping[str, Any]) -> bytes:
    normalized = _normalize_key_registry(registry)
    return (json.dumps(normalized, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_session_receipt_from_registry(
    receipt: Mapping[str, Any], registry: Mapping[str, Any]
) -> bool:
    """Verify a receipt with the key selected by its signed key id.

    Expired entries remain usable for historical receipts. Rotation adds a new
    current entry and never removes older public keys.
    """
    if not _is_receipt(receipt):
        return False
    normalized = _normalize_key_registry(registry)
    signature = receipt.get("signature")
    key_id = (
        str(signature.get("public_key_id", "")).strip()
        if isinstance(signature, Mapping)
        else ""
    )
    entry = next(
        (item for item in normalized["keys"] if item["public_key_id"] == key_id), None
    )
    if entry is None:
        return False
    return verify_bundle(
        receipt, _load_public_key_pem(entry["public_key_pem"].encode("ascii"))
    )


__all__ = [
    "ENV_PRIVATE_KEY_B64",
    "ENV_PRIVATE_KEY_PATH",
    "ENV_PUBLIC_KEY_B64",
    "ENV_PUBLIC_KEY_PATH",
    "ENV_PUBLIC_KEY_REGISTRY_B64",
    "ENV_PUBLIC_KEY_REGISTRY_PATH",
    "ENV_PUBLIC_KEY_VALID_FROM",
    "ENV_PUBLIC_KEY_VALID_TO",
    "KEY_REGISTRY_SCHEMA",
    "RECEIPT_FRAMEWORK",
    "RECEIPT_ID_PREFIX",
    "RECEIPT_SCHEMA",
    "SessionReceiptError",
    "configured_private_key_pem",
    "configured_public_key_pem",
    "configured_public_key_registry",
    "create_session_receipt",
    "normalize_sha256",
    "public_key_id_from_pem",
    "public_key_registry_json_bytes",
    "receipt_json_bytes",
    "verify_session_receipt",
    "verify_session_receipt_from_registry",
]
