"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
Test LLM Manager environment variable merging functionality.

Tests that environment variables are properly merged with file configuration,
with file configuration taking precedence.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

# PATCH: Cursor-2025-08-15 CL-LLM-Manager Environment merge tests
from src.llm_manager import LLMManager


class TestLLMManagerEnvironmentMerge:
    """Test LLM Manager environment variable merging."""
    
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
    
    def test_merge_openai_env_vars(self):
        """Test merging OpenAI environment variables."""
        # Set environment variables
        env_vars = {
            "OPENAI_API_KEY": "sk-env-test123",
            "OPENAI_MODEL": "gpt-4o-env"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = LLMManager(str(self.config_dir))
            
            # Check that environment variables were merged
            assert "openai" in manager._config["providers"]
            assert manager._config["providers"]["openai"]["api_key"] == "sk-env-test123"
            assert manager._config["providers"]["openai"]["model"] == "gpt-4o-env"
    
    def test_merge_anthropic_env_vars(self):
        """Test merging Anthropic environment variables."""
        # Set environment variables
        env_vars = {
            "ANTHROPIC_API_KEY": "sk-ant-env-test456",
            "ANTHROPIC_MODEL": "claude-3-sonnet-env"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = LLMManager(str(self.config_dir))
            
            # Check that environment variables were merged
            assert "anthropic" in manager._config["providers"]
            assert manager._config["providers"]["anthropic"]["api_key"] == "sk-ant-env-test456"
            assert manager._config["providers"]["anthropic"]["model"] == "claude-3-sonnet-env"
    
    def test_merge_google_env_vars(self):
        """Test merging Google environment variables."""
        # Set environment variables
        env_vars = {
            "GOOGLE_API_KEY": "google-env-test789",
            "GOOGLE_MODEL": "gemini-1.5-flash-env"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = LLMManager(str(self.config_dir))
            
            # Check that environment variables were merged
            assert "google" in manager._config["providers"]
            assert manager._config["providers"]["google"]["api_key"] == "google-env-test789"
            assert manager._config["providers"]["google"]["model"] == "gemini-1.5-flash-env"
    
    def test_merge_groq_env_vars(self):
        """Test merging Groq environment variables."""
        # Set environment variables
        env_vars = {
            "GROQ_API_KEY": "groq-env-test101",
            "GROQ_MODEL": "llama-3-70b-env"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = LLMManager(str(self.config_dir))
            
            # Check that environment variables were merged
            assert "groq" in manager._config["providers"]
            assert manager._config["providers"]["groq"]["api_key"] == "groq-env-test101"
            assert manager._config["providers"]["groq"]["model"] == "llama-3-70b-env"
    
    def test_merge_ollama_env_vars(self):
        """Test merging Ollama environment variables."""
        # Set environment variables
        env_vars = {
            "OLLAMA_HOST": "http://localhost:11435",
            "OLLAMA_MODEL": "llama3-env"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = LLMManager(str(self.config_dir))
            
            # Check that environment variables were merged
            assert "ollama" in manager._config["providers"]
            assert manager._config["providers"]["ollama"]["host"] == "http://localhost:11435"
            assert manager._config["providers"]["ollama"]["model"] == "llama3-env"
    
    def test_file_config_takes_precedence(self):
        """Test that file configuration takes precedence over environment variables."""
        # Set environment variables
        env_vars = {
            "OPENAI_API_KEY": "sk-env-test123",
            "OPENAI_MODEL": "gpt-4o-env"
        }
        
        # Create file configuration
        llm_config_path = self.config_dir / "llm.json"
        file_config = {
            "version": 1,
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "sk-file-test456",
                    "model": "gpt-4o-file"
                }
            }
        }
        
        import json
        with open(llm_config_path, 'w') as f:
            json.dump(file_config, f)
        
        # Initialize manager with both file and env config
        with patch.dict(os.environ, env_vars):
            manager = LLMManager(str(self.config_dir))
            
            # Check that file configuration takes precedence
            assert "openai" in manager._config["providers"]
            assert manager._config["providers"]["openai"]["api_key"] == "sk-file-test456"
            assert manager._config["providers"]["openai"]["model"] == "gpt-4o-file"
    
    def test_partial_env_merge(self):
        """Test merging when only some environment variables are set."""
        # Set only API key, not model
        env_vars = {
            "OPENAI_API_KEY": "sk-env-test123"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = LLMManager(str(self.config_dir))
            
            # Check that API key was merged
            assert "openai" in manager._config["providers"]
            assert manager._config["providers"]["openai"]["api_key"] == "sk-env-test123"
            
            # Check that default model is used
            assert "model" not in manager._config["providers"]["openai"]
    
    def test_multiple_providers_from_env(self):
        """Test merging multiple providers from environment variables."""
        # Set environment variables for multiple providers
        env_vars = {
            "OPENAI_API_KEY": "sk-openai-env",
            "OPENAI_MODEL": "gpt-4o-mini",
            "ANTHROPIC_API_KEY": "sk-ant-env",
            "ANTHROPIC_MODEL": "claude-3-haiku",
            "GOOGLE_API_KEY": "google-env",
            "GOOGLE_MODEL": "gemini-1.5-pro"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = LLMManager(str(self.config_dir))
            
            # Check that all providers were merged
            providers = manager.list_providers()
            assert "openai" in providers
            assert "anthropic" in providers
            assert "google" in providers
            
            # Check OpenAI configuration
            openai_config = manager.get_provider_config("openai")
            assert openai_config["api_key"] == "sk-openai-env"
            assert openai_config["model"] == "gpt-4o-mini"
            
            # Check Anthropic configuration
            anthropic_config = manager.get_provider_config("anthropic")
            assert anthropic_config["api_key"] == "sk-ant-env"
            assert anthropic_config["model"] == "claude-3-haiku"
            
            # Check Google configuration
            google_config = manager.get_provider_config("google")
            assert google_config["api_key"] == "google-env"
            assert google_config["model"] == "gemini-1.5-pro"
    
    def test_env_merge_with_existing_file_config(self):
        """Test merging environment variables with existing file configuration."""
        # Create initial file configuration
        llm_config_path = self.config_dir / "llm.json"
        initial_config = {
            "version": 1,
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "sk-file-initial",
                    "model": "gpt-4o-mini"
                }
            }
        }
        
        import json
        with open(llm_config_path, 'w') as f:
            json.dump(initial_config, f)
        
        # Set environment variables
        env_vars = {
            "ANTHROPIC_API_KEY": "sk-ant-env-new",
            "ANTHROPIC_MODEL": "claude-3-haiku"
        }
        
        # Initialize manager
        with patch.dict(os.environ, env_vars):
            manager = LLMManager(str(self.config_dir))
            
            # Check that existing file config is preserved
            openai_config = manager.get_provider_config("openai")
            assert openai_config["api_key"] == "sk-file-initial"
            assert openai_config["model"] == "gpt-4o-mini"
            
            # Check that new env config was added
            anthropic_config = manager.get_provider_config("anthropic")
            assert anthropic_config["api_key"] == "sk-ant-env-new"
            assert anthropic_config["model"] == "claude-3-haiku"
    
    def test_env_merge_handles_missing_vars(self):
        """Test that missing environment variables don't cause errors."""
        # Don't set any environment variables
        manager = LLMManager(str(self.config_dir))
        
        # Should initialize with default configuration
        assert manager._config["version"] == 1
        assert manager._config["default_provider"] == "openai"
        assert manager._config["providers"] == {}
    
    def test_env_merge_with_special_characters(self):
        """Test merging environment variables with special characters."""
        # Set environment variables with special characters
        env_vars = {
            "OPENAI_API_KEY": "sk-test!@#$%^&*()",
            "OPENAI_MODEL": "gpt-4o-mini-v2.0"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = LLMManager(str(self.config_dir))
            
            # Check that special characters are preserved
            openai_config = manager.get_provider_config("openai")
            assert openai_config["api_key"] == "sk-test!@#$%^&*()"
            assert openai_config["model"] == "gpt-4o-mini-v2.0"
