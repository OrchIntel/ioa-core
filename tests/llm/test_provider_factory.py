""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

"""
Provider Factory Test Module for IOA Core

Tests the provider factory functionality including precedence-based API key resolution,
offline mode support, and proper provider instantiation for all supported providers.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.llm_providers.factory import create_provider, list_available_providers
from src.llm_providers.base import LLMService

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add comprehensive factory tests>


class TestProviderFactory:
    """Test provider factory functionality."""
    
    def test_list_available_providers(self):
        """Test that all expected providers are listed."""
        providers = list_available_providers()
        
        expected_providers = ["openai", "anthropic", "xai", "grok", "google", "ollama", "deepseek"]
        for provider in expected_providers:
            assert provider in providers
        
        # Check provider details
        assert providers["openai"]["name"] == "OpenAI"
        assert providers["anthropic"]["name"] == "Anthropic"
        assert providers["ollama"]["requires_key"] == False
        assert providers["openai"]["requires_key"] == True
    
    def test_create_provider_openai(self):
        """Test creating OpenAI provider."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test12345678901234567890"}):
            service = create_provider("openai", model="gpt-4")
            
            assert service.provider == "openai"
            assert service.model == "gpt-4"
            assert service.api_key == "sk-test12345678901234567890"
            assert service.offline == False
    
    def test_create_provider_anthropic(self):
        """Test creating Anthropic provider."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test12345678901234567890"}):
            service = create_provider("anthropic", model="claude-3-sonnet")
            
            assert service.provider == "anthropic"
            assert service.model == "claude-3-sonnet"
            assert service.api_key == "sk-ant-test12345678901234567890"
            assert service.offline == False
    
    def test_create_provider_xai(self):
        """Test creating XAI provider."""
        with patch.dict(os.environ, {"XAI_API_KEY": "xai-test12345678901234567890"}):
            service = create_provider("xai", model="grok-1")
            
            assert service.provider == "xai"
            assert service.model == "grok-1"
            assert service.api_key == "xai-test12345678901234567890"
            assert service.offline == False
    
    def test_create_provider_grok(self):
        """Test creating Grok provider with GROK_API_KEY."""
        with patch.dict(os.environ, {"GROK_API_KEY": "grok_test12345678901234567890"}):
            service = create_provider("grok", model="grok-1")
            
            assert service.provider == "xai"  # Grok maps to XAI service
            assert service.model == "grok-1"
            assert service.api_key == "grok_test12345678901234567890"
            assert service.offline == False
    
    def test_create_provider_google(self):
        """Test creating Google Gemini provider."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "AIza-test123456789012345678901234567890"}):
            service = create_provider("google", model="gemini-1.5-pro")
            
            assert service.provider == "google"
            assert service.model == "gemini-1.5-pro"
            assert service.api_key == "AIza-test123456789012345678901234567890"
            assert service.offline == False
    
    def test_create_provider_ollama(self):
        """Test creating Ollama provider."""
        with patch.dict(os.environ, {"OLLAMA_HOST": "http://localhost:11434"}):
            service = create_provider("ollama", model="llama3")
            
            assert service.provider == "ollama"
            assert service.model == "llama3"
            assert service.api_key is None  # Ollama doesn't need API key
            assert service.offline == False
    
    def test_create_provider_deepseek(self):
        """Test creating DeepSeek provider."""
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test12345678901234567890"}):
            service = create_provider("deepseek", model="deepseek-coder")
            
            assert service.provider == "deepseek"
            assert service.model == "deepseek-coder"
            assert service.api_key == "sk-test12345678901234567890"
            assert service.offline == False
    
    def test_create_provider_offline_mode(self):
        """Test creating provider in offline mode."""
        service = create_provider("openai", offline=True)
        
        assert service.provider == "openai"
        assert service.offline == True
        assert service.is_available() == True
    
    def test_create_provider_offline_env_var(self):
        """Test offline mode via environment variable."""
        with patch.dict(os.environ, {"IOA_OFFLINE": "true"}):
            service = create_provider("anthropic")
            
            assert service.offline == True
            assert service.is_available() == True
    
    def test_create_provider_explicit_key_precedence(self):
        """Test that explicit key takes precedence over environment."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env12345678901234567890"}):
            explicit_key = "sk-explicit12345678901234567890"
            service = create_provider("openai", api_key=explicit_key)
            
            assert service.api_key == explicit_key
    
    def test_create_provider_config_fallback(self):
        """Test config file fallback for API keys."""
        config_dir = Path("/tmp/test_config")
        config_file = config_dir / "llm.json"
        
        # Create test config
        config_dir.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            import json
            json.dump({
                "providers": {
                    "openai": {
                        "api_key": "sk-config12345678901234567890"
                    }
                }
            }, f)
        
        try:
            # No env var, should fall back to config
            with patch.dict(os.environ, {}, clear=True):
                service = create_provider("openai", config_dir=config_dir)
                assert service.api_key == "sk-config12345678901234567890"
        finally:
            # Cleanup
            config_file.unlink()
            config_dir.rmdir()
    
    def test_create_provider_no_key_available(self):
        """Test creating provider when no key is available."""
        with patch.dict(os.environ, {}, clear=True):
            service = create_provider("openai")
            
            assert service.api_key is None
            assert service.is_available() == False
    
    def test_create_provider_ollama_no_key_required(self):
        """Test that Ollama works without API key."""
        with patch.dict(os.environ, {}, clear=True):
            service = create_provider("ollama")
            
            assert service.api_key is None
            # Ollama doesn't need API key, but needs host to be available
            # When no host is provided, it's not available (offline mode would work)
            assert service.is_available() == False
    
    def test_create_provider_unknown_provider(self):
        """Test that unknown provider raises error."""
        with pytest.raises(Exception, match="Unknown provider"):
            create_provider("unknown_provider")
    
    def test_create_provider_with_model_override(self):
        """Test creating provider with custom model."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test12345678901234567890"}):
            service = create_provider("openai", model="gpt-3.5-turbo")
            
            assert service.model == "gpt-3.5-turbo"
    
    def test_create_provider_default_models(self):
        """Test that providers use correct default models."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test12345678901234567890"}):
            service = create_provider("openai")
            assert service.model == "gpt-4"
        
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test12345678901234567890"}):
            service = create_provider("anthropic")
            assert service.model == "claude-3-sonnet"
        
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "AIza-test123456789012345678901234567890"}):
            service = create_provider("google")
            assert service.model == "gemini-1.5-flash"  # Actual default model
    
    def test_create_provider_offline_execution(self):
        """Test that offline providers return deterministic responses."""
        service = create_provider("openai", offline=True)
        
        response1 = service.execute("Hello world")
        response2 = service.execute("Hello world")
        
        assert response1 == response2
        assert "[OFFLINE-OPENAI]" in response1
        assert "Hello world" in response1
    
    def test_create_provider_offline_model_info(self):
        """Test that offline providers return valid model info."""
        service = create_provider("anthropic", offline=True)
        
        info = service.get_model_info()
        assert info["provider"] == "anthropic"
        assert info["offline"] == True
        assert info["available"] == True


class TestProviderFactoryIntegration:
    """Integration tests for provider factory."""
    
    def test_provider_chain_creation(self):
        """Test creating multiple providers in sequence."""
        providers = []
        
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test12345678901234567890",
            "ANTHROPIC_API_KEY": "sk-ant-test12345678901234567890"
        }):
            providers.append(create_provider("openai"))
            providers.append(create_provider("anthropic"))
            providers.append(create_provider("ollama"))  # No key needed
        
        assert len(providers) == 3
        assert all(isinstance(p, LLMService) for p in providers)
        assert providers[0].provider == "openai"
        assert providers[1].provider == "anthropic"
        assert providers[2].provider == "ollama"
    
    def test_provider_offline_chain(self):
        """Test creating multiple offline providers."""
        providers = []
        
        for provider_name in ["openai", "anthropic", "google", "xai", "ollama", "deepseek"]:
            service = create_provider(provider_name, offline=True)
            providers.append(service)
            
            # Test offline execution
            response = service.execute("Test prompt")
            assert "[OFFLINE-" in response
            assert service.offline == True
        
        assert len(providers) == 6
        assert all(p.offline for p in providers)
