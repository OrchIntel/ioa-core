""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Stub mood engine for open‑core; defines basic enums and placeholders.
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.

"""
Stub Mood Engine for IOA Core

This module provides minimal definitions to satisfy imports
when the full emotion simulation engine is not available. It defines
basic mood types and a simple data class to avoid import errors in
components that reference the mood engine. No actual mood computation
is performed in the open‑core edition.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class MoodType(Enum):
    """Minimal mood type enumeration for open‑core."""
    NEUTRAL = "neutral"


@dataclass
class MoodState:
    """Placeholder mood state used in open‑core when no mood engine is available."""
    mood_type: MoodType = MoodType.NEUTRAL
    timestamp: str = ""
    intensity: float = 0.0
    stability: float = 0.0
    color_hex: str = "#808080"
    description: str = "No mood engine available"


def get_mood_from_metrics(*args, **kwargs) -> Optional[MoodState]:
    """Stub function for mood computation.

    Always returns None to indicate that no mood state can be derived
    in the open‑core version.
    """
    return None


def create_mood_engine(*args, **kwargs) -> None:
    """Stub function for creating a mood engine instance.

    In the open‑core edition this returns None.
    """
    return None