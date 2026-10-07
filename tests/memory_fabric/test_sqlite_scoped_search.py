# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""
Scope filters must apply before LIMIT (OP-60).

Incident: the SDK fetched `limit` rows globally and filtered afterwards, so
105 newer records from another owner made an owner's own summary vanish at
limits 1, 5 and 100.
"""

import pytest

from ioa_core.memory_fabric import MemoryFabric, MemoryType


@pytest.fixture
def fabric(tmp_path):
    return MemoryFabric(backend="sqlite", config={"data_dir": str(tmp_path), "db_name": "scoped.db"})


def _store(fabric, record_id, owner, conversation, content="steward summary of the conversation", **extra):
    meta = {"type": "steward_summary", "scope": "conversation", "conversation_id": conversation, "user_id": owner, **extra}
    return fabric.store(content=content, metadata=meta, tags=["steward", "conversation"], memory_type=MemoryType.KNOWLEDGE, record_id=record_id)


def _ids(records):
    return [r.id for r in records]


def test_own_summary_survives_many_newer_foreign_records(fabric):
    _store(fabric, "own_1", "owner", "conv_a", content="steward summary: review Wednesday")
    for i in range(105):
        _store(fabric, f"foreign_{i}", "other", "conv_b", content="steward summary neutral fact")
    own_filter = {"type": "steward_summary", "conversation_id": "conv_a", "user_id": "owner"}
    for limit in (1, 5, 100):
        results = fabric.search("steward summary", limit=limit, metadata_filter=own_filter, tags=["steward"])
        assert _ids(results) == ["own_1"], f"limit {limit}"
    assert all(r.metadata["user_id"] == "owner" for r in fabric.search("steward summary", limit=200, metadata_filter={"user_id": "owner"}))


def test_foreign_owner_never_returned(fabric):
    _store(fabric, "own_1", "owner", "conv_a")
    _store(fabric, "foreign_1", "other", "conv_a")  # same conversation id, other owner
    results = fabric.search("steward summary", limit=10, metadata_filter={"conversation_id": "conv_a", "user_id": "owner"})
    assert _ids(results) == ["own_1"]


def test_recent_order_and_limit(fabric):
    for i in range(5):
        _store(fabric, f"own_{i}", "owner", "conv_a", version=i + 1)
    results = fabric.search("steward summary", limit=2, metadata_filter={"user_id": "owner"}, order="recent")
    assert _ids(results) == ["own_4", "own_3"]


def test_ne_filter_excludes_archived_and_matches_absent_key(fabric):
    _store(fabric, "live", "owner", "conv_a")
    _store(fabric, "archived", "owner", "conv_a", archived=True)
    _store(fabric, "unarchived", "owner", "conv_a", archived=False)
    results = fabric.search("steward summary", limit=10, metadata_filter={"user_id": "owner", "archived": {"$ne": True}})
    assert sorted(_ids(results)) == ["live", "unarchived"]


def test_tags_match_any(fabric):
    fabric.store(content="alpha note", metadata={"user_id": "owner"}, tags=["pinned"], record_id="a")
    fabric.store(content="alpha note", metadata={"user_id": "owner"}, tags=["document"], record_id="b")
    fabric.store(content="alpha note", metadata={"user_id": "owner"}, tags=["other"], record_id="c")
    results = fabric.search("alpha", limit=10, tags=["pinned", "document"])
    assert sorted(_ids(results)) == ["a", "b"]


def test_empty_query_returns_rows_by_filters_alone(fabric):
    _store(fabric, "own_1", "owner", "conv_a")
    _store(fabric, "own_2", "owner", "conv_b")
    results = fabric.search("", limit=10, metadata_filter={"user_id": "owner", "conversation_id": "conv_b"})
    assert _ids(results) == ["own_2"]


def test_default_order_unchanged_without_filters(fabric):
    fabric.store(content="zeta first", metadata={}, record_id="first")
    fabric.store(content="zeta second", metadata={}, record_id="second")
    results = fabric.search("zeta", limit=10)
    assert sorted(_ids(results)) == ["first", "second"]


def test_client_side_fallback_for_stores_without_pushdown(fabric):
    class LegacyStore:
        def __init__(self, inner):
            self.inner = inner

        def search(self, query, limit=10, memory_type=None):
            return self.inner.search(query, limit, memory_type)

        def __getattr__(self, name):
            return getattr(self.inner, name)

    _store(fabric, "own_1", "owner", "conv_a")
    for i in range(105):
        _store(fabric, f"foreign_{i}", "other", "conv_b")
    fabric._store = LegacyStore(fabric._store)
    assert fabric._store_supports_scope_pushdown() is False
    results = fabric.search("steward summary", limit=1, metadata_filter={"user_id": "owner"})
    assert _ids(results) == ["own_1"]
