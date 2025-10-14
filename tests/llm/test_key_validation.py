"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import pytest
from src.llm_manager import LLMManager, LLMConfigError


class TestKeyValidation:
    """Test provider-specific API key validation."""
    
    def setup_method(self):
        """Set up test environment."""
        # PATCH: Cursor-2025-08-16 CL-ONBOARD-Provider-Key-Fix+UX <add comprehensive key validation tests>
        self.manager = LLMManager(allow_config_fallback=False)
    
    def test_openai_key_validation(self):
        """Test OpenAI API key validation patterns."""
        # Valid keys
        valid_keys = [
            "sk-123456789012345678901234567890",
            "sk-test123456789012345678901234567890",
            "sk-live123456789012345678901234567890",
            "sk-proj123456789012345678901234567890"
        ]
        
        for key in valid_keys:
            result = self.manager.validate_api_key("openai", key)
            assert result["valid"], f"Key {key} should be valid: {result}"
        
        # Invalid keys
        invalid_keys = [
            "sk-123",  # Too short
            "sk_123456789012345678901234567890",  # Wrong separator
            "123456789012345678901234567890",  # Missing prefix
            "sk-123456789012345678901234567890!"  # Invalid characters (special chars)
        ]
        
        for key in invalid_keys:
            result = self.manager.validate_api_key("openai", key)
            assert not result["valid"], f"Key {key} should be invalid: {result}"
            assert "can_force" in result
    
    def test_anthropic_key_validation(self):
        """Test Anthropic API key validation patterns."""
        # Valid keys
        valid_keys = [
            "sk-ant-123456789012345678901234567890",
            "sk-ant-abc123def456ghi789jkl012mno345"
        ]
        
        for key in valid_keys:
            result = self.manager.validate_api_key("anthropic", key)
            assert result["valid"], f"Key {key} should be valid: {result}"
        
        # Invalid keys
        invalid_keys = [
            "sk-ant-123",  # Too short
            "sk-123456789012345678901234567890",  # Missing -ant-
            "sk-ant_123456789012345678901234567890",  # Wrong separator
            "123456789012345678901234567890"  # Missing prefix
        ]
        
        for key in invalid_keys:
            result = self.manager.validate_api_key("anthropic", key)
            assert not result["valid"], f"Key {key} should be invalid: {result}"
            assert "can_force" in result
    
    def test_xai_grok_key_validation(self):
        """Test XAI/Grok API key validation patterns."""
        # Valid keys
        valid_keys = [
            "xai-123456789012345678901234567890",
            "grok_123456789012345678901234567890",
            "xai-abc123.def456-ghi789_jkl012"
        ]
        
        for key in valid_keys:
            if key.startswith("xai-"):
                result = self.manager.validate_api_key("xai", key)
                assert result["valid"], f"Key {key} should be valid for xai: {result}"
            elif key.startswith("grok_"):
                result = self.manager.validate_api_key("grok", key)
                assert result["valid"], f"Key {key} should be valid for grok: {result}"
        
        # Invalid keys
        invalid_keys = [
            "xai-123",  # Too short
            "grok_123",  # Too short
            "123456789012345678901234567890",  # Missing prefix
            "xai_123456789012345678901234567890"  # Wrong separator for xai
        ]
        
        for key in invalid_keys:
            result = self.manager.validate_api_key("xai", key)
            assert not result["valid"], f"Key {key} should be invalid: {result}"
            assert "can_force" in result
    
    def test_google_key_validation(self):
        """Test Google Gemini API key validation patterns."""
        # Valid keys
        valid_keys = [
            "AIza123456789012345678901234567890123456789",
            "AIzaabcdefghijklmnopqrstuvwxyz123456789"
        ]
        
        for key in valid_keys:
            result = self.manager.validate_api_key("google", key)
            assert result["valid"], f"Key {key} should be valid: {result}"
        
        # Invalid keys
        invalid_keys = [
            "AIza123",  # Too short (3 + 3 = 6 < 30)
            "123456789012345678901234567890123456789",  # Missing AIza prefix
            "AIza12345678901234567890123456789",  # Too short (3 + 29 = 32 < 33)
            "AIza123456789012345678901234567890123456789!"  # Too long and invalid chars
        ]
        
        for key in invalid_keys:
            result = self.manager.validate_api_key("google", key)
            assert not result["valid"], f"Key {key} should be invalid: {result}"
            assert "can_force" in result
    
    def test_ollama_no_key_required(self):
        """Test that Ollama doesn't require an API key."""
        result = self.manager.validate_api_key("ollama", "")
        assert result["valid"], "Ollama should not require a key"
        assert "local provider" in result["message"]
        
        result = self.manager.validate_api_key("ollama", "any-key")
        assert result["valid"], "Ollama should accept any key"
    
    def test_placeholder_key_detection(self):
        """Test detection of placeholder and test keys."""
        placeholder_keys = [
            "sk-ant-test-key",
            "your-api-key-here",
            "placeholder",
            "example",
            "demo",
            "sk-...",
            "sk-ant-..."
        ]
        
        for key in placeholder_keys:
            result = self.manager.validate_api_key("anthropic", key)
            assert not result["valid"], f"Key {key} should be detected as placeholder"
            assert "placeholder" in result["error"] or "test key" in result["error"]
            assert result["can_force"]
    
    def test_force_override_behavior(self):
        """Test force override behavior for invalid keys."""
        invalid_key = "invalid-key-format"
        
        # Without force
        result = self.manager.validate_api_key("anthropic", invalid_key, force=False)
        assert not result["valid"]
        assert result["can_force"]
        
        # With force (should still validate but allow override)
        result = self.manager.validate_api_key("anthropic", invalid_key, force=True)
        assert not result["valid"]  # Still invalid
        assert result["can_force"]  # But can be forced
    
    def test_empty_key_handling(self):
        """Test handling of empty or whitespace-only keys."""
        empty_keys = ["", "   ", "\n", "\t"]
        
        for key in empty_keys:
            result = self.manager.validate_api_key("anthropic", key)
            assert not result["valid"]
            assert "empty" in result["error"]
            assert not result["can_force"]  # Empty keys cannot be forced
    
    def test_unknown_provider_handling(self):
        """Test handling of unknown provider names."""
        result = self.manager.validate_api_key("unknown_provider", "any-key")
        assert not result["valid"]
        assert "Unknown provider" in result["error"]
        assert not result["can_force"]  # Unknown providers cannot be forced
    
    def test_key_trimming(self):
        """Test that keys are properly trimmed."""
        key_with_whitespace = "  sk-ant-123456789012345678901234567890  "
        result = self.manager.validate_api_key("anthropic", key_with_whitespace)
        assert result["valid"], "Key should be valid after trimming"
    
    def test_validation_result_structure(self):
        """Test that validation results have the expected structure."""
        result = self.manager.validate_api_key("anthropic", "sk-ant-123456789012345678901234567890")
        
        # Valid result should have these fields
        assert "valid" in result
        assert "message" in result
        assert "can_force" in result
        
        # Invalid result should have these fields
        invalid_result = self.manager.validate_api_key("anthropic", "invalid-key")
        assert "valid" in invalid_result
        assert "error" in invalid_result
        assert "can_force" in invalid_result
        assert "suggestion" in invalid_result
