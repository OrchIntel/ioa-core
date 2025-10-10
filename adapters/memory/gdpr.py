""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


import logging
import hashlib
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

# PATCH: Cursor-2025-01-27 DISPATCH-GPT-20250825-031 <memory engine modularization>

from .core import MemoryEntry, MemoryError

@dataclass
class GDPRRequest:
    """GDPR data subject request."""
    request_id: str
    data_subject_id: str
    request_type: str  # "access", "erasure", "portability", "rectification"
    timestamp: datetime
    status: str = "pending"  # "pending", "processing", "completed", "failed"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class GDPRCompliance:
    """GDPR compliance handler for memory operations."""
    
    def __init__(self, enable_audit_logging: bool = True):
        """
        Initialize GDPR compliance handler.
        
        Args:
            enable_audit_logging: Enable audit logging for GDPR operations
        """
        self.logger = logging.getLogger(__name__)
        self.enable_audit_logging = enable_audit_logging
        
        # Track GDPR requests
        self._requests: Dict[str, GDPRRequest] = {}
        
        # Data subject identifiers (hashed for privacy)
        self._data_subjects: Set[str] = set()
        
        # Audit log
        self._audit_log: List[Dict[str, Any]] = []
    
    def identify_data_subject(self, content: str, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Identify if content contains personal data and extract data subject identifier.
        
        Args:
            content: Content to analyze
            metadata: Associated metadata
            
        Returns:
            Hashed data subject identifier or None if no personal data found
        """
        try:
            # Simple personal data detection (in production, use more sophisticated NLP)
            personal_indicators = [
                "email", "phone", "address", "ssn", "passport", "credit_card",
                "name", "birth", "age", "gender", "location", "ip_address"
            ]
            
            content_lower = content.lower()
            metadata_lower = {k.lower(): v.lower() for k, v in metadata.items()}
            
            # Check for personal data indicators
            found_indicators = []
            for indicator in personal_indicators:
                if indicator in content_lower or any(indicator in str(v) for v in metadata_lower.values()):
                    found_indicators.append(indicator)
            
            if not found_indicators:
                return None
            
            # Create a hash of the content for data subject identification
            # In production, use more sophisticated entity extraction
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            
            # Add to tracked data subjects
            self._data_subjects.add(content_hash)
            
            if self.enable_audit_logging:
                self._log_audit("data_subject_identified", {
                    "indicators": found_indicators,
                    "hash": content_hash,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            return content_hash
            
        except Exception as e:
            self.logger.error(f"Failed to identify data subject: {e}")
            return None
    
    def create_gdpr_request(self, data_subject_id: str, request_type: str) -> str:
        """
        Create a GDPR request for a data subject.
        
        Args:
            data_subject_id: Identifier for the data subject
            request_type: Type of GDPR request
            
        Returns:
            Request ID
        """
        request_id = f"gdpr_{data_subject_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        request = GDPRRequest(
            request_id=request_id,
            data_subject_id=data_subject_id,
            request_type=request_type,
            timestamp=datetime.now(timezone.utc)
        )
        
        self._requests[request_id] = request
        
        if self.enable_audit_logging:
            self._log_audit("gdpr_request_created", {
                "request_id": request_id,
                "data_subject_id": data_subject_id,
                "request_type": request_type
            })
        
        return request_id
    
    def process_gdpr_request(self, request_id: str, entries: List[MemoryEntry]) -> Dict[str, Any]:
        """
        Process a GDPR request.
        
        Args:
            request_id: ID of the GDPR request
            entries: List of memory entries to process
            
        Returns:
            Processing result
        """
        if request_id not in self._requests:
            raise MemoryError(f"GDPR request {request_id} not found")
        
        request = self._requests[request_id]
        request.status = "processing"
        
        try:
            if request.request_type == "access":
                result = self._process_access_request(request, entries)
            elif request.request_type == "erasure":
                result = self._process_erasure_request(request, entries)
            elif request.request_type == "portability":
                result = self._process_portability_request(request, entries)
            elif request.request_type == "rectification":
                result = self._process_rectification_request(request, entries)
            else:
                raise MemoryError(f"Unsupported GDPR request type: {request.request_type}")
            
            request.status = "completed"
            request.metadata["result"] = result
            
            if self.enable_audit_logging:
                self._log_audit("gdpr_request_completed", {
                    "request_id": request_id,
                    "request_type": request.request_type,
                    "result": result
                })
            
            return result
            
        except Exception as e:
            request.status = "failed"
            request.metadata["error"] = str(e)
            
            if self.enable_audit_logging:
                self._log_audit("gdpr_request_failed", {
                    "request_id": request_id,
                    "error": str(e)
                })
            
            raise
    
    def _process_access_request(self, request: GDPRRequest, entries: List[MemoryEntry]) -> Dict[str, Any]:
        """Process a data access request."""
        relevant_entries = [
            entry for entry in entries
            if self._is_data_subject_entry(entry, request.data_subject_id)
        ]
        
        return {
            "request_type": "access",
            "data_subject_id": request.data_subject_id,
            "entries_found": len(relevant_entries),
            "data": [entry.to_dict() for entry in relevant_entries],
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _process_erasure_request(self, request: GDPRRequest, entries: List[MemoryEntry]) -> Dict[str, Any]:
        """Process a data erasure request."""
        relevant_entries = [
            entry for entry in entries
            if self._is_data_subject_entry(entry, request.data_subject_id)
        ]
        
        # Mark entries for deletion (actual deletion handled by storage layer)
        for entry in relevant_entries:
            entry.metadata["gdpr_erasure_requested"] = True
            entry.metadata["erasure_request_id"] = request.request_id
            entry.metadata["erasure_requested_at"] = datetime.now(timezone.utc).isoformat()
        
        return {
            "request_type": "erasure",
            "data_subject_id": request.data_subject_id,
            "entries_marked": len(relevant_entries),
            "erasure_request_id": request.request_id,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _process_portability_request(self, request: GDPRRequest, entries: List[MemoryEntry]) -> Dict[str, Any]:
        """Process a data portability request."""
        relevant_entries = [
            entry for entry in entries
            if self._is_data_subject_entry(entry, request.data_subject_id)
        ]
        
        # Export data in portable format
        export_data = {
            "export_info": {
                "request_id": request.request_id,
                "data_subject_id": request.data_subject_id,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "format": "json"
            },
            "entries": [entry.to_dict() for entry in relevant_entries]
        }
        
        return {
            "request_type": "portability",
            "data_subject_id": request.data_subject_id,
            "entries_exported": len(relevant_entries),
            "export_data": export_data,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _process_rectification_request(self, request: GDPRRequest, entries: List[MemoryEntry]) -> Dict[str, Any]:
        """Process a data rectification request."""
        # This would typically involve updating specific fields
        # For now, return a placeholder implementation
        return {
            "request_type": "rectification",
            "data_subject_id": request.data_subject_id,
            "status": "not_implemented",
            "note": "Rectification requests require specific field updates",
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _is_data_subject_entry(self, entry: MemoryEntry, data_subject_id: str) -> bool:
        """Check if an entry belongs to a specific data subject."""
        # Simple check - in production, use more sophisticated matching
        return (
            data_subject_id in entry.content or
            data_subject_id in str(entry.metadata) or
            data_subject_id in str(entry.tags)
        )
    
    def _log_audit(self, event: str, data: Dict[str, Any]):
        """Log audit event."""
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "data": data,
            "module": "gdpr_compliance"
        }
        
        self._audit_log.append(audit_entry)
        
        # Keep audit log size manageable
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-500:]
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        return self._audit_log[-limit:]
    
    def get_gdpr_request(self, request_id: str) -> Optional[GDPRRequest]:
        """Get a specific GDPR request."""
        return self._requests.get(request_id)
    
    def list_gdpr_requests(self, status: Optional[str] = None) -> List[GDPRRequest]:
        """List GDPR requests, optionally filtered by status."""
        if status is None:
            return list(self._requests.values())
        
        return [req for req in self._requests.values() if req.status == status]
    
    def cleanup_expired_requests(self, max_age_days: int = 90):
        """Clean up old GDPR requests."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        
        expired_requests = [
            req_id for req_id, req in self._requests.items()
            if req.timestamp < cutoff_date and req.status in ["completed", "failed"]
        ]
        
        for req_id in expired_requests:
            del self._requests[req_id]
        
        if expired_requests:
            self.logger.info(f"Cleaned up {len(expired_requests)} expired GDPR requests")
