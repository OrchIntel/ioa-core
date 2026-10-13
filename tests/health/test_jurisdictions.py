# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""State-level jurisdiction model: layered templates, country fallback, gate text."""

from __future__ import annotations

import re

import pytest

from ioa_core.health import (
    AU_STATE_CODES,
    GATE_JURISDICTION_TEMPLATES,
    build_health_session_context,
    gate_jurisdiction_template_id,
    gate_jurisdiction_text,
    get_jurisdiction_template_registry,
    get_subcategory_profile,
    recommend_subcategory_profile,
)
from ioa_core.health.registry import (
    _split_jurisdiction_code,
    _template_implied_jurisdiction,
    _template_implied_sub_jurisdiction,
)

REGISTRY = get_jurisdiction_template_registry()


def test_split_jurisdiction_code():
    assert _split_jurisdiction_code("AU-NSW") == ("AU", "NSW")
    assert _split_jurisdiction_code("au-nsw") == ("AU", "NSW")
    assert _split_jurisdiction_code("US-CA") == ("US", "CA")
    assert _split_jurisdiction_code("NZ") == ("NZ", None)


def test_state_prefix_inference():
    assert _template_implied_jurisdiction("au_nsw_child_protection_reporting") == "AU"
    assert (
        _template_implied_sub_jurisdiction("au_nsw_child_protection_reporting")
        == "AU-NSW"
    )
    assert _template_implied_sub_jurisdiction("au_privacy_act") is None
    assert _template_implied_sub_jurisdiction("nz_hipc") is None


def test_layered_lookup_adds_national_templates_under_a_state():
    layered = [t.template_id for t in REGISTRY.for_jurisdiction("AU-NSW", layered=True)]
    assert "au_privacy_act" in layered
    assert "au_ahpra_ai_guidance" in layered
    assert "au_nsw_child_protection_reporting" in layered
    assert "au_nsw_mental_health_act" in layered
    assert "au_nsw_hripa" in layered
    assert not any("_vic_" in t for t in layered)
    # National templates come first.
    assert layered.index("au_privacy_act") < layered.index(
        "au_nsw_child_protection_reporting"
    )


def test_exact_lookup_is_unchanged():
    assert [t.template_id for t in REGISTRY.for_jurisdiction("US-CA")] == [
        "us_ca_ab3030"
    ]
    assert [t.template_id for t in REGISTRY.for_jurisdiction("AU-NSW")] == sorted(
        [
            "au_nsw_child_protection_reporting",
            "au_nsw_hripa",
            "au_nsw_mental_health_act",
        ]
    )
    assert REGISTRY.for_jurisdiction("AU") == REGISTRY.for_jurisdiction(
        "AU", layered=True
    )


def test_recommendation_never_falls_to_nz_for_an_australian_state():
    assert recommend_subcategory_profile("something unknown", "AU-VIC").id == "gp_au"
    assert recommend_subcategory_profile("something unknown", "AU").id == "gp_au"
    assert recommend_subcategory_profile("something unknown", "NZ").id == "gp_nz"
    assert (
        recommend_subcategory_profile("youth mental health", "AU-QLD").id
        == "youth_mental_health_au"
    )
    assert (
        recommend_subcategory_profile("Mental Health", "AU-TAS").id
        == "mental_health_au"
    )
    assert recommend_subcategory_profile("General Practice", "AU-WA").id == "gp_au"
    # Existing recommendations unchanged.
    assert (
        recommend_subcategory_profile("Youth Mental Health", "NZ").id
        == "youth_mental_health_nz"
    )
    assert recommend_subcategory_profile("Telehealth", "NZ").id == "telehealth_au_nz"


