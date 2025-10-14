"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
Test LLM Manager persistence functionality.

Tests file operations, secret masking, and permission handling for secure
configuration storage.
"""

import os
import json
import tempfile
import shutil
import stat
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# PATCH: Cursor-2025-08-15 CL-LLM-Manager LLM Manager persistence tests
from src.llm_manager import LLMManager, LLMConfigError, LLMProviderError, LLMStorageError


class TestLLMManagerPersistence:
    """Test LLM Manager persistence and file operations."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / ".ioa" / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock HOME directory
        self.original_home = os.path.expanduser("~")
        self.patched_home = patch.dict(os.environ, {"HOME": self.temp_dir})
        self.patched_home.start()
    
    def teardown_method(self):
        """Clean up test environment."""
        self.patched_home.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_config_directory(self):
        """Test that config directory is created if it doesn't exist."""
        # Remove config directory
        shutil.rmtree(self.config_dir, ignore_errors=True)
        
        # Initialize manager - should create directory
        manager = LLMManager(str(self.config_dir))
        
        assert self.config_dir.exists()
        assert (self.config_dir / "llm.json").exists()
        assert (self.config_dir / "roundtable.json").exists()
    
    def test_load_default_config(self):
        """Test loading default configuration when no files exist."""
        manager = LLMManager(str(self.config_dir))
        
        # Check default configuration
        assert manager._config["version"] == 1
        assert manager._config["default_provider"] == "openai"
        assert manager._config["providers"] == {}
        
        # Check default roundtable configuration
        assert manager._roundtable_config["version"] == 1
        assert manager._roundtable_config["active"] == "default"
        assert "default" in manager._roundtable_config["tables"]
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        manager = LLMManager(str(self.config_dir))
        
        # Add a provider
        manager.add_provider("openai", {
            "api_key": "sk-test123",
            "model": "gpt-4o-mini"
        })
        
        # Create new manager instance to test loading
        manager2 = LLMManager(str(self.config_dir))
        
        # Check that configuration was loaded
        assert "openai" in manager2._config["providers"]
        assert manager2._config["providers"]["openai"]["api_key"] == "sk-test123"
        assert manager2._config["providers"]["openai"]["model"] == "gpt-4o-mini"
    
    def test_secret_masking_in_string_representation(self):
        """Test that API keys are masked in string representation."""
        manager = LLMManager(str(self.config_dir))
        
        # Add providers with API keys
        manager.add_provider("openai", {
            "api_key": "sk-test123",
            "model": "gpt-4o-mini"
        })
        manager.add_provider("anthropic", {
            "api_key": "sk-ant-test456",
            "model": "claude-3-haiku"
        })
        
        # Convert to string - should mask secrets
        str_repr = str(manager)
        repr_repr = repr(manager)
        
        # Check that secrets are masked
        assert "sk-test123" not in str_repr
        assert "sk-ant-test456" not in str_repr
        assert "********" in str_repr
        
        # Check that non-secret fields are visible
        assert "openai" in str_repr
        assert "anthropic" in str_repr
        assert "gpt-4o-mini" in str_repr
        assert "claude-3-haiku" in str_repr
    
    @pytest.mark.skipif(os.name != 'posix', reason="POSIX-specific test")
    def test_file_permissions_on_posix(self):
        """Test that files get secure permissions on POSIX systems."""
        
        manager = LLMManager(str(self.config_dir))
        
        # Add a provider to trigger file save
        manager.add_provider("openai", {
            "api_key": "sk-test123",
            "model": "gpt-4o-mini"
        })
        
        # Check file permissions
        llm_config_path = self.config_dir / "llm.json"
        roundtable_config_path = self.config_dir / "roundtable.json"
        
        # Should be 600 (user read/write only)
        expected_mode = stat.S_IRUSR | stat.S_IWUSR
        
        assert llm_config_path.stat().st_mode & 0o777 == expected_mode
        assert roundtable_config_path.stat().st_mode & 0o777 == expected_mode
    
    def test_backup_creation_on_save(self):
        """Test that backup files are created when saving."""
        manager = LLMManager(str(self.config_dir))
        
        # Add initial provider
        manager.add_provider("openai", {
            "api_key": "sk-test123",
            "model": "gpt-4o-mini"
        })
        
        # Check that backup was created
        backup_files = list(self.config_dir.glob("*.backup"))
        assert len(backup_files) == 1
        assert backup_files[0].name == "llm.json.backup"
        
        # Add another provider - should create another backup
        manager.add_provider("anthropic", {
            "api_key": "sk-ant-test456",
            "model": "claude-3-haiku"
        })
        
        backup_files = list(self.config_dir.glob("*.backup"))
        assert len(backup_files) == 1  # Only one backup at a time
        assert backup_files[0].name == "llm.json.backup"
    
    def test_error_handling_on_corrupted_config(self):
        """Test handling of corrupted configuration files."""
        # Create corrupted JSON file
        corrupted_config = self.config_dir / "llm.json"
        with open(corrupted_config, 'w') as f:
            f.write("{ invalid json content")
        
        # Manager should handle corruption gracefully
        manager = LLMManager(str(self.config_dir))
        
        # Should fall back to default configuration
        assert manager._config["version"] == 1
        assert manager._config["default_provider"] == "openai"
        assert manager._config["providers"] == {}
    
    def test_roundtable_config_persistence(self):
        """Test roundtable configuration persistence."""
        manager = LLMManager(str(self.config_dir))
        
        # Create custom roundtable
        custom_roundtable = {
            "quorum": 3,
            "merge_strategy": "confidence_weighted",
            "participants": [
                {"provider": "openai", "model": "gpt-4o-mini", "weight": 1.0, "max_tokens": 1024},
                {"provider": "anthropic", "model": "claude-3-haiku", "weight": 0.8, "max_tokens": 512}
            ]
        }
        
        manager.create_roundtable("custom", custom_roundtable)
        
        # Create new manager instance to test loading
        manager2 = LLMManager(str(self.config_dir))
        
        # Check that roundtable was loaded
        loaded_roundtable = manager2.get_roundtable("custom")
        assert loaded_roundtable["quorum"] == 3
        assert loaded_roundtable["merge_strategy"] == "confidence_weighted"
        assert len(loaded_roundtable["participants"]) == 2
        
        # Check participant details
        openai_participant = next(p for p in loaded_roundtable["participants"] if p["provider"] == "openai")
        assert openai_participant["model"] == "gpt-4o-mini"
        assert openai_participant["weight"] == 1.0
        assert openai_participant["max_tokens"] == 1024


