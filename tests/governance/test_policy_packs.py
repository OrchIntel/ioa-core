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


def test_healthcare_nz_is_a_policy_pack_with_its_own_manifest() -> None:
    pack = resolve_policy_pack_definition("healthcare-nz")
    assert pack is not None
    assert pack["pack_id"] == "qix_health_nz"
    assert pack["default_jurisdiction"] == "NZ"
    assert resolve_manifest_filename("healthcare-nz") == "system_laws_nz_health.json"
    assert resolve_manifest_filename("qixhealth-nz") == "system_laws_nz_health.json"
    # The AU aliases are unchanged.
    assert resolve_manifest_filename("qixhealth") == "system_laws_au_health.json"


def test_every_bundled_manifest_loads_and_is_valid_for_at_least_30_days() -> None:
    """A manifest that is about to expire must fail CI, not raise in production."""
    import json
    from datetime import datetime, timedelta, timezone
    from importlib import resources

    from ioa_core.governance.policy_packs import list_policy_packs

    seen = set()
    for pack in list_policy_packs().values():
        manifest_name = pack["manifest"]
        if manifest_name in seen:
            continue
        seen.add(manifest_name)
        path = resources.files("ioa_core.governance").joinpath(manifest_name)
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["laws"], manifest_name
        expires = datetime.fromisoformat(
            payload["metadata"]["expires"].replace("Z", "+00:00")
        )
        assert expires > datetime.now(timezone.utc) + timedelta(
            days=30
        ), f"{manifest_name} expires {expires.date()}; renew it before release"
