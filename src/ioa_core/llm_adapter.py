# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Compatibility shim for ``ioa_core.llm_adapter`` imports."""

from llm_adapter import LLMService, OpenAIService, LLMServiceError, LLMAuthenticationError, LLMAPIError

__all__ = [
    "LLMService",
    "OpenAIService",
    "LLMServiceError",
    "LLMAuthenticationError",
    "LLMAPIError",
]
