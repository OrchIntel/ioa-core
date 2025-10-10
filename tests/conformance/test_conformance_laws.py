""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the modules we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ioa_core.governance.manifest import (
    load_manifest, verify_signature, get_laws, SystemLaws
)
from ioa_core.governance.policy_engine import (
    PolicyEngine, ActionContext, ValidationStatus, ActionRiskLevel
)
from ioa_core.governance.system_laws import (
    SystemIntegrityError, SignatureVerificationError, LawViolationError, SystemLawsError
)
from ioa_core.connectors.base import ConnectorBase, ConnectorCapabilities, ConnectorContext


class TestSystemLawsManifest:
    """Test System Laws manifest loading and validation."""
    
    def test_manifest_structure_validation(self):
        """Test that manifest structure validation works correctly."""
        # Create a valid manifest structure
        valid_manifest = {
            "version": "1.0",
            "laws": [
                {
                    "id": "law1",
                    "name": "Test Law",
                    "enforcement": "critical",
                    "description": "Test law description",
                    "scope": ["test_scope"]
                }
            ],
            "policy": {
                "conflict_resolution": ["law1"],
                "jurisdiction": {"default": "global", "affinity": ["global"]},
                "fairness": {"threshold": 0.2, "metrics": [], "mitigation_strategies": []}
            },
            "signature": {
                "alg": "RS256",
                "kid": "test-key",
                "value": "test-signature",
                "timestamp": "2025-09-03T00:00:00Z"
            },
            "metadata": {
                "created": "2025-09-03T00:00:00Z",
                "expires": "2026-09-03T00:00:00Z",
                "issuer": "Test Issuer",
                "audience": "Test Audience"
            }
        }
        
        system_laws = SystemLaws(valid_manifest)
        assert system_laws.validate_manifest_structure() is True
    
    def test_manifest_missing_required_fields(self):
        """Test that manifest with missing fields fails validation."""
        invalid_manifest = {
            "version": "1.0",
            "laws": []  # Missing other required fields
        }
        
        system_laws = SystemLaws(invalid_manifest)
        assert system_laws.validate_manifest_structure() is False
    
    def test_law_lookup_by_id(self):
        """Test that laws can be looked up by ID."""
        manifest = {
            "version": "1.0",
            "laws": [
                {
                    "id": "law1",
                    "name": "Test Law 1",
                    "enforcement": "critical",
                    "description": "Test law 1 description",
                    "scope": ["test_scope"]
                },
                {
                    "id": "law2", 
                    "name": "Test Law 2",
                    "enforcement": "high",
                    "description": "Test law 2 description",
                    "scope": ["test_scope"]
                }
            ],
            "policy": {
                "conflict_resolution": ["law1", "law2"],
                "jurisdiction": {"default": "global", "affinity": ["global"]},
                "fairness": {"threshold": 0.2, "metrics": [], "mitigation_strategies": []}
            },
            "signature": {
                "alg": "RS256",
                "kid": "test-key",
                "value": "test-signature",
                "timestamp": "2025-09-03T00:00:00Z"
            },
            "metadata": {
                "created": "2025-09-03T00:00:00Z",
                "expires": "2026-09-03T00:00:00Z",
                "issuer": "Test Issuer",
                "audience": "Test Audience"
            }
        }
        
        system_laws = SystemLaws(manifest)
        
        law1 = system_laws.get_law("law1")
        assert law1 is not None
        assert law1["name"] == "Test Law 1"
        assert law1["enforcement"] == "critical"
        
        law2 = system_laws.get_law("law2")
        assert law2 is not None
        assert law2["name"] == "Test Law 2"
        assert law2["enforcement"] == "high"
        
        # Test non-existent law
        non_existent = system_laws.get_law("law99")
        assert non_existent is None
    
    def test_critical_law_detection(self):
        """Test that critical laws are correctly identified."""
        manifest = {
            "version": "1.0",
            "laws": [
                {
                    "id": "law1",
                    "name": "Critical Law",
                    "enforcement": "critical",
                    "description": "Critical law description",
                    "scope": ["test_scope"]
                },
                {
                    "id": "law2",
                    "name": "High Law", 
                    "enforcement": "high",
                    "description": "High law description",
                    "scope": ["test_scope"]
                }
            ],
            "policy": {
                "conflict_resolution": ["law1", "law2"],
                "jurisdiction": {"default": "global", "affinity": ["global"]},
                "fairness": {"threshold": 0.2, "metrics": [], "mitigation_strategies": []}
            },
            "signature": {
                "alg": "RS256",
                "kid": "test-key",
                "value": "test-signature",
                "timestamp": "2025-09-03T00:00:00Z"
            },
            "metadata": {
                "created": "2025-09-03T00:00:00Z",
                "expires": "2026-09-03T00:00:00Z",
                "issuer": "Test Issuer",
                "audience": "Test Audience"
            }
        }
        
        system_laws = SystemLaws(manifest)
        
        assert system_laws.is_critical_law("law1") is True
        assert system_laws.is_critical_law("law2") is False
        assert system_laws.is_critical_law("law99") is False


