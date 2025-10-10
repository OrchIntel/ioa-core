""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

"""
LLM Services Stubbed Test Module for IOA Core

Tests that each LLM service provider works correctly in offline mode,
returning deterministic responses and never making network calls.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.llm_providers.factory import create_provider
from src.llm_providers.base import LLMService

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add offline service tests>


class TestServicesOfflineMode:
    """Test all services in offline mode."""
    
    def test_openai_service_offline(self):
        """Test OpenAI service in offline mode."""
        service = create_provider("openai", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("Hello world")
        assert "[OFFLINE-OPENAI]" in response
        assert "Hello world" in response
        
        # Test model info
        info = service.get_model_info()
        assert info["provider"] == "openai"
        assert info["offline"] == True
        assert info["available"] == True
    
    def test_anthropic_service_offline(self):
        """Test Anthropic service in offline mode."""
        service = create_provider("anthropic", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("Test prompt")
        assert "[OFFLINE-ANTHROPIC]" in response
        assert "Test prompt" in response
        
        # Test model info
        info = service.get_model_info()
        assert info["provider"] == "anthropic"
        assert info["offline"] == True
        assert info["available"] == True
    
    def test_xai_service_offline(self):
        """Test XAI service in offline mode."""
        service = create_provider("xai", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("Grok test")
        assert "[OFFLINE-XAI]" in response
        assert "Grok test" in response
        
        # Test model info
        info = service.get_model_info()
        assert info["provider"] == "xai"
        assert info["offline"] == True
        assert info["available"] == True
    
    def test_grok_service_offline(self):
        """Test Grok service in offline mode."""
        service = create_provider("grok", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("Grok test")
        assert "[OFFLINE-XAI]" in response  # Grok maps to XAI service
        assert "Grok test" in response
        
        # Test model info
        info = service.get_model_info()
        assert info["provider"] == "xai"
        assert info["offline"] == True
        assert info["available"] == True
    
    def test_google_service_offline(self):
        """Test Google Gemini service in offline mode."""
        service = create_provider("google", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("Gemini test")
        assert "[OFFLINE-GOOGLE]" in response
        assert "Gemini test" in response
        
        # Test model info
        info = service.get_model_info()
        assert info["provider"] == "google"
        assert info["offline"] == True
        assert info["available"] == True
    
    def test_ollama_service_offline(self):
        """Test Ollama service in offline mode."""
        service = create_provider("ollama", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("Ollama test")
        assert "[OFFLINE-OLLAMA]" in response
        assert "Ollama test" in response
        
        # Test model info
        info = service.get_model_info()
        assert info["provider"] == "ollama"
        assert info["offline"] == True
        assert info["available"] == True
    
    def test_deepseek_service_offline(self):
        """Test DeepSeek service in offline mode."""
        service = create_provider("deepseek", offline=True)
        
        assert service.offline == True
        assert service.is_available() == True
        
        # Test execution
        response = service.execute("DeepSeek test")
        assert "[OFFLINE-DEEPSEEK]" in response
        assert "DeepSeek test" in response
        
        # Test model info
        info = service.get_model_info()
        assert info["provider"] == "deepseek"
        assert info["offline"] == True
        assert info["available"] == True


class TestOfflineDeterministic:
    """Test that offline responses are deterministic."""
    
    def test_offline_response_consistency(self):
        """Test that offline responses are consistent for the same input."""
        providers = ["openai", "anthropic", "xai", "google", "ollama", "deepseek"]
        
        for provider_name in providers:
            service = create_provider(provider_name, offline=True)
            
            # Same input should give same output
            response1 = service.execute("Consistent test")
            response2 = service.execute("Consistent test")
            assert response1 == response2
            
            # Different input should give different output
            response3 = service.execute("Different test")
            assert response3 != response1
    
    def test_offline_response_format(self):
        """Test that offline responses follow expected format."""
        service = create_provider("openai", offline=True)
        
        # Test short prompt
        short_response = service.execute("Hi")
        assert short_response == "[OFFLINE-OPENAI] Hi"
        
        # Test long prompt (should be truncated)
        long_prompt = "This is a very long prompt that should be truncated to 20 characters"
        long_response = service.execute(long_prompt)
        assert long_response == "[OFFLINE-OPENAI] This is a very long ..."
    
    def test_offline_response_content(self):
        """Test that offline responses contain the expected content."""
        service = create_provider("anthropic", offline=True)
        
        test_prompts = [
            "Hello world",
            "Python programming",
            "Machine learning",
            "12345",
            "Special chars: !@#$%"
        ]
        
        for prompt in test_prompts:
            response = service.execute(prompt)
            assert "[OFFLINE-ANTHROPIC]" in response
            assert prompt[:20] in response  # First 20 chars should be included


class TestOfflineServiceBehavior:
    """Test offline service behavior and properties."""
    
    def test_offline_service_initialization(self):
        """Test that offline services initialize correctly without API keys."""
        # Test with no API key
        service = create_provider("openai", offline=True)
        assert service.api_key is None
        assert service.offline == True
        assert service.is_available() == True
        
        # Test with explicit API key (should be ignored in offline mode)
        service = create_provider("openai", api_key="sk-test123", offline=True)
        assert service.offline == True
        assert service.is_available() == True
    
    def test_offline_service_provider_info(self):
        """Test that offline services return correct provider info."""
        service = create_provider("google", offline=True)
        
        info = service.get_provider_info()
        assert info["provider"] == "google"
        assert info["offline"] == True
        assert info["requires_key"] == True
        assert info["has_key"] == False
        assert info["available"] == True
    
    def test_offline_service_string_representation(self):
        """Test string representation of offline services."""
        service = create_provider("xai", offline=True)
        
        str_repr = str(service)
        assert "xai" in str_repr
        assert "OFFLINE" in str_repr
        assert "NO_KEY" in str_repr
        
        repr_repr = repr(service)
        assert "xai" in repr_repr
        assert "offline=True" in repr_repr
    
    def test_offline_service_validation(self):
        """Test that offline services don't validate API keys."""
        service = create_provider("openai", offline=True)
        
        # Should not require API key validation in offline mode
        validation = service._validate_api_key_format("invalid-key")
        # In offline mode, validation should still work but not affect availability
        assert service.is_available() == True


