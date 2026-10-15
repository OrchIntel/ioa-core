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

import hashlib
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


_JURISDICTION_CODE_RE = re.compile(r"^[A-Z]{2}(-[A-Z]{2,3})?$")
_TEMPLATE_ID_RE = re.compile(r"^[a-z0-9_]{1,80}$")
_OPAQUE_REF_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_EPISODE_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
_NHI_SHAPE_RE = re.compile(r"^[A-Z]{3}[0-9]{4}$|^[A-Z]{3}[0-9]{2}[A-Z]{2}$")
_MEDICARE_SHAPE_RE = re.compile(r"^[0-9]{10,11}$")
_MAX_TEMPLATES_SHOWN = 40


def _normalize_jurisdiction_block(value: Any) -> Any:
    """Accept the v1 string or a mapping {code, country, state, templates_shown, policy_pack}."""
    if value is None:
        return None
    if not isinstance(value, Mapping):
        text = str(value).strip()
        return text or None
    code = str(value.get("code") or "").strip().upper()
    if not _JURISDICTION_CODE_RE.fullmatch(code):
        raise SessionReceiptError(
            "session.jurisdiction.code must look like NZ or AU-NSW"
        )
    country, _, state = code.partition("-")
    templates_raw = value.get("templates_shown") or []
    if not isinstance(templates_raw, list):
        raise SessionReceiptError(
            "session.jurisdiction.templates_shown must be a list of template ids"
        )
    if len(templates_raw) > _MAX_TEMPLATES_SHOWN:
        raise SessionReceiptError(
            "session.jurisdiction.templates_shown lists too many templates"
        )
    templates: List[str] = []
    for item in templates_raw:
        template_id = str(item or "").strip()
        if not _TEMPLATE_ID_RE.fullmatch(template_id):
            raise SessionReceiptError(
                "templates_shown must contain template ids only, never text"
            )
        templates.append(template_id)
    return {
        "code": code,
        "country": str(value.get("country") or country).strip().upper(),
        "state": (str(value.get("state") or state).strip().upper() or None),
        "templates_shown": templates,
        "policy_pack": _optional_str(value, "policy_pack"),
    }


def _normalize_session(session: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "evidence_bundle_id": _required_str(session, "evidence_bundle_id", "session"),
        "evidence_chain_id": _optional_str(session, "evidence_chain_id"),
        "workflow_key": _required_str(session, "workflow_key", "session"),
        "care_setting": _required_str(session, "care_setting", "session"),
        "profile_id": _required_str(session, "profile_id", "session"),
        "jurisdiction": _normalize_jurisdiction_block(session.get("jurisdiction")),
        "policy_pack": _optional_str(session, "policy_pack"),
        "runtime_service": str(session.get("runtime_service") or "qixhealth").strip(),
        "provider": _optional_str(session, "provider"),
        "model": _optional_str(session, "model"),
    }


# Optional longitudinal and care-event blocks (schema stays v1; emitted only when
# supplied). Enumerations are closed so a receipt can never carry free text here.
EPISODE_TYPES = ("care_episode", "programme", "admission", "community")
CARE_EVENT_TYPES = (
    "clinician_review",
    "service_review",
    "follow_up",
    "escalation",
    "self_report",
    "ambient_signal",
)
SIGNAL_TYPES = (
    "clinician_text",
    "structured_measure",
    "self_report_text",
    "passive_sensor",
    "wearable",
    "voice",
    "other",
)
INFERENCE_CATEGORIES = (
    "none",
    "summary",
    "risk_indicator_flag",
    "pattern_over_time",
    "triage_suggestion",
    "diagnosis",
)
# Categories that would cross into a regulated medical device claim are
# rejected in v1 even though they are named, so the enum is forward compatible.
_INFERENCE_NOT_PERMITTED_V1 = {"triage_suggestion", "diagnosis"}
WITHHELD_KINDS = ("model_output", "inference", "section", "signal_summary")
WITHHELD_REASONS = (
    "content_gate_hold",
    "policy",
    "consent_absent",
    "jurisdiction",
    "clinician_decision",
)
REVIEW_SERVICE_LEVELS = (
    "not_required",
    "pending",
    "reviewed",
    "escalated_to_service",
    "closed",
)
DISCLOSURE_MODES = ("verbal", "written", "notice", "not_recorded")
CONSENT_SCOPES = ("session", "episode", "service")


