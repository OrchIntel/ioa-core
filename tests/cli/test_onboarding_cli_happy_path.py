"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
Test onboarding CLI happy path functionality.

Tests the interactive setup process, file creation, and command-line
operations for LLM provider management.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# PATCH: Cursor-2025-08-15 CL-LLM-Manager Onboarding CLI tests
from ioa_core.onboard import OnboardingCLI


class TestOnboardingCLIHappyPath:
    """Test onboarding CLI happy path scenarios."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / ".ioa" / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock HOME directory
        self.patched_home = patch.dict(os.environ, {"HOME": self.temp_dir})
        self.patched_home.start()
    
    def teardown_method(self):
        """Clean up test environment."""
        self.patched_home.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_initialization(self):
        """Test CLI initialization."""
        cli = OnboardingCLI()
        assert cli.manager is not None
        assert hasattr(cli, 'PROVIDER_OPTIONS')
        assert 'openai' in cli.PROVIDER_OPTIONS
        assert 'anthropic' in cli.PROVIDER_OPTIONS
    
    def test_provider_options_structure(self):
        """Test that provider options have correct structure."""
        cli = OnboardingCLI()
        
        for provider, info in cli.PROVIDER_OPTIONS.items():
            assert 'name' in info
            assert 'description' in info
            assert 'fields' in info
            assert 'defaults' in info
            assert isinstance(info['fields'], list)
            assert isinstance(info['defaults'], dict)
    
    def test_non_interactive_setup_success(self):
        """Test non-interactive setup with valid parameters."""
        cli = OnboardingCLI()
        
        # Mock the manager to avoid actual file operations
        mock_manager = MagicMock()
        cli.manager = mock_manager
        
        # Test successful setup
        cli._non_interactive_setup("openai", "sk-test123")
        
        # Verify manager was called correctly
        mock_manager.add_provider.assert_called_once_with("openai", {"api_key": "sk-test123"})
        mock_manager.set_default_provider.assert_called_once_with("openai")
    
    def test_non_interactive_setup_ollama(self):
        """Test non-interactive setup with Ollama provider."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        cli.manager = mock_manager
        
        # Test Ollama setup (host instead of api_key)
        cli._non_interactive_setup("ollama", "http://localhost:11435")
        
        # Verify manager was called with host
        mock_manager.add_provider.assert_called_once_with("ollama", {"host": "http://localhost:11435"})
        mock_manager.set_default_provider.assert_called_once_with("ollama")
    
    def test_non_interactive_setup_missing_params(self):
        """Test non-interactive setup with missing parameters."""
        cli = OnboardingCLI()
        
        # Test with missing provider
        with pytest.raises(SystemExit):
            cli._non_interactive_setup("", "sk-test123")
        
        # Test with missing key
        with pytest.raises(SystemExit):
            cli._non_interactive_setup("openai", "")
    
    def test_non_interactive_setup_invalid_provider(self):
        """Test non-interactive setup with invalid provider."""
        cli = OnboardingCLI()
        
        # Test with unsupported provider
        with pytest.raises(SystemExit):
            cli._non_interactive_setup("unsupported", "sk-test123")
    
    def test_provider_selection_all(self):
        """Test selecting all providers."""
        cli = OnboardingCLI()
        
        # Mock input to return "all"
        with patch('builtins.input', return_value="all"):
            selected = cli._select_providers()
            
            # Should return all available providers
            expected_providers = ['openai', 'anthropic', 'google', 'groq', 'ollama']
            assert selected == expected_providers
    
    def test_provider_selection_specific(self):
        """Test selecting specific providers."""
        cli = OnboardingCLI()
        
        # Mock input to return specific numbers
        with patch('builtins.input', return_value="1,3"):
            selected = cli._select_providers()
            
            # Should return selected providers
            expected_providers = ['openai', 'google']
            assert selected == expected_providers
    
    def test_provider_selection_invalid_input(self):
        """Test provider selection with invalid input."""
        cli = OnboardingCLI()
        
        # Mock input to return invalid input, then valid
        with patch('builtins.input', side_effect=["invalid", "1,2"]):
            selected = cli._select_providers()
            
            # Should handle invalid input gracefully
            expected_providers = ['openai', 'anthropic']
            assert selected == expected_providers
    
    def test_provider_configuration(self):
        """Test provider configuration process."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        cli.manager = mock_manager
        
        # Mock input for provider configuration
        inputs = [
            "sk-test123",  # API key
            "gpt-4o-mini", # Model
            ""             # Base URL (skip)
        ]
        
        with patch('builtins.input', side_effect=inputs):
            cli._configure_provider("openai")
            
            # Verify manager was called with correct config
            mock_manager.add_provider.assert_called_once_with("openai", {
                "api_key": "sk-test123",
                "model": "gpt-4o-mini"
            })
    
    def test_provider_configuration_skip_on_no_key(self):
        """Test that provider configuration is skipped when no API key is provided."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        cli.manager = mock_manager
        
        # Mock input to skip API key
        with patch('builtins.input', return_value=""):
            cli._configure_provider("openai")
            
            # Verify manager was not called
            mock_manager.add_provider.assert_not_called()
    
    def test_default_provider_selection_single(self):
        """Test default provider selection when only one provider is configured."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        cli.manager = mock_manager
        
        # Test with single provider
        providers = ["openai"]
        cli._set_default_provider(providers)
        
        # Should automatically set the single provider as default
        mock_manager.set_default_provider.assert_called_once_with("openai")
    
    def test_default_provider_selection_multiple(self):
        """Test default provider selection with multiple providers."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        cli.manager = mock_manager
        
        # Mock input to select second provider
        with patch('builtins.input', return_value="2"):
            providers = ["openai", "anthropic"]
            cli._set_default_provider(providers)
            
            # Should set selected provider as default
            mock_manager.set_default_provider.assert_called_once_with("anthropic")
    
    def test_roundtable_configuration(self):
        """Test roundtable configuration process."""
        cli = OnboardingCLI()
        
        # Mock the manager to return configured providers
        mock_manager = MagicMock()
        mock_manager.list_providers.return_value = ["openai", "anthropic"]
        mock_manager.get_provider_config.side_effect = lambda p: {"model": "default"}
        cli.manager = mock_manager
        
        # Mock input for roundtable configuration
        inputs = [
            "1,2",           # Select providers
            "1.0",           # OpenAI weight
            "512",           # OpenAI max tokens
            "0.8",           # Anthropic weight
            "256",           # Anthropic max tokens
            "2",             # Quorum size
            "vote_majority"  # Merge strategy
        ]
        
        with patch('builtins.input', side_effect=inputs):
            cli._configure_roundtable()
            
            # Verify roundtable was created
            mock_manager.create_roundtable.assert_called_once()
            mock_manager.activate_roundtable.assert_called_once_with("default")
    
    def test_roundtable_configuration_insufficient_providers(self):
        """Test roundtable configuration with insufficient providers."""
        cli = OnboardingCLI()
        
        # Mock the manager to return only one provider
        mock_manager = MagicMock()
        mock_manager.list_providers.return_value = ["openai"]
        cli.manager = mock_manager
        
        cli._configure_roundtable()
        
        # Should skip roundtable configuration
        mock_manager.create_roundtable.assert_not_called()
    
    def test_ask_yes_no_positive(self):
        """Test yes/no question with positive response."""
        cli = OnboardingCLI()
        
        with patch('builtins.input', return_value="y"):
            result = cli._ask_yes_no("Test question?")
            assert result is True
        
        with patch('builtins.input', return_value="yes"):
            result = cli._ask_yes_no("Test question?")
            assert result is True
    
    def test_ask_yes_no_negative(self):
        """Test yes/no question with negative response."""
        cli = OnboardingCLI()
        
        with patch('builtins.input', return_value="n"):
            result = cli._ask_yes_no("Test question?")
            assert result is False
        
        with patch('builtins.input', return_value="no"):
            result = cli._ask_yes_no("Test question?")
            assert result is False
    
    def test_list_providers_empty(self):
        """Test listing providers when none are configured."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        mock_manager.list_providers.return_value = []
        mock_manager.get_default_provider.return_value = "openai"
        cli.manager = mock_manager
        
        # Should handle empty provider list gracefully
        cli.list_providers()
    
    def test_list_providers_with_config(self):
        """Test listing providers with configuration."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        mock_manager.list_providers.return_value = ["openai", "anthropic"]
        mock_manager.get_provider_status.side_effect = lambda p: {
            "configured": True,
            "source": "config"
        }
        mock_manager.get_provider_config.side_effect = lambda p: {
            "api_key": "sk-test",
            "model": "gpt-4o-mini" if p == "openai" else "claude-3-haiku"
        }
        mock_manager.get_default_provider.return_value = "openai"
        cli.manager = mock_manager
        
        # Should list providers with masked API keys
        cli.list_providers()
    
    def test_add_provider_success(self):
        """Test adding a provider successfully."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        cli.manager = mock_manager
        
        # Mock the validation method to return success
        with patch.object(cli, '_validate_key_format', return_value=(True, "Valid")):
            cli.add_provider("openai", "sk-test123")
        
        # Verify manager was called
        mock_manager.add_provider.assert_called_once_with("openai", {"api_key": "sk-test123"})
    
    def test_add_provider_unsupported(self):
        """Test adding an unsupported provider."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        cli.manager = mock_manager
        
        # Should raise SystemExit for unsupported provider
        with pytest.raises(SystemExit):
            cli.add_provider("unsupported", "key")
        
        # Should not call manager for unsupported provider
        mock_manager.add_provider.assert_not_called()
    
    def test_set_default_provider(self):
        """Test setting default provider."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        cli.manager = mock_manager
        
        cli.set_default("openai")
        
        # Verify manager was called
        mock_manager.set_default_provider.assert_called_once_with("openai")
    
    def test_show_provider(self):
        """Test showing provider configuration."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        mock_manager.get_provider_config.return_value = {
            "api_key": "sk-test123",
            "model": "gpt-4o-mini"
        }
        cli.manager = mock_manager
        
        # Should show provider config with masked API key
        cli.show_provider("openai")
    
    def test_remove_provider(self):
        """Test removing a provider."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        cli.manager = mock_manager
        
        cli.remove_provider("openai")
        
        # Verify manager was called
        mock_manager.remove_provider.assert_called_once_with("openai", purge=False)
    
    def test_list_roundtables(self):
        """Test listing roundtables."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        mock_manager.list_roundtables.return_value = ["default", "custom"]
        mock_manager.get_active_roundtable.return_value = "default"
        cli.manager = mock_manager
        
        # Should list roundtables with active indicator
        cli.list_roundtables()
    
    def test_show_roundtable(self):
        """Test showing roundtable configuration."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        mock_manager.get_roundtable.return_value = {
            "quorum": 2,
            "merge_strategy": "vote_majority",
            "participants": [
                {"provider": "openai", "model": "gpt-4o-mini", "weight": 1.0, "max_tokens": 512}
            ]
        }
        cli.manager = mock_manager
        
        # Should show roundtable configuration
        cli.show_roundtable("default")
    
    def test_activate_roundtable(self):
        """Test activating a roundtable."""
        cli = OnboardingCLI()
        
        # Mock the manager
        mock_manager = MagicMock()
        cli.manager = mock_manager
        
        cli.activate_roundtable("custom")
        
        # Verify manager was called
        mock_manager.activate_roundtable.assert_called_once_with("custom")
