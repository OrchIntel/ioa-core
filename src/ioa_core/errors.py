# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



Custom exception classes for IOA Core CLI operations.

Provides specific exception types for handling CLI-specific errors
like non-interactive environments and user cancellations.
"""

"""Errors module."""


class NonInteractiveError(Exception):
    """Raised when an interactive operation is attempted in a non-interactive environment."""

    def __init__(
        self,
        message: str = "Interactive operation not allowed in non-interactive environment",
    ):
        self.message = message
        super().__init__(self.message)


class UserAbort(Exception):
    """Raised when a user cancels an operation."""

    def __init__(self, message: str = "Operation cancelled by user"):
        self.message = message
        super().__init__(self.message)


class CLIValidationError(Exception):
    """Raised when CLI input validation fails."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class ProviderNotFoundError(Exception):
    """Raised when a requested LLM provider is not found."""

    def __init__(self, provider: str):
        self.provider = provider
        self.message = f"Provider '{provider}' not found"
        super().__init__(self.message)


class ConfigurationError(Exception):
    """Raised when there's a configuration-related error."""

    def __init__(self, message: str, config_path: str = None):
        self.message = message
        self.config_path = config_path
        super().__init__(self.message)
