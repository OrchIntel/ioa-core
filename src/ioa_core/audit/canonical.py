# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



Canonical JSON processing and hashing utilities.

Ensures deterministic JSON serialization and SHA-256 hashing for
audit chain entries to maintain tamper-evidence.
"""

"""Canonical module."""

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Union


def canonicalize_json(data: Union[Dict[str, Any], str]) -> str:
    """Convert data to canonical JSON string.
    
    Ensures deterministic serialization by:
    - Sorting dictionary keys alphabetically
    - Using consistent whitespace (no extra spaces)
    - Using UTF-8 encoding
    - Using LF line endings
    
    Args:
        data: Dictionary or JSON string to canonicalize
        
    Returns:
        Canonical JSON string
        
    Raises:
        ValueError: If data cannot be serialized to JSON
    """
    if isinstance(data, str):
        try:
            # Parse and re-serialize to ensure canonical form
            parsed = json.loads(data)
            return _canonicalize_dict(parsed)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")
    elif isinstance(data, dict):
        return _canonicalize_dict(data)
    else:
        raise ValueError(f"Expected dict or str, got {type(data)}")


def _canonicalize_dict(data: Dict[str, Any]) -> str:
    """Canonicalize a dictionary to JSON string.
    
    Args:
        data: Dictionary to canonicalize
        
    Returns:
        Canonical JSON string
    """
    def _sort_keys(obj):
        """Recursively sort dictionary keys."""
        if isinstance(obj, dict):
            return {k: _sort_keys(v) for k, v in sorted(obj.items())}
        elif isinstance(obj, list):
            return [_sort_keys(item) for item in obj]
        else:
            return obj
    
    def _convert_datetime(obj):
        """Convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: _convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_convert_datetime(item) for item in obj]
        else:
            return obj
    
    # Convert datetime objects to strings
    converted_data = _convert_datetime(data)
    
    # Sort all keys recursively
    sorted_data = _sort_keys(converted_data)
    
    # Serialize with consistent formatting
    return json.dumps(
        sorted_data,
        separators=(',', ':'),  # No extra spaces
        ensure_ascii=False,     # Allow UTF-8
        sort_keys=True          # Redundant but explicit
    )


def compute_hash(data: Union[Dict[str, Any], str]) -> str:
    """Compute SHA-256 hash of canonical JSON.
    
    Args:
        data: Dictionary or JSON string to hash
        
    Returns:
        64-character hexadecimal hash string
    """
    canonical_json = canonicalize_json(data)
    
    # Compute SHA-256 hash
    hash_obj = hashlib.sha256()
    hash_obj.update(canonical_json.encode('utf-8'))
    
    return hash_obj.hexdigest()


def verify_hash(data: Union[Dict[str, Any], str], expected_hash: str) -> bool:
    """Verify that data produces the expected hash.
    
    Args:
        data: Dictionary or JSON string to verify
        expected_hash: Expected 64-character hex hash
        
    Returns:
        True if hash matches, False otherwise
    """
    if len(expected_hash) != 64:
        return False
    
    try:
        computed_hash = compute_hash(data)
        return computed_hash == expected_hash
    except (ValueError, TypeError):
        return False


def validate_hash_format(hash_str: str) -> bool:
    """Validate that a string is a valid SHA-256 hash format.
    
    Args:
        hash_str: String to validate
        
    Returns:
        True if valid 64-character hex string, False otherwise
    """
    if not isinstance(hash_str, str) or len(hash_str) != 64:
        return False
    
    try:
        int(hash_str, 16)
        return True
    except ValueError:
        return False