class TestPolicyEngine:
    """Test Policy Engine enforcement of System Laws."""
    
    @pytest.fixture
    def policy_engine(self):
        """Create a policy engine for testing."""
        with patch('ioa_core.governance.manifest.get_laws') as mock_get_laws:
            # Create a mock SystemLaws instance
            mock_laws = MagicMock()
            mock_laws.get_fairness_threshold.return_value = 0.2
            mock_laws.get_conflict_resolution_order.return_value = ["law1", "law2", "law3"]
            mock_laws.get_law.side_effect = lambda law_id: {
                "id": law_id,
                "name": f"Test {law_id}",
                "enforcement": "critical" if law_id == "law1" else "high",
                "description": f"Test {law_id} description",
                "scope": ["test_scope"]
            }
            mock_laws.is_critical_law.side_effect = lambda law_id: law_id == "law1"
            
            mock_get_laws.return_value = mock_laws
            
            return PolicyEngine()
    
    def test_action_validation_approved(self, policy_engine):
        """Test that valid actions are approved."""
        action_ctx = ActionContext(
            action_id="test-action-1",
            action_type="test_action",
            actor_id="test-actor",
            risk_level=ActionRiskLevel.LOW
        )
        
        result = policy_engine.validate_against_laws(action_ctx)
        
        assert result.status == ValidationStatus.APPROVED
        assert result.action_id == "test-action-1"
        assert result.audit_id is not None
        assert len(result.laws_checked) > 0
        assert len(result.violations) == 0
        assert len(result.required_approvals) == 0
    
    def test_action_validation_requires_approval(self, policy_engine):
        """Test that high-risk actions require approval."""
        action_ctx = ActionContext(
            action_id="test-action-2",
            action_type="reflex_action",
            actor_id="test-actor",
            risk_level=ActionRiskLevel.HIGH
        )
        
        result = policy_engine.validate_against_laws(action_ctx)
        
        assert result.status == ValidationStatus.REQUIRES_APPROVAL
        assert result.action_id == "test-action-2"
        assert len(result.required_approvals) > 0
    
    def test_fairness_violation_detection(self, policy_engine):
        """Test that fairness violations are detected and blocked."""
        action_ctx = ActionContext(
            action_id="test-action-3",
            action_type="llm_generation",
            actor_id="test-actor",
            risk_level=ActionRiskLevel.LOW,
            metadata={
                "demographic_data": {
                    "age_bias": 0.9,  # Above threshold
                    "gender_bias": 0.1
                }
            }
        )
        
        result = policy_engine.validate_against_laws(action_ctx)
        
        # Should be blocked due to fairness violation
        assert result.status == ValidationStatus.BLOCKED
        assert result.fairness_score is not None
        assert result.fairness_score > 0.2  # Above threshold
    
    def test_policy_event_emission(self, policy_engine):
        """Test that policy events are emitted during validation."""
        events_received = []
        
        def event_handler(event):
            events_received.append(event)
        
        policy_engine.register_policy_event_handler(event_handler)
        
        action_ctx = ActionContext(
            action_id="test-action-4",
            action_type="test_action",
            actor_id="test-actor",
            risk_level=ActionRiskLevel.LOW
        )
        
        policy_engine.validate_against_laws(action_ctx)
        
        assert len(events_received) > 0
        assert events_received[0]["event_type"] == "action_validated"
        assert "action_id" in events_received[0]["data"]


