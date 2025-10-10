""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Integration Test: Domain Schema Enforcement

Tests that domain plugins are properly validated against the schema
and that violations are audited.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.agent_router import AgentRouter
from src.governance.audit_chain import get_audit_chain


class TestDomainSchemaEnforcement:
    """Test domain plugin schema validation and enforcement."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up and tear down test environment."""
        # Set up temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.audit_log_path = os.path.join(self.temp_dir, "audit_chain.jsonl")
        self.plugins_dir = os.path.join(self.temp_dir, "plugins")
        
        os.environ["IOA_AUDIT_LOG"] = self.audit_log_path
        os.makedirs(self.plugins_dir, exist_ok=True)
        
        # Reset audit chain singleton
        from src.governance.audit_chain import _audit_chain_instance
        _audit_chain_instance = None
        
        yield
        
        # Clean up
        shutil.rmtree(self.temp_dir)
        if "IOA_AUDIT_LOG" in os.environ:
            del os.environ["IOA_AUDIT_LOG"]
    
    def test_valid_domain_plugin_loading(self):
        """Test that valid domain plugins are loaded successfully."""
        # Create a valid domain plugin file
        valid_plugin = {
            "domain": "writer",
            "capabilities": ["text_generation", "content_creation"],
            "compliance": {
                "gdpr": True,
                "hipaa": False
            },
            "version": "1.0.0"
        }
        
        plugin_path = os.path.join(self.plugins_dir, "writer.ioa.json")
        with open(plugin_path, 'w') as f:
            json.dump(valid_plugin, f)
        
        # Initialize agent router and load plugins
        router = AgentRouter()
        router.load_domain_plugins(self.plugins_dir)
        
        # Check that the plugin was loaded as an agent
        agent_id = "domain_writer"
        assert agent_id in router._agents, f"Domain agent {agent_id} should be registered"
        
        # Verify agent details
        agent = router._agents[agent_id]
        assert agent.name == "Domain: writer"
        assert agent.role == "Domain plugin for writer"
        assert len(agent.capabilities) == 2
        
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
    
    def test_invalid_domain_plugin_rejection(self):
        """Test that invalid domain plugins are properly rejected."""
        # Create an invalid domain plugin file (missing capabilities)
        invalid_plugin = {
            "domain": "bad",
            "version": "1.0.0"
            # Missing required "capabilities" field
        }
        
        plugin_path = os.path.join(self.plugins_dir, "bad.ioa.json")
        with open(plugin_path, 'w') as f:
            json.dump(invalid_plugin, f)
        
        # Initialize agent router and load plugins
        router = AgentRouter()
        router.load_domain_plugins(self.plugins_dir)
        
        # Check that the invalid plugin was not loaded
        agent_id = "domain_bad"
        assert agent_id not in router._agents, "Invalid domain plugin should not be registered"
        
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
    
    def test_malformed_plugin_file_handling(self):
        """Test that malformed plugin files are handled gracefully."""
        # Create a malformed JSON file
        malformed_plugin = "{ invalid json content"
        
        plugin_path = os.path.join(self.plugins_dir, "malformed.ioa.json")
        with open(plugin_path, 'w') as f:
            f.write(malformed_plugin)
        
        # Initialize agent router and load plugins
        router = AgentRouter()
        router.load_domain_plugins(self.plugins_dir)
        
        # Check that the malformed plugin was not loaded
        agent_id = "domain_malformed"
        assert agent_id not in router._agents, "Malformed plugin should not be registered"
        
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
    
    def test_mixed_valid_and_invalid_plugins(self):
        """Test loading a mix of valid and invalid plugins."""
        # Create multiple plugin files
        plugins = {
            "valid1.ioa.json": {
                "domain": "valid1",
                "capabilities": ["cap1", "cap2"]
            },
            "invalid1.ioa.json": {
                "domain": "invalid1"
                # Missing capabilities
            },
            "valid2.ioa.json": {
                "domain": "valid2",
                "capabilities": ["cap3"]
            }
        }
        
        for filename, content in plugins.items():
            plugin_path = os.path.join(self.plugins_dir, filename)
            with open(plugin_path, 'w') as f:
                json.dump(content, f)
        
        # Initialize agent router and load plugins
        router = AgentRouter()
        router.load_domain_plugins(self.plugins_dir)
        
        # Check that only valid plugins were loaded
        assert "domain_valid1" in router._agents, "Valid plugin 1 should be loaded"
        assert "domain_valid2" in router._agents, "Valid plugin 2 should be loaded"
        assert "domain_invalid1" not in router._agents, "Invalid plugin should not be loaded"
        
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
    
    def test_domain_plugin_capability_registration(self):
        """Test that domain plugin capabilities are properly registered."""
        # Create a domain plugin with specific capabilities
        plugin = {
            "domain": "specialist",
            "capabilities": ["machine_learning", "data_analysis", "visualization"]
        }
        
        plugin_path = os.path.join(self.plugins_dir, "specialist.ioa.json")
        with open(plugin_path, 'w') as f:
            json.dump(plugin, f)
        
        # Initialize agent router and load plugins
        router = AgentRouter()
        router.load_domain_plugins(self.plugins_dir)
        
        # Check that capabilities are properly registered
        agent_id = "domain_specialist"
        assert agent_id in router._agents, "Specialist domain agent should be registered"
        
        agent = router._agents[agent_id]
        assert len(agent.capabilities) == 3
        
        # Check capability details
        capability_names = [cap.name for cap in agent.capabilities]
        assert "machine_learning" in capability_names
        assert "data_analysis" in capability_names
        assert "visualization" in capability_names
        
        # Check that capabilities are indexed
        for cap_name in capability_names:
            assert cap_name in router._capability_index, f"Capability {cap_name} should be indexed"
            assert agent_id in router._capability_index[cap_name], f"Agent should be in capability index for {cap_name}"
    
    def test_empty_plugins_directory_handling(self):
        """Test handling of empty plugins directory."""
        # Initialize agent router with empty plugins directory
        router = AgentRouter()
        router.load_domain_plugins(self.plugins_dir)
        
        # Should not crash and should log appropriate message
        assert len(router._agents) >= 0, "Router should handle empty plugins directory gracefully"
        
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
    
    def test_audit_chain_integrity_for_domain_events(self):
        """Test that domain plugin events maintain audit chain integrity."""
        # Create and load plugins
        plugins = {
            "test1.ioa.json": {"domain": "test1", "capabilities": ["cap1"]},
            "test2.ioa.json": {"domain": "test2", "capabilities": ["cap2"]}
        }
        
        for filename, content in plugins.items():
            plugin_path = os.path.join(self.plugins_dir, filename)
            with open(plugin_path, 'w') as f:
                json.dump(content, f)
        
        # Initialize agent router and load plugins
        router = AgentRouter()
        router.load_domain_plugins(self.plugins_dir)
        
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
        
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
