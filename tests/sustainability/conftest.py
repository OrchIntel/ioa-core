""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

import os
import pytest

@pytest.fixture(autouse=True)
def sustainability_mode(monkeypatch):
    if os.getenv("SUSTAINABILITY_BACKEND", "mock") == "mock":
        monkeypatch.setenv("CARBONTRACKER_FAKE", "1")
