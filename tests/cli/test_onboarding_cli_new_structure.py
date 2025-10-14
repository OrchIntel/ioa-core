"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
Test new CLI structure for LLM provider management.

Tests the new subcommand structure, interactive wizard, provider validation,
and all CLI commands for managing LLM providers.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# PATCH: Cursor-2025-08-16 CL-Onboarding-CLI-Fix+Wizard <test new CLI structure>
from ioa_core.onboard import OnboardingCLI


class TestOnboardingCLINewStructure:
    """Test new CLI structure and functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / ".ioa" / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock HOME directory
        self.patched_home = patch.dict(os.environ, {"HOME": self.temp_dir})
        self.patched_home.start()
        
        # Mock LLM manager
        self.mock_manager = MagicMock()
        
    def teardown_method(self):
        """Clean up test environment."""
        self.patched_home.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_initialization(self):
        """Test CLI initialization with banner."""
        with patch('sys.stdout.isatty', return_value=True):
            with patch('builtins.print') as mock_print:
                cli = OnboardingCLI()
                assert cli.manager is not None
                assert hasattr(cli, 'PROVIDER_OPTIONS')
                assert 'openai' in cli.PROVIDER_OPTIONS
                assert 'anthropic' in cli.PROVIDER_OPTIONS
                
                # Check banner was printed
                mock_print.assert_called()
    
    def test_provider_options_structure(self):
        """Test that provider options have correct structure."""
        cli = OnboardingCLI()
        
        for provider, info in cli.PROVIDER_OPTIONS.items():
            assert 'name' in info
            assert 'description' in info
            assert 'env_var' in info
            assert 'key_pattern' in info
            assert 'min_length' in info
    
    def test_validate_provider_valid(self):
        """Test provider validation with valid provider."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Should not raise exception
        cli._validate_provider("openai")
        cli._validate_provider("anthropic")
        cli._validate_provider("groq")
    
    def test_validate_provider_invalid(self):
        """Test provider validation with invalid provider."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        with pytest.raises(SystemExit) as exc_info:
            cli._validate_provider("invalid_provider")
        
        assert exc_info.value.code == 1
    
    def test_detect_placeholder_key(self):
        """Test placeholder key detection."""
        cli = OnboardingCLI()
        
        # Test placeholder patterns
        assert cli._detect_placeholder_key("sk-test-key", "openai")
        assert cli._detect_placeholder_key("sk-ant-test-key", "anthropic")
        assert cli._detect_placeholder_key("XXXX", "openai")
        assert cli._detect_placeholder_key("demo", "openai")
        assert cli._detect_placeholder_key("your-api-key-here", "openai")
        
        # Test valid keys
        assert not cli._detect_placeholder_key("sk-1234567890abcdef1234567890abcdef", "openai")
        assert not cli._detect_placeholder_key("sk-ant-1234567890abcdef1234567890abcdef", "anthropic")
    
    def test_validate_key_format(self):
        """Test API key format validation."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock the manager's validate_api_key method to return success
        self.mock_manager.validate_api_key.return_value = {"valid": True, "message": "Valid"}
    
        # Test OpenAI
        is_valid, message = cli._validate_key_format("sk-1234567890abcdef1234567890abcdef", "openai")
        assert is_valid
        assert message == "Valid"
    
        is_valid, message = cli._validate_key_format("sk-123", "openai")
        assert not is_valid
        assert "too short" in message
    
        # Test Anthropic
        is_valid, message = cli._validate_key_format("sk-ant-1234567890abcdef1234567890abcdef", "anthropic")
        assert is_valid
    
        # Test Groq
        is_valid, message = cli._validate_key_format("gsk_1234567890abcdef1234567890abcdef", "groq")
        assert is_valid
    
        # Test Ollama (no key required)
        is_valid, message = cli._validate_key_format("", "ollama")
        assert is_valid
        assert "requires no API key" in message
    
    def test_get_key_from_env(self):
        """Test getting API key from environment."""
        cli = OnboardingCLI()
        
        # Test with environment variable set
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}):
            key = cli._get_key_from_env("openai")
            assert key == "sk-test123"
        
        # Test with environment variable not set
        with patch.dict(os.environ, {}, clear=True):
            key = cli._get_key_from_env("openai")
            assert key is None
    
    def test_create_provider_config(self):
        """Test provider configuration creation."""
        cli = OnboardingCLI()
        
        # Test OpenAI
        config = cli._create_provider_config("openai", "sk-test123", False)
        assert config["api_key"] == "sk-test123"
        assert "source" not in config
        
        # Test with env source
        config = cli._create_provider_config("openai", "sk-test123", True)
        assert config["source"] == "env"
        
        # Test Ollama
        config = cli._create_provider_config("ollama", "local", False)
        assert config["host"] == "http://localhost:11434"
    
    def test_list_providers_configured_only(self):
        """Test listing only configured providers."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock manager methods
        self.mock_manager.list_providers.return_value = ["openai", "anthropic"]
        self.mock_manager.get_provider_status.side_effect = [
            {"configured": True, "source": "config"},
            {"configured": True, "source": "env"}
        ]
        self.mock_manager.get_default_provider.return_value = "openai"
        
        with patch('builtins.print') as mock_print:
            cli.list_providers(include_unset=False)
            
            # Check that manager was called correctly
            self.mock_manager.list_providers.assert_called_once()
            self.mock_manager.list_all_providers.assert_not_called()
    
    def test_list_providers_include_unset(self):
        """Test listing all providers including unset ones."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock manager methods
        self.mock_manager.list_all_providers.return_value = ["openai", "anthropic", "groq"]
        self.mock_manager.get_provider_status.side_effect = [
            {"configured": True, "source": "config"},
            {"configured": False, "source": "config"},
            {"configured": True, "source": "env"}
        ]
        self.mock_manager.get_default_provider.return_value = "openai"
        
        with patch('builtins.print') as mock_print:
            cli.list_providers(include_unset=True)
            
            # Check that manager was called correctly
            self.mock_manager.list_all_providers.assert_called_once()
    
    def test_show_provider(self):
        """Test showing provider configuration."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock manager methods
        self.mock_manager.get_provider_config.return_value = {
            "api_key": "sk-1234567890abcdef1234567890abcdef",
            "model": "gpt-4o-mini"
        }
        self.mock_manager.get_provider_status.return_value = {
            "status": "configured",
            "source": "config"
        }
        
        with patch('builtins.print') as mock_print:
            cli.show_provider("openai")
            
            # Check that API key was masked (last 4 characters)
            mock_print.assert_any_call("  api_key: ********cdef")
    
    def test_add_provider_with_key(self):
        """Test adding provider with explicit key."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock manager methods
        self.mock_manager.add_provider.return_value = None
        
        with patch.object(cli, '_ensure_secure_permissions'):
            with patch.object(cli, 'list_providers'):
                cli.add_provider("openai", "sk-1234567890abcdef1234567890abcdef")
                
                # Check that manager was called correctly
                self.mock_manager.add_provider.assert_called_once()
                config = self.mock_manager.add_provider.call_args[0][1]
                assert config["api_key"] == "sk-1234567890abcdef1234567890abcdef"
    
    def test_add_provider_from_env(self):
        """Test adding provider from environment variable."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock environment variable
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env1234567890abcdef1234567890abcdef"}):
            with patch.object(cli, '_ensure_secure_permissions'):
                with patch.object(cli, 'list_providers'):
                    cli.add_provider("openai", None, from_env=True)
                    
                    # Check that manager was called correctly
                    self.mock_manager.add_provider.assert_called_once()
                    config = self.mock_manager.add_provider.call_args[0][1]
                    assert config["api_key"] == "sk-env1234567890abcdef1234567890abcdef"
                    assert config["source"] == "env"
    
    def test_add_provider_invalid_key(self):
        """Test adding provider with invalid key."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        with pytest.raises(SystemExit) as exc_info:
            cli.add_provider("openai", "invalid-key")
        
        assert exc_info.value.code == 1
    
    def test_set_key_existing_provider(self):
        """Test updating key for existing provider."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock manager methods
        self.mock_manager.list_all_providers.return_value = ["openai"]
        self.mock_manager.add_provider.return_value = None
        
        with patch.object(cli, '_ensure_secure_permissions'):
            cli.set_key("openai", "sk-new1234567890abcdef1234567890abcdef")
            
            # Check that manager was called correctly
            self.mock_manager.add_provider.assert_called_once()
    
    def test_set_key_provider_not_found(self):
        """Test updating key for non-existent provider."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock manager methods
        self.mock_manager.list_all_providers.return_value = []
        
        with pytest.raises(SystemExit) as exc_info:
            cli.set_key("openai", "sk-1234567890abcdef1234567890abcdef")
        
        assert exc_info.value.code == 1
    
    def test_set_default_provider(self):
        """Test setting default provider."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock manager methods
        self.mock_manager.set_default_provider.return_value = None
        
        cli.set_default("openai")
        
        # Check that manager was called correctly
        self.mock_manager.set_default_provider.assert_called_once_with("openai")
    
    def test_set_default_provider_error(self):
        """Test setting default provider with error."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock manager methods to raise exception
        self.mock_manager.set_default_provider.side_effect = Exception("Provider not configured")
        
        with pytest.raises(SystemExit) as exc_info:
            cli.set_default("openai")
        
        assert exc_info.value.code == 1
    
    def test_remove_provider(self):
        """Test removing provider."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock manager methods
        self.mock_manager.remove_provider.return_value = None
        
        cli.remove_provider("openai", purge=False)
        
        # Check that manager was called correctly
        self.mock_manager.remove_provider.assert_called_once_with("openai", purge=False)
    
    def test_remove_provider_purge(self):
        """Test removing provider with purge."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock manager methods
        self.mock_manager.remove_provider.return_value = None
        
        cli.remove_provider("openai", purge=True)
        
        # Check that manager was called correctly
        self.mock_manager.remove_provider.assert_called_once_with("openai", purge=True)
    
    def test_doctor_command(self):
        """Test doctor command functionality."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock manager methods
        self.mock_manager.list_all_providers.return_value = ["openai", "anthropic"]
        self.mock_manager.get_provider_status.side_effect = [
            {"configured": True, "source": "config"},
            {"configured": False, "source": "config"},
            {"configured": True, "source": "config"}  # For default provider check
        ]
        self.mock_manager.get_default_provider.return_value = "openai"
        self.mock_manager.validate_default_provider.return_value = "openai"
        
        # Mock file operations
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_config_file.stat.return_value = MagicMock()
        mock_config_file.stat.return_value.st_mode = 0o644  # Insecure permissions
        
        with patch.object(cli.manager, 'llm_config_path', mock_config_file):
            with patch('builtins.input', return_value='y'):  # User chooses to remove unset provider
                with patch('builtins.print') as mock_print:
                    cli.doctor()
                    
                    # Check that manager was called correctly
                    self.mock_manager.list_all_providers.assert_called_once()
                    self.mock_manager.get_provider_status.assert_called()
    
    def test_ensure_secure_permissions(self):
        """Test secure permissions enforcement."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock config file
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_config_file.stat.return_value = MagicMock()
        mock_config_file.stat.return_value.st_mode = 0o644  # Insecure permissions
        
        with patch.object(cli.manager, 'llm_config_path', mock_config_file):
            with patch('builtins.print') as mock_print:
                cli._ensure_secure_permissions()
                
                # Check that permissions were fixed
                mock_config_file.chmod.assert_called_once_with(0o600)
                mock_print.assert_called_with("Note: Fixed config file permissions to 600")


