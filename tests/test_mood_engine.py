"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
Tests for the open‑core mood engine stub.

Ensures that stub functions are importable and return expected placeholder values.
"""

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR.parent / 'src'
sys.path.insert(0, str(SRC_DIR))

from mood_engine import MoodType, MoodState, get_mood_from_metrics  # type: ignore  # noqa


def test_stub_mood_engine():
    # Ensure the NEUTRAL mood type exists
    assert MoodType.NEUTRAL.name == 'NEUTRAL'
    # Ensure get_mood_from_metrics returns None for stub
    assert get_mood_from_metrics(0.5, 0.5) is None
    # The MoodState dataclass should instantiate without error
    state = MoodState()
    assert state.mood_type == MoodType.NEUTRAL