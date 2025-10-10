""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Test canonical JSON processing and hashing utilities.

Tests the canonicalization and hashing functions to ensure
deterministic JSON serialization and SHA-256 hash computation.
"""

import pytest
import json
from src.audit.canonical import (
    canonicalize_json,
    compute_hash,
    verify_hash,
    validate_hash_format
)


def test_canonicalize_dict():
    """Test canonicalization of dictionary."""
    data = {
        "c": 3,
        "a": 1,
        "b": 2,
        "nested": {
            "z": 26,
            "x": 24,
            "y": 25
        }
    }
    
    canonical = canonicalize_json(data)
    
    # Should be sorted by keys
    expected = '{"a":1,"b":2,"c":3,"nested":{"x":24,"y":25,"z":26}}'
    assert canonical == expected


def test_canonicalize_json_string():
    """Test canonicalization of JSON string."""
    json_str = '{"c":3,"a":1,"b":2}'
    
    canonical = canonicalize_json(json_str)
    
    # Should be sorted by keys
    expected = '{"a":1,"b":2,"c":3}'
    assert canonical == expected


def test_canonicalize_nested_structures():
    """Test canonicalization of nested structures."""
    data = {
        "list": [3, 1, 2],
        "dict": {"c": 3, "a": 1, "b": 2},
        "mixed": [
            {"z": 26, "x": 24},
            {"m": 13, "n": 14}
        ]
    }
    
    canonical = canonicalize_json(data)
    
    # Should be deterministic
    canonical2 = canonicalize_json(data)
    assert canonical == canonical2


def test_canonicalize_consistent_whitespace():
    """Test that canonicalization produces consistent whitespace."""
    data1 = {"a": 1, "b": 2}
    data2 = {"a":1,"b":2}
    data3 = {"a": 1,"b": 2}
    
    canonical1 = canonicalize_json(data1)
    canonical2 = canonicalize_json(data2)
    canonical3 = canonicalize_json(data3)
    
    # All should produce the same result
    assert canonical1 == canonical2 == canonical3


def test_canonicalize_unicode():
    """Test canonicalization with Unicode characters."""
    data = {
        "unicode": "café",
        "emoji": "🚀",
        "chinese": "你好"
    }
    
    canonical = canonicalize_json(data)
    
    # Should handle Unicode properly
    assert "café" in canonical
    assert "🚀" in canonical
    assert "你好" in canonical


def test_compute_hash():
    """Test hash computation."""
    data = {"a": 1, "b": 2}
    
    hash1 = compute_hash(data)
    hash2 = compute_hash(data)
    
    # Should be deterministic
    assert hash1 == hash2
    
    # Should be 64 characters (SHA-256)
    assert len(hash1) == 64
    
    # Should be hexadecimal
    assert all(c in '0123456789abcdef' for c in hash1)


def test_compute_hash_different_data():
    """Test that different data produces different hashes."""
    data1 = {"a": 1, "b": 2}
    data2 = {"a": 1, "b": 3}
    
    hash1 = compute_hash(data1)
    hash2 = compute_hash(data2)
    
    assert hash1 != hash2


def test_compute_hash_order_independent():
    """Test that hash is independent of key order."""
    data1 = {"a": 1, "b": 2, "c": 3}
    data2 = {"c": 3, "a": 1, "b": 2}
    
    hash1 = compute_hash(data1)
    hash2 = compute_hash(data2)
    
    assert hash1 == hash2


def test_verify_hash():
    """Test hash verification."""
    data = {"a": 1, "b": 2}
    computed_hash = compute_hash(data)
    
    # Should verify correctly
    assert verify_hash(data, computed_hash) is True
    
    # Should fail with wrong hash
    wrong_hash = "1" * 64
    assert verify_hash(data, wrong_hash) is False


def test_verify_hash_invalid_format():
    """Test hash verification with invalid hash format."""
    data = {"a": 1, "b": 2}
    
    # Should fail with invalid hash format
    assert verify_hash(data, "invalid") is False
    assert verify_hash(data, "123") is False  # Too short
    assert verify_hash(data, "x" * 64) is False  # Invalid hex


def test_verify_hash_invalid_data():
    """Test hash verification with invalid data."""
    data = {"a": 1, "b": 2}
    hash_str = compute_hash(data)
    
    # Should fail with different data
    different_data = {"a": 1, "b": 3}
    assert verify_hash(different_data, hash_str) is False


def test_validate_hash_format():
    """Test hash format validation."""
    # Valid hashes
    assert validate_hash_format("a" * 64) is True
    assert validate_hash_format("1" * 64) is True
    assert validate_hash_format("0123456789abcdef" * 4) is True
    
    # Invalid hashes
    assert validate_hash_format("a" * 63) is False  # Too short
    assert validate_hash_format("a" * 65) is False  # Too long
    assert validate_hash_format("g" * 64) is False  # Invalid hex
    assert validate_hash_format("") is False  # Empty
    assert validate_hash_format("123") is False  # Too short


def test_canonicalize_error_handling():
    """Test error handling in canonicalization."""
    # Should raise ValueError for invalid JSON string
    with pytest.raises(ValueError):
        canonicalize_json('{"invalid": json}')
    
    # Should raise ValueError for unsupported types
    with pytest.raises(ValueError):
        canonicalize_json(123)
    
    with pytest.raises(ValueError):
        canonicalize_json([1, 2, 3])


def test_compute_hash_error_handling():
    """Test error handling in hash computation."""
    # Should raise ValueError for invalid data
    with pytest.raises(ValueError):
        compute_hash('{"invalid": json}')


def test_canonicalize_empty_structures():
    """Test canonicalization of empty structures."""
    # Empty dict
    assert canonicalize_json({}) == '{}'
    
    # Empty list
    data = {"list": []}
    assert canonicalize_json(data) == '{"list":[]}'
    
    # Nested empty structures
    data = {"a": {}, "b": []}
    assert canonicalize_json(data) == '{"a":{},"b":[]}'


def test_canonicalize_special_values():
    """Test canonicalization of special JSON values."""
    data = {
        "null": None,
        "true": True,
        "false": False,
        "number": 42.5,
        "string": "hello"
    }
    
    canonical = canonicalize_json(data)
    
    # Should handle special values correctly
    assert "null" in canonical
    assert "true" in canonical
    assert "false" in canonical
    assert "42.5" in canonical
    assert '"hello"' in canonical


def test_canonicalize_unicode_consistency():
    """Test that Unicode canonicalization is consistent."""
    data = {
        "unicode": "café",
        "emoji": "🚀",
        "chinese": "你好"
    }
    
    # Multiple calls should produce identical results
    canonical1 = canonicalize_json(data)
    canonical2 = canonicalize_json(data)
    
    assert canonical1 == canonical2
    
    # Hash should be identical
    hash1 = compute_hash(data)
    hash2 = compute_hash(data)
    
    assert hash1 == hash2


def test_canonicalize_large_structure():
    """Test canonicalization of large nested structure."""
    # Create a large nested structure
    data = {}
    for i in range(100):
        data[f"key_{i:03d}"] = {
            "nested": {
                "value": i,
                "text": f"item_{i}",
                "list": list(range(i % 10))
            }
        }
    
    canonical = canonicalize_json(data)
    
    # Should be deterministic
    canonical2 = canonicalize_json(data)
    assert canonical == canonical2
    
    # Should produce valid JSON
    parsed = json.loads(canonical)
    assert len(parsed) == 100
