""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

from __future__ import annotations

"""
"""

"""
Module responsibilities:
- Define canonical, versioned message models used across IOA Core.
- Provide forward-compatible fields for identity/governance hooks (zero-trust ready).
- Keep models small and dependency-light; Pydantic v2 is required at runtime.

Key public objects:
- TaskMessage: User/system-initiated task with context.
- AgentResponse: Agent output with scoring/trace.
- FeedbackMessage: Human/automated feedback loop message.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

try:
    from pydantic import BaseModel, Field
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "Pydantic is required for message_schema. Install pydantic>=2.0"
    ) from exc




class IdentityContext(BaseModel):
    """Identity and authorization context for zero-trust hardening.

    Fields are designed to be optional at first and filled in by future
    identity providers or token verifiers.
    """

    subject_id: Optional[str] = Field(default=None, description="Stable principal identifier")
    token_hash: Optional[str] = Field(default=None, description="Hash/fingerprint of presented token")
    scopes: List[str] = Field(default_factory=list, description="Granted scopes at evaluation time")
    issued_at_utc: Optional[datetime] = Field(default=None, description="Token issued-at in UTC")
    expires_at_utc: Optional[datetime] = Field(default=None, description="Token expiry in UTC")


class TaskMessage(BaseModel):
    """Canonical task message entering the IOA orchestration pipeline."""

    task_id: str = Field(..., description="Unique task identifier")
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp")
    task_type: Literal["analysis", "generation", "classification", "workflow"] = Field(
        ..., description="High-level task category"
    )
    prompt: str = Field(..., description="Primary instruction or content")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Structured inputs for the task")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="User/system provided metadata")
    identity: Optional[IdentityContext] = Field(default=None, description="AuthN/Z context")


class AgentTrace(BaseModel):
    """Trace metadata from an agent run."""

    provider: Optional[str] = Field(default=None)
    latency_ms: Optional[float] = Field(default=None)
    tokens_prompt: Optional[int] = Field(default=None)
    tokens_completion: Optional[int] = Field(default=None)
    cost_usd: Optional[float] = Field(default=None)


class AgentResponse(BaseModel):
    """Response from an agent execution step."""

    task_id: str
    agent_id: str
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content: str
    reasoning: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)
    trace: Optional[AgentTrace] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeedbackMessage(BaseModel):
    """Feedback emitted by humans or evaluators about a task/response."""

    feedback_id: str
    task_id: str
    source: Literal["human", "evaluator", "system"] = "system"
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_agent_id: Optional[str] = None
    target_response_id: Optional[str] = None
    message: str = Field(..., description="Feedback content")
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "IdentityContext",
    "TaskMessage",
    "AgentTrace",
    "AgentResponse",
    "FeedbackMessage",
]


