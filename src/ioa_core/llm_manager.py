# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



"""
Minimal LLMManager implementation for ioa_core package.

This provides a basic implementation that allows the CLI to function
without requiring the full src.llm_manager module.
"""

from typing import Optional


class LLMConfigError(Exception):
    """Base exception for LLM configuration errors."""

    pass


class LLMProviderError(LLMConfigError):
    """Raised when provider operations fail."""

    pass


class LLMManager:
    """Minimal LLMManager implementation for CLI functionality."""

    def __init__(self):
        """Initialize the LLM manager."""
        pass

    def create_service(
    ):
        """Create a service for the given provider."""
        return MockLLMService(provider, model, offline)


class MockLLMService:
    """Mock LLM service for testing purposes."""

    def __init__(
    ):
        self.provider = provider
        self.model = model
        self.offline = offline

    def execute(self, prompt: str, timeout: int = 30, max_tokens: int = 3) -> str:
        """Execute a prompt and return a mock response."""
        # For testing purposes, return a simple response
        if "hello" in prompt.lower():
            return "hello"
        return "mock response"


# Export the main classes
__all__ = ["LLMManager", "LLMConfigError", "LLMProviderError"]
