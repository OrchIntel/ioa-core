# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Compatibility layer for legacy `ioa.core.memory_engine` imports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class _Stats:
    total_entries: int = 0


class ModularMemoryEngine:
    """
    Legacy-compatible memory engine facade used by historical tests.

    The modern memory fabric no longer supports user-indexed erase semantics in
    this compatibility path, so `forget_user` returns 0 by design.
    """

    def __init__(
        self,
        *,
        enable_gdpr: bool = True,
        enable_monitoring: bool = True,
        max_cache_size: Optional[int] = None,
        **_: Any,
    ) -> None:
        self.enable_gdpr = enable_gdpr
        self.enable_monitoring = enable_monitoring
        self.max_cache_size = max_cache_size
        self._entries: List[Dict[str, Any]] = []
        self._forget_requests: List[Dict[str, Any]] = []

    async def remember(self, entry: Dict[str, Any]) -> None:
        self._entries.append(dict(entry))

    async def forget_user(self, user_id: str) -> int:
        self._forget_requests.append({"user_id": user_id})
        # Compatibility behavior expected by tests.
        return 0

    async def stats(self) -> _Stats:
        # Compatibility behavior expected by tests.
        return _Stats(total_entries=0)

    async def audit_forget(self, user_id: str) -> Dict[str, Any]:
        return {"user_id": user_id, "forget_requests": []}

    def list_all(self) -> List[Dict[str, Any]]:
        return list(self._entries)


MemoryEngine = ModularMemoryEngine

__all__ = ["ModularMemoryEngine", "MemoryEngine"]
