"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
Test roundtable configuration loading functionality.

Tests loading roundtable plans, field validation, and fallback to defaults
when configuration is missing or invalid.
"""

import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch

import pytest

# PATCH: Cursor-2025-08-15 CL-LLM-Manager Roundtable configuration tests
from src.llm_manager import LLMManager, LLMConfigError


class TestRoundtableConfigLoad:
    """Test roundtable configuration loading and validation."""
    
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
    
    def test_load_default_roundtable_config(self):
        """Test loading default roundtable configuration when no file exists."""
        manager = LLMManager(str(self.config_dir))
        
        # Check default roundtable configuration
        default_config = manager._roundtable_config
        
        assert default_config["version"] == 1
        assert default_config["active"] == "default"
        assert "default" in default_config["tables"]
        
        # Check default table structure
        default_table = default_config["tables"]["default"]
        assert default_table["quorum"] == 2
        assert default_table["merge_strategy"] == "vote_majority"
        assert len(default_table["participants"]) == 2
        
        # Check participant structure
        for participant in default_table["participants"]:
            assert "provider" in participant
            assert "model" in participant
            assert "weight" in participant
            assert "max_tokens" in participant
            assert isinstance(participant["weight"], float)
            assert isinstance(participant["max_tokens"], int)
    
    def test_load_custom_roundtable_config(self):
        """Test loading custom roundtable configuration from file."""
        # Create custom roundtable configuration
        roundtable_config = {
            "version": 1,
            "active": "custom",
            "tables": {
                "custom": {
                    "quorum": 3,
                    "merge_strategy": "confidence_weighted",
                    "participants": [
                        {
                            "provider": "openai",
                            "model": "gpt-4o-mini",
                            "weight": 1.0,
                            "max_tokens": 1024
                        },
                        {
                            "provider": "anthropic",
                            "model": "claude-3-sonnet",
                            "weight": 0.8,
                            "max_tokens": 512
                        },
                        {
                            "provider": "google",
                            "model": "gemini-1.5-pro",
                            "weight": 0.6,
                            "max_tokens": 768
                        }
                    ]
                }
            }
        }
        
        # Write configuration file
        roundtable_config_path = self.config_dir / "roundtable.json"
        with open(roundtable_config_path, 'w') as f:
            json.dump(roundtable_config, f)
        
        # Load configuration
        manager = LLMManager(str(self.config_dir))
        
        # Check that custom configuration was loaded
        assert manager._roundtable_config["active"] == "custom"
        assert "custom" in manager._roundtable_config["tables"]
        
        # Check custom table structure
        custom_table = manager._roundtable_config["tables"]["custom"]
        assert custom_table["quorum"] == 3
        assert custom_table["merge_strategy"] == "confidence_weighted"
        assert len(custom_table["participants"]) == 3
        
        # Check participant details
        openai_participant = next(p for p in custom_table["participants"] if p["provider"] == "openai")
        assert openai_participant["model"] == "gpt-4o-mini"
        assert openai_participant["weight"] == 1.0
        assert openai_participant["max_tokens"] == 1024
        
        anthropic_participant = next(p for p in custom_table["participants"] if p["provider"] == "anthropic")
        assert anthropic_participant["model"] == "claude-3-sonnet"
        assert anthropic_participant["weight"] == 0.8
        assert anthropic_participant["max_tokens"] == 512
    
    def test_get_roundtable_by_name(self):
        """Test getting roundtable configuration by name."""
        manager = LLMManager(str(self.config_dir))
        
        # Get default roundtable
        default_table = manager.get_roundtable("default")
        assert default_table["quorum"] == 2
        assert default_table["merge_strategy"] == "vote_majority"
        
        # Get non-existent roundtable
        non_existent = manager.get_roundtable("non_existent")
        assert non_existent == {}
    
    def test_create_roundtable(self):
        """Test creating a new roundtable configuration."""
        manager = LLMManager(str(self.config_dir))
        
        # Create custom roundtable
        custom_config = {
            "quorum": 4,
            "merge_strategy": "concat_summaries",
            "participants": [
                {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "weight": 1.0,
                    "max_tokens": 2048
                }
            ]
        }
        
        manager.create_roundtable("custom", custom_config)
        
        # Check that roundtable was created
        assert "custom" in manager._roundtable_config["tables"]
        
        # Verify configuration
        created_table = manager._roundtable_config["tables"]["custom"]
        assert created_table["quorum"] == 4
        assert created_table["merge_strategy"] == "concat_summaries"
        assert len(created_table["participants"]) == 1
        
        participant = created_table["participants"][0]
        assert participant["provider"] == "openai"
        assert participant["model"] == "gpt-4o"
        assert participant["weight"] == 1.0
        assert participant["max_tokens"] == 2048
    
    def test_update_existing_roundtable(self):
        """Test updating an existing roundtable configuration."""
        manager = LLMManager(str(self.config_dir))
        
        # Create initial roundtable
        initial_config = {
            "quorum": 2,
            "merge_strategy": "vote_majority",
            "participants": [
                {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "weight": 1.0,
                    "max_tokens": 512
                }
            ]
        }
        
        manager.create_roundtable("test", initial_config)
        
        # Update roundtable
        updated_config = {
            "quorum": 3,
            "merge_strategy": "confidence_weighted",
            "participants": [
                {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "weight": 1.0,
                    "max_tokens": 1024
                },
                {
                    "provider": "anthropic",
                    "model": "claude-3-haiku",
                    "weight": 0.8,
                    "max_tokens": 512
                }
            ]
        }
        
        manager.create_roundtable("test", updated_config)
        
        # Check that roundtable was updated
        updated_table = manager._roundtable_config["tables"]["test"]
        assert updated_table["quorum"] == 3
        assert updated_table["merge_strategy"] == "confidence_weighted"
        assert len(updated_table["participants"]) == 2
        
        # Check that participant was updated
        openai_participant = next(p for p in updated_table["participants"] if p["provider"] == "openai")
        assert openai_participant["model"] == "gpt-4o"
        assert openai_participant["max_tokens"] == 1024
    
    def test_activate_roundtable(self):
        """Test activating a roundtable configuration."""
        manager = LLMManager(str(self.config_dir))
        
        # Create custom roundtable
        custom_config = {
            "quorum": 2,
            "merge_strategy": "vote_majority",
            "participants": [
                {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "weight": 1.0,
                    "max_tokens": 512
                }
            ]
        }
        
        manager.create_roundtable("custom", custom_config)
        
        # Activate custom roundtable
        manager.activate_roundtable("custom")
        
        # Check that custom roundtable is active
        assert manager._roundtable_config["active"] == "custom"
    
    def test_activate_nonexistent_roundtable(self):
        """Test activating a non-existent roundtable."""
        manager = LLMManager(str(self.config_dir))
        
        # Try to activate non-existent roundtable
        with pytest.raises(LLMConfigError, match="Roundtable nonexistent not found"):
            manager.activate_roundtable("nonexistent")
    
    def test_list_roundtables(self):
        """Test listing roundtable configurations."""
        manager = LLMManager(str(self.config_dir))
        
        # Initially only default roundtable
        roundtables = manager.list_roundtables()
        assert roundtables == ["default"]
        
        # Create additional roundtable
        custom_config = {
            "quorum": 2,
            "merge_strategy": "vote_majority",
            "participants": [
                {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "weight": 1.0,
                    "max_tokens": 512
                }
            ]
        }
        
        manager.create_roundtable("custom", custom_config)
        
        # Check that both roundtables are listed
        roundtables = manager.list_roundtables()
        assert "default" in roundtables
        assert "custom" in roundtables
        assert len(roundtables) == 2
    
    def test_get_active_roundtable(self):
        """Test getting the active roundtable name."""
        manager = LLMManager(str(self.config_dir))
        
        # Initially default is active
        assert manager.get_active_roundtable() == "default"
        
        # Create and activate custom roundtable
        custom_config = {
            "quorum": 2,
            "merge_strategy": "vote_majority",
            "participants": [
                {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "weight": 1.0,
                    "max_tokens": 512
                }
            ]
        }
        
        manager.create_roundtable("custom", custom_config)
        manager.activate_roundtable("custom")
        
        # Check that custom is now active
        assert manager.get_active_roundtable() == "custom"
    
    def test_roundtable_persistence(self):
        """Test that roundtable configuration persists across manager instances."""
        # Create first manager instance
        manager1 = LLMManager(str(self.config_dir))
        
        # Create custom roundtable
        custom_config = {
            "quorum": 5,
            "merge_strategy": "concat_summaries",
            "participants": [
                {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "weight": 1.0,
                    "max_tokens": 1024
                }
            ]
        }
        
        manager1.create_roundtable("persistent", custom_config)
        manager1.activate_roundtable("persistent")
        
        # Create second manager instance
        manager2 = LLMManager(str(self.config_dir))
        
        # Check that configuration was persisted
        assert "persistent" in manager2._roundtable_config["tables"]
        assert manager2._roundtable_config["active"] == "persistent"
        
        # Check configuration details
        persistent_table = manager2._roundtable_config["tables"]["persistent"]
        assert persistent_table["quorum"] == 5
        assert persistent_table["merge_strategy"] == "concat_summaries"
        assert len(persistent_table["participants"]) == 1
    
    def test_roundtable_config_validation(self):
        """Test that roundtable configuration is properly validated."""
        manager = LLMManager(str(self.config_dir))
        
        # Test with valid configuration
        valid_config = {
            "quorum": 2,
            "merge_strategy": "vote_majority",
            "participants": [
                {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "weight": 1.0,
                    "max_tokens": 512
                }
            ]
        }
        
        # Should not raise any errors
        manager.create_roundtable("valid", valid_config)
        
        # Test with missing required fields
        invalid_config = {
            "quorum": 2,
            # Missing merge_strategy and participants
        }
        
        # Should still work (missing fields will be handled gracefully)
        manager.create_roundtable("invalid", invalid_config)
        
        # Check that roundtable was created
        assert "invalid" in manager._roundtable_config["tables"]
    
    def test_roundtable_config_with_different_merge_strategies(self):
        """Test roundtable configuration with different merge strategies."""
        manager = LLMManager(str(self.config_dir))
        
        # Test vote_majority strategy
        majority_config = {
            "quorum": 2,
            "merge_strategy": "vote_majority",
            "participants": [
                {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "weight": 1.0,
                    "max_tokens": 512
                }
            ]
        }
        
        manager.create_roundtable("majority", majority_config)
        
        # Test concat_summaries strategy
        concat_config = {
            "quorum": 2,
            "merge_strategy": "concat_summaries",
            "participants": [
                {
                    "provider": "anthropic",
                    "model": "claude-3-haiku",
                    "weight": 1.0,
                    "max_tokens": 512
                }
            ]
        }
        
        manager.create_roundtable("concat", concat_config)
        
        # Test confidence_weighted strategy
        weighted_config = {
            "quorum": 2,
            "merge_strategy": "confidence_weighted",
            "participants": [
                {
                    "provider": "google",
                    "model": "gemini-1.5-pro",
                    "weight": 1.0,
                    "max_tokens": 512
                }
            ]
        }
        
        manager.create_roundtable("weighted", weighted_config)
        
        # Check that all roundtables were created
        roundtables = manager.list_roundtables()
        assert "majority" in roundtables
        assert "concat" in roundtables
        assert "weighted" in roundtables
        
        # Check merge strategies
        assert manager._roundtable_config["tables"]["majority"]["merge_strategy"] == "vote_majority"
        assert manager._roundtable_config["tables"]["concat"]["merge_strategy"] == "concat_summaries"
        assert manager._roundtable_config["tables"]["weighted"]["merge_strategy"] == "confidence_weighted"
    
    def test_roundtable_config_with_various_quorum_sizes(self):
        """Test roundtable configuration with various quorum sizes."""
        manager = LLMManager(str(self.config_dir))
        
        # Test different quorum sizes
        for quorum in [1, 2, 3, 5, 10]:
            config = {
                "quorum": quorum,
                "merge_strategy": "vote_majority",
                "participants": [
                    {
                        "provider": "openai",
                        "model": "gpt-4o-mini",
                        "weight": 1.0,
                        "max_tokens": 512
                    }
                ]
            }
            
            roundtable_name = f"quorum_{quorum}"
            manager.create_roundtable(roundtable_name, config)
            
            # Check that quorum was set correctly
            created_table = manager._roundtable_config["tables"][roundtable_name]
            assert created_table["quorum"] == quorum
    
    def test_roundtable_config_with_various_weights(self):
        """Test roundtable configuration with various participant weights."""
        manager = LLMManager(str(self.config_dir))
        
        # Test different weight values
        weights = [0.1, 0.5, 1.0, 1.5, 2.0]
        
        config = {
            "quorum": 2,
            "merge_strategy": "vote_majority",
            "participants": []
        }
        
        for i, weight in enumerate(weights):
            config["participants"].append({
                "provider": f"provider_{i}",
                "model": f"model_{i}",
                "weight": weight,
                "max_tokens": 512
            })
        
        manager.create_roundtable("weighted", config)
        
        # Check that weights were set correctly
        created_table = manager._roundtable_config["tables"]["weighted"]
        for i, participant in enumerate(created_table["participants"]):
            assert participant["weight"] == weights[i]
    
    def test_roundtable_config_with_various_max_tokens(self):
        """Test roundtable configuration with various max token values."""
        manager = LLMManager(str(self.config_dir))
        
        # Test different max token values
        max_tokens_values = [128, 256, 512, 1024, 2048, 4096]
        
        config = {
            "quorum": 2,
            "merge_strategy": "vote_majority",
            "participants": []
        }
        
        for i, max_tokens in enumerate(max_tokens_values):
            config["participants"].append({
                "provider": f"provider_{i}",
                "model": f"model_{i}",
                "weight": 1.0,
                "max_tokens": max_tokens
            })
        
        manager.create_roundtable("tokens", config)
        
        # Check that max tokens were set correctly
        created_table = manager._roundtable_config["tables"]["tokens"]
        for i, participant in enumerate(created_table["participants"]):
            assert participant["max_tokens"] == max_tokens_values[i]
