"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
CLI Onboarding Providers Test Module for IOA Core

Tests the CLI onboarding functionality for all LLM providers including
list, add, set-key, show, remove, and doctor commands.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from ioa_core.onboard import OnboardingCLI

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add CLI onboarding tests>


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup handled by test

@pytest.fixture
def cli_with_temp_config(temp_config_dir):
    """Create CLI instance with temporary config."""
    with patch.dict(os.environ, {"IOA_CONFIG_HOME": str(temp_config_dir)}):
        cli = OnboardingCLI()
        yield cli

class TestCLIOnboardingProviders:
    """Test CLI onboarding functionality for all providers."""
    
    def test_list_providers_empty(self, cli_with_temp_config):
        """Test listing providers when none are configured."""
        cli = cli_with_temp_config
        
        # Mock the manager to return empty provider list
        cli.manager.list_all_providers = MagicMock(return_value=[])
        cli.manager.get_provider_status = MagicMock(return_value={"configured": False})
        
        # Should not raise error
        cli.list_providers(include_unset=False)
    
    def test_list_providers_with_configured(self, cli_with_temp_config):
        """Test listing providers when some are configured."""
        cli = cli_with_temp_config
        
        # Mock the manager to return configured providers
        cli.manager.list_all_providers = MagicMock(return_value=["openai", "anthropic"])
        cli.manager.get_provider_status = MagicMock(return_value={"configured": True})
        cli.manager.resolve_api_key = MagicMock(return_value="sk-test123")
        
        # Should not raise error
        cli.list_providers(include_unset=False)
    
    def test_list_providers_include_unset(self, cli_with_temp_config):
        """Test listing providers including unset ones."""
        cli = cli_with_temp_config
        
        # Mock the manager to return mixed providers
        cli.manager.list_all_providers = MagicMock(return_value=["openai", "anthropic", "google"])
        cli.manager.get_provider_status = MagicMock(side_effect=lambda p: {
            "configured": p in ["openai", "anthropic"]
        })
        
        # Should not raise error
        cli.list_providers(include_unset=True)
    
    def test_show_provider_configured(self, cli_with_temp_config):
        """Test showing configured provider details."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=["openai"])
        cli.manager.get_provider_status = MagicMock(return_value={"status": "CONFIGURED", "configured": True})
        cli.manager.get_provider_config = MagicMock(return_value={
            "api_key": "sk-test123",
            "model": "gpt-4",
            "source": "env"
        })
        
        # Should not raise error
        cli.show_provider("openai")
    
    def test_show_provider_not_found(self, cli_with_temp_config):
        """Test showing non-existent provider."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=[])
        
        # Should raise SystemExit for unknown provider
        with pytest.raises(SystemExit):
            cli.show_provider("unknown")
    
    def test_add_provider_interactive(self, cli_with_temp_config):
        """Test adding provider with interactive key entry."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=[])
        cli.manager.add_provider = MagicMock()
        cli.manager._ensure_secure_permissions = MagicMock()
        
        # Mock key validation
        cli._validate_key_format = MagicMock(return_value=(True, "Valid key"))
        cli._prompt_for_key = MagicMock(return_value="sk-test123")
        
        # Should not raise error
        cli.add_provider("openai", key=None, from_env=False, validate_live=False, force=False)
    
    def test_add_provider_with_key(self, cli_with_temp_config):
        """Test adding provider with explicit key."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=[])
        cli.manager.add_provider = MagicMock()
        cli.manager._ensure_secure_permissions = MagicMock()
        
        # Mock key validation
        cli._validate_key_format = MagicMock(return_value=(True, "Valid key"))
        
        # Should not raise error
        cli.add_provider("openai", key="sk-test123", from_env=False, validate_live=False, force=False)
    
    def test_add_provider_from_env(self, cli_with_temp_config):
        """Test adding provider from environment variable."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=[])
        cli.manager.add_provider = MagicMock()
        cli.manager._ensure_secure_permissions = MagicMock()
        
        # Mock environment key retrieval
        cli._get_key_from_env = MagicMock(return_value="sk-test123")
        cli._validate_key_format = MagicMock(return_value=(True, "Valid key"))
        
        # Should not raise error
        cli.add_provider("openai", key=None, from_env=True, validate_live=False, force=False)
    
    def test_add_provider_force_validation(self, cli_with_temp_config):
        """Test adding provider with force override for validation."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=[])
        cli.manager.add_provider = MagicMock()
        cli.manager._ensure_secure_permissions = MagicMock()
        
        # Mock key validation failure
        cli._validate_key_format = MagicMock(return_value=(False, "Invalid key format"))
        
        # Should not raise error with force
        cli.add_provider("openai", key="invalid-key", from_env=False, validate_live=False, force=True)
    
    def test_set_key_interactive(self, cli_with_temp_config):
        """Test setting key interactively."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=["openai"])
        cli.manager.add_provider = MagicMock()
        cli.manager._ensure_secure_permissions = MagicMock()
        
        # Mock key validation
        cli._validate_key_format = MagicMock(return_value=(True, "Valid key"))
        cli._prompt_for_key = MagicMock(return_value="sk-new123")
        
        # Should not raise error
        cli.set_key("openai", key=None, from_env=False, validate_live=False, force=False)
    
    def test_set_key_with_key(self, cli_with_temp_config):
        """Test setting key with explicit value."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=["openai"])
        cli.manager.add_provider = MagicMock()
        cli.manager._ensure_secure_permissions = MagicMock()
        
        # Mock key validation
        cli._validate_key_format = MagicMock(return_value=(True, "Valid key"))
        
        # Should not raise error
        cli.set_key("openai", key="sk-new123", from_env=False, validate_live=False, force=False)
    
    def test_set_key_from_env(self, cli_with_temp_config):
        """Test setting key from environment variable."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=["openai"])
        cli.manager.add_provider = MagicMock()
        cli.manager._ensure_secure_permissions = MagicMock()
        
        # Mock environment key retrieval
        cli._get_key_from_env = MagicMock(return_value="sk-env123")
        cli._validate_key_format = MagicMock(return_value=(True, "Valid key"))
        
        # Should not raise error
        cli.set_key("openai", key=None, from_env=True, validate_live=False, force=False)
    
    def test_set_default_provider(self, cli_with_temp_config):
        """Test setting default provider."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.set_default_provider = MagicMock()
        
        # Should not raise error
        cli.set_default("openai")
    
    def test_remove_provider(self, cli_with_temp_config):
        """Test removing provider."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=["openai"])
        cli.manager.remove_provider = MagicMock()
        
        # Should not raise error
        cli.remove_provider("openai", purge=False)
    
    def test_remove_provider_purge(self, cli_with_temp_config):
        """Test removing provider with purge."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=["openai"])
        cli.manager.remove_provider = MagicMock()
        
        # Should not raise error
        cli.remove_provider("openai", purge=True)
    
    def test_doctor_no_issues(self, cli_with_temp_config):
        """Test doctor command with no issues."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.llm_config_path = MagicMock()
        cli.manager.llm_config_path.exists = MagicMock(return_value=False)
        cli.manager.list_all_providers = MagicMock(return_value=[])
        
        # Should not raise error
        cli.doctor()
    
    def test_doctor_with_issues(self, cli_with_temp_config):
        """Test doctor command with issues to fix."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.llm_config_path = MagicMock()
        cli.manager.llm_config_path.exists = MagicMock(return_value=True)
        cli.manager.llm_config_path.stat = MagicMock()
        cli.manager.llm_config_path.chmod = MagicMock()
        cli.manager.list_all_providers = MagicMock(return_value=["openai"])
        cli.manager.get_provider_status = MagicMock(return_value={"configured": False})
        cli.manager.remove_provider = MagicMock()
        
        # Mock user input
        with patch('builtins.input', return_value='y'):
            cli.doctor()
    
    def test_smoke_test_offline(self, cli_with_temp_config):
        """Test smoke test in offline mode."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.create_service = MagicMock()
        mock_service = MagicMock()
        mock_service.execute.return_value = "[OFFLINE-OPENAI] Hello, this is a test."
        mock_service.get_provider_info.return_value = {
            "available": True,
            "model": "gpt-4"
        }
        cli.manager.create_service.return_value = mock_service
        
        # Should not raise error
        cli.smoke_test(provider="openai", offline=True)
    
    def test_smoke_test_live(self, cli_with_temp_config):
        """Test smoke test in live mode."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.create_service = MagicMock()
        mock_service = MagicMock()
        mock_service.execute.return_value = "Hello! This is a test response from the API."
        mock_service.get_provider_info.return_value = {
            "available": True,
            "model": "gpt-4"
        }
        cli.manager.create_service.return_value = mock_service
        
        # Should not raise error
        cli.smoke_test(provider="openai", live=True)
    
    def test_smoke_test_all_providers(self, cli_with_temp_config):
        """Test smoke test for all providers."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.create_service = MagicMock()
        mock_service = MagicMock()
        mock_service.execute.return_value = "[OFFLINE-TEST] Hello, this is a test."
        mock_service.get_provider_info.return_value = {
            "available": True,
            "model": "test-model"
        }
        cli.manager.create_service.return_value = mock_service
        
        # Should not raise error
        cli.smoke_test(provider=None, offline=True)
    
    def test_smoke_test_service_creation_failure(self, cli_with_temp_config):
        """Test smoke test when service creation fails."""
        cli = cli_with_temp_config
        
        # Mock the manager to raise error
        cli.manager.create_service = MagicMock(side_effect=Exception("Service creation failed"))
        
        # Should handle error gracefully
        cli.smoke_test(provider="openai", offline=True)
    
    def test_smoke_test_execution_failure(self, cli_with_temp_config):
        """Test smoke test when execution fails."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.create_service = MagicMock()
        mock_service = MagicMock()
        mock_service.execute.side_effect = Exception("Execution failed")
        cli.manager.create_service.return_value = mock_service
        
        # Should handle error gracefully
        cli.smoke_test(provider="openai", offline=True)


