""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

"""
LLM Connectivity Smoke Test Module for IOA Core

Tests LLM provider connectivity with support for both offline and live testing.
Live tests are marked with @pytest.mark.live and skipped by default unless
--live flag is provided and relevant API keys exist.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.llm_providers.factory import create_provider


def is_ollama_available():
    """Check if Ollama service is available."""
    try:
        service = create_provider("ollama", offline=False)
        return service.is_available()
    except Exception:
        return False

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <update smoke tests for multi-provider support>


class TestLLMConnectivityOffline:
    """Test LLM connectivity in offline mode (default)."""
    
    def test_openai_offline_connectivity(self):
        """Test OpenAI connectivity in offline mode."""
        service = create_provider("openai", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("Hello world")
        assert "[OFFLINE-OPENAI]" in response
        assert "Hello world" in response
    
    def test_anthropic_offline_connectivity(self):
        """Test Anthropic connectivity in offline mode."""
        service = create_provider("anthropic", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("Test prompt")
        assert "[OFFLINE-ANTHROPIC]" in response
        assert "Test prompt" in response
    
    def test_xai_offline_connectivity(self):
        """Test XAI connectivity in offline mode."""
        service = create_provider("xai", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("Grok test")
        assert "[OFFLINE-XAI]" in response
        assert "Grok test" in response
    
    def test_google_offline_connectivity(self):
        """Test Google Gemini connectivity in offline mode."""
        service = create_provider("google", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("Gemini test")
        assert "[OFFLINE-GOOGLE]" in response
        assert "Gemini test" in response
    
    def test_ollama_offline_connectivity(self):
        """Test Ollama connectivity in offline mode."""
        service = create_provider("ollama", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("Ollama test")
        assert "[OFFLINE-OLLAMA]" in response
        assert "Ollama test" in response
    
    def test_deepseek_offline_connectivity(self):
        """Test DeepSeek connectivity in offline mode."""
        service = create_provider("deepseek", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("DeepSeek test")
        assert "[OFFLINE-DEEPSEEK]" in response
        assert "DeepSeek test" in response


@pytest.mark.slow
class TestLLMConnectivityLive:
    """Test LLM connectivity in live mode (requires API keys)."""
    
    @pytest.mark.live
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No OPENAI_API_KEY found")
    def test_openai_live_connectivity(self):
        """Test OpenAI connectivity with live API call."""
        service = create_provider("openai", offline=False)
        
        assert service.offline == False
        assert service.is_available() == True
        
        # Test execution with minimal tokens
        response = service.execute("Hello", max_tokens=1)
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.live
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="No ANTHROPIC_API_KEY found")
    def test_anthropic_live_connectivity(self):
        """Test Anthropic connectivity with live API call."""
        service = create_provider("anthropic", offline=False)
        
        assert service.offline == False
        assert service.is_available() == True
        
        # Test execution with minimal tokens
        response = service.execute("Hello", max_tokens=1)
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.live
    @pytest.mark.skipif(not (os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")), reason="No XAI_API_KEY or GROK_API_KEY found")
    def test_xai_live_connectivity(self):
        """Test XAI connectivity with live API call."""
        service = create_provider("xai", offline=False)
        
        assert service.offline == False
        assert service.is_available() == True
        
        # Test execution with minimal tokens
        response = service.execute("Hello", max_tokens=1)
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.live
    @pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="No GOOGLE_API_KEY found")
    def test_google_live_connectivity(self):
        """Test Google Gemini connectivity with live API call."""
        service = create_provider("google", offline=False)
        
        assert service.offline == False
        assert service.is_available() == True
        
        # Test execution with minimal tokens
        response = service.execute("Hello", max_output_tokens=1)
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.live
    @pytest.mark.skipif(not os.getenv("DEEPSEEK_API_KEY"), reason="No DEEPSEEK_API_KEY found")
    def test_deepseek_live_connectivity(self):
        """Test DeepSeek connectivity with live API call."""
        service = create_provider("deepseek", offline=False)
        
        assert service.offline == False
        assert service.is_available() == True
        
        # Test execution with minimal tokens
        response = service.execute("Hello", max_tokens=1)
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.live
    @pytest.mark.skipif(not is_ollama_available(), reason="Ollama service not available")
    def test_ollama_live_connectivity(self):
        """Test Ollama connectivity with live API call."""
        service = create_provider("ollama", offline=False)
        
        assert service.offline == False
        assert service.is_available() == True
        
        # Test execution with minimal tokens
        response = service.execute("Hello", max_tokens=1)
        assert response is not None
        assert len(response) > 0


class TestLLMConnectivityIntegration:
    """Integration tests for LLM connectivity."""
    
    def test_all_providers_offline(self):
        """Test all providers in offline mode simultaneously."""
        providers = ["openai", "anthropic", "xai", "google", "ollama", "deepseek"]
        services = {}
        
        for provider in providers:
            service = create_provider(provider, offline=True)
            services[provider] = service
            
            assert service.offline == True
            assert service.is_available() == True
        
        # Test all services
        for provider_name, service in services.items():
            response = service.execute(f"Test for {provider_name}")
            assert f"[OFFLINE-{provider_name.upper()}]" in response
        
        assert len(services) == 6
    
    def test_provider_fallback_behavior(self):
        """Test provider fallback behavior when keys are missing."""
        # Test with no environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Should create offline services
            service = create_provider("openai", offline=True)
            assert service.offline == True
            assert service.is_available() == True
            
            # Should handle missing keys gracefully
            service = create_provider("openai", offline=False)
            assert service.is_available() == False
    
    def test_ollama_no_key_required(self):
        """Test that Ollama works without API key."""
        with patch.dict(os.environ, {}, clear=True):
            service = create_provider("ollama", offline=False)
            # Ollama doesn't require API key, so it should be available
            # (assuming Ollama service is running)
            assert service.api_key is None


class TestLLMConnectivityErrorHandling:
    """Test error handling in LLM connectivity."""
    
    def test_service_creation_failure(self):
        """Test handling of service creation failures."""
        with pytest.raises(Exception, match="Unknown provider"):
            create_provider("unknown_provider")
    
    def test_offline_execution_consistency(self):
        """Test that offline execution is consistent."""
        service = create_provider("openai", offline=True)
        
        # Same input should give same output
        response1 = service.execute("Consistent test")
        response2 = service.execute("Consistent test")
        assert response1 == response2
        
        # Different input should give different output
        response3 = service.execute("Different test")
        assert response3 != response1
    
    def test_offline_response_format(self):
        """Test that offline responses follow expected format."""
        service = create_provider("anthropic", offline=True)
        
        # Test short prompt
        short_response = service.execute("Hi")
        assert short_response == "[OFFLINE-ANTHROPIC] Hi"
        
        # Test long prompt (should be truncated)
        long_prompt = "This is a very long prompt that should be truncated to 20 characters"
        long_response = service.execute(long_prompt)
        assert long_response == "[OFFLINE-ANTHROPIC] This is a very long ..."


class TestLLMConnectivityConfiguration:
    """Test LLM connectivity configuration options."""
    
    def test_model_override(self):
        """Test that model overrides work correctly."""
        service = create_provider("openai", model="gpt-3.5-turbo", offline=True)
        assert service.model == "gpt-3.5-turbo"
        
        service = create_provider("anthropic", model="claude-3-haiku", offline=True)
        assert service.model == "claude-3-haiku"
    
    def test_offline_mode_override(self):
        """Test that offline mode can be explicitly set."""
        # Test explicit offline
        service = create_provider("openai", offline=True)
        assert service.offline == True
        
        # Test explicit online
        service = create_provider("openai", offline=False)
        assert service.offline == False
    
    def test_environment_offline_mode(self):
        """Test that IOA_OFFLINE environment variable works."""
        with patch.dict(os.environ, {"IOA_OFFLINE": "true"}):
            service = create_provider("openai")
            assert service.offline == True
        
        with patch.dict(os.environ, {"IOA_OFFLINE": "false"}):
            service = create_provider("openai")
            assert service.offline == False
