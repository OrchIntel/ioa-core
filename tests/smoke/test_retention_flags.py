""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import os
import types
import pytest

from src.llm_providers.openai_service import OpenAIService
from src.llm_providers.deepseek_service import DeepSeekService
from src.llm_providers.xai_service import XAIService
from src.llm_providers.gemini_service import GeminiService


def _has_key(env_var: str) -> bool:
    return bool(os.environ.get(env_var))


@pytest.mark.skipif(not _has_key("OPENAI_API_KEY"), reason="No OpenAI API key")
def test_openai_retention_flags(monkeypatch):
    svc = OpenAIService(api_key=os.environ.get("OPENAI_API_KEY"), model="gpt-4o-mini")

    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        class R:
            choices = [types.SimpleNamespace(message=types.SimpleNamespace(content="ok"))]
        return R()

    # Patch underlying client
    import openai as openai_pkg
    monkeypatch.setattr(openai_pkg.ChatCompletion, "create", fake_create)

    svc.execute("hello")
    meta = captured.get("metadata", {})
    assert meta.get("data_retention") is False
    assert meta.get("retain") is False
    # Headers are passed separately
    headers = captured.get("headers", {})
    assert headers.get("X-Data-Retention-Opt-Out") == "true"


@pytest.mark.skipif(not _has_key("DEEPSEEK_API_KEY"), reason="No DeepSeek API key")
def test_deepseek_retention_flags(monkeypatch):
    svc = DeepSeekService(api_key=os.environ.get("DEEPSEEK_API_KEY"))

    captured = {"json": None, "headers": None}

    class FakeResp:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": "ok"}}]}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["json"] = json
        captured["headers"] = headers
        return FakeResp()

    import requests as req
    monkeypatch.setattr(req, "post", fake_post)

    svc.execute("hello")
    assert captured["json"]["metadata"]["data_retention"] is False
    assert captured["json"]["metadata"]["retain"] is False
    assert captured["headers"]["X-Data-Retention-Opt-Out"] == "true"


@pytest.mark.skipif(not _has_key("XAI_API_KEY") and not _has_key("GROK_API_KEY"), reason="No XAI/Grok API key")
def test_xai_retention_flags(monkeypatch):
    api_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    svc = XAIService(api_key=api_key)

    captured = {"json": None, "headers": None}

    class FakeResp:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": "ok"}}]}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["json"] = json
        captured["headers"] = headers
        return FakeResp()

    import requests as req
    monkeypatch.setattr(req, "post", fake_post)

    svc.execute("hello")
    assert captured["json"]["metadata"]["data_retention"] is False
    assert captured["json"]["metadata"]["retain"] is False
    assert captured["headers"]["X-Data-Retention-Opt-Out"] == "true"


@pytest.mark.skipif(not _has_key("GOOGLE_API_KEY"), reason="No Google API key")
def test_gemini_retention_flags(monkeypatch):
    svc = GeminiService(api_key=os.environ.get("GOOGLE_API_KEY"))

        def generate_content(self, prompt, request_options=None):
            class R:
                text = "ok"
            # Assert header passed via request_options
            assert request_options and request_options.get("headers", {}).get("X-Data-Retention-Opt-Out") == "true"
            return R()

    class FakeGenAI:
        def GenerativeModel(self, model, generation_config=None):
            return FakeModel()

    import google.generativeai as genai
    monkeypatch.setattr(genai, "GenerativeModel", FakeGenAI().GenerativeModel)

    svc.execute("hello")


