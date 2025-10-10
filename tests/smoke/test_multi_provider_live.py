""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import os
import pytest

from src.llm_providers.openai_service import OpenAIService
from src.llm_providers.deepseek_service import DeepSeekService
from src.llm_providers.gemini_service import GeminiService


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Missing OPENAI_API_KEY")
def test_live_openai_hello_world():
    svc = OpenAIService(api_key=os.environ.get("OPENAI_API_KEY"), model="gpt-4o-mini")
    resp = svc.execute("Say 'hello world' in one word")
    assert isinstance(resp, str) and len(resp) > 0


@pytest.mark.skipif(not os.getenv("DEEPSEEK_API_KEY"), reason="Missing DEEPSEEK_API_KEY")
def test_live_deepseek_hello_world(monkeypatch):
    # This test calls network; leave unpatched for real live smoke
    svc = DeepSeekService(api_key=os.environ.get("DEEPSEEK_API_KEY"))
    resp = svc.execute("hello world")
    assert isinstance(resp, str) and len(resp) > 0


@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Missing GOOGLE_API_KEY")
def test_live_gemini_hello_world():
    svc = GeminiService(api_key=os.environ.get("GOOGLE_API_KEY"))
    resp = svc.execute("hello world")
    assert isinstance(resp, str) and len(resp) > 0


