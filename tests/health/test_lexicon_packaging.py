# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""The lexicons must ship as package data so installed wheels load them."""

import json
from importlib import resources

import pytest

from ioa_core.health import GATE_DEFINITIONS

EXPECTED = {
    "crisis_risk_to_self",
    "risk_to_others",
    "child_protection",
    "crisis_mandatory_reporting",
}


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_lexicon_is_packaged_and_well_formed(name: str):
    path = resources.files("ioa_core.health.lexicons").joinpath(f"{name}.json")
    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"]
    assert payload["category"]
    assert payload["default_severity"] == "escalate"
    assert payload["words"] or payload["patterns"]
    assert "synthetic" in payload.get("notes", "").lower()


def test_every_defined_gate_has_a_lexicon():
    assert {definition.lexicon for definition in GATE_DEFINITIONS.values()} == EXPECTED
