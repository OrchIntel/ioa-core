# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ioa_core.health import (
    FollowUpError,
    FollowUpObligation,
    compute_follow_up_deadline,
    follow_up_state,
    no_follow_up_required,
)

T0 = datetime(2026, 10, 13, 1, 0, tzinfo=timezone.utc)


def test_deadline_is_fired_at_plus_hours():
    assert compute_follow_up_deadline(T0, 24) == T0 + timedelta(hours=24)


@pytest.mark.parametrize("hours", [0, -1, "x", None])
def test_invalid_hours_rejected(hours):
    with pytest.raises(FollowUpError):
        compute_follow_up_deadline(T0, hours)


def test_naive_datetimes_rejected():
    with pytest.raises(FollowUpError):
        compute_follow_up_deadline(datetime(2026, 10, 13), 24)


def test_state_transitions():
    deadline = T0 + timedelta(hours=24)
    assert follow_up_state(deadline_at=deadline, closed_at=None, now=T0) == "open"
    assert follow_up_state(deadline_at=deadline, closed_at=None, now=deadline) == "open"
    assert (
        follow_up_state(
            deadline_at=deadline, closed_at=None, now=deadline + timedelta(seconds=1)
        )
        == "overdue"
    )
    assert (
        follow_up_state(deadline_at=deadline, closed_at=T0 + timedelta(hours=6), now=T0)
        == "closed"
    )
    # A late closure is still closed; lateness is visible from the timestamps.
    assert (
        follow_up_state(
            deadline_at=deadline,
            closed_at=deadline + timedelta(hours=2),
            now=deadline + timedelta(hours=3),
        )
        == "closed"
    )


def test_obligation_receipt_block_has_ids_roles_and_no_names():
    deadline = compute_follow_up_deadline(T0, 24)
    obligation = FollowUpObligation(
        obligation_id="ob-synthetic-1",
        gate="crisis_risk_to_self",
        severity="escalate",
        created_at=T0,
        deadline_at=deadline,
        deadline_hours=24,
        closed_at=None,
        alert_id="al-1",
        alert_raised_at=deadline + timedelta(hours=1),
        alert_raised_by="read_time",
    )
    block = obligation.to_receipt_dict(now=deadline + timedelta(hours=2))
    assert block["required"] is True
    assert block["status"] == "overdue"
    assert block["deadline_at"] == "2026-10-14T01:00:00Z"
    assert block["alert"] == {
        "alert_id": "al-1",
        "raised_at": "2026-10-14T02:00:00Z",
        "raised_by": "read_time",
    }
    assert block["alert_evaluation"] == "read_time_and_daily_sweep"
    assert block["closed_late"] is None
    assert not any(key.endswith("name") for key in block)

    closed = FollowUpObligation(
        obligation_id="ob-2",
        gate="child_protection",
        severity="escalate",
        created_at=T0,
        deadline_at=deadline,
        deadline_hours=24,
        closed_at=T0 + timedelta(hours=6),
        closed_by_role="supervisor",
        closure_review_event_id="77",
    ).to_receipt_dict(now=deadline)
    assert closed["status"] == "closed"
    assert closed["closed_late"] is False
    assert closed["closed_by_role"] == "supervisor"
    assert closed["alert"] is None


def test_no_follow_up_block():
    assert no_follow_up_required() == {"required": False}
