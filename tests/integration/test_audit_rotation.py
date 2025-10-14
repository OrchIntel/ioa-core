"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone

from src.governance.audit_chain import AuditChain


def test_audit_rotation(tmp_path):
    log_path = tmp_path / "audit_rotation.jsonl"
    # Force very small rotation threshold
    chain = AuditChain(log_path=str(log_path), rotate_bytes=256)

    # Write enough entries to trigger rotation
    for i in range(200):
        chain.log("event", {"i": i, "message": "x" * 50})

    # Check directory contents for rotated file(s)
    files = list(tmp_path.iterdir())
    rotated = [p for p in files if p.is_file() and p.name.startswith("audit_rotation-")]
    assert len(rotated) >= 1
    # Rotated filename should contain a 12-hex digest prefix per implementation
    assert any(len(p.stem.split("-")) >= 3 and len(p.stem.split("-")[-1]) == 12 for p in rotated)


