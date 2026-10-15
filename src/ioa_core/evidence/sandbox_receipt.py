# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""QiXMind Sandbox Evaluation Receipts (synthetic partner sandbox).

A sandbox evaluation receipt records one evaluation a partner ran in the
QiXMind partner sandbox, on server-held synthetic fixtures only. It must never
be mistaken for a production Session Evidence Receipt, so it is separate at
every level:

* its own framework (``QIXMIND_SANDBOX_EVALUATION_RECEIPT``), schema and id
  prefix (``qixmind-sbx-``), which ``verify_session_receipt`` rejects;
* signed environment fields: ``environment: sandbox_evaluation`` and
  ``not_for_clinical_use: true``, required by the sandbox verifier;
* its own signing key and key registry schema, so a production registry can
  never select a sandbox key and the sandbox verifier can refuse production
  keys;
* every field labelled: ``computed_by: qixmind`` for what QiXMind computed
  itself (fingerprints, live gate results, review-output status, evaluation
  findings, draft-policy required actions, provenance) and
  ``asserted_by: partner`` for what the partner states (model, provider,
  clinician role, its own timestamps, acknowledgements and dispositions).
  A partner-asserted field cannot be placed among computed fields, and the
  labels are inside the signature.

Like session receipts it carries hashes, identifiers, codes, roles and
timestamps only, never text, and it is never emitted unsigned.
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
from typing import Any, Dict, Iterable, List, Optional

from .evidence_bundle import EvidenceBundle
from .session_receipt import (
    SessionReceiptError,
    _load_public_key_pem,
    _normalize_content_gates,
    _reject_content_fields,
    normalize_sha256,
    public_key_id_from_pem,
)
from .signing import load_public_key, public_key_id, verify_bundle

SANDBOX_RECEIPT_SCHEMA = "qixmind.sandbox-evaluation-receipt.v1"
SANDBOX_RECEIPT_FRAMEWORK = "QIXMIND_SANDBOX_EVALUATION_RECEIPT"
SANDBOX_KEY_REGISTRY_SCHEMA = "qixmind.sandbox-evaluation-key-registry.v1"
SANDBOX_RECEIPT_ID_PREFIX = "qixmind-sbx-"
SANDBOX_ENVIRONMENT = "sandbox_evaluation"
SANDBOX_NOTICE = "Sandbox evaluation receipt: synthetic data, not a clinical record"

COMPUTED_BY = "qixmind"
ASSERTED_BY = "partner"
# Every partner assertion is labelled unverified, in the signed receipt and in
# every verifier result: QiXMind records what the partner stated and checks
# its shape only.
ASSERTION_VERIFICATION = "unverified"
PARTNER_ASSERTIONS_NOTICE = (
    "Partner assertions (model, provider, clinician role, partner timestamps, "
    "acknowledged gates and dispositions) are recorded as the partner stated them. "
    "QiXMind has not verified them."
)
# Registry key status. A revoked key never verifies; a retired key (no longer
# current, not revoked) still verifies receipts issued inside its validity.
REVOCATION_REASONS = ("key_compromise", "administrative")

# What QiXMind computes itself. Nothing in this list may come from a partner.
COMPUTED_FIELDS = (
    "fixtures",
    "model_input",
    "model_output",
    "content_gates",
    "review_output",
    "findings",
    "required_actions",
    "provenance",
    "sign_off_checks",
)
# What a partner states. These are labelled as assertions and never as
# computed, whatever the caller passes.
PARTNER_ASSERTED_FIELDS = (
    "model",
    "provider",
    "clinician_role",
    "partner_timestamps",
    "acknowledged_gates",
    "dispositions",
)
REQUIRED_COMPUTED_FIELDS = ("fixtures", "model_input", "model_output", "content_gates")
REQUIRED_ASSERTED_FIELDS = ("clinician_role", "acknowledged_gates")

PARTNER_TIMESTAMP_KEYS = ("generated_at", "reviewed_at", "signed_off_at")
DISPOSITION_CODES = (
    "escalated",
    "referred",
    "already_managed_under_plan",
    "not_applicable_with_reason",
)
DISPOSITION_REASON_CODES = (
    "negated_in_source",
    "historical_not_current",
    "third_party_not_the_person",
    "wording_not_about_this_concern",
    "duplicate_of_another_finding",
)

