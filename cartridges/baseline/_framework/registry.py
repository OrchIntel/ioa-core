"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional


@dataclass(frozen=True)
class CartridgeInfo:
    """Metadata describing a registered cartridge."""

    name: str
    description: str


class CartridgeRegistry:
    """In-memory registry for available cartridges.

    This simple registry can be extended later with entrypoint-based discovery.
    """

    def __init__(self) -> None:
        self._cartridges: Dict[str, CartridgeInfo] = {}
        self._doctors: Dict[str, Callable[[], bool]] = {}

    def register(
        self,
        info: CartridgeInfo,
        doctor: Optional[Callable[[], bool]] = None,
    ) -> None:
        if info.name in self._cartridges:
            raise ValueError(f"Cartridge already registered: {info.name}")
        self._cartridges[info.name] = info
        if doctor is not None:
            self._doctors[info.name] = doctor

    def get(self, name: str) -> CartridgeInfo:
        try:
            return self._cartridges[name]
        except KeyError as error:
            raise KeyError(f"Unknown cartridge: {name}") from error

    def doctor(self, name: str) -> bool:
        func = self._doctors.get(name)
        if func is None:
            # doctor hook optional; absence means non-failing
            return True
        return bool(func())

    def list(self) -> Dict[str, CartridgeInfo]:
        return dict(self._cartridges)


_GLOBAL_REGISTRY: Optional[CartridgeRegistry] = None


def get_registry() -> CartridgeRegistry:
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = CartridgeRegistry()
    return _GLOBAL_REGISTRY


