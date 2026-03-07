# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Cross-domain governance primitives.

These models provide shared contracts for identity attribution, domain context,
evidence chain linking, and incident emission across QiX suites.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class IdentityEntity:
    """Canonical identity envelope for governed operations."""

    entity_id: str
    entity_type: str
    role: str
    domain: str
    tenant_id: str
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DomainContext:
    """Canonical domain routing metadata for governance evaluation."""

    domain: str
    subdomain: Optional[str] = None
    jurisdiction: Optional[str] = None
    policy_pack: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GovernanceIncidentEvent:
    """Minimal cross-domain incident event schema."""

    event_id: str
    event_type: str
    source_domain: str
    target_domain: Optional[str]
    severity: str
    evidence_chain_id: str
    evidence_bundle_id: Optional[str]
    tenant_id: str
    entity_id: Optional[str]
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        source_domain: str,
        tenant_id: str,
        severity: str = "medium",
        target_domain: Optional[str] = None,
        evidence_chain_id: Optional[str] = None,
        evidence_bundle_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> "GovernanceIncidentEvent":
        return cls(
            event_id=f"govinc-{uuid.uuid4().hex[:16]}",
            event_type=event_type,
            source_domain=source_domain,
            target_domain=target_domain,
            severity=severity,
            evidence_chain_id=evidence_chain_id or f"chain-{uuid.uuid4().hex}",
            evidence_bundle_id=evidence_bundle_id,
            tenant_id=tenant_id,
            entity_id=entity_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details or {},
        )
