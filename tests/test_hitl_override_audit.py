"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
Test HITL Override Audit Method

PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250907-SMOKETEST-PROVIDER-LIVE-HARDEN-v2
Tests for the enhanced HITL override audit method and policy hook.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, mock_open

# Import the HITL functions
from apps.command_deck.hitl import _log_hitl_override_audit, create_hitl_override_policy_hook


class TestHITLOverrideAudit:
    """Test HITL override audit functionality."""
    
    def test_log_hitl_override_audit_basic(self):
        """Test basic HITL override audit logging."""
        override_record = {
            "override_id": "test-override-123",
            "action_id": "test-action-456",
            "actor_id": "test-actor-789",
            "action_type": "test_action",
            "approver_id": "test-approver",
            "rationale": "Test justification",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "audit_id": "test-audit-123",
            "metadata": {"ttl_minutes": 30}
        }
        
        # Mock the file writing
        with patch('apps.command_deck.hitl._write_audit_log') as mock_write:
            _log_hitl_override_audit(override_record)
            
            # Verify audit log was written
            mock_write.assert_called_once()
            
            # Check the audit entry structure
            call_args = mock_write.call_args[0][0]
            assert call_args["audit_type"] == "hitl_override"
            assert call_args["override_used"] is True
            assert call_args["approver"] == "test-approver"
            assert call_args["ttl_minutes"] == 30
            assert call_args["justification"] == "Test justification"
            assert call_args["override_id"] == "test-override-123"
    
    def test_log_hitl_override_audit_minimal(self):
        """Test HITL override audit with minimal data."""
        override_record = {
            "override_id": "minimal-override",
            "action_id": "minimal-action",
            "actor_id": "minimal-actor",
            "action_type": "minimal_action",
            "approver_id": "minimal-approver",
            "rationale": "Minimal justification",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "audit_id": "minimal-audit",
            "metadata": {}
        }
        
        with patch('apps.command_deck.hitl._write_audit_log') as mock_write:
            _log_hitl_override_audit(override_record)
            
            call_args = mock_write.call_args[0][0]
            assert call_args["ttl_minutes"] == 15  # Default value
            assert call_args["justification"] == "Minimal justification"
    
    def test_log_hitl_override_audit_missing_fields(self):
        """Test HITL override audit with missing fields."""
        override_record = {
            "override_id": "missing-fields-override",
            "action_id": "missing-action",
            "actor_id": "missing-actor",
            "action_type": "missing_action",
            # Missing approver_id, rationale, metadata
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "audit_id": "missing-audit"
        }
        
        with patch('apps.command_deck.hitl._write_audit_log') as mock_write:
            _log_hitl_override_audit(override_record)
            
            call_args = mock_write.call_args[0][0]
            assert call_args["approver"] == "unknown"
            assert call_args["ttl_minutes"] == 15  # Default value
            assert call_args["justification"] == "No justification provided"
    
    def test_write_audit_log(self):
        """Test writing audit log to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the audit directory path
            with patch('pathlib.Path') as mock_path:
                mock_audit_dir = Path(temp_dir) / "logs" / "audit"
                mock_audit_dir.mkdir(parents=True, exist_ok=True)
                mock_path.return_value = mock_audit_dir
                
                audit_entry = {
                    "audit_type": "hitl_override",
                    "override_used": True,
                    "approver": "test-approver",
                    "ttl_minutes": 15,
                    "justification": "Test justification",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                from apps.command_deck.hitl import _write_audit_log
                _write_audit_log(audit_entry)
                
                # Check if audit file was created
                audit_file = mock_audit_dir / "hitl_overrides.jsonl"
                assert audit_file.exists()
                
                # Check file content
                with audit_file.open('r') as f:
                    content = f.read().strip()
                    data = json.loads(content)
                    assert data["audit_type"] == "hitl_override"
                    assert data["override_used"] is True
    
    def test_create_hitl_override_policy_hook(self):
        """Test creating HITL override policy hook."""
        hook = create_hitl_override_policy_hook()
        assert callable(hook)
        
        # Test hook with valid event
        event = {
            "event_type": "hitl_override_created",
            "override_id": "test-override",
            "approver": "test-approver"
        }
        
        with patch('apps.command_deck.hitl.logger') as mock_logger:
            hook(event)
            mock_logger.info.assert_called_once()
            assert "HITL override policy event" in mock_logger.info.call_args[0][0]
    
    def test_policy_hook_invalid_event(self):
        """Test policy hook with invalid event."""
        hook = create_hitl_override_policy_hook()
        
        # Test with different event type
        event = {
            "event_type": "other_event",
            "override_id": "test-override"
        }
        
        with patch('apps.command_deck.hitl.logger') as mock_logger:
            hook(event)
            # Should not log anything for different event type
            mock_logger.info.assert_not_called()
    
    def test_policy_hook_exception_handling(self):
        """Test policy hook exception handling."""
        hook = create_hitl_override_policy_hook()
        
        # Test with malformed event
        event = None
        
        with patch('apps.command_deck.hitl.logger') as mock_logger:
            hook(event)
            mock_logger.error.assert_called_once()
            assert "HITL override policy hook error" in mock_logger.error.call_args[0][0]


def test_hitl_override_audit_integration():
    """Integration test for HITL override audit functionality."""
    # Test the complete flow
    override_record = {
        "override_id": "integration-test-override",
        "action_id": "integration-test-action",
        "actor_id": "integration-test-actor",
        "action_type": "integration_test_action",
        "approver_id": "integration-test-approver",
        "rationale": "Integration test justification",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_id": "integration-test-audit",
        "metadata": {"ttl_minutes": 45, "priority": "high"}
    }
    
    with patch('apps.command_deck.hitl._write_audit_log') as mock_write:
        # Test audit logging
        _log_hitl_override_audit(override_record)
        
        # Test policy hook
        hook = create_hitl_override_policy_hook()
        event = {
            "event_type": "hitl_override_created",
            "override_id": "integration-test-override"
        }
        
        with patch('apps.command_deck.hitl.logger') as mock_logger:
            hook(event)
            
            # Verify both functions work
            mock_write.assert_called_once()
            mock_logger.info.assert_called_once()
            
            # Check audit entry has all required fields
            call_args = mock_write.call_args[0][0]
            required_fields = [
                "audit_type", "override_used", "approver", "ttl_minutes", 
                "justification", "override_id", "action_id", "actor_id", 
                "action_type", "timestamp", "audit_id", "metadata"
            ]
            
            for field in required_fields:
                assert field in call_args, f"Missing required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__])
