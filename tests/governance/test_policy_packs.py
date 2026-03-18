# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

from ioa_core.governance.policy_packs import (
    list_policy_packs,
    resolve_manifest_filename,
    resolve_policy_pack_definition,
)


def test_healthcare_au_is_first_class_policy_pack_definition() -> None:
    pack = resolve_policy_pack_definition("healthcare-au")
    assert pack is not None
    assert pack["pack_id"] == "qix_health_au"
    assert pack["policy_pack"] == "healthcare-au"
    assert pack["default_jurisdiction"] == "AU"
    assert "AU Privacy Act 1988" in pack["regulatory_frameworks"]


def test_healthcare_aliases_resolve_same_manifest() -> None:
    assert resolve_manifest_filename("healthcare-au") == "system_laws_au_health.json"
    assert resolve_manifest_filename("healthcare_au") == "system_laws_au_health.json"
    assert resolve_manifest_filename("qixhealth") == "system_laws_au_health.json"


def test_policy_pack_catalog_contains_expected_packs() -> None:
    packs = list_policy_packs()
    assert "qix_general" in packs
    assert "qix_health_au" in packs
    assert "qixcite_legal" in packs