# Environment names are sandbox-specific and never shared with production
# receipts (QIXMIND_EVIDENCE_*), so a production key cannot be picked up here.
ENV_SANDBOX_PRIVATE_KEY_B64 = "QIXMIND_SANDBOX_PRIVATE_KEY_B64"
ENV_SANDBOX_PRIVATE_KEY_PATH = "QIXMIND_SANDBOX_PRIVATE_KEY_PATH"
ENV_SANDBOX_KEY_REGISTRY_PATH = "QIXMIND_SANDBOX_PUBLIC_KEY_REGISTRY_PATH"
ENV_SANDBOX_KEY_REGISTRY_B64 = "QIXMIND_SANDBOX_PUBLIC_KEY_REGISTRY_B64"
_PRODUCTION_PRIVATE_KEY_ENVS = (
    "QIXMIND_EVIDENCE_PRIVATE_KEY_B64",
    "QIXMIND_EVIDENCE_PRIVATE_KEY_PATH",
)

# Identifier shapes. None of them admits spaces, so prose cannot pass.
_IDENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+@-]{0,79}$")
_OPAQUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_ROLE_RE = re.compile(r"^[a-z][a-z_]{0,39}$")
_GATE_RE = re.compile(r"^[a-z][a-z0-9_]{0,79}$")
_OCCURRENCE_RE = re.compile(
    r"^[a-z][a-z0-9_]{0,79}\|(input|output)\|[a-z_]{1,40}\|[A-Za-z0-9_.@:-]{1,120}$"
)
_MAX_LIST = 64


