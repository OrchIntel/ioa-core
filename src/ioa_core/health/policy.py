# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Versioned action policies for QiXMind findings (evaluation only until approved).

Detection (:mod:`ioa_core.health.findings`) says what was seen; a policy says
what each finding requires. A policy is an immutable, versioned definition with
a fingerprint. Its approval is recorded separately and never changes the
definition, so a receipt can name exactly which rules applied and whether they
were approved at the time.

Rules (QiXMind source-aware gates design, 14 October 2026):

* Every finding needs at least a documented clinician disposition.
* ``escalate_with_follow_up`` also creates a follow-up obligation, and with
  ``dismissal_allowed`` false it cannot be closed as not applicable.
* Rules match on gate, source and context. The packaged default does not treat
  input-only findings differently from output findings.
* Only an ``approved`` policy may be used on a live path
  (:func:`require_live_approval`). Packaged defaults are ``draft``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .findings import CONTEXTS, FindingsReport
from .registry import canonical_fingerprint

POLICY_SCHEMA = "qixmind.action-policy.v1"
ACTIONS: Tuple[str, ...] = ("disposition_required", "escalate_with_follow_up")
STATUSES: Tuple[str, ...] = ("draft", "approved", "retired")
_ACTION_RANK = {name: index for index, name in enumerate(ACTIONS)}
_SOURCES = ("input", "output")


class PolicyError(ValueError):
    """Raised for malformed policies or a policy used where it is not allowed."""


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    gates: Tuple[str, ...]  # empty means every gate
    sources: Tuple[str, ...]  # empty means any source
    contexts: Tuple[str, ...]
    action: str
    follow_up_hours: Optional[int]
    dismissal_allowed: bool

    def matches(self, gate: str, source: str, context: str) -> bool:
        return (
            (not self.gates or gate in self.gates)
            and (not self.sources or source in self.sources)
            and context in self.contexts
        )


@dataclass(frozen=True)
class RequiredAction:
    """What one occurrence group of a finding requires under a policy."""

    gate: str
    source: str
    context: str
    entry: str
    action: str
    follow_up_hours: Optional[int]
    dismissal_allowed: bool
    rule_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate": self.gate,
            "source": self.source,
            "context": self.context,
            "entry": self.entry,
            "action": self.action,
            "follow_up_hours": self.follow_up_hours,
            "dismissal_allowed": self.dismissal_allowed,
            "rule_id": self.rule_id,
        }


@dataclass(frozen=True)
class ActionPolicy:
    policy_id: str
    version: str
    status: str
    profile_ids: Tuple[str, ...]
    rules: Tuple[PolicyRule, ...]
    default_rule: PolicyRule
    definition: Mapping[str, Any]  # the policy as loaded, for fingerprinting
    approval: Optional[Mapping[str, Any]] = None

    @property
    def fingerprint(self) -> str:
        """Fingerprint of the definition. Status and approval are excluded, so
        approving a policy does not change what it says."""
        return canonical_fingerprint(_definition_core(self.definition))

    def applies_to(self, profile_id: str) -> bool:
        return not self.profile_ids or profile_id in self.profile_ids

    def rule_for(self, gate: str, source: str, context: str) -> PolicyRule:
        for rule in self.rules:
            if rule.matches(gate, source, context):
                return rule
        return self.default_rule

    def required_actions(self, report: FindingsReport) -> List[RequiredAction]:
        """One required action per occurrence group, so nothing is merged away."""
        if not self.applies_to(report.profile_id):
            raise PolicyError(
                f"Policy {self.policy_id} does not apply to profile {report.profile_id}"
            )
        actions: List[RequiredAction] = []
        for finding in report.findings:
            groups = finding.occurrences or ()
            for group in groups:
                rule = self.rule_for(finding.gate, group.source, group.context)
                actions.append(
                    RequiredAction(
                        gate=finding.gate,
                        source=group.source,
                        context=group.context,
                        entry=group.entry,
                        action=rule.action,
                        follow_up_hours=rule.follow_up_hours,
                        dismissal_allowed=rule.dismissal_allowed,
                        rule_id=rule.rule_id,
                    )
                )
        return actions

    def summary_by_gate(self, report: FindingsReport) -> Dict[str, Dict[str, Any]]:
        """Strongest requirement per gate, for presentation only."""
        summary: Dict[str, Dict[str, Any]] = {}
        for item in self.required_actions(report):
            current = summary.get(item.gate)
            if (
                current is None
                or _ACTION_RANK[item.action] > _ACTION_RANK[current["action"]]
            ):
                summary[item.gate] = {
                    "action": item.action,
                    "follow_up_hours": item.follow_up_hours,
                    "dismissal_allowed": item.dismissal_allowed,
                }
            elif not item.dismissal_allowed:
                current["dismissal_allowed"] = False
        return summary

    def provenance(self) -> Dict[str, Any]:
        """The policy as a receipt names it: id, version, status, fingerprint."""
        return {
            "applied": True,
            "policy_id": self.policy_id,
            "version": self.version,
            "status": self.status,
            "fingerprint": self.fingerprint,
        }


