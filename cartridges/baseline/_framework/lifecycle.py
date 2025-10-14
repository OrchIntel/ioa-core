"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class CartridgeContext:
    """Execution context provided to cartridge hooks."""

    profile: str
    dry_run: bool = False


class CartridgeHooks(Protocol):
    """Interface for cartridge lifecycle.

    Implementations can selectively provide hooks; non-implemented hooks
    should be treated as no-ops by the runner.
    """

    def pre(self, context: CartridgeContext) -> None:  # noqa: D401
        """Run before main execution."""

    def hitl(self, context: CartridgeContext) -> None:  # noqa: D401
        """Human-in-the-loop step if required."""

    def post(self, context: CartridgeContext) -> None:  # noqa: D401
        """Run after main execution."""