class TestLLMManagerProviderOperations:
    """Test LLM Manager provider operations."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / ".ioa" / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.patched_home = patch.dict(os.environ, {"HOME": self.temp_dir})
        self.patched_home.start()
    
    def teardown_method(self):
        """Clean up test environment."""
        self.patched_home.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_provider(self):
        """Test adding a provider."""
        manager = LLMManager(str(self.config_dir))
        
        # Add provider
        manager.add_provider("openai", {
            "api_key": "sk-test123",
            "model": "gpt-4o-mini"
        })
        
        # Check that provider was added
        assert "openai" in manager._config["providers"]
        assert manager._config["providers"]["openai"]["api_key"] == "sk-test123"
        assert manager._config["providers"]["openai"]["model"] == "gpt-4o-mini"
    
    def test_update_existing_provider(self):
        """Test updating an existing provider."""
        manager = LLMManager(str(self.config_dir))
        
        # Add initial provider
        manager.add_provider("openai", {
            "api_key": "sk-test123",
            "model": "gpt-4o-mini"
        })
        
        # Update provider
        manager.add_provider("openai", {
            "model": "gpt-4o",
            "base_url": "https://api.openai.com/v1"
        })
        
        # Check that fields were updated
        provider_config = manager._config["providers"]["openai"]
        assert provider_config["api_key"] == "sk-test123"  # Should be preserved
        assert provider_config["model"] == "gpt-4o"  # Should be updated
        assert provider_config["base_url"] == "https://api.openai.com/v1"  # Should be added
    
    def test_remove_provider(self):
        """Test removing a provider."""
        manager = LLMManager(str(self.config_dir))
        
        # Add providers
        manager.add_provider("openai", {"api_key": "sk-test123"})
        manager.add_provider("anthropic", {"api_key": "sk-ant-test456"})
        manager.set_default_provider("openai")
        
        # Remove provider
        manager.remove_provider("openai")
        
        # Check that provider was removed
        assert "openai" not in manager._config["providers"]
        assert "anthropic" in manager._config["providers"]
        
        # Check that default provider was updated
        assert manager._config["default_provider"] == "anthropic"
    
    def test_remove_last_provider(self):
        """Test removing the last provider."""
        manager = LLMManager(str(self.config_dir))
        
        # Add single provider
        manager.add_provider("openai", {"api_key": "sk-test123"})
        manager.set_default_provider("openai")
        
        # Remove provider
        manager.remove_provider("openai")
        
        # Check that default provider falls back to "openai"
        assert manager._config["default_provider"] == "openai"
        assert len(manager._config["providers"]) == 0
    
    def test_set_default_provider(self):
        """Test setting default provider."""
        manager = LLMManager(str(self.config_dir))
        
        # Add providers
        manager.add_provider("openai", {"api_key": "sk-test123"})
        manager.add_provider("anthropic", {"api_key": "sk-ant-test456"})
        
        # Set default
        manager.set_default_provider("anthropic")
        
        # Check that default was set
        assert manager._config["default_provider"] == "anthropic"
    
    def test_set_default_provider_not_configured(self):
        """Test setting default provider that is not configured."""
        manager = LLMManager(str(self.config_dir))
        
        # Try to set unconfigured provider as default
        with pytest.raises(LLMProviderError, match="Provider nonexistent not found in configuration"):
            manager.set_default_provider("nonexistent")
    
    def test_list_providers(self):
        """Test listing providers."""
        manager = LLMManager(str(self.config_dir))
        
        # Initially no providers
        assert manager.list_providers() == []
        
        # Add providers
        manager.add_provider("openai", {"api_key": "sk-test123"})
        manager.add_provider("anthropic", {"api_key": "sk-ant-test456"})
        
        # Check list
        providers = manager.list_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert len(providers) == 2
    
    def test_get_provider_config(self):
        """Test getting provider configuration."""
        manager = LLMManager(str(self.config_dir))
        
        # Add provider
        manager.add_provider("openai", {
            "api_key": "sk-test123",
            "model": "gpt-4o-mini"
        })
        
        # Get configuration
        config = manager.get_provider_config("openai")
        assert config["api_key"] == "sk-test123"
        assert config["model"] == "gpt-4o-mini"
        
        # Get non-existent provider
        config = manager.get_provider_config("nonexistent")
        assert config == {}
    
    def test_get_default_provider(self):
        """Test getting default provider."""
        manager = LLMManager(str(self.config_dir))
        
        # Check default
        assert manager.get_default_provider() == "openai"
        
        # Change default
        manager.add_provider("anthropic", {"api_key": "sk-ant-test456"})
        manager.set_default_provider("anthropic")
        
        # Check new default
        assert manager.get_default_provider() == "anthropic"