class TestConnectorGuardrails:
    """Test connector guardrails and System Laws enforcement."""
    
    class MockConnector(ConnectorBase):
        """Mock connector implementation for testing."""
        
        def __init__(self, connector_id: str, capabilities: ConnectorCapabilities):
            """Initialize mock connector with required attributes."""
            super().__init__(connector_id, capabilities)
            self.data = {"test": "data"}
            self.execution_count = 0
            self.name = "mock-connector"
        
        def _execute_action(self, action_type: str, ctx, **kwargs):
            self.execution_count += 1
            return {"result": "success", "action_type": action_type, "execution_count": self.execution_count}
    
    @pytest.fixture
    def test_connector(self):
        """Create a test connector."""
        capabilities = ConnectorCapabilities(
            name="Test Connector",
            version="1.0.0",
            supported_actions=["test_action", "data_export"],
            data_classifications=["public", "internal"],
            jurisdictions=["global", "US"],
            security_clearance="standard"
        )
        
        # Use the explicit class reference to avoid relying on 'self' in pytest fixtures
        return TestConnectorGuardrails.MockConnector("test-connector-1", capabilities)
    
    def test_connector_capability_validation(self, test_connector):
        """Test that connector capabilities are validated."""
        # Valid action
        ctx = ConnectorContext(
            connector_id="test-connector-1",
            action_type="test_action",
            actor_id="test-actor",
            data_classification="public",
            jurisdiction="global"
        )
        
        result = test_connector.validate_connector_caps(ctx)
        assert result.status == ValidationStatus.APPROVED
        
        # Invalid action type
        ctx.action_type = "unsupported_action"
        result = test_connector.validate_connector_caps(ctx)
        assert result.status == ValidationStatus.BLOCKED
    
    def test_connector_jurisdiction_validation(self, test_connector):
        """Test that connector jurisdiction constraints are enforced."""
        ctx = ConnectorContext(
            connector_id="test-connector-1",
            action_type="test_action",
            actor_id="test-actor",
            jurisdiction="EU"  # Not supported
        )
        
        result = test_connector.validate_connector_caps(ctx)
        assert result.status == ValidationStatus.BLOCKED
    
    def test_connector_security_clearance(self, test_connector):
        """Test that connector security clearance is enforced."""
        ctx = ConnectorContext(
            connector_id="test-connector-1",
            action_type="test_action",
            actor_id="test-actor",
            risk_level=ActionRiskLevel.CRITICAL
        )
        
        result = test_connector.validate_connector_caps(ctx)
        assert result.status == ValidationStatus.BLOCKED
    
    def test_connector_execution_with_laws(self, test_connector):
        """Test that connector execution respects System Laws."""
        # Valid execution
        result = test_connector.execute_with_laws(
            action_type="test_action",
            actor_id="test-actor"
        )
        
        assert "result" in result
        assert "audit_id" in result
        assert "policy_validation" in result
        
        # Blocked execution
        with pytest.raises(SystemLawsError):
            test_connector.execute_with_laws(
                action_type="unsupported_action",
                actor_id="test-actor"
            )


class TestSystemLawsIntegration:
    """Integration tests for System Laws enforcement."""
    
    def test_startup_verification_failure(self):
        """Test that IOA fails fast if manifest is invalid."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Create invalid manifest
            invalid_manifest = {
                "version": "1.0",
                "laws": []  # Missing required fields
            }
            json.dump(invalid_manifest, f)
            temp_path = f.name
        
        try:
            with pytest.raises(SystemIntegrityError):
                load_manifest(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_audit_id_propagation(self):
        """Test that audit_id appears in all governed actions."""
        # This test would verify that audit_id is propagated through
        # the entire execution chain
        pass
    
    def test_fairness_guard_functionality(self):
        """Test that fairness guard blocks biased outputs."""
        # This test would verify that the fairness detection
        # actually prevents biased outputs from being generated
        pass
    
    def test_hitl_override_functionality(self):
        """Test that HITL override unblocks actions."""
        # This test would verify that human approval
        # can unblock previously blocked actions
        pass


class TestConformanceChecklist:
    """Test the "Powered by IOA" conformance checklist."""
    
    def test_signature_tamper_detection(self):
        """Test that signature tampering is detected and startup fails."""
        # This test would verify that modifying the manifest
        # causes signature verification to fail
        pass
    
    def test_law_enforcement_before_side_effects(self):
        """Test that law checks happen before external side effects."""
        # This test would verify that policy validation
        # occurs before any external API calls or data modifications
        pass
    
    def test_audit_trail_completeness(self):
        """Test that audit trails are complete and traceable."""
        # This test would verify that all actions have
        # complete audit trails with audit_id
        pass
    
    def test_connector_bypass_prevention(self):
        """Test that connectors cannot bypass policy enforcement."""
        # This test would verify that connectors are
        # properly validated and cannot execute without policy checks
        pass


if __name__ == "__main__":
    pytest.main([__file__])
