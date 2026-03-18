# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Canonical governance policy-pack registry for IOA Core."""

from __future__ import annotations

from typing import Any, Dict, Optional


_POLICY_PACKS: Dict[str, Dict[str, Any]] = {
    "qix_general": {
        "pack_id": "qix_general",
        "policy_pack": "qixchat-default",
        "manifest": "system_laws.json",
        "domain": "general",
        "default_jurisdiction": "GLOBAL",
        "aliases": {
            "qixchat-default",
            "general",
            "default",
        },
    },
    "qix_health_au": {
        "pack_id": "qix_health_au",
        "policy_pack": "healthcare-au",
        "manifest": "system_laws_au_health.json",
        "domain": "health",
        "default_jurisdiction": "AU",
        "aliases": {
            "healthcare-au",
            "healthcare_au",
            "qixhealth-au",
            "qixhealth_au",
            "qixhealth",
            "au-healthcare",
            "au_healthcare",
            "au-health",
            "au_health",
            "health",
            "hipaa",
        },
        "regulatory_frameworks": [
            "AU Privacy Act 1988",
            "Australian Privacy Principles",
            "My Health Records Act",
        ],
    },
    "qixcite_legal": {
        "pack_id": "qixcite_legal",
        "policy_pack": "qixcite-legal",
        "manifest": "system_laws.json",
        "domain": "law",
        "default_jurisdiction": "US-FED",
        "aliases": {
            "qixcite-legal",
            "law",
        },
    },
}


def normalize_policy_pack(value: Optional[str]) -> Optional[str]:
    text = str(value or "").strip().lower()
    return text if text else None


def resolve_policy_pack_definition(policy_pack: Optional[str]) -> Optional[Dict[str, Any]]:
    normalized = normalize_policy_pack(policy_pack)
    if not normalized:
        return None
    for pack in _POLICY_PACKS.values():
        aliases = {str(item).strip().lower() for item in pack.get("aliases", set()) if str(item).strip()}
        canonical = str(pack.get("policy_pack") or "").strip().lower()
        if normalized == canonical or normalized in aliases:
            return dict(pack)
    return None


def resolve_manifest_filename(policy_pack: Optional[str]) -> Optional[str]:
    pack = resolve_policy_pack_definition(policy_pack)
    if not pack:
        return None
    manifest = str(pack.get("manifest") or "").strip()
    return manifest or None


def list_policy_packs() -> Dict[str, Dict[str, Any]]:
    return {key: dict(value) for key, value in _POLICY_PACKS.items()}