@pytest.mark.parametrize("state", AU_STATE_CODES)
def test_every_state_has_child_protection_and_mental_health_act_templates(state: str):
    code = f"AU-{state}"
    ids = {t.template_id for t in REGISTRY.for_jurisdiction(code)}
    assert f"au_{state.lower()}_child_protection_reporting" in ids
    assert any(t.startswith(f"au_{state.lower()}_mental_health") for t in ids)
    cp = REGISTRY.require(f"au_{state.lower()}_child_protection_reporting")
    assert cp.requires_explicit_confirm is True
    assert cp.review_status == "draft_pending_legal_review"
    assert cp.summary and len(cp.summary) <= 300
    assert gate_jurisdiction_template_id("child_protection", code) == cp.template_id


def test_gate_text_reflects_the_state_and_is_neutral_nationally():
    wa = gate_jurisdiction_text("child_protection", "AU-WA")
    assert wa and "sexual abuse" in wa and "psychologists" in wa
    qld = gate_jurisdiction_text("child_protection", "AU-QLD")
    assert qld and "not mandated" in qld
    nsw = gate_jurisdiction_text("child_protection", "AU-NSW")
    assert nsw and "significant harm" in nsw and "domestic violence" in nsw
    nz = gate_jurisdiction_text("child_protection", "NZ")
    assert nz and "permissive" in nz and "does not report" in nz
    national = gate_jurisdiction_text("child_protection", "AU")
    assert national and "select the patient's state" in national
    assert gate_jurisdiction_text("risk_to_others", "AU-NSW") is None
    assert gate_jurisdiction_text("child_protection", "UK") is None
    assert set(GATE_JURISDICTION_TEMPLATES["child_protection"]) == {
        "NZ",
        *(f"AU-{s}" for s in AU_STATE_CODES),
    }


def test_template_hygiene():
    for template in REGISTRY.list():
        assert re.fullmatch(
            r"[a-z0-9_]{1,80}", template.template_id
        ), template.template_id
        assert len(template.summary) <= 300, template.template_id
        assert template.review_status in {
            "reviewed",
            "draft_pending_legal_review",
            "unspecified",
        }
    for template in REGISTRY.list():
        if template.template_id.startswith(
            "au_"
        ) and _template_implied_sub_jurisdiction(template.template_id):
            assert template.jurisdiction == _template_implied_sub_jurisdiction(
                template.template_id
            )
    assert len({t.template_id for t in REGISTRY.list()}) == len(REGISTRY.list())


def test_session_context_layers_state_templates_for_an_australian_youth_profile():
    context = build_health_session_context(
        profile_id="youth_mental_health_au", patient_jurisdiction="AU-NSW"
    )
    ids = [t["template_id"] for t in context["jurisdiction_templates"]]
    assert ids[:4] == [
        "au_privacy_act",
        "au_privacy_act_ai",
        "au_ahpra_ai_guidance",
        "au_privacy_act_adm_transparency",
    ]
    assert "au_nsw_child_protection_reporting" in ids
    assert "au_nsw_hripa" in ids
    assert not any("_vic_" in i for i in ids)
    assert len(ids) == len(set(ids))
    defaults = context["runtime_defaults"]
    assert defaults["supported_sub_jurisdictions"] == [
        f"AU-{s}" for s in AU_STATE_CODES
    ]
    profile = get_subcategory_profile("youth_mental_health_au")
    assert profile.policy_pack_note == ""
    assert any("Gillick" in note for note in profile.jurisdiction_notes)


def test_nz_profiles_carry_the_2026_guidance_templates_and_nz_pack():
    for pid in ("youth_mental_health_nz", "mental_health_nz"):
        profile = get_subcategory_profile(pid)
        assert profile.policy_pack == "healthcare-nz"
        for tid in (
            "nz_mental_health_act_2026_transition",
            "nz_mcnz_ai_guidance_2026",
            "nz_health_nz_ai_framework_2026",
        ):
            assert tid in profile.jurisdiction.templates, (pid, tid)
    assert (
        "nz_oranga_tamariki_s15"
        in get_subcategory_profile("youth_mental_health_nz").jurisdiction.templates
    )
    mcnz = REGISTRY.require("nz_mcnz_ai_guidance_2026")
    assert mcnz.requires_explicit_confirm is True
    assert "consent" in mcnz.summary.lower()
