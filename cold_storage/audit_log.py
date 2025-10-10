""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""

This module provides immutable audit logging with JSONL format and configurable
rotation policies based on size and time. Enterprise versions can extend this
with advanced retention and compliance features.
"""

import json
import os
import time
import hashlib
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime, timezone, timedelta
import logging
import threading

logger = logging.getLogger(__name__)

class AuditLogEntry:
    """Immutable audit log entry."""
    
    def __init__(self, action: str, user_id: str, resource: str, 
                 details: Dict[str, Any], timestamp: Optional[datetime] = None):
        """
        Initialize audit log entry.
        
        Args:
            action: Action performed (e.g., 'read', 'write', 'delete')
            user_id: ID of user performing action
            resource: Resource affected by action
            details: Additional details about the action
            timestamp: Timestamp of action (defaults to current time)
        """
        self.action = action
        self.user_id = user_id
        self.resource = resource
        self.details = details
        self.timestamp = timestamp or datetime.now(timezone.utc)
        
        # Generate immutable hash for integrity
        self._hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of entry content."""
        content = {
            'action': self.action,
            'user_id': self.user_id,
            'resource': self.resource,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary with hash."""
        return {
            'action': self.action,
            'user_id': self.user_id,
            'resource': self.resource,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'hash': self._hash
        }
    
    def to_jsonl(self) -> str:
        """Convert entry to JSONL format."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_jsonl(cls, jsonl_line: str) -> 'AuditLogEntry':
        """Create entry from JSONL line."""
        data = json.loads(jsonl_line)
        timestamp = datetime.fromisoformat(data['timestamp'])
        entry = cls(
            action=data['action'],
            user_id=data['user_id'],
            resource=data['resource'],
            details=data['details'],
            timestamp=timestamp
        )
        
        # Verify hash integrity
        if entry._hash != data.get('hash'):
            raise ValueError("Audit log entry hash verification failed")
        
        return entry

class AuditLogRotator:
    """Manages audit log rotation based on size and time policies."""
    
    def __init__(self, max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 max_file_age: timedelta = timedelta(days=30),
                 max_files: int = 10):
        """
        Initialize rotator with rotation policies.
        
        Args:
            max_file_size: Maximum file size in bytes before rotation
            max_file_age: Maximum file age before rotation
            max_files: Maximum number of rotated files to keep
        """
        self.max_file_size = max_file_size
        self.max_file_age = max_file_age
        self.max_files = max_files
        self._lock = threading.Lock()
    
    def should_rotate(self, log_file: Path) -> bool:
        """Check if log file should be rotated."""
        if not log_file.exists():
            return False
        
        # Check file size
        if log_file.stat().st_size >= self.max_file_size:
            return True
        
        # Check file age
        file_age = datetime.now(timezone.utc) - datetime.fromtimestamp(
            log_file.stat().st_mtime, tz=timezone.utc
        )
        if file_age >= self.max_file_age:
            return True
        
        return False
    
    def rotate_log(self, log_file: Path) -> Path:
        """Rotate log file and return new file path."""
        with self._lock:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            rotated_name = f"{log_file.stem}_{timestamp}{log_file.suffix}"
            rotated_path = log_file.parent / rotated_name
            
            # Rename current file
            log_file.rename(rotated_path)
            
            # Clean up old rotated files
            self._cleanup_old_files(log_file.parent)
            
            logger.info(f"Rotated audit log: {log_file} -> {rotated_path}")
            return rotated_path
    
    def _cleanup_old_files(self, log_dir: Path) -> None:
        """Remove old rotated log files beyond max_files limit."""
        pattern = f"{log_dir.name}_*{log_dir.suffix}"
        rotated_files = sorted(
            log_dir.parent.glob(pattern),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        # Keep only max_files most recent
        for old_file in rotated_files[self.max_files:]:
            try:
                old_file.unlink()
                logger.info(f"Removed old audit log: {old_file}")
            except Exception as e:
                logger.warning(f"Failed to remove old audit log {old_file}: {e}")

class AuditLogger:
    """Immutable JSONL audit logger with rotation."""
    
    def __init__(self, log_dir: Union[str, Path],
                 log_filename: str = "audit.log",
                 enable_rotation: bool = True,
                 rotation_config: Optional[Dict[str, Any]] = None):
        """
        Initialize audit logger.
        
        Args:
            log_dir: Directory for audit logs
            log_filename: Name of current log file
            enable_rotation: Whether to enable log rotation
            rotation_config: Configuration for log rotation
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / log_filename
        self.enable_rotation = enable_rotation
        
        if enable_rotation:
            rotation_config = rotation_config or {}
            self.rotator = AuditLogRotator(**rotation_config)
        else:
            self.rotator = None
        
        self._lock = threading.Lock()
        logger.info(f"Audit logger initialized: {self.log_file}")
    
    def log(self, action: str, user_id: str, resource: str, 
            details: Dict[str, Any]) -> bool:
        """
        Log an audit event.
        
        Args:
            action: Action performed
            user_id: ID of user performing action
            resource: Resource affected by action
            details: Additional details about the action
            
        Returns:
            True if successful, False otherwise
        """
        try:
            entry = AuditLogEntry(action, user_id, resource, details)
            
            with self._lock:
                # Check if rotation is needed
                if self.enable_rotation and self.rotator.should_rotate(self.log_file):
                    self.rotator.rotate_log(self.log_file)
                
                # Write entry to log file
                with open(self.log_file, 'a') as f:
                    f.write(entry.to_jsonl() + '\n')
                
                logger.debug(f"Audit log entry: {action} by {user_id} on {resource}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False
    
    def read_entries(self, start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None,
                    action: Optional[str] = None,
                    user_id: Optional[str] = None,
                    resource: Optional[str] = None) -> List[AuditLogEntry]:
        """
        Read audit log entries with optional filtering.
        
        Args:
            start_time: Filter entries after this time
            end_time: Filter entries before this time
            action: Filter by action type
            user_id: Filter by user ID
            resource: Filter by resource
            
        Returns:
            List of matching audit log entries
        """
        entries = []
        
        try:
            # Read current log file
            if self.log_file.exists():
                entries.extend(self._read_file_entries(self.log_file, start_time, end_time,
                                                   action, user_id, resource))
            
            # Read rotated log files
            if self.enable_rotation:
                pattern = f"{self.log_file.stem}_*{self.log_file.suffix}"
                rotated_files = sorted(
                    self.log_dir.glob(pattern),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                
                for rotated_file in rotated_files:
                    entries.extend(self._read_file_entries(rotated_file, start_time, end_time,
                                                        action, user_id, resource))
            
            # Sort by timestamp
            entries.sort(key=lambda x: x.timestamp)
            return entries
            
        except Exception as e:
            logger.error(f"Failed to read audit entries: {e}")
            return []
    
    def _read_file_entries(self, file_path: Path, start_time: Optional[datetime],
                          end_time: Optional[datetime], action: Optional[str],
                          user_id: Optional[str], resource: Optional[str]) -> List[AuditLogEntry]:
        """Read entries from a specific log file with filtering."""
        entries = []
        
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = AuditLogEntry.from_jsonl(line)
                        
                        # Apply filters
                        if start_time and entry.timestamp < start_time:
                            continue
                        if end_time and entry.timestamp > end_time:
                            continue
                        if action and entry.action != action:
                            continue
                        if user_id and entry.user_id != user_id:
                            continue
                        if resource and entry.resource != resource:
                            continue
                        
                        entries.append(entry)
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse audit log line {line_num} in {file_path}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to read audit log file {file_path}: {e}")
        
        return entries
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get audit log statistics."""
        try:
            stats = {
                'current_log_size': self.log_file.stat().st_size if self.log_file.exists() else 0,
                'total_entries': 0,
                'rotated_files': 0,
                'earliest_entry': None,
                'latest_entry': None
            }
            
            # Count entries and find time range
            all_entries = self.read_entries()
            stats['total_entries'] = len(all_entries)
            
            if all_entries:
                stats['earliest_entry'] = all_entries[0].timestamp.isoformat()
                stats['latest_entry'] = all_entries[-1].timestamp.isoformat()
            
            # Count rotated files
            if self.enable_rotation:
                pattern = f"{self.log_file.stem}_*{self.log_file.suffix}"
                rotated_files = list(self.log_dir.glob(pattern))
                stats['rotated_files'] = len(rotated_files)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get audit log stats: {e}")
            return {}

# Convenience function
def create_audit_logger(log_dir: Union[str, Path], 
                       log_filename: str = "audit.log",
                       enable_rotation: bool = True) -> AuditLogger:
    """Create an audit logger with default settings."""
    return AuditLogger(
        log_dir=log_dir,
        log_filename=log_filename,
        enable_rotation=enable_rotation
    )