class SandboxReceiptError(SessionReceiptError):
    """Raised when a sandbox receipt cannot be created or verified safely."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _timestamp(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SandboxReceiptError(f"{field} is required")
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SandboxReceiptError(f"{field} must be an ISO 8601 timestamp") from exc
    return text


def _match(value: Any, pattern: re.Pattern[str], field: str) -> str:
    text = str(value or "").strip()
    if not pattern.fullmatch(text):
        raise SandboxReceiptError(f"{field} must be an identifier, never free text")
    return text


def _computed_block(name: str, value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SandboxReceiptError(f"computed.{name} must be an object")
    if "asserted_by" in value:
        raise SandboxReceiptError(
            f"computed.{name} cannot carry a partner assertion label"
        )
    label = value.get("computed_by", COMPUTED_BY)
    if label != COMPUTED_BY:
        raise SandboxReceiptError(f"computed.{name} must be computed by QiXMind")
    block = {str(k): v for k, v in value.items() if k != "computed_by"}
    return {"computed_by": COMPUTED_BY, **block}


def _normalize_fixtures(value: Mapping[str, Any]) -> Dict[str, Any]:
    if value.get("label") != "SYNTHETIC":
        raise SandboxReceiptError("computed.fixtures.label must be SYNTHETIC")
    return {
        "computed_by": COMPUTED_BY,
        "label": "SYNTHETIC",
        "fixture_set_version": _match(
            value.get("fixture_set_version"), _OPAQUE_RE, "fixtures.fixture_set_version"
        ),
        "input_fixture_id": _match(
            value.get("input_fixture_id"), _OPAQUE_RE, "fixtures.input_fixture_id"
        ),
        "output_fixture_id": _match(
            value.get("output_fixture_id"), _OPAQUE_RE, "fixtures.output_fixture_id"
        ),
        "profile_id": _match(
            value.get("profile_id"), _OPAQUE_RE, "fixtures.profile_id"
        ),
        "jurisdiction": _match(
            value.get("jurisdiction"), _OPAQUE_RE, "fixtures.jurisdiction"
        ),
    }


def _normalize_hash_block(value: Mapping[str, Any], name: str) -> Dict[str, Any]:
    length = value.get("length")
    if length is not None and (not isinstance(length, int) or length < 0):
        raise SandboxReceiptError(
            f"computed.{name}.length must be a non-negative integer"
        )
    block: Dict[str, Any] = {
        "computed_by": COMPUTED_BY,
        "sha256": normalize_sha256(value.get("sha256"), f"computed.{name}.sha256"),
        "length": length,
        "content_included": False,
    }
    if name == "model_output":
        block["held"] = bool(value.get("held", False))
    return block


def _normalize_computed(computed: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(computed, Mapping):
        raise SandboxReceiptError("computed must be an object")
    for key in computed:
        if key in PARTNER_ASSERTED_FIELDS:
            raise SandboxReceiptError(
                f"{key} is asserted by the partner and cannot be marked as computed"
            )
        if key not in COMPUTED_FIELDS:
            raise SandboxReceiptError(f"computed.{key} is not a recognised field")
    for key in REQUIRED_COMPUTED_FIELDS:
        if key not in computed:
            raise SandboxReceiptError(f"computed.{key} is required")
    out: Dict[str, Any] = {}
    for key in COMPUTED_FIELDS:
        if key not in computed or computed[key] is None:
            continue
        block = _computed_block(key, computed[key])
        if key == "fixtures":
            block = _normalize_fixtures(block)
        elif key in ("model_input", "model_output"):
            block = _normalize_hash_block(block, key)
        elif key == "content_gates":
            block = {"computed_by": COMPUTED_BY, **_normalize_content_gates(block)}
        elif key == "findings":
            if block.get("status") != "evaluation_only":
                raise SandboxReceiptError(
                    "computed.findings must be labelled evaluation_only"
                )
        elif key == "required_actions":
            policy = block.get("policy")
            status = policy.get("status") if isinstance(policy, Mapping) else None
            if status not in ("draft", "approved", "retired"):
                raise SandboxReceiptError(
                    "computed.required_actions must name its policy status"
                )
            if not isinstance(block.get("actions"), list):
                raise SandboxReceiptError(
                    "computed.required_actions.actions must be a list"
                )
            block["label"] = status
        out[key] = block
    return out


def _assertion(value: Any) -> Dict[str, Any]:
    return {
        "asserted_by": ASSERTED_BY,
        "verification": ASSERTION_VERIFICATION,
        "value": value,
    }


def _unwrap_assertion(name: str, value: Any) -> Any:
    if isinstance(value, Mapping) and ("value" in value or "computed_by" in value):
        if "computed_by" in value:
            raise SandboxReceiptError(
                f"{name} is asserted by the partner and cannot be marked as computed"
            )
        label = value.get("asserted_by", ASSERTED_BY)
        if label != ASSERTED_BY:
            raise SandboxReceiptError(
                f"assertions.{name} must be asserted by the partner"
            )
        verification = value.get("verification", ASSERTION_VERIFICATION)
        if verification != ASSERTION_VERIFICATION:
            raise SandboxReceiptError(
                f"assertions.{name} is a partner assertion and is always unverified"
            )
        extra = set(value) - {"value", "asserted_by", "verification"}
        if extra:
            raise SandboxReceiptError(
                f"assertions.{name} has unexpected keys: {', '.join(sorted(extra))}"
            )
        return value.get("value")
    return value


def _normalize_dispositions(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list) or len(value) > _MAX_LIST:
        raise SandboxReceiptError("assertions.dispositions must be a short list")
    items: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise SandboxReceiptError(f"dispositions[{index}] must be an object")
        extra = set(item) - {"occurrence_key", "disposition", "reason_code"}
        if extra:
            raise SandboxReceiptError(
                f"dispositions[{index}] has unexpected keys: {', '.join(sorted(extra))}"
            )
        key = _match(
            item.get("occurrence_key"),
            _OCCURRENCE_RE,
            f"dispositions[{index}].occurrence_key",
        )
        if key in seen:
            raise SandboxReceiptError(f"dispositions[{index}] repeats an occurrence")
        seen.add(key)
        code = str(item.get("disposition") or "")
        if code not in DISPOSITION_CODES:
            raise SandboxReceiptError(
                f"dispositions[{index}].disposition is not recognised"
            )
        reason = item.get("reason_code")
        if code == "not_applicable_with_reason":
            if reason not in DISPOSITION_REASON_CODES:
                raise SandboxReceiptError(
                    f"dispositions[{index}] needs a reason code for not applicable"
                )
        elif reason is not None:
            raise SandboxReceiptError(
                f"dispositions[{index}] has a reason code without not applicable"
            )
        items.append(
            {"occurrence_key": key, "disposition": code, "reason_code": reason}
        )
    return items


def _normalize_assertions(assertions: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(assertions, Mapping):
        raise SandboxReceiptError("assertions must be an object")
    for key in assertions:
        if key in COMPUTED_FIELDS:
            raise SandboxReceiptError(
                f"{key} is computed by QiXMind and cannot be asserted by the partner"
            )
        if key not in PARTNER_ASSERTED_FIELDS:
            raise SandboxReceiptError(f"assertions.{key} is not a recognised field")
    for key in REQUIRED_ASSERTED_FIELDS:
        if assertions.get(key) is None:
            raise SandboxReceiptError(f"assertions.{key} is required")
    out: Dict[str, Any] = {}
    for key in PARTNER_ASSERTED_FIELDS:
        if key not in assertions or assertions[key] is None:
            continue
        raw = _unwrap_assertion(key, assertions[key])
        if raw is None:
            continue
        if key in ("model", "provider"):
            value: Any = _match(raw, _IDENT_RE, f"assertions.{key}")
        elif key == "clinician_role":
            value = _match(raw, _ROLE_RE, "assertions.clinician_role")
        elif key == "partner_timestamps":
            if not isinstance(raw, Mapping):
                raise SandboxReceiptError(
                    "assertions.partner_timestamps must be an object"
                )
            extra = set(raw) - set(PARTNER_TIMESTAMP_KEYS)
            if extra:
                raise SandboxReceiptError(
                    "assertions.partner_timestamps has unexpected keys: "
                    + ", ".join(sorted(extra))
                )
            value = {
                k: _timestamp(raw[k], f"assertions.partner_timestamps.{k}")
                for k in PARTNER_TIMESTAMP_KEYS
                if raw.get(k) is not None
            }
        elif key == "acknowledged_gates":
            if not isinstance(raw, list) or len(raw) > _MAX_LIST:
                raise SandboxReceiptError(
                    "assertions.acknowledged_gates must be a short list"
                )
            value = sorted(
                {_match(g, _GATE_RE, "assertions.acknowledged_gates") for g in raw}
            )
        else:  # dispositions
            value = _normalize_dispositions(raw)
        out[key] = _assertion(value)
    return out


def _required_action_keys(computed: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    block = computed.get("required_actions")
    if not isinstance(block, Mapping):
        return {}
    actions = block.get("actions") or []
    if not isinstance(actions, list):
        raise SandboxReceiptError("computed.required_actions.actions must be a list")
    keyed: Dict[str, Dict[str, Any]] = {}
    for item in actions:
        if isinstance(item, Mapping) and item.get("occurrence_key"):
            keyed[str(item["occurrence_key"])] = dict(item)
    return keyed


def _check_sign_off(
    computed: Dict[str, Any], assertions: Dict[str, Any]
) -> Dict[str, Any]:
    """The checks QiXMind runs on the partner's sign-off, recorded as computed."""
    gates = computed["content_gates"]
    fired = sorted({r["gate"] for r in gates["results"] if r["fired"]})
    acknowledged = assertions["acknowledged_gates"]["value"]
    missing = [gate for gate in fired if gate not in acknowledged]
    if missing:
        raise SandboxReceiptError(
            "every fired gate must be acknowledged before a receipt is issued: "
            + ", ".join(missing)
        )
    if computed["model_output"]["held"] or gates["overall_action"] == "hold":
        raise SandboxReceiptError("a held output cannot be issued a receipt")
    actions = _required_action_keys(computed)
    given = {
        item["occurrence_key"]: item
        for item in (assertions.get("dispositions") or {}).get("value", [])
    }
    unknown = sorted(set(given) - set(actions))
    if unknown:
        raise SandboxReceiptError(
            "a disposition names a finding outside this evaluation"
        )
    absent = sorted(set(actions) - set(given))
    if absent:
        raise SandboxReceiptError("every required action needs a disposition")
    for key, action in actions.items():
        if given[key]["disposition"] == "not_applicable_with_reason" and not action.get(
            "dismissal_allowed"
        ):
            raise SandboxReceiptError(
                "a required escalation cannot be closed as not applicable"
            )
    return {
        "computed_by": COMPUTED_BY,
        "fired_gates": fired,
        "all_fired_gates_acknowledged": True,
        "required_actions_count": len(actions),
        "all_required_actions_dispositioned": True,
        "output_held": False,
    }