class TestOnboardingCLIInteractive:
    """Test interactive CLI functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / ".ioa" / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock HOME directory
        self.patched_home = patch.dict(os.environ, {"HOME": self.temp_dir})
        self.patched_home.start()
        
        # Mock LLM manager
        self.mock_manager = MagicMock()
    
    def teardown_method(self):
        """Clean up test environment."""
        self.patched_home.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('os.getenv', return_value=None)  # Mock non-interactive check
    @patch('sys.stdin.isatty', return_value=True)  # Mock TTY check
    def test_prompt_for_key_openai(self, mock_isatty, mock_getenv):
        """Test interactive key prompting for OpenAI."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock user input
        with patch('getpass.getpass', return_value="sk-1234567890abcdef1234567890abcdef"):
            with patch('builtins.input', return_value=""):  # Default to yes
                key = cli._prompt_for_key("openai")
                assert key == "sk-1234567890abcdef1234567890abcdef"
    
    def test_prompt_for_key_ollama(self):
        """Test interactive key prompting for Ollama."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        key = cli._prompt_for_key("ollama")
        assert key == "local"
    
    @patch('os.getenv', return_value=None)  # Mock non-interactive check
    @patch('sys.stdin.isatty', return_value=True)  # Mock TTY check
    def test_prompt_for_key_placeholder_detection(self, mock_isatty, mock_getenv):
        """Test placeholder key detection in interactive mode."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock user input for placeholder key
        with patch('getpass.getpass', return_value="sk-test-key"):
            with patch('builtins.input', return_value="keep"):  # User chooses to keep as unset
                key = cli._prompt_for_key("openai")
                assert key == ""
    
    @patch('os.getenv', return_value=None)  # Mock non-interactive check
    @patch('sys.stdin.isatty', return_value=True)  # Mock TTY check
    def test_prompt_for_key_retry_on_invalid(self, mock_isatty, mock_getenv):
        """Test retry logic for invalid keys."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        # Mock user input: first invalid, then valid
        with patch('getpass.getpass', side_effect=["invalid", "sk-1234567890abcdef1234567890abcdef"]):
            with patch('builtins.input', side_effect=["y", ""]):  # Retry, then confirm
                key = cli._prompt_for_key("openai")
                assert key == "sk-1234567890abcdef1234567890abcdef"
    
    def test_validate_live_success(self):
        """Test live validation success."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        with patch('builtins.print') as mock_print:
            result = cli._validate_live("openai", "sk-1234567890abcdef1234567890abcdef")
            assert result is True
            mock_print.assert_any_call("✅ API key validated successfully")
    
    def test_validate_live_ollama_skip(self):
        """Test live validation skip for Ollama."""
        cli = OnboardingCLI()
        cli.manager = self.mock_manager
        
        with patch('builtins.print') as mock_print:
            result = cli._validate_live("ollama", "local")
            assert result is True
            mock_print.assert_any_call("Skipping live validation for Ollama (local provider)")


if __name__ == "__main__":
    pytest.main([__file__])
