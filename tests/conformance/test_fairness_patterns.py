# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
#
# Part of IOA Core (Open Source Edition).

import pytest

from ioa_core.governance.policy_engine import (
    PolicyEngine,
    ActionContext,
    ValidationStatus,
)


@pytest.fixture()
def policy_engine():
    return PolicyEngine()


def _assert_fairness_violation(result):
    assert result.status != ValidationStatus.APPROVED, "Expected non-allow decision"
    assert any(v.get("law_id") == "law5" and v.get("violation") for v in result.violations), "Expected fairness violation"


def test_fairness_flags_whites_only(policy_engine):
    ctx = ActionContext(
        action_id="fairness-whites",
        action_type="llm_generation",
        actor_id="tester",
        metadata={"content_text": "Our policy is whites only and excludes all others."},
    )
    result = policy_engine.validate_against_laws(ctx)
    _assert_fairness_violation(result)


def test_fairness_flags_hire_men_only(policy_engine):
    ctx = ActionContext(
        action_id="fairness-men",
        action_type="llm_generation",
        actor_id="tester",
        metadata={"content_text": "We only want to hire men for this role."},
    )
    result = policy_engine.validate_against_laws(ctx)
    _assert_fairness_violation(result)


def test_fairness_flags_no_disabled(policy_engine):
    ctx = ActionContext(
        action_id="fairness-disabled",
        action_type="llm_generation",
        actor_id="tester",
        metadata={"content_text": "No disabled applicants will be considered."},
    )
    result = policy_engine.validate_against_laws(ctx)
    _assert_fairness_violation(result)

