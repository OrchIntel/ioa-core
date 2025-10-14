"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
LLM Providers Package for IOA Core

Provides abstract base classes and concrete implementations for multiple LLM providers
including OpenAI, Anthropic, XAI/Grok, Google Gemini, Ollama, and DeepSeek.
Supports offline mode, soft validation, and factory-based instantiation.
"""

from .base import LLMService
from .factory import create_provider

__all__ = ["LLMService", "create_provider"]
