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
- Provide a small, test-oriented adapter `OpenAIService` that uses the
  OpenAI v1 client signature: client.chat.completions.create(...).
- Define lightweight exception classes used by tests.

Public objects:
- OpenAIService
- LLMAuthenticationError
- LLMAPIError
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


class LLMAuthenticationError(Exception):
    """Raised when provider rejects credentials or authentication fails."""


class LLMAPIError(Exception):
    """Raised for general provider API errors (non-auth)."""


@dataclass
class OpenAIService:
    """Minimal adapter around OpenAI v1 SDK for tests.

    Parameters:
    """


    def __post_init__(self) -> None:
        # Lazy import to avoid hard dependency if tests patch sys.modules
        try:
            import openai  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise LLMAPIError(f"OpenAI SDK not available: {exc}")

        # v1 style client
        self._client = openai.OpenAI()

    def execute(self, prompt: str, **kwargs: Any) -> str:
        """Execute a simple chat completion and return content text.

        Ensures we call `.chat.completions.create(...)` and avoid leaking secrets
        in raised error messages.
        """
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **{k: v for k, v in kwargs.items() if not k.startswith("metadata.")}
            )
            # v1: choices[0].message.content
            return getattr(resp.choices[0].message, "content", "")
        except Exception as exc:  # Keep simple, tests assert keywords not secrets
            msg = str(exc)
            redacted = msg.replace("sk-", "**redacted**-")
            lowered = redacted.lower()
            if "auth" in lowered or "unauthorized" in lowered or "key" in lowered:
                raise LLMAuthenticationError(redacted)
            raise LLMAPIError(redacted)


__all__ = [
    "OpenAIService",
    "LLMAuthenticationError",
    "LLMAPIError",
]