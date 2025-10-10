""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Test IOA Governance: Immutable Audit Chain

Verifies that the audit chain correctly appends entries and maintains hash continuity.
"""

import json
from pathlib import Path
from src.governance.audit_chain import AuditChain

def test_audit_chain_appends_and_chains(tmp_path: Path):
    """Test that audit chain correctly appends entries and maintains hash chain."""
    logf = tmp_path / "audit_chain.jsonl"
    ac = AuditChain(str(logf))
    # append 100 entries
    for i in range(100):
        ac.log("evt", {"i": i})
    lines = logf.read_text().strip().splitlines()
    assert len(lines) == 100
    prev = "0" * 64
    for line in lines:
        obj = json.loads(line)
        assert obj["prev_hash"] == prev
        assert isinstance(obj["hash"], str) and len(obj["hash"]) == 64
        prev = obj["hash"]
