# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Escalation follow-up semantics for health content gates.

When a gate fires at ``escalate`` or above, the service that committed the
output takes on an obligation to confirm follow-up within the profile's
``escalation_follow_up_hours``. This module holds the deadline and state logic
so that every consumer (console, runtime, receipts, demos) computes the same
answer. Storage and alerting live with the consumer.

Nothing here carries a person's name. Receipts record roles and identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

FOLLOW_UP_STATES = ("open", "closed", "overdue")


class FollowUpError(ValueError):
    """Raised when follow-up inputs are invalid."""


def _ensure_aware(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise FollowUpError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise FollowUpError(f"{name} must be timezone-aware")
    return value


def compute_follow_up_deadline(fired_at: datetime, hours: int) -> datetime:
    """Return the moment by which follow-up must be confirmed."""
    fired = _ensure_aware(fired_at, "fired_at")
    try:
        hours_int = int(hours)
    except (TypeError, ValueError) as exc:
        raise FollowUpError("hours must be an integer") from exc
    if hours_int <= 0:
        raise FollowUpError("hours must be positive")
    return fired + timedelta(hours=hours_int)


def follow_up_state(
    *,
    deadline_at: datetime,
    closed_at: Optional[datetime],
    now: Optional[datetime] = None,
) -> str:
    """Return ``closed``, ``overdue`` or ``open``.

    A closure recorded at any time counts as closed; whether it happened after
    the deadline is visible from the timestamps, and an alert raised before
    closure stays in the record.
    """
    deadline = _ensure_aware(deadline_at, "deadline_at")
    if closed_at is not None:
        _ensure_aware(closed_at, "closed_at")
        return "closed"
    current = _ensure_aware(now or datetime.now(timezone.utc), "now")
    return "overdue" if current > deadline else "open"


def _iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class FollowUpObligation:
    """A single follow-up obligation created by a fired gate."""

    obligation_id: str
    gate: str
    severity: str
    created_at: datetime
    deadline_at: datetime
    deadline_hours: int
    closed_at: Optional[datetime] = None
    closed_by_role: Optional[str] = None
    closure_review_event_id: Optional[str] = None
    alert_id: Optional[str] = None
    alert_raised_at: Optional[datetime] = None
    alert_raised_by: Optional[str] = None  # "read_time" or "daily_sweep"

    def state(self, now: Optional[datetime] = None) -> str:
        return follow_up_state(
            deadline_at=self.deadline_at, closed_at=self.closed_at, now=now
        )

    def closed_late(self) -> Optional[bool]:
        if self.closed_at is None:
            return None
        return self.closed_at > self.deadline_at

    def to_receipt_dict(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        """Return the receipt block for this obligation (identifiers and roles only)."""
        alert: Optional[Dict[str, Any]] = None
        if self.alert_id or self.alert_raised_at:
            alert = {
                "alert_id": self.alert_id,
                "raised_at": _iso(self.alert_raised_at),
                "raised_by": self.alert_raised_by,
            }
        return {
            "required": True,
            "obligation_id": self.obligation_id,
            "gate": self.gate,
            "severity": self.severity,
            "created_at": _iso(self.created_at),
            "deadline_at": _iso(self.deadline_at),
            "deadline_hours": int(self.deadline_hours),
            "status": self.state(now),
            "closed_at": _iso(self.closed_at),
            "closed_late": self.closed_late(),
            "closed_by_role": self.closed_by_role,
            "closure_review_event_id": self.closure_review_event_id,
            "alert": alert,
            "alert_evaluation": "read_time_and_daily_sweep",
        }


def no_follow_up_required() -> Dict[str, Any]:
    """Receipt block used when no gate fired at escalate or above."""
    return {"required": False}


__all__ = [
    "FOLLOW_UP_STATES",
    "FollowUpError",
    "FollowUpObligation",
    "compute_follow_up_deadline",
    "follow_up_state",
    "no_follow_up_required",
]