class TestOfflineServiceIntegration:
    """Integration tests for offline services."""
    
    def test_multiple_offline_services(self):
        """Test creating and using multiple offline services simultaneously."""
        services = {}
        
        # Create all services in offline mode
        for provider in ["openai", "anthropic", "xai", "google", "ollama", "deepseek"]:
            services[provider] = create_provider(provider, offline=True)
        
        # Test all services
        for provider_name, service in services.items():
            assert service.offline == True
            assert service.is_available() == True
            
            # Test execution
            response = service.execute(f"Test for {provider_name}")
            assert f"[OFFLINE-{provider_name.upper()}]" in response
        
        assert len(services) == 6
    
    def test_offline_service_model_override(self):
        """Test that offline services respect model overrides."""
        service = create_provider("openai", model="gpt-3.5-turbo", offline=True)
        
        assert service.model == "gpt-3.5-turbo"
        assert service.offline == True
        
        # Model info should reflect the override
        info = service.get_model_info()
        assert info["model"] == "gpt-3.5-turbo"
    
    def test_offline_service_error_handling(self):
        """Test that offline services handle errors gracefully."""
        service = create_provider("anthropic", offline=True)
        
        # Should not raise errors for invalid inputs in offline mode
        try:
            response = service.execute("")
            assert response == "[OFFLINE-ANTHROPIC] "
        except Exception:
            pytest.fail("Offline service should not raise errors for empty input")
        
        try:
            response = service.execute(None)
            # Should handle None gracefully
            assert response is not None
        except Exception:
            pytest.fail("Offline service should not raise errors for None input")