def _labels(
    computed: Mapping[str, Any], assertions: Mapping[str, Any]
) -> Dict[str, Any]:
    return {
        "computed_by_qixmind": sorted(computed),
        "asserted_by_partner": sorted(assertions),
    }


def create_sandbox_receipt(
    *,
    sandbox: Mapping[str, Any],
    computed: Mapping[str, Any],
    assertions: Mapping[str, Any],
    software: Mapping[str, Any],
    issued_at: Optional[str] = None,
    private_key_path: Optional[str] = None,
    private_key_pem: Optional[bytes] = None,
    production_registry: Optional[Mapping[str, Any]] = None,
    sandbox_registry: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Create and sign a Sandbox Evaluation Receipt.

    ``computed`` holds what QiXMind computed; ``assertions`` holds what the
    partner states. A partner field placed in ``computed`` (or a computed field
    in ``assertions``) is refused. When ``production_registry`` is given, a
    signing key listed there is refused, so a production key never signs a
    sandbox receipt. When ``sandbox_registry`` is given, only its current,
    unrevoked key may sign.
    """
    for section_name, section in (
        ("sandbox", sandbox),
        ("computed", computed),
        ("assertions", assertions),
        ("software", software),
    ):
        _reject_content_fields(section, section_name)
    normalized_computed = _normalize_computed(computed)
    normalized_assertions = _normalize_assertions(assertions)
    normalized_computed["sign_off_checks"] = _check_sign_off(
        normalized_computed, normalized_assertions
    )
    payload: Dict[str, Any] = {
        "schema": SANDBOX_RECEIPT_SCHEMA,
        "notice": SANDBOX_NOTICE,
        "environment": SANDBOX_ENVIRONMENT,
        "not_for_clinical_use": True,
        "synthetic_data_only": True,
        "partner_assertions_notice": PARTNER_ASSERTIONS_NOTICE,
        "issued_at": str(issued_at or _now()),
        "disclaimers": {
            "no_diagnosis": True,
            "no_efficacy_claim": True,
            "not_a_clinical_record": True,
            "no_follow_up_obligation_created": True,
            "content_included": False,
        },
        "sandbox": {
            "computed_by": COMPUTED_BY,
            "tenant_id": _match(
                sandbox.get("tenant_id"), _OPAQUE_RE, "sandbox.tenant_id"
            ),
            "evaluation_id": _match(
                sandbox.get("evaluation_id"), _OPAQUE_RE, "sandbox.evaluation_id"
            ),
        },
        "computed": normalized_computed,
        "assertions": normalized_assertions,
        "labels": _labels(normalized_computed, normalized_assertions),
        "software": {
            "computed_by": COMPUTED_BY,
            "product": "QiXMind partner sandbox",
            "ioa_core_version": str(software.get("ioa_core_version") or "unknown"),
            "console_version": str(software.get("console_version") or "unknown"),
        },
    }
    _reject_content_fields(payload)

    if production_registry is not None or sandbox_registry is not None:
        signing_pem = private_key_pem
        if signing_pem is None and private_key_path:
            signing_pem = Path(private_key_path).read_bytes()
        if signing_pem is not None:
            from cryptography.hazmat.primitives import serialization

            key = serialization.load_pem_private_key(signing_pem, password=None)
            signing_id = public_key_id(key.public_key())  # type: ignore[arg-type]
            if production_registry is not None and signing_id in _registry_key_ids(
                production_registry
            ):
                raise SandboxReceiptError(
                    "the sandbox signing key is a production key; refusing to sign"
                )
            if sandbox_registry is not None:
                registry_view = normalize_sandbox_key_registry(sandbox_registry)
                if signing_id != registry_view["current_public_key_id"]:
                    raise SandboxReceiptError(
                        "the signing key is not the sandbox registry's current key"
                    )

    bundle = EvidenceBundle(
        bundle_id=f"{SANDBOX_RECEIPT_ID_PREFIX}{uuid.uuid4().hex[:16]}",
        version="1.0.0",
        framework=SANDBOX_RECEIPT_FRAMEWORK,
        generated_at=payload["issued_at"],
        validations=[dict(r) for r in normalized_computed["content_gates"]["results"]],
        metadata=payload,
        evidence_chain_id=f"sbx-chain-{uuid.uuid4()}",
        related_bundle_ids=[payload["sandbox"]["evaluation_id"]],
    )
    bundle.generate_signature(
        private_key_path=private_key_path, private_key_pem=private_key_pem
    )
    receipt = bundle.to_dict()
    _reject_content_fields(receipt)
    return receipt


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------


def _structure_problem(receipt: Mapping[str, Any]) -> Optional[str]:
    """None when the receipt is a well-formed sandbox receipt, else a reason code."""
    if receipt.get("framework") != SANDBOX_RECEIPT_FRAMEWORK:
        return "not_a_sandbox_receipt"
    metadata = receipt.get("metadata")
    if (
        not isinstance(metadata, Mapping)
        or metadata.get("schema") != SANDBOX_RECEIPT_SCHEMA
    ):
        return "not_a_sandbox_receipt"
    if not str(receipt.get("bundle_id") or "").startswith(SANDBOX_RECEIPT_ID_PREFIX):
        return "not_a_sandbox_receipt"
    if metadata.get("environment") != SANDBOX_ENVIRONMENT:
        return "environment_missing"
    if metadata.get("not_for_clinical_use") is not True:
        return "environment_missing"
    computed = metadata.get("computed")
    assertions = metadata.get("assertions")
    if not isinstance(computed, Mapping) or not isinstance(assertions, Mapping):
        return "labels_invalid"
    for key, block in computed.items():
        if key not in COMPUTED_FIELDS or key in PARTNER_ASSERTED_FIELDS:
            return "labels_invalid"
        if not isinstance(block, Mapping) or block.get("computed_by") != COMPUTED_BY:
            return "labels_invalid"
        if "asserted_by" in block:
            return "labels_invalid"
    for key, block in assertions.items():
        if key not in PARTNER_ASSERTED_FIELDS:
            return "labels_invalid"
        if not isinstance(block, Mapping) or block.get("asserted_by") != ASSERTED_BY:
            return "labels_invalid"
        if "computed_by" in block:
            return "labels_invalid"
        # Receipts from 2.17.0 carry no per-field label; any label present
        # must say unverified.
        if block.get("verification", ASSERTION_VERIFICATION) != ASSERTION_VERIFICATION:
            return "labels_invalid"
    if (
        metadata.get("partner_assertions_notice", PARTNER_ASSERTIONS_NOTICE)
        != PARTNER_ASSERTIONS_NOTICE
    ):
        return "labels_invalid"
    for key in REQUIRED_COMPUTED_FIELDS:
        if key not in computed:
            return "labels_invalid"
    if metadata.get("labels") != _labels(computed, assertions):
        return "labels_invalid"
    try:
        _reject_content_fields(receipt)
    except SessionReceiptError:
        return "content_not_allowed"
    return None


def _registry_key_ids(registry: Mapping[str, Any]) -> set[str]:
    entries = registry.get("keys") if isinstance(registry, Mapping) else None
    ids: set[str] = set()
    for entry in entries or []:
        if isinstance(entry, Mapping) and entry.get("public_key_id"):
            ids.add(str(entry["public_key_id"]).strip())
    return ids


def check_sandbox_receipt(
    receipt: Mapping[str, Any],
    registry: Mapping[str, Any],
    *,
    production_registry: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Verify a sandbox receipt against the sandbox registry, with a reason.

    The result always starts with the sandbox notice. ``valid`` is true only
    for a well-formed sandbox receipt whose signature verifies with a key in
    the sandbox registry that is not also a production key.
    """
    result: Dict[str, Any] = {
        "notice": SANDBOX_NOTICE,
        "valid": False,
        "reason": None,
        "receipt_id": None,
        "framework": None,
        "environment": None,
        "public_key_id": None,
        "key_status": None,
        "signature_valid": None,
        "revoked_at": None,
        "revocation_reason": None,
        "partner_assertions": {
            "verification": ASSERTION_VERIFICATION,
            "notice": PARTNER_ASSERTIONS_NOTICE,
            "fields": [],
        },
    }
    if not isinstance(receipt, Mapping):
        result["reason"] = "not_a_sandbox_receipt"
        return result
    result["receipt_id"] = receipt.get("bundle_id")
    result["framework"] = receipt.get("framework")
    metadata = receipt.get("metadata")
    if isinstance(metadata, Mapping):
        result["environment"] = metadata.get("environment")
        asserted = metadata.get("assertions")
        if isinstance(asserted, Mapping):
            result["partner_assertions"]["fields"] = sorted(
                str(k) for k in asserted if k in PARTNER_ASSERTED_FIELDS
            )
    signature = receipt.get("signature")
    key_id = (
        str(signature.get("public_key_id", "")).strip()
        if isinstance(signature, Mapping)
        else ""
    )
    result["public_key_id"] = key_id or None
    problem = _structure_problem(receipt)
    if problem:
        result["reason"] = problem
        return result
    normalized = normalize_sandbox_key_registry(registry)
    if production_registry is not None and key_id in _registry_key_ids(
        production_registry
    ):
        result["reason"] = "production_key_not_accepted"
        return result
    entry = next(
        (item for item in normalized["keys"] if item["public_key_id"] == key_id), None
    )
    if entry is None:
        result["reason"] = "key_not_in_sandbox_registry"
        return result
    ok = bool(
        verify_bundle(
            receipt, _load_public_key_pem(entry["public_key_pem"].encode("ascii"))
        )
    )
    result["signature_valid"] = ok
    if entry.get("revoked_at"):
        # A revoked key is never trusted again, whatever date a receipt claims:
        # whoever held the key could have written any issued_at.
        result["key_status"] = "revoked"
        result["revoked_at"] = entry["revoked_at"]
        result["revocation_reason"] = entry.get("revocation_reason")
        result["reason"] = "key_revoked"
        return result
    result["key_status"] = (
        "current" if key_id == normalized["current_public_key_id"] else "retired"
    )
    if not ok:
        result["reason"] = "signature_invalid"
        return result
    issued_day = str(metadata.get("issued_at") or "")[:10]
    if issued_day < entry["valid_from"][:10] or (
        entry.get("valid_to") and issued_day > str(entry["valid_to"])[:10]
    ):
        result["reason"] = "issued_outside_key_validity"
        return result
    result["valid"] = True
    return result


def verify_sandbox_receipt(
    receipt: Mapping[str, Any], public_key_path: str | Path
) -> bool:
    """Verify a sandbox receipt offline with one sandbox public key.

    A single key carries no revocation status; use
    ``verify_sandbox_receipt_from_registry`` or ``check_sandbox_receipt`` with
    the published sandbox registry to see a revoked key.
    """
    if not isinstance(receipt, Mapping) or _structure_problem(receipt):
        return False
    return verify_bundle(receipt, load_public_key(public_key_path))


def verify_sandbox_receipt_from_registry(
    receipt: Mapping[str, Any],
    registry: Mapping[str, Any],
    *,
    production_registry: Optional[Mapping[str, Any]] = None,
) -> bool:
    """Verify with the sandbox registry key selected by the signed key id."""
    return bool(
        check_sandbox_receipt(
            receipt, registry, production_registry=production_registry
        )["valid"]
    )


# --------------------------------------------------------------------------
# Sandbox key registry and signing key
# --------------------------------------------------------------------------


def normalize_sandbox_key_registry(registry: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a sandbox registry; a production registry is refused."""
    if (
        not isinstance(registry, Mapping)
        or registry.get("schema") != SANDBOX_KEY_REGISTRY_SCHEMA
    ):
        raise SandboxReceiptError("sandbox key registry schema is unsupported")
    entries = registry.get("keys")
    current_id = str(registry.get("current_public_key_id", "")).strip()
    if not isinstance(entries, list) or not entries:
        raise SandboxReceiptError("sandbox key registry must contain keys")
    normalized: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise SandboxReceiptError("sandbox key registry entries must be objects")
        key_id = str(entry.get("public_key_id", "")).strip()
        pem_value = entry.get("public_key_pem", "")
        valid_from = str(entry.get("valid_from") or "").strip()
        valid_to = str(entry.get("valid_to") or "").strip() or None
        if not isinstance(pem_value, str) or not key_id or not valid_from:
            raise SandboxReceiptError(
                "sandbox key registry entries require id, PEM, and valid_from"
            )
        if key_id in seen:
            raise SandboxReceiptError(f"duplicate public key id: {key_id}")
        if public_key_id_from_pem(pem_value.encode("ascii", "strict")) != key_id:
            raise SandboxReceiptError(f"public key id does not match PEM: {key_id}")
        _timestamp(valid_from, f"{key_id}.valid_from")
        if valid_to:
            _timestamp(valid_to, f"{key_id}.valid_to")
        revoked_at = str(entry.get("revoked_at") or "").strip() or None
        reason = entry.get("revocation_reason")
        if revoked_at:
            _timestamp(revoked_at, f"{key_id}.revoked_at")
            if reason not in REVOCATION_REASONS:
                raise SandboxReceiptError(
                    "a revoked key needs a revocation_reason: "
                    + ", ".join(REVOCATION_REASONS)
                )
            if key_id == current_id:
                raise SandboxReceiptError("the current key cannot be revoked")
        elif reason is not None:
            raise SandboxReceiptError("revocation_reason needs revoked_at")
        seen.add(key_id)
        normalized.append(
            {
                "public_key_id": key_id,
                "public_key_pem": pem_value,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "revoked_at": revoked_at,
                "revocation_reason": reason if revoked_at else None,
                "status": (
                    "revoked"
                    if revoked_at
                    else ("current" if key_id == current_id else "retired")
                ),
            }
        )
    if current_id not in seen:
        raise SandboxReceiptError("current public key id is absent from registry")
    return {
        "schema": SANDBOX_KEY_REGISTRY_SCHEMA,
        "framework": SANDBOX_RECEIPT_FRAMEWORK,
        "environment": SANDBOX_ENVIRONMENT,
        "notice": SANDBOX_NOTICE,
        "current_public_key_id": current_id,
        "keys": normalized,
    }


def assert_registries_disjoint(
    sandbox_registry: Mapping[str, Any], production_registry: Mapping[str, Any]
) -> None:
    """Raise if any key id appears in both the sandbox and production registries."""
    shared = _registry_key_ids(sandbox_registry) & _registry_key_ids(
        production_registry
    )
    if shared:
        raise SandboxReceiptError(
            "sandbox and production key registries share keys: "
            + ", ".join(sorted(shared))
        )


def sandbox_key_registry_json_bytes(registry: Mapping[str, Any]) -> bytes:
    normalized = normalize_sandbox_key_registry(registry)
    return (json.dumps(normalized, indent=2, sort_keys=True) + "\n").encode("utf-8")


def configured_sandbox_key_registry() -> Dict[str, Any]:
    """Load the sandbox registry from its own environment variables."""
    path = os.getenv(ENV_SANDBOX_KEY_REGISTRY_PATH, "").strip()
    if path:
        raw = Path(path).read_bytes()
    else:
        encoded = os.getenv(ENV_SANDBOX_KEY_REGISTRY_B64, "").strip()
        if not encoded:
            raise SandboxReceiptError("sandbox key registry is not configured")
        raw = b64decode(encoded, validate=True)
    try:
        registry = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SandboxReceiptError("sandbox key registry is not valid JSON") from exc
    return normalize_sandbox_key_registry(registry)


def _env_bytes(names: Iterable[str]) -> Optional[bytes]:
    for name in names:
        value = os.getenv(name, "").strip()
        if not value:
            continue
        if name.endswith("_PATH"):
            return Path(value).read_bytes()
        return b64decode(value, validate=True)
    return None


def configured_sandbox_private_key_pem() -> bytes:
    """The sandbox signing key; refused if it is the production signing key."""
    pem = _env_bytes((ENV_SANDBOX_PRIVATE_KEY_PATH, ENV_SANDBOX_PRIVATE_KEY_B64))
    if pem is None:
        raise SandboxReceiptError("sandbox signing key is not configured")
    production = _env_bytes(_PRODUCTION_PRIVATE_KEY_ENVS)
    if production is not None and production.strip() == pem.strip():
        raise SandboxReceiptError("the sandbox signing key is the production key")
    return pem


__all__ = [
    "ASSERTED_BY",
    "ASSERTION_VERIFICATION",
    "COMPUTED_BY",
    "COMPUTED_FIELDS",
    "DISPOSITION_CODES",
    "DISPOSITION_REASON_CODES",
    "ENV_SANDBOX_KEY_REGISTRY_B64",
    "ENV_SANDBOX_KEY_REGISTRY_PATH",
    "ENV_SANDBOX_PRIVATE_KEY_B64",
    "ENV_SANDBOX_PRIVATE_KEY_PATH",
    "PARTNER_ASSERTED_FIELDS",
    "PARTNER_ASSERTIONS_NOTICE",
    "REVOCATION_REASONS",
    "PARTNER_TIMESTAMP_KEYS",
    "SANDBOX_ENVIRONMENT",
    "SANDBOX_KEY_REGISTRY_SCHEMA",
    "SANDBOX_NOTICE",
    "SANDBOX_RECEIPT_FRAMEWORK",
    "SANDBOX_RECEIPT_ID_PREFIX",
    "SANDBOX_RECEIPT_SCHEMA",
    "SandboxReceiptError",
    "assert_registries_disjoint",
    "check_sandbox_receipt",
    "configured_sandbox_key_registry",
    "configured_sandbox_private_key_pem",
    "create_sandbox_receipt",
    "normalize_sandbox_key_registry",
    "sandbox_key_registry_json_bytes",
    "verify_sandbox_receipt",
    "verify_sandbox_receipt_from_registry",
]
