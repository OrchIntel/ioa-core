""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

# PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <test precedence resolution>
import os
import pytest
from unittest.mock import patch, MagicMock
from src.llm_manager import LLMManager, LLMConfigError


class TestPrecedenceResolution:
    """Test precedence-based API key resolution."""
    
    def test_explicit_key_highest_precedence(self, temp_config_dir):
        """Test that explicit key takes highest precedence."""
        # Create config with API key
        config_file = temp_config_dir / "llm.json"
        config_data = {
            "version": 1,
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "config_file_key",
                    "model": "gpt-4"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            import json
            json.dump(config_data, f)
        
        # Set environment variable
        os.environ["OPENAI_API_KEY"] = "env_key"
        
        # Test explicit key takes precedence
        manager = LLMManager(config_dir=str(temp_config_dir))
        resolved_key = manager.resolve_api_key("openai", explicit_key="explicit_key")
        
        assert resolved_key == "explicit_key"
    
    def test_env_over_config_file(self, temp_config_dir):
        """Test that environment variable takes precedence over config file."""
        # Create config with API key
        config_file = temp_config_dir / "llm.json"
        config_data = {
            "version": 1,
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "config_file_key",
                    "model": "gpt-4"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            import json
            json.dump(config_data, f)
        
        # Set environment variable
        os.environ["OPENAI_API_KEY"] = "env_key"
        
        # Test environment takes precedence over config file
        manager = LLMManager(config_dir=str(temp_config_dir))
        resolved_key = manager.resolve_api_key("openai")
        
        assert resolved_key == "env_key"
    
    def test_config_file_fallback(self, temp_config_dir):
        """Test that config file is used when env is not set."""
        # Create config with API key
        config_file = temp_config_dir / "llm.json"
        config_data = {
            "version": 1,
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "config_file_key",
                    "model": "gpt-4"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            import json
            json.dump(config_data, f)
        
        # Clear environment variable
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        # Test config file is used
        manager = LLMManager(config_dir=str(temp_config_dir))
        resolved_key = manager.resolve_api_key("openai")
        
        assert resolved_key == "config_file_key"
    
    def test_no_key_found(self, temp_config_dir):
        """Test that None is returned when no key is found."""
        # Create empty config
        config_file = temp_config_dir / "llm.json"
        config_data = {
            "version": 1,
            "default_provider": "openai",
            "providers": {}
        }
        
        with open(config_file, 'w') as f:
            import json
            json.dump(config_data, f)
        
        # Clear environment variable
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        # Test no key found
        manager = LLMManager(config_dir=str(temp_config_dir))
        resolved_key = manager.resolve_api_key("openai")
        
        assert resolved_key is None
    
    def test_test_mode_disables_config(self, temp_config_dir):
        """Test that test mode with IOA_DISABLE_LLM_CONFIG disables config file lookup."""
        # Create config with API key
        config_file = temp_config_dir / "llm.json"
        config_data = {
            "version": 1,
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "config_file_key",
                    "model": "gpt-4"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            import json
            json.dump(config_data, f)
        
        # Clear environment variable
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        # Set test mode flags
        os.environ["IOA_TEST_MODE"] = "1"
        os.environ["IOA_DISABLE_LLM_CONFIG"] = "1"
        
        # Test config file is ignored in test mode
        manager = LLMManager(config_dir=str(temp_config_dir))
        resolved_key = manager.resolve_api_key("openai")
        
        assert resolved_key is None
    
    def test_allow_config_fallback_parameter(self, temp_config_dir):
        """Test that allow_config_fallback parameter controls config file access."""
        # Create config with API key
        config_file = temp_config_dir / "llm.json"
        config_data = {
            "version": 1,
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "config_file_key",
                    "model": "gpt-4"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            import json
            json.dump(config_data, f)
        
        # Clear environment variable
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        # Clear test mode flags for this specific test
        original_test_mode = os.environ.get("IOA_TEST_MODE")
        original_disable_config = os.environ.get("IOA_DISABLE_LLM_CONFIG")
        if "IOA_TEST_MODE" in os.environ:
            del os.environ["IOA_TEST_MODE"]
        if "IOA_DISABLE_LLM_CONFIG" in os.environ:
            del os.environ["IOA_DISABLE_LLM_CONFIG"]
        
        try:
            # Test with allow_config_fallback=False
            manager = LLMManager(config_dir=str(temp_config_dir), allow_config_fallback=False)
            resolved_key = manager.resolve_api_key("openai")
            
            assert resolved_key is None
            
            # Test with allow_config_fallback=True
            manager = LLMManager(config_dir=str(temp_config_dir), allow_config_fallback=True)
            resolved_key = manager.resolve_api_key("openai")
            
            assert resolved_key == "config_file_key"
        finally:
            # Restore original environment
            if original_test_mode:
                os.environ["IOA_TEST_MODE"] = original_test_mode
            if original_disable_config:
                os.environ["IOA_DISABLE_LLM_CONFIG"] = original_disable_config
    
    def test_ioa_config_home_override(self, tmp_path):
        """Test that $IOA_CONFIG_HOME overrides default config directory."""
        # Create config in custom location
        custom_config_dir = tmp_path / "custom_config"
        custom_config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = custom_config_dir / "llm.json"
        config_data = {
            "version": 1,
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "custom_config_key",
                    "model": "gpt-4"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            import json
            json.dump(config_data, f)
        
        # Set IOA_CONFIG_HOME
        os.environ["IOA_CONFIG_HOME"] = str(custom_config_dir)
        
        # Clear environment variable
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        # Clear test mode flags for this specific test
        original_test_mode = os.environ.get("IOA_TEST_MODE")
        original_disable_config = os.environ.get("IOA_DISABLE_LLM_CONFIG")
        if "IOA_TEST_MODE" in os.environ:
            del os.environ["IOA_TEST_MODE"]
        if "IOA_DISABLE_LLM_CONFIG" in os.environ:
            del os.environ["IOA_DISABLE_LLM_CONFIG"]
        
        try:
            # Test custom config is used
            manager = LLMManager()  # Should use IOA_CONFIG_HOME
            resolved_key = manager.resolve_api_key("openai")
            
            assert resolved_key == "custom_config_key"
            assert str(manager.config_dir) == str(custom_config_dir)
        finally:
            # Restore original environment
            if original_test_mode:
                os.environ["IOA_TEST_MODE"] = original_test_mode
            if original_disable_config:
                os.environ["IOA_DISABLE_LLM_CONFIG"] = original_disable_config
