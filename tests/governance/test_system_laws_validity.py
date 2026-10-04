# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""
The bundled System Laws manifests must load and stay valid well ahead of
expiry. An expired manifest makes PolicyEngine() raise at startup, which in
QIXChat silently disabled governance checks (OP-14). This test fails 60 days
before expiry so renewal happens in CI, not in production.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from ioa_core.governance import manifest as manifest_module

GOVERNANCE_DIR = Path(manifest_module.__file__).parent
MANIFESTS = sorted(
    p for p in GOVERNANCE_DIR.glob("system_laws*.json") if not p.name.endswith(".schema.json")
)
RENEWAL_WINDOW = timedelta(days=60)


def test_manifests_found():
    assert any(p.name == "system_laws.json" for p in MANIFESTS)


@pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: p.name)
def test_manifest_not_near_expiry(path):
    data = json.loads(path.read_text())
    expires = datetime.fromisoformat(data["metadata"]["expires"].replace("Z", "+00:00"))
    remaining = expires - datetime.now(timezone.utc)
    assert remaining > RENEWAL_WINDOW, f"{path.name} expires {expires.isoformat()}; renew it now"


def test_default_manifest_loads():
    laws = manifest_module.load_manifest(verify_signature_flag=False)
    assert laws is not None
