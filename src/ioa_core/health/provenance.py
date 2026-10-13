# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""What governed a session: the profile, detector and action policy applied.

A runtime calls :func:`capture_session_provenance` at the moment it evaluates a
session, and passes the result through to the receipt unchanged. The console
must not reconstruct it later from its own (possibly different) ioa-core, and a
receipt issued without it must not be back-filled with current versions.

Each element is identified by version and by a fingerprint of its exact
definition, so it stays interpretable after the definitions change.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .. import __version__ as IOA_CORE_VERSION
from .content_gates import (
    DETECTOR_NAME as GATE_DETECTOR_NAME,
    DETECTOR_VERSION as GATE_DETECTOR_VERSION,
    REVIEW_OUTPUT_DETECTOR_VERSION,
    ruleset_fingerprint as gate_ruleset_fingerprint,
)
from .registry import profile_definition_fingerprint

PROVENANCE_SCHEMA = "qixmind.session-provenance.v1"


def capture_session_provenance(
    *,
    profile_id: str,
    policy: Optional[Any] = None,
    findings_report: Optional[Any] = None,
) -> Dict[str, Any]:
    """Provenance for one session, captured where the session was evaluated.

    ``policy`` is an :class:`ioa_core.health.policy.ActionPolicy` when one was
    applied. Without one, the record says so: actions came from the profile's
    own gate severities, and no action policy was applied.
    """
    record: Dict[str, Any] = {
        "schema": PROVENANCE_SCHEMA,
        "source": "runtime",
        "ioa_core_version": IOA_CORE_VERSION,
        "profile": {
            "profile_id": str(profile_id),
            "fingerprint": profile_definition_fingerprint(profile_id),
        },
        "content_gates": {
            "detector": GATE_DETECTOR_NAME,
            "detector_version": GATE_DETECTOR_VERSION,
            "review_output_version": REVIEW_OUTPUT_DETECTOR_VERSION,
            "ruleset_sha256": gate_ruleset_fingerprint(),
        },
        "action_policy": (
            policy.provenance()
            if policy is not None
            else {"applied": False, "basis": "profile_gate_severities"}
        ),
    }
    if findings_report is not None:
        record["findings"] = {
            "detector": findings_report.detector,
            "detector_version": findings_report.detector_version,
            "context_rules_version": findings_report.context_rules_version,
            "status": findings_report.status,
            "ruleset_sha256": findings_report.ruleset_sha256,
        }
    return record


def is_provenance(value: Any) -> bool:
    return isinstance(value, Mapping) and value.get("schema") == PROVENANCE_SCHEMA


__all__ = ["PROVENANCE_SCHEMA", "capture_session_provenance", "is_provenance"]
