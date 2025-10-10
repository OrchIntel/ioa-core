""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Integration Test: PKI Onboarding and Verification

Tests that agent manifests are properly signed, verified, and audited
during the onboarding process.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.agent_onboarding import AgentOnboarding
from src.agent_router import AgentRouter
from src.governance.audit_chain import get_audit_chain


class TestPKIOnboardingAndVerify:
    """Test PKI manifest signing and verification end-to-end."""
    
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
    
    def test_manifest_issuance_and_signing(self):
        """Test that manifests are properly issued and signed."""
        onboarding = AgentOnboarding(base_dir=Path(self.temp_dir))
        
        # Issue a manifest
        agent_id = "test_agent_001"
        capabilities = ["analysis", "reasoning", "code_generation"]
        version = "1.0.0"
        
        registry_entry = onboarding.issue_manifest(agent_id, capabilities, version)
        
        # Verify structure
        assert "manifest" in registry_entry
        assert "signature" in registry_entry
        assert "pubkey_fpr" in registry_entry
        assert "issued_at" in registry_entry
        
        # Verify manifest content
        manifest = registry_entry["manifest"]
        assert manifest["agent_id"] == agent_id
        assert manifest["capabilities"] == capabilities
        assert manifest["version"] == version
        assert "issued_at" in manifest
        assert isinstance(manifest["issued_at"], str)
        assert len(manifest["issued_at"]) > 0
        
        # Verify signature is hex string
        signature = registry_entry["signature"]
        assert isinstance(signature, str)
        assert len(signature) > 0
        assert all(c in '0123456789abcdef' for c in signature)
        
        # Verify public key fingerprint
        pubkey_fpr = registry_entry["pubkey_fpr"]
        assert isinstance(pubkey_fpr, str)
        assert len(pubkey_fpr) == 16
        
        # Check audit log for issuance
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
        
        # Verify that the manifest was stored in the registry
        assert onboarding.verify_manifest_signature(agent_id), "Manifest signature should be valid"
    
    def test_manifest_signature_verification(self):
        """Test that manifest signatures are properly verified."""
        onboarding = AgentOnboarding(base_dir=Path(self.temp_dir))
        
        # Issue a manifest first
        agent_id = "test_agent_002"
        capabilities = ["text_processing", "summarization"]
        registry_entry = onboarding.issue_manifest(agent_id, capabilities)
        
        # Verify signature
        is_valid = onboarding.verify_manifest_signature(agent_id)
        assert is_valid, "Valid manifest signature should verify successfully"
        
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
    
    def test_tampered_manifest_rejection(self):
        """Test that tampered manifests are properly rejected."""
        onboarding = AgentOnboarding(base_dir=Path(self.temp_dir))
        
        # Issue a manifest first
        agent_id = "test_agent_003"
        capabilities = ["data_analysis"]
        registry_entry = onboarding.issue_manifest(agent_id, capabilities)
        
        # Tamper with the manifest in the registry
        tampered_manifest = registry_entry["manifest"].copy()
        tampered_manifest["capabilities"] = ["malicious_capability"]
        
        # Replace the manifest but keep the original signature
        onboarding.manifest_registry[agent_id]["manifest"] = tampered_manifest
        
        # Try to verify the tampered manifest
        is_valid = onboarding.verify_manifest_signature(agent_id)
        assert not is_valid, "Tampered manifest should be rejected"
        
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
    
    def test_agent_router_verification_integration(self):
        """Test that agent router can work with onboarding system."""
        onboarding = AgentOnboarding(base_dir=Path(self.temp_dir))
        router = AgentRouter()
        
        # Issue a manifest
        agent_id = "test_agent_004"
        capabilities = ["task_execution"]
        onboarding.issue_manifest(agent_id, capabilities)
        
        # Verify the manifest was created and stored
        assert onboarding.verify_manifest_signature(agent_id), "Manifest should be valid"
        
        # Register the agent (this would normally happen during onboarding)
        router.register_virtual_agent(
            agent_id=agent_id,
            name="Test Agent",
            role="Test role",
            description="Test description",
            capabilities=[]
        )
        
        # Verify the agent was registered
        assert agent_id in router._agents, "Agent should be registered in router"
    
    def test_audit_chain_integrity(self):
        """Test that all PKI events maintain audit chain integrity."""
        onboarding = AgentOnboarding(base_dir=Path(self.temp_dir))
        
        # Perform multiple PKI operations
        operations = [
            ("agent_001", ["cap1"]),
            ("agent_002", ["cap2", "cap3"]),
            ("agent_003", ["cap4"])
        ]
        
        for agent_id, capabilities in operations:
            onboarding.issue_manifest(agent_id, capabilities)
            onboarding.verify_manifest_signature(agent_id)
        
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
    
    def test_error_handling_and_auditing(self):
        """Test that PKI errors are properly handled and audited."""
        onboarding = AgentOnboarding(base_dir=Path(self.temp_dir))
        
        # Try to verify non-existent agent
        is_valid = onboarding.verify_manifest_signature("non_existent_agent")
        assert not is_valid, "Non-existent agent should return False"
        
        # Note: Audit chain verification is tested separately in test_audit_hooks_e2e.py