def _enum(
    mapping: Mapping[str, Any],
    key: str,
    allowed: tuple,
    section: str,
    *,
    required: bool = True,
) -> Optional[str]:
    value = mapping.get(key)
    if value is None:
        if required:
            raise SessionReceiptError(f"{section}.{key} is required")
        return None
    text = str(value).strip()
    if text not in allowed:
        raise SessionReceiptError(
            f"{section}.{key} must be one of: {', '.join(allowed)}"
        )
    return text


def _normalize_episode(
    episode: Optional[Mapping[str, Any]]
) -> Optional[Dict[str, Any]]:
    if episode is None:
        return None
    episode_id = str(episode.get("episode_id") or "").strip()
    if (
        not _EPISODE_ID_RE.fullmatch(episode_id)
        or _NHI_SHAPE_RE.fullmatch(episode_id)
        or _MEDICARE_SHAPE_RE.fullmatch(episode_id)
    ):
        raise SessionReceiptError(
            "episode.episode_id must be an opaque pseudonymous token (8 to 128 characters), never an NHI, Medicare or similar identifier"
        )
    return {
        "episode_id": episode_id,
        "episode_type": _enum(
            episode, "episode_type", EPISODE_TYPES, "episode", required=False
        ),
        "opened_at": _optional_str(episode, "opened_at"),
    }


def _normalize_care_event(
    care_event: Optional[Mapping[str, Any]]
) -> Optional[Dict[str, Any]]:
    if care_event is None:
        return None
    event_type = _enum(care_event, "type", CARE_EVENT_TYPES, "care_event")
    signal_type = _enum(
        care_event, "signal_type", SIGNAL_TYPES, "care_event", required=False
    )
    if event_type in {"self_report", "ambient_signal"} and not signal_type:
        raise SessionReceiptError(
            "care_event.signal_type is required for self_report and ambient_signal events"
        )
    return {
        "type": event_type,
        "signal_type": signal_type,
        "source_role": _optional_str(care_event, "source_role"),
    }


def _normalize_inference(
    inference: Optional[Mapping[str, Any]]
) -> Optional[Dict[str, Any]]:
    if inference is None:
        return None
    category = _enum(inference, "category", INFERENCE_CATEGORIES, "inference")
    if category in _INFERENCE_NOT_PERMITTED_V1:
        raise SessionReceiptError(
            f"inference.category {category!r} is not permitted in a v1 receipt (QiXMind does not triage or diagnose)"
        )
    return {"category": category, "permitted": True}


def _normalize_withheld(
    withheld: Optional[Mapping[str, Any]]
) -> Optional[Dict[str, Any]]:
    if withheld is None:
        return None
    items_raw = withheld.get("items") or []
    if not isinstance(items_raw, list):
        raise SessionReceiptError("withheld.items must be a list")
    items: List[Dict[str, Any]] = []
    for index, item in enumerate(items_raw):
        if not isinstance(item, Mapping):
            raise SessionReceiptError(f"withheld.items[{index}] must be an object")
        count = _optional_int(item.get("count"))
        if count is None or count < 0:
            raise SessionReceiptError(
                f"withheld.items[{index}].count must be a non-negative integer"
            )
        items.append(
            {
                "kind": _enum(item, "kind", WITHHELD_KINDS, f"withheld.items[{index}]"),
                "reason_code": _enum(
                    item, "reason_code", WITHHELD_REASONS, f"withheld.items[{index}]"
                ),
                "count": count,
            }
        )
    return {"items": items, "total": sum(item["count"] for item in items)}


def _normalize_review_state(
    review_state: Optional[Mapping[str, Any]]
) -> Optional[Dict[str, Any]]:
    if review_state is None:
        return None
    return {
        "service_level": _enum(
            review_state, "service_level", REVIEW_SERVICE_LEVELS, "review_state"
        ),
        "reviewed_by_role": _optional_str(review_state, "reviewed_by_role"),
        "reviewed_at": _optional_str(review_state, "reviewed_at"),
    }


