# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""
IOA Module: src/llm_providers/__init__.py
Version: v2.5.0
Last-Updated: 2025-08-16
Agents: Cursor assist
Summary: Multi-provider LLM service package with factory pattern
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