class TestCLIProviderValidation:
    """Test CLI provider validation functionality."""
    
    def test_validate_provider_exists(self, cli_with_temp_config):
        """Test validation of existing provider."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=["openai"])
        
        # Should not raise error
        cli._validate_provider("openai")
    
    def test_validate_provider_not_exists(self, cli_with_temp_config):
        """Test validation of non-existent provider."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=[])
        
        # Should raise error
        with pytest.raises(SystemExit):
            cli._validate_provider("unknown")
    
    def test_validate_key_format_valid(self, cli_with_temp_config):
        """Test validation of valid key format."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.validate_api_key = MagicMock(return_value={"valid": True, "message": "Valid key"})
        
        # Should return valid (using a key that meets minimum length requirement)
        is_valid, message = cli._validate_key_format("sk-test12345678901234567890", "openai", force=False)
        assert is_valid == True
    
    def test_validate_key_format_invalid(self, cli_with_temp_config):
        """Test validation of invalid key format."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.validate_api_key = MagicMock(return_value=(False, "Invalid key format"))
        
        # Should return invalid
        is_valid, message = cli._validate_key_format("invalid-key", "openai", force=False)
        assert is_valid == False
    
    def test_validate_key_format_force_override(self, cli_with_temp_config):
        """Test validation with force override."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.validate_api_key = MagicMock(return_value={"valid": False, "error": "Invalid key format"})
        
        # With force=True, should still validate but manager validation is called
        # The key "invalid-key" is too short for OpenAI (min 20 chars), so local validation fails
        is_valid, message = cli._validate_key_format("invalid-key", "openai", force=True)
        assert is_valid == False
        assert "too short" in message


class TestCLIErrorHandling:
    """Test CLI error handling."""
    
    def test_handle_manager_errors(self, cli_with_temp_config):
        """Test handling of manager errors."""
        cli = cli_with_temp_config
        
        # Mock the manager to raise error
        cli.manager.add_provider = MagicMock(side_effect=Exception("Manager error"))
        
        # Should handle error gracefully
        with pytest.raises(SystemExit):
            cli.add_provider("openai", key="sk-test123")
    
    def test_handle_validation_errors(self, cli_with_temp_config):
        """Test handling of validation errors."""
        cli = cli_with_temp_config
        
        # Mock validation to fail
        cli._validate_key_format = MagicMock(return_value=(False, "Invalid key"))
        
        # Should handle error gracefully
        with pytest.raises(SystemExit):
            cli.add_provider("openai", key="invalid-key")
    
    def test_handle_missing_provider(self, cli_with_temp_config):
        """Test handling of missing provider errors."""
        cli = cli_with_temp_config
        
        # Mock the manager
        cli.manager.list_all_providers = MagicMock(return_value=[])
        
        # Should handle error gracefully
        with pytest.raises(SystemExit):
            cli.show_provider("unknown")
