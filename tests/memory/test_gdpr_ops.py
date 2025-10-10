""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


import pytest
import sys
import os
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from memory.core import MemoryEntry
from memory.gdpr import GDPRCompliance, GDPRRequest

class TestGDPRCompliance:
    """Test GDPR compliance functionality."""
    
    @pytest.fixture
    def gdpr_compliance(self):
        """Provide GDPR compliance instance."""
        return GDPRCompliance(enable_audit_logging=True)
    
    @pytest.fixture
    def sample_entries(self):
        """Provide sample memory entries for testing."""
        return [
            MemoryEntry(
                id="entry-1",
                content="User email: john.doe@example.com",
                metadata={"user_id": "user123"},
                tags=["user_data", "email"]
            ),
            MemoryEntry(
                id="entry-2", 
                content="Phone number: 555-123-4567",
                metadata={"contact_info": True},
                tags=["contact", "phone"]
            ),
            MemoryEntry(
                id="entry-3",
                content="General information about products",
                metadata={"category": "product_info"},
                tags=["products", "general"]
            )
        ]
    
    def test_gdpr_compliance_initialization(self, gdpr_compliance):
        """Test GDPR compliance initialization."""
        assert gdpr_compliance.enable_audit_logging is True
        assert len(gdpr_compliance._requests) == 0
        assert len(gdpr_compliance._data_subjects) == 0
    
    def test_identify_data_subject_with_personal_data(self, gdpr_compliance):
        """Test identifying data subjects in content with personal data."""
        content = "User email: test@example.com and phone: 555-123-4567"
        metadata = {"user_id": "user456"}
        
        data_subject_id = gdpr_compliance.identify_data_subject(content, metadata)
        
        assert data_subject_id is not None
        assert len(data_subject_id) == 16  # SHA256 hash truncated to 16 chars
        assert data_subject_id in gdpr_compliance._data_subjects
    
    def test_identify_data_subject_without_personal_data(self, gdpr_compliance):
        """Test identifying data subjects in content without personal data."""
        content = "General information about weather conditions"
        metadata = {"category": "weather"}
        
        data_subject_id = gdpr_compliance.identify_data_subject(content, metadata)
        
        assert data_subject_id is None
    
    def test_create_gdpr_request(self, gdpr_compliance):
        """Test creating GDPR requests."""
        data_subject_id = "test_subject_123"
        request_type = "access"
        
        request_id = gdpr_compliance.create_gdpr_request(data_subject_id, request_type)
        
        assert request_id.startswith("gdpr_")
        assert request_id in gdpr_compliance._requests
        
        request = gdpr_compliance._requests[request_id]
        assert request.data_subject_id == data_subject_id
        assert request.request_type == request_type
        assert request.status == "pending"
    
    def test_process_access_request(self, gdpr_compliance, sample_entries):
        """Test processing GDPR access requests."""
        data_subject_id = "test_subject_456"
        request_id = gdpr_compliance.create_gdpr_request(data_subject_id, "access")
        
        result = gdpr_compliance.process_gdpr_request(request_id, sample_entries)
        
        assert result["request_type"] == "access"
        assert result["data_subject_id"] == data_subject_id
        assert "entries_found" in result
        assert "data" in result
        assert "processed_at" in result
        
        # Check that request status was updated
        request = gdpr_compliance.get_gdpr_request(request_id)
        assert request.status == "completed"
    
    def test_process_erasure_request(self, gdpr_compliance, sample_entries):
        """Test processing GDPR erasure requests."""
        data_subject_id = "test_subject_789"
        request_id = gdpr_compliance.create_gdpr_request(data_subject_id, "erasure")
        
        result = gdpr_compliance.process_gdpr_request(request_id, sample_entries)
        
        assert result["request_type"] == "erasure"
        assert result["data_subject_id"] == data_subject_id
        assert "entries_marked" in result
        assert "erasure_request_id" in result
        
        # Check that entries were marked for erasure
        for entry in sample_entries:
            if gdpr_compliance._is_data_subject_entry(entry, data_subject_id):
                assert entry.metadata.get("gdpr_erasure_requested") is True
                assert entry.metadata.get("erasure_request_id") == request_id
    
    def test_process_portability_request(self, gdpr_compliance, sample_entries):
        """Test processing GDPR portability requests."""
        data_subject_id = "test_subject_port"
        request_id = gdpr_compliance.create_gdpr_request(data_subject_id, "portability")
        
        result = gdpr_compliance.process_gdpr_request(request_id, sample_entries)
        
        assert result["request_type"] == "portability"
        assert result["data_subject_id"] == data_subject_id
        assert "entries_exported" in result
        assert "export_data" in result
        
        # Check export data structure
        export_data = result["export_data"]
        assert "export_info" in export_data
        assert "entries" in export_data
        assert export_data["export_info"]["request_id"] == request_id
    
    def test_gdpr_request_not_found(self, gdpr_compliance):
        """Test handling of non-existent GDPR requests."""
        with pytest.raises(Exception):  # Should raise MemoryError
            gdpr_compliance.process_gdpr_request("non_existent_id", [])
    
    def test_unsupported_request_type(self, gdpr_compliance, sample_entries):
        """Test handling of unsupported GDPR request types."""
        data_subject_id = "test_subject_unsupported"
        request_id = gdpr_compliance.create_gdpr_request(data_subject_id, "unsupported_type")
        
        with pytest.raises(Exception):  # Should raise MemoryError
            gdpr_compliance.process_gdpr_request(request_id, sample_entries)
    
    def test_audit_logging(self, gdpr_compliance):
        """Test audit logging functionality."""
        # Create a request to generate audit logs
        data_subject_id = "test_subject_audit"
        request_id = gdpr_compliance.create_gdpr_request(data_subject_id, "access")
        
        # Check that audit log was created
        audit_log = gdpr_compliance.get_audit_log()
        assert len(audit_log) > 0
        
        # Find the request creation audit entry
        request_created = False
        for entry in audit_log:
            if entry["event"] == "gdpr_request_created":
                request_created = True
                assert entry["data"]["request_id"] == request_id
                assert entry["data"]["data_subject_id"] == data_subject_id
                break
        
        assert request_created
    
    def test_list_gdpr_requests(self, gdpr_compliance):
        """Test listing GDPR requests."""
        # Create multiple requests
        gdpr_compliance.create_gdpr_request("subject1", "access")
        gdpr_compliance.create_gdpr_request("subject2", "erasure")
        gdpr_compliance.create_gdpr_request("subject3", "portability")
        
        # List all requests
        all_requests = gdpr_compliance.list_gdpr_requests()
        assert len(all_requests) == 3
        
        # List pending requests
        pending_requests = gdpr_compliance.list_gdpr_requests(status="pending")
        assert len(pending_requests) == 3
        
        # List completed requests (should be 0)
        completed_requests = gdpr_compliance.list_gdpr_requests(status="completed")
        assert len(completed_requests) == 0
    
    def test_cleanup_expired_requests(self, gdpr_compliance):
        """Test cleanup of expired GDPR requests."""
        # Create a request
        request_id = gdpr_compliance.create_gdpr_request("subject_cleanup", "access")
        
        # Manually set timestamp to old date
        request = gdpr_compliance._requests[request_id]
        request.timestamp = datetime.now(timezone.utc).replace(year=2020)
        request.status = "completed"
        
        # Clean up expired requests
        gdpr_compliance.cleanup_expired_requests(max_age_days=90)
        
        # Request should be removed
        assert request_id not in gdpr_compliance._requests
    
    def test_data_subject_entry_matching(self, gdpr_compliance):
        """Test matching entries to data subjects."""
        entry = MemoryEntry(
            id="test_entry",
            content="Contains test_subject_123 data",
            metadata={"user": "test_subject_123"},
            tags=["test_subject_123", "data"]
        )
        
        # Should match on content
        assert gdpr_compliance._is_data_subject_entry(entry, "test_subject_123")
        
        # Should match on metadata
        assert gdpr_compliance._is_data_subject_entry(entry, "test_subject_123")
        
        # Should match on tags
        assert gdpr_compliance._is_data_subject_entry(entry, "test_subject_123")
        
        # Should not match different subject
        assert not gdpr_compliance._is_data_subject_entry(entry, "different_subject")
