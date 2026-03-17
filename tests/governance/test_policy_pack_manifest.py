# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

import os

from ioa_core.governance import manifest


def test_load_au_health_manifest_via_env(monkeypatch):
    monkeypatch.setenv("IOA_POLICY_PACK", "healthcare_au")
    laws = manifest.load_manifest(policy_pack="healthcare_au", verify_signature_flag=False)
    assert laws.policy.get("jurisdiction", {}).get("default") == "AU"
    assert laws.get_jurisdiction_affinity() == ["AU"]


def test_get_laws_uses_policy_pack_override(monkeypatch):
    monkeypatch.setenv("IOA_POLICY_PACK", "healthcare_au")
    laws = manifest.get_laws(policy_pack="healthcare_au")
    assert laws.policy.get("jurisdiction", {}).get("default") == "AU"