def _definition_core(definition: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in definition.items()
        if key not in ("status", "approval")
    }


def _tuple(value: Any, allowed: Optional[Sequence[str]], field: str) -> Tuple[str, ...]:
    if value in (None, "*"):
        return ()
    if not isinstance(value, list) or not value:
        raise PolicyError(f"{field} must be '*' or a non-empty list")
    items = tuple(str(item).strip() for item in value)
    if allowed is not None:
        unknown = [item for item in items if item not in allowed]
        if unknown:
            raise PolicyError(f"{field} has unknown values: {unknown}")
    return items


def _rule(raw: Mapping[str, Any], *, default: bool = False) -> PolicyRule:
    action = str(raw.get("action") or "")
    if action not in ACTIONS:
        raise PolicyError(f"unknown action: {action!r}")
    hours = raw.get("follow_up_hours")
    if action == "escalate_with_follow_up":
        if not isinstance(hours, int) or hours <= 0:
            raise PolicyError("escalate_with_follow_up needs positive follow_up_hours")
    elif hours is not None:
        raise PolicyError("follow_up_hours applies only to escalate_with_follow_up")
    return PolicyRule(
        rule_id=str(raw.get("rule_id") or "").strip() or "unnamed",
        gates=() if default else _tuple(raw.get("gates"), None, "gates"),
        sources=() if default else _tuple(raw.get("sources"), _SOURCES, "sources"),
        contexts=(
            CONTEXTS if default else _tuple(raw.get("contexts"), CONTEXTS, "contexts")
        ),
        action=action,
        follow_up_hours=hours,
        dismissal_allowed=bool(raw.get("dismissal_allowed")),
    )


def policy_from_mapping(definition: Mapping[str, Any]) -> ActionPolicy:
    if definition.get("schema") != POLICY_SCHEMA:
        raise PolicyError("unsupported policy schema")
    status = str(definition.get("status") or "")
    if status not in STATUSES:
        raise PolicyError(f"unknown policy status: {status!r}")
    approval = definition.get("approval")
    if status == "approved" and not isinstance(approval, Mapping):
        raise PolicyError("an approved policy must carry its approval record")
    if status == "draft" and approval:
        raise PolicyError("a draft policy cannot carry an approval record")
    rules = definition.get("rules")
    if not isinstance(rules, list) or not rules:
        raise PolicyError("a policy needs at least one rule")
    return ActionPolicy(
        policy_id=str(definition.get("policy_id") or "").strip(),
        version=str(definition.get("version") or "").strip(),
        status=status,
        profile_ids=_tuple(definition.get("profile_ids"), None, "profile_ids"),
        rules=tuple(_rule(rule) for rule in rules),
        default_rule=_rule(definition.get("default_rule") or {}, default=True),
        definition=json.loads(json.dumps(definition)),
        approval=approval if isinstance(approval, Mapping) else None,
    )


def load_packaged_policy(name: str = "qixmind_default_draft") -> ActionPolicy:
    with (
        resources.files("ioa_core.health.policies")
        .joinpath(f"{name}.json")
        .open("r", encoding="utf-8") as handle
    ):
        return policy_from_mapping(json.load(handle))


def require_live_approval(policy: ActionPolicy) -> ActionPolicy:
    """Refuse any policy that is not approved. Call before any live use."""
    if policy.status != "approved":
        raise PolicyError(
            f"Policy {policy.policy_id} {policy.version} is {policy.status}; "
            "only an approved policy may be used on a live path"
        )
    return policy


__all__ = [
    "ACTIONS",
    "ActionPolicy",
    "POLICY_SCHEMA",
    "PolicyError",
    "PolicyRule",
    "RequiredAction",
    "STATUSES",
    "load_packaged_policy",
    "policy_from_mapping",
    "require_live_approval",
]
