"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

from __future__ import annotations

"""

PATCH: Cursor-2025-08-22 DISPATCH-GPT-20250822-011 <Phase 2: agent→model terminology cleanup>
"""

"""
This minimal evaluator reads a final report dict and produces a FeedbackMessage
with a coarse score based on presence of key fields. It is intentionally simple
to seed the evaluation loop and will evolve in roadmap v4.3.
"""

from typing import Any, Dict

from schemas.message_schema import FeedbackMessage
from datetime import datetime, timezone


    """Minimal evaluator for FinalReports."""

    def review_final_report(self, task_id: str, report: Dict[str, Any]) -> FeedbackMessage:
        score = 0.0
        if report.get("consensus_achieved"):
            score += 0.5
        if report.get("summary"):
            score += 0.3
        if report.get("votes"):
            score += 0.2
        score = min(score, 1.0)

        return FeedbackMessage(
            feedback_id=f"fbk-{int(datetime.now(timezone.utc).timestamp())}",
            task_id=task_id,
            source="evaluator",
            message="Automated evaluation of final report",
            score=score,
            metadata={"heuristics": ["consensus", "summary", "votes"]},
        )


__all__ = ["EvaluationModel"]


