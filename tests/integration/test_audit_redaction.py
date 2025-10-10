""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone

from src.governance.audit_chain import AuditChain


def test_audit_redaction(tmp_path):
    log_path = tmp_path / "audit_redaction.jsonl"
    os.environ["IOA_AUDIT_LOG"] = str(log_path)
    chain = AuditChain(log_path=str(log_path), rotate_bytes=10_000_000)

    payload = {
        "api_key": "sk-abcdef0123456789",
        "Authorization": "Bearer xyz",
        "email": "user@example.com",
        "nested": {"password": "secret", "token": "abc"},
        "list": [
            {"apikey": "sk-foo"},
            "plain text",
            "contact user@example.com",
        ],
    }

    chain.log("test_event", payload)

    assert log_path.exists()
    data = log_path.read_text(encoding="utf-8").strip().splitlines()[-1]
    record = json.loads(data)
    d = record["data"]
    assert d["api_key"] == "[REDACTED]"
    assert d["Authorization"] == "[REDACTED]"
    assert d["email"] == "[REDACTED]"
    assert d["nested"]["password"] == "[REDACTED]"
    assert d["nested"]["token"] == "[REDACTED]"
    assert d["list"][0]["apikey"] == "[REDACTED]"
    # Plain text should remain unchanged
    assert d["list"][1] == "plain text"


