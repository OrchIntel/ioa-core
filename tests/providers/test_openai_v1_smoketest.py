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
from unittest.mock import patch, Mock


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True)
def test_openai_service_uses_v1_client_signature():
    """Ensure we call client.chat.completions.create with v1 SDK pattern."""
    from ioa_core.llm_adapter import OpenAIService

    with patch('openai.OpenAI') as mock_client_cls:
        mock_client = Mock()
        mock_client_cls.return_value = mock_client

        # Mock response structure similar to v1
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "ok"
        mock_choice.message = mock_message
        mock_resp = Mock()
        mock_resp.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_resp

        svc = OpenAIService(model="gpt-4o-mini")
        out = svc.execute("ping")
        assert out == "ok"
        mock_client.chat.completions.create.assert_called_once()


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-bad"}, clear=True)
def test_invalid_key_yields_captured_error(monkeypatch):
    """Invalid API key should surface as LLMAuthenticationError or LLMAPIError without secrets leaked."""
    from ioa_core.llm_adapter import OpenAIService, LLMAuthenticationError, LLMAPIError

    class FakeAuthError(Exception):
        pass

    # Simulate SDK raising AuthenticationError on create
    fake_openai = Mock()
    fake_client = Mock()
    def raise_auth(*args, **kwargs):
        raise FakeAuthError("Incorrect API key provided")
    fake_client.chat.completions.create.side_effect = raise_auth
    fake_openai.OpenAI.return_value = fake_client

    with patch.dict('sys.modules', {'openai': fake_openai}):
        svc = OpenAIService(model="gpt-4o-mini")
        with pytest.raises((LLMAuthenticationError, LLMAPIError, Exception)) as ei:
            svc.execute("ping")
        msg = str(ei.value)
        assert "key" in msg.lower()
        assert "sk-" not in msg  # ensure no secret leakage pattern


def test_openai_payload_has_no_metadata_booleans(monkeypatch):
    """Fail if any metadata.* boolean keys are passed in payload to v1 client."""
    from ioa_core.llm_adapter import OpenAIService
    with patch('openai.OpenAI') as mock_client_cls:
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
        # Prepare a benign response
        mock_choice = Mock(); mock_msg = Mock(); mock_msg.content = "ok"; mock_choice.message = mock_msg
        mock_resp = Mock(); mock_resp.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_resp

        svc = OpenAIService(model="gpt-4o-mini")
        _ = svc.execute("ping")
        # Inspect the call kwargs
        _, kwargs = mock_client.chat.completions.create.call_args
        forbidden = [k for k, v in kwargs.items() if k.startswith('metadata.') and isinstance(v, bool)]
        assert not forbidden, f"Forbidden metadata booleans found: {forbidden}"