def _normalize_disclosure(
    disclosure: Optional[Mapping[str, Any]]
) -> Optional[Dict[str, Any]]:
    if disclosure is None:
        return None
    ref = _optional_str(disclosure, "consent_record_ref")
    if ref and not _OPAQUE_REF_RE.fullmatch(ref):
        raise SessionReceiptError(
            "disclosure.consent_record_ref must be an opaque identifier"
        )
    basis = _optional_str(disclosure, "basis_template_id")
    if basis and not _TEMPLATE_ID_RE.fullmatch(basis):
        raise SessionReceiptError("disclosure.basis_template_id must be a template id")
    return {
        "ai_use_disclosed": bool(disclosure.get("ai_use_disclosed", False)),
        "disclosure_mode": _enum(
            disclosure,
            "disclosure_mode",
            DISCLOSURE_MODES,
            "disclosure",
            required=False,
        )
        or "not_recorded",
        "consent_recorded": bool(disclosure.get("consent_recorded", False)),
        "consent_record_ref": ref,
        "consent_scope": _enum(
            disclosure, "consent_scope", CONSENT_SCOPES, "disclosure", required=False
        ),
        "basis_template_id": basis,
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


# Where the acting role came from (2.18.0). Emitted only when supplied, so
# receipts issued without it are byte-identical to earlier v1 receipts.
#   claims          a role claim in the verified session token
#   clerk_org_role  the sign-in provider's organisation role (org:<role>)
#   self_declared   chosen by the verified member in the request
#   role_directory  a verified staff role directory held by the operator
#   unrecorded      the operator did not record a source
ROLE_SOURCES = (
    "claims",
    "clerk_org_role",
    "self_declared",
    "role_directory",
    "unrecorded",
)
_ROLE_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]{1,39}$")


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
    block: Dict[str, Any] = {
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
    if acknowledgement.get("role_source") is not None:
        block["role_source"] = _enum(
            acknowledgement, "role_source", ROLE_SOURCES, "acknowledgement"
        )
    return block


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


_PROVENANCE_SCHEMA = "qixmind.session-provenance.v1"
_POLICY_STATUSES = {"draft", "approved", "retired"}


def _normalize_provenance(
    provenance: Optional[Mapping[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Validate the optional provenance block captured by the runtime.

    The block is copied, not computed here: a receipt must name what governed
    the session at the time, so a missing block stays missing.
    """
    if provenance is None:
        return None
    if not isinstance(provenance, Mapping):
        raise SessionReceiptError("provenance must be an object")
    if provenance.get("schema") != _PROVENANCE_SCHEMA:
        raise SessionReceiptError("provenance has an unsupported schema")
    if provenance.get("source") != "runtime":
        raise SessionReceiptError("provenance must be captured by the runtime")
    profile = provenance.get("profile")
    gates = provenance.get("content_gates")
    policy = provenance.get("action_policy")
    if not isinstance(profile, Mapping) or not isinstance(gates, Mapping):
        raise SessionReceiptError("provenance needs profile and content_gates")
    if not isinstance(policy, Mapping):
        raise SessionReceiptError("provenance needs action_policy")
    block: Dict[str, Any] = {
        "schema": _PROVENANCE_SCHEMA,
        "source": "runtime",
        "ioa_core_version": _required_str(provenance, "ioa_core_version", "provenance"),
        "profile": {
            "profile_id": _required_str(profile, "profile_id", "provenance.profile"),
            "fingerprint": normalize_sha256(
                profile.get("fingerprint"), "provenance.profile.fingerprint"
            ),
        },
        "content_gates": {
            "detector": _required_str(gates, "detector", "provenance.content_gates"),
            "detector_version": _required_str(
                gates, "detector_version", "provenance.content_gates"
            ),
            "review_output_version": _optional_str(gates, "review_output_version"),
            "ruleset_sha256": normalize_sha256(
                gates.get("ruleset_sha256"), "provenance.content_gates.ruleset_sha256"
            ),
        },
    }
    if policy.get("applied") is True:
        status = str(policy.get("status") or "")
        if status not in _POLICY_STATUSES:
            raise SessionReceiptError("provenance action_policy status is unknown")
        block["action_policy"] = {
            "applied": True,
            "policy_id": _required_str(policy, "policy_id", "provenance.action_policy"),
            "version": _required_str(policy, "version", "provenance.action_policy"),
            "status": status,
            "fingerprint": normalize_sha256(
                policy.get("fingerprint"), "provenance.action_policy.fingerprint"
            ),
        }
    elif policy.get("applied") is False:
        block["action_policy"] = {
            "applied": False,
            "basis": _required_str(policy, "basis", "provenance.action_policy"),
        }
    else:
        raise SessionReceiptError(
            "provenance action_policy.applied must be true or false"
        )
    findings = provenance.get("findings")
    if findings is not None:
        if not isinstance(findings, Mapping):
            raise SessionReceiptError("provenance findings must be an object")
        block["findings"] = {
            "detector": _required_str(findings, "detector", "provenance.findings"),
            "detector_version": _required_str(
                findings, "detector_version", "provenance.findings"
            ),
            "context_rules_version": _optional_str(findings, "context_rules_version"),
            "status": _required_str(findings, "status", "provenance.findings"),
            "ruleset_sha256": normalize_sha256(
                findings.get("ruleset_sha256"), "provenance.findings.ruleset_sha256"
            ),
        }
    return block


# Amendments (2.18.0). An amendment never changes the receipt it corrects: it
# is a new signed receipt whose signed ``amendment`` block names the amended
# receipt by id and by the SHA-256 of its exported bytes, with a reason code,
# the acting role and where that role came from. Chains are linear: the
# operator amends only the latest receipt in a chain.
AMENDMENT_SCHEMA = "qixmind.receipt-amendment.v1"
AMENDMENT_REASON_CODES = (
    "episode_reference_corrected",
    "care_event_type_corrected",
    "administrative_correction",
)
# Fields an amendment may correct. Gate results, hashes, acknowledgement and
# provenance are evidence of what happened and are never amendable.
AMENDABLE_FIELDS = ("episode.episode_id", "care_event.type")
_REASON_FIELDS = {
    "episode_reference_corrected": frozenset({"episode.episode_id"}),
    "care_event_type_corrected": frozenset({"care_event.type"}),
    "administrative_correction": frozenset(),
}
AMENDMENT_AUTHORITIES = ("original_signer", "supervising_role")
_RECEIPT_ID_RE = re.compile(r"^qixmind-ser-[0-9a-f]{16}$")


def receipt_sha256(receipt: Mapping[str, Any]) -> str:
    """SHA-256 of the receipt's exported bytes (``receipt_json_bytes``).

    This is the hash of the file a holder downloads, so it can be checked with
    any SHA-256 tool as well as with ``verify_amendment_link``.
    """
    return "sha256:" + hashlib.sha256(receipt_json_bytes(receipt)).hexdigest()


def _normalize_amendment(amendment: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(amendment, Mapping):
        raise SessionReceiptError("amendment must be an object")
    amends_id = str(amendment.get("amends_receipt_id") or "").strip()
    if not _RECEIPT_ID_RE.fullmatch(amends_id):
        raise SessionReceiptError(
            "amendment.amends_receipt_id must be a session receipt id"
        )
    reason_code = _enum(amendment, "reason_code", AMENDMENT_REASON_CODES, "amendment")
    fields_raw = amendment.get("corrected_fields") or []
    if not isinstance(fields_raw, list):
        raise SessionReceiptError("amendment.corrected_fields must be a list")
    fields = sorted({str(item).strip() for item in fields_raw})
    unknown = [item for item in fields if item not in AMENDABLE_FIELDS]
    if unknown:
        raise SessionReceiptError(
            "amendment.corrected_fields may name only: " + ", ".join(AMENDABLE_FIELDS)
        )
    if frozenset(fields) != _REASON_FIELDS[str(reason_code)]:
        raise SessionReceiptError(
            f"amendment reason {reason_code} does not match the corrected fields"
        )
    actor = amendment.get("amended_by")
    if not isinstance(actor, Mapping):
        raise SessionReceiptError("amendment.amended_by is required")
    role = str(actor.get("role") or "").strip()
    if not _ROLE_TOKEN_RE.fullmatch(role):
        raise SessionReceiptError("amendment.amended_by.role must be a role token")
    reason_sha = amendment.get("reason_sha256")
    return {
        "schema": AMENDMENT_SCHEMA,
        "amends_receipt_id": amends_id,
        "amends_receipt_sha256": normalize_sha256(
            amendment.get("amends_receipt_sha256"), "amendment.amends_receipt_sha256"
        ),
        "amends_issued_at": _optional_str(amendment, "amends_issued_at"),
        "reason_code": reason_code,
        "reason_sha256": (
            normalize_sha256(reason_sha, "amendment.reason_sha256")
            if reason_sha not in (None, "")
            else None
        ),
        "corrected_fields": fields,
        "amended_by": {
            "role": role,
            "role_source": _enum(
                actor, "role_source", ROLE_SOURCES, "amendment.amended_by"
            ),
            "authority": _enum(
                actor, "authority", AMENDMENT_AUTHORITIES, "amendment.amended_by"
            ),
            "name_included": False,
        },
        "amended_at": _required_str(amendment, "amended_at", "amendment"),
        "original_preserved": True,
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
    episode: Optional[Mapping[str, Any]] = None,
    care_event: Optional[Mapping[str, Any]] = None,
    inference: Optional[Mapping[str, Any]] = None,
    withheld: Optional[Mapping[str, Any]] = None,
    review_state: Optional[Mapping[str, Any]] = None,
    disclosure: Optional[Mapping[str, Any]] = None,
    provenance: Optional[Mapping[str, Any]] = None,
    amendment: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Create and sign a Session Evidence Receipt.

    Every section is validated and reduced to hashes, identifiers, roles and
    timestamps. Signing uses the operator key supplied by path or PEM bytes;
    no key is generated here and signing errors propagate, so an unsigned
    receipt can never be returned.

    ``amendment`` (2.18.0) marks this receipt as an amendment of an earlier
    one; it implies ``supersedes_receipt_id``. Prefer ``amend_session_receipt``,
    which builds it from the original.
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
        ("episode", episode),
        ("care_event", care_event),
        ("inference", inference),
        ("withheld", withheld),
        ("review_state", review_state),
        ("disclosure", disclosure),
        ("provenance", provenance),
        ("amendment", amendment),
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
    # Optional blocks appear only when supplied, so receipts issued without them
    # are byte-identical to earlier v1 receipts.
    for key, block in (
        ("episode", _normalize_episode(episode)),
        ("care_event", _normalize_care_event(care_event)),
        ("inference", _normalize_inference(inference)),
        ("withheld", _normalize_withheld(withheld)),
        ("review_state", _normalize_review_state(review_state)),
        ("disclosure", _normalize_disclosure(disclosure)),
        ("provenance", _normalize_provenance(provenance)),
    ):
        if block is not None:
            payload[key] = block
    if payload["model_output"]["held"]:
        raise SessionReceiptError("a held output cannot be issued a receipt")
    if amendment is not None:
        amendment_block = _normalize_amendment(amendment)
        amends_id = amendment_block["amends_receipt_id"]
        if supersedes_receipt_id and str(supersedes_receipt_id).strip() != amends_id:
            raise SessionReceiptError(
                "an amendment supersedes exactly the receipt it amends"
            )
        supersedes_receipt_id = amends_id
        payload["amendment"] = amendment_block
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
    # A production receipt never carries an environment designation; a sandbox
    # evaluation receipt (its own framework, ioa_core.evidence.sandbox_receipt)
    # is refused here even if its framework field were altered.
    return (
        receipt.get("framework") == RECEIPT_FRAMEWORK
        and isinstance(metadata, Mapping)
        and metadata.get("schema") == RECEIPT_SCHEMA
        and "environment" not in metadata
        and not str(receipt.get("bundle_id") or "").startswith("qixmind-sbx-")
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


_KEEP = object()
# Optional blocks carried from the original into an amendment unchanged.
_CARRIED_BLOCKS = (
    "episode",
    "care_event",
    "inference",
    "withheld",
    "review_state",
    "disclosure",
    "provenance",
)


def amend_session_receipt(
    original: Mapping[str, Any],
    *,
    reason_code: str,
    amended_by: Mapping[str, Any],
    software: Mapping[str, Any],
    corrections: Optional[Mapping[str, Any]] = None,
    reason_sha256: Optional[str] = None,
    escalation_follow_up: Any = _KEEP,
    review_state: Any = _KEEP,
    amended_at: Optional[str] = None,
    registry: Optional[Mapping[str, Any]] = None,
    private_key_path: Optional[str] = None,
    private_key_pem: Optional[bytes] = None,
) -> Dict[str, Any]:
    """Issue a new signed receipt that amends ``original``.

    The original is read, never modified. The new receipt repeats the
    original's evidence (session, hashes, gate results, acknowledgement,
    provenance), applies only the named ``corrections`` (``AMENDABLE_FIELDS``),
    may carry the current follow-up state and review state, and records a
    signed ``amendment`` block linking the original by id and by
    ``receipt_sha256``. ``amended_by`` is ``{role, role_source, authority}``;
    a free-text reason is never stored in the receipt, only its SHA-256.

    Pass ``registry`` to refuse an original whose signature does not verify.
    """
    if not _is_receipt(original):
        raise SessionReceiptError("only a QiXMind session receipt can be amended")
    if registry is not None and not verify_session_receipt_from_registry(
        original, registry
    ):
        raise SessionReceiptError("the receipt to amend does not verify")
    metadata = original["metadata"]
    original_id = str(original.get("bundle_id") or "").strip()
    changes = dict(corrections or {})
    unknown = sorted(set(changes) - set(AMENDABLE_FIELDS))
    if unknown:
        raise SessionReceiptError(
            "corrections may name only: " + ", ".join(AMENDABLE_FIELDS)
        )
    blocks: Dict[str, Any] = {
        key: metadata[key] for key in _CARRIED_BLOCKS if metadata.get(key) is not None
    }
    if "episode.episode_id" in changes:
        value = str(changes["episode.episode_id"] or "").strip()
        current = (blocks.get("episode") or {}).get("episode_id")
        if value == current:
            raise SessionReceiptError("the corrected episode id is unchanged")
        blocks["episode"] = {**(blocks.get("episode") or {}), "episode_id": value}
    if "care_event.type" in changes:
        value = str(changes["care_event.type"] or "").strip()
        current = (blocks.get("care_event") or {}).get("type")
        if value == current:
            raise SessionReceiptError("the corrected care event type is unchanged")
        blocks["care_event"] = {**(blocks.get("care_event") or {}), "type": value}
    if review_state is not _KEEP:
        if review_state is None:
            blocks.pop("review_state", None)
        else:
            blocks["review_state"] = review_state
    follow_up = (
        metadata.get("escalation_follow_up")
        if escalation_follow_up is _KEEP
        else escalation_follow_up
    )
    timestamp = _timestamp(amended_at)
    amendment = {
        "amends_receipt_id": original_id,
        "amends_receipt_sha256": receipt_sha256(original),
        "amends_issued_at": metadata.get("issued_at"),
        "reason_code": reason_code,
        "reason_sha256": reason_sha256,
        "corrected_fields": sorted(changes),
        "amended_by": dict(amended_by),
        "amended_at": timestamp,
    }
    return create_session_receipt(
        session=metadata["session"],
        model_input=metadata["model_input"],
        model_output=metadata["model_output"],
        content_gates=metadata["content_gates"],
        acknowledgement=metadata["acknowledgement"],
        escalation_follow_up=follow_up,
        software=software,
        issued_at=timestamp,
        supersedes_receipt_id=original_id,
        private_key_path=private_key_path,
        private_key_pem=private_key_pem,
        amendment=amendment,
        **blocks,
    )


def describe_amendment(receipt: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    """The signed amendment block of a receipt, or None when it amends nothing."""
    metadata = receipt.get("metadata") if isinstance(receipt, Mapping) else None
    block = metadata.get("amendment") if isinstance(metadata, Mapping) else None
    return dict(block) if isinstance(block, Mapping) else None


def verify_amendment_link(
    amending: Mapping[str, Any], original: Mapping[str, Any]
) -> bool:
    """True when ``amending`` is a signed amendment of exactly ``original``.

    Checks the link only (id, exported-bytes hash and supersession); verify
    each receipt's signature separately with the published registry.
    """
    if not (_is_receipt(amending) and _is_receipt(original)):
        return False
    block = describe_amendment(amending)
    if not block or block.get("schema") != AMENDMENT_SCHEMA:
        return False
    original_id = str(original.get("bundle_id") or "")
    try:
        original_hash = receipt_sha256(original)
    except SessionReceiptError:
        return False
    return (
        block.get("amends_receipt_id") == original_id
        and block.get("amends_receipt_sha256") == original_hash
        and amending["metadata"].get("supersedes_receipt_id") == original_id
    )


__all__ = [
    "AMENDABLE_FIELDS",
    "AMENDMENT_AUTHORITIES",
    "AMENDMENT_REASON_CODES",
    "AMENDMENT_SCHEMA",
    "ROLE_SOURCES",
    "amend_session_receipt",
    "describe_amendment",
    "receipt_sha256",
    "verify_amendment_link",
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
