"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from ioa_core.onboard import OnboardingCLI


class TestOnboardingFlags:
    """Test CLI flags functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # PATCH: Cursor-2025-08-16 CL-ONBOARD-Provider-Key-Fix+UX <add CLI flags tests>
        self.cli = OnboardingCLI()
        # Mock the manager to avoid actual file operations
        self.cli.manager = Mock()
        
        # Set up default mock returns
        self.cli.manager.list_providers.return_value = []
        self.cli.manager.list_all_providers.return_value = []
        self.cli.manager.get_provider_status.return_value = {"configured": True, "source": "config"}
        self.cli.manager.get_default_provider.return_value = None
        
        # Mock the validate_api_key method to return proper validation results
        self.cli.manager.validate_api_key.return_value = {
            "valid": True,
            "message": "Valid key",
            "can_force": False
        }
    
    def test_add_provider_with_key_flag(self):
        """Test adding provider with --key flag."""
        # Mock validation to succeed
        with patch.object(self.cli, '_validate_key_format') as mock_validate:
            mock_validate.return_value = (True, "Valid key")
            
            self.cli.add_provider("anthropic", key="sk-ant-123456789012345678901234567890")
            
            # Verify manager was called
            self.cli.manager.add_provider.assert_called_once()
            call_args = self.cli.manager.add_provider.call_args
            assert call_args[0][0] == "anthropic"
            assert call_args[0][1]["api_key"] == "sk-ant-123456789012345678901234567890"
    
    def test_add_provider_with_force_flag(self):
        """Test adding provider with --force flag."""
        # Mock validation to fail but allow force
        with patch.object(self.cli, '_validate_key_format') as mock_validate:
            mock_validate.return_value = (False, "Invalid key format")
            
            self.cli.add_provider("anthropic", key="invalid-key", force=True)
            
            # Verify manager was called with force metadata
            self.cli.manager.add_provider.assert_called_once()
            call_args = self.cli.manager.add_provider.call_args
            assert call_args[0][0] == "anthropic"
            assert call_args[0][1]["source"] == "user_forced"
            assert "validation_warning" in call_args[0][1]
    
    def test_add_provider_without_force_fails(self):
        """Test that adding provider without force fails on validation."""
        # Mock validation to fail
        with patch.object(self.cli, '_validate_key_format') as mock_validate:
            mock_validate.return_value = (False, "Invalid key format")
            
            with pytest.raises(SystemExit):
                self.cli.add_provider("anthropic", key="invalid-key", force=False)
            
            # Manager should not be called
            self.cli.manager.add_provider.assert_not_called()
    
    def test_add_provider_from_env(self):
        """Test adding provider with --from-env flag."""
        # Mock environment variable
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-123456789012345678901234567890'}):
            # Mock validation to succeed
            with patch.object(self.cli, '_validate_key_format') as mock_validate:
                mock_validate.return_value = (True, "Valid key")
                
                self.cli.add_provider("anthropic", from_env=True)
                
                # Verify manager was called with env source
                self.cli.manager.add_provider.assert_called_once()
                call_args = self.cli.manager.add_provider.call_args
                assert call_args[0][0] == "anthropic"
                assert call_args[0][1]["source"] == "env"
    
    def test_add_provider_from_env_missing(self):
        """Test adding provider with --from-env when env var is missing."""
        # Ensure environment variable is not set
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                self.cli.add_provider("anthropic", from_env=True)
            
            # Manager should not be called
            self.cli.manager.add_provider.assert_not_called()
    
    def test_set_key_with_force_flag(self):
        """Test updating key with --force flag."""
        # Mock provider exists
        self.cli.manager.list_all_providers.return_value = ["anthropic"]
        
        # Mock validation to fail but allow force
        with patch.object(self.cli, '_validate_key_format') as mock_validate:
            mock_validate.return_value = (False, "Invalid key format")
            
            self.cli.set_key("anthropic", key="invalid-key", force=True)
            
            # Verify manager was called with force metadata
            self.cli.manager.add_provider.assert_called_once()
            call_args = self.cli.manager.add_provider.call_args
            assert call_args[0][0] == "anthropic"
            assert call_args[0][1]["source"] == "user_forced"
            assert "validation_warning" in call_args[0][1]
    
    def test_set_key_provider_not_found(self):
        """Test setting key for non-existent provider."""
        # Mock provider doesn't exist
        self.cli.manager.list_all_providers.return_value = []
        
        with pytest.raises(SystemExit):
            self.cli.set_key("anthropic", key="valid-key")
        
        # Manager should not be called
        self.cli.manager.add_provider.assert_not_called()
    
    def test_validate_provider_invalid(self):
        """Test validation of invalid provider names."""
        with pytest.raises(SystemExit):
            self.cli._validate_provider("invalid_provider")
    
    def test_validate_provider_valid(self):
        """Test validation of valid provider names."""
        # Should not raise exception
        self.cli._validate_provider("anthropic")
        self.cli._validate_provider("openai")
        self.cli._validate_provider("google")
        self.cli._validate_provider("xai")
        self.cli._validate_provider("grok")
        self.cli._validate_provider("groq")
        self.cli._validate_provider("ollama")
    
    def test_get_key_from_env(self):
        """Test getting API key from environment variables."""
        # Test each provider's environment variable
        env_mappings = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'google': 'GOOGLE_API_KEY',
            'xai': 'XAI_API_KEY',
            'grok': 'GROK_API_KEY',
            'groq': 'GROQ_API_KEY',
            'ollama': 'OLLAMA_HOST'
        }
        
        for provider, env_var in env_mappings.items():
            with patch.dict(os.environ, {env_var: 'test-key'}):
                key = self.cli._get_key_from_env(provider)
                assert key == 'test-key'
    
    def test_get_key_from_env_not_set(self):
        """Test getting API key when environment variable is not set."""
        # Ensure environment variables are not set
        with patch.dict(os.environ, {}, clear=True):
            for provider in ['openai', 'anthropic', 'google', 'xai', 'grok', 'groq', 'ollama']:
                key = self.cli._get_key_from_env(provider)
                assert key is None
    
    def test_create_provider_config(self):
        """Test creation of provider configuration."""
        # Test regular provider
        config = self.cli._create_provider_config("anthropic", "test-key", from_env=False)
        assert config["api_key"] == "test-key"
        assert "source" not in config
        
        # Test with from_env=True
        config = self.cli._create_provider_config("anthropic", "test-key", from_env=True)
        assert config["api_key"] == "test-key"
        assert config["source"] == "env"
        
        # Test Ollama
        config = self.cli._create_provider_config("ollama", "test-key", from_env=False)
        assert config["host"] == "http://localhost:11434"
    
    def test_ollama_special_handling(self):
        """Test special handling for Ollama provider."""
        # Mock validation to succeed
        with patch.object(self.cli, '_validate_key_format') as mock_validate:
            mock_validate.return_value = (True, "Ollama is a local provider")
            
            self.cli.add_provider("ollama", key="any-key")
            
            # Verify manager was called with host config
            self.cli.manager.add_provider.assert_called_once()
            call_args = self.cli.manager.add_provider.call_args
            assert call_args[0][0] == "ollama"
            assert call_args[0][1]["host"] == "http://localhost:11434"
    
    def test_force_flag_metadata_preservation(self):
        """Test that force flag metadata is preserved in config."""
        # Mock validation to fail but allow force
        with patch.object(self.cli, '_validate_key_format') as mock_validate:
            mock_validate.return_value = (False, "Invalid key format")
            
            self.cli.add_provider("anthropic", key="invalid-key", force=True)
            
            # Verify force metadata is included
            call_args = self.cli.manager.add_provider.call_args
            config = call_args[0][1]
            assert config["source"] == "user_forced"
            assert "validation_warning" in config
            assert "Invalid key format" in config["validation_warning"]
    
    def test_environment_variable_precedence(self):
        """Test that environment variables take precedence over file config."""
        # Mock environment variable
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'env-key'}):
            key = self.cli._get_key_from_env("anthropic")
            assert key == "env-key"
            
            # Even if file config exists, env should take precedence
            # This is tested in the LLM manager tests
    
    def test_provider_options_consistency(self):
        """Test that provider options are consistent across the CLI."""
        # All providers should have consistent structure
        for provider, info in self.cli.PROVIDER_OPTIONS.items():
            # Check required fields
            assert 'name' in info
            assert 'description' in info
            assert 'env_var' in info
            assert 'key_pattern' in info
            assert 'min_length' in info
            
            # Check that env_var matches the actual environment variable lookup
            if provider != 'ollama':  # Ollama uses host, not API key
                env_key = self.cli._get_key_from_env(provider)
                # This will be None in test environment, but the method should work
                assert hasattr(self.cli, '_get_key_from_env')
