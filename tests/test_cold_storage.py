""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
Unit tests for the ColdStorage module.

These tests exercise the batch storage and retrieval functionality of
``ColdStorage``.  The implementation writes entries into JSONL shards
with integrity hashes and retrieves them with validation.  The tests
ensure that batches of various sizes are stored and retrieved correctly
and that invalid or corrupted entries are skipped.
"""

import asyncio
import json
import os
import tempfile
import sys
from pathlib import Path
import hashlib

import pytest

# Add src directory to Python path for imports
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cold_storage import ColdStorage


@pytest.mark.asyncio
async def test_empty_batch(tempdir=None) -> None:
    """Retrieving a non‑existent batch should raise FileNotFoundError."""
    # Use a temporary directory for storage
    with tempfile.TemporaryDirectory() as tmp:
        cs = ColdStorage(path=tmp)
        # No batches stored yet
        with pytest.raises(FileNotFoundError):
            await cs.retrieve_batch_from_cold("nonexistent")


@pytest.mark.asyncio
async def test_small_batch_roundtrip() -> None:
    """Store and retrieve a small batch of entries."""
    with tempfile.TemporaryDirectory() as tmp:
        cs = ColdStorage(path=tmp)
        entries = [
            {"content": f"test_content_{i}", "pattern_id": f"pattern_{i}"}
            for i in range(50)
        ]
        batch_file_id = await cs.store_batch_to_cold(entries)
        # The returned ID has the form cold_batch_<id>_0.jsonl
        # Extract the batch_id part
        batch_id = batch_file_id.replace("cold_batch_", "").split("_")[0]
        retrieved = await cs.retrieve_batch_from_cold(batch_id)
        assert len(retrieved) == len(entries)
        # Ensure order is preserved within shards
        for i, entry in enumerate(retrieved):
            assert entry["content"] == f"test_content_{i}"
            assert entry["pattern_id"] == f"pattern_{i}"


@pytest.mark.asyncio
async def test_large_batch_spanning_shards() -> None:
    """Store and retrieve a large batch that spans multiple shards."""
    with tempfile.TemporaryDirectory() as tmp:
        cs = ColdStorage(path=tmp)
        # 2500 entries should create 3 shards at the default shard size of 1000
        entries = [
            {"content": f"content_{i}", "pattern_id": f"pattern_{i}"}
            for i in range(2500)
        ]
        batch_file_id = await cs.store_batch_to_cold(entries)
        batch_id = batch_file_id.replace("cold_batch_", "").split("_")[0]
        retrieved = await cs.retrieve_batch_from_cold(batch_id)
        assert len(retrieved) == len(entries)
        # Check some sample entries to ensure integrity
        for idx in [0, 999, 1000, 1499, 2000, 2499]:
            assert retrieved[idx]["content"] == f"content_{idx}"
            assert retrieved[idx]["pattern_id"] == f"pattern_{idx}"


@pytest.mark.asyncio
async def test_corrupted_entries_are_skipped() -> None:
    """Entries with invalid JSON or incorrect hashes should be skipped."""
    with tempfile.TemporaryDirectory() as tmp:
        cs = ColdStorage(path=tmp)
        # Manually create a shard file with valid and invalid lines
        batch_id = "testbatch"
        file_path = Path(tmp) / f"cold_batch_{batch_id}_0.jsonl"
        with file_path.open("w", encoding="utf-8") as f:
            # Valid entry
            entry = {"content": "valid", "pattern_id": "pattern_1"}
            data = {
                "content": entry["content"],
                "pattern_id": entry["pattern_id"],
                "variables": {},
                "metadata": {},
                "feeling": {"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
                "id": "1234",
                "schema_version": "2.5.0",
                "stored_at": "2025-08-12T00:00:00Z",
            }
            integrity = hashlib.sha256(json.dumps(data, separators=(",", ":")).encode()).hexdigest()
            data["integrity_hash"] = integrity
            f.write(json.dumps(data) + "\n")
            # Invalid JSON
            f.write("not_a_json\n")
            # Entry with wrong hash
            bad = data.copy()
            bad["content"] = "tampered"
            bad["integrity_hash"] = "bad_hash"
            f.write(json.dumps(bad) + "\n")
        retrieved = await cs.retrieve_batch_from_cold(batch_id)
        # Only the valid entry should be returned
        assert len(retrieved) == 1
        assert retrieved[0]["content"] == "valid"