# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

import pytest

from ioa_core.health import (
    build_health_session_context,
    gate_severity_for,
    get_jurisdiction_template,
    get_jurisdiction_template_registry,
    get_subcategory_profile,
    get_subcategory_profile_registry,
    recommend_subcategory_profile,
)


def test_recommend_profile_matches_dispatch_launch_profiles():
    assert recommend_subcategory_profile("General Practice", "NZ").id == "gp_nz"
    assert recommend_subcategory_profile("Mental Health", "AU").id == "mental_health_au"
    assert recommend_subcategory_profile("Telehealth", "NZ").id == "telehealth_au_nz"
    assert (
        recommend_subcategory_profile("Allied Health", "AU").id == "allied_health_au_nz"
    )
    assert recommend_subcategory_profile("Aged Care", "NZ").id == "aged_care_au_nz"
    assert recommend_subcategory_profile("Midwifery", "NZ").id == "midwifery_au_nz"
    assert recommend_subcategory_profile("Dental", "AU").id == "dental_au_nz"


def test_builtin_profile_registry_exposes_launch_profiles():
    registry = get_subcategory_profile_registry()
    profile_ids = {profile.id for profile in registry.list()}
    assert {
        "gp_nz",
        "gp_au",
        "mental_health_au",
        "mental_health_nz",
        "telehealth_au_nz",
        "allied_health_au_nz",
        "aged_care_au_nz",
        "midwifery_au_nz",
        "dental_au_nz",
    }.issubset(profile_ids)


def test_builtin_template_registry_contains_cross_jurisdiction_templates():
    registry = get_jurisdiction_template_registry()
    assert get_jurisdiction_template("nz_ipp3a_ai_disclosure").jurisdiction == "NZ"
    assert get_jurisdiction_template("au_ahpra_ai_guidance").jurisdiction == "AU"
    assert get_jurisdiction_template("hipaa").jurisdiction == "US"
    assert get_jurisdiction_template("au_aged_care_act").jurisdiction == "AU"
    assert get_jurisdiction_template("eu_ai_act_high_risk").jurisdiction == "EU"
    assert any(
        template.template_id == "uk_ico_ai_dpia"
        for template in registry.for_jurisdiction("UK")
    )


def test_build_health_session_context_stacks_patient_templates_without_duplicates():
    context = build_health_session_context(
        profile_id="mental_health_nz",
        patient_jurisdiction="AU",
        include_offshore_disclosure=True,
    )
    template_ids = [
        template["template_id"] for template in context["jurisdiction_templates"]
    ]
    assert "nz_ipp3a_ai_disclosure" in template_ids
    assert "au_privacy_act_ai" in template_ids
    assert template_ids.count("nz_hipc_rule12_offshore") == 1
    assert len(template_ids) == len(set(template_ids))


def test_profile_runtime_defaults_include_consent_and_deid_controls():
    profile = get_subcategory_profile("aged_care_au_nz")
    runtime_defaults = profile.to_runtime_defaults()
    assert runtime_defaults["consent"]["flow"] == "proxy_guardian"
    assert runtime_defaults["deid"]["incapacitated_patient_flag"] is True
    assert "mandatory_reporting_gate" in runtime_defaults["content_gates"]
    # New optional fields default safely on profiles that do not declare them.
    assert runtime_defaults["content_gate_policy"] == {}
    assert runtime_defaults["escalation_follow_up_hours"] is None


def test_youth_mental_health_profiles_are_registered_and_recommended():
    registry = get_subcategory_profile_registry()
    profile_ids = {profile.id for profile in registry.list()}
    assert {"youth_mental_health_nz", "youth_mental_health_au"}.issubset(profile_ids)
    assert (
        recommend_subcategory_profile("Youth Mental Health", "NZ").id
        == "youth_mental_health_nz"
    )
    assert recommend_subcategory_profile("CAMHS", "AU").id == "youth_mental_health_au"
    assert (
        recommend_subcategory_profile("adolescent mental health", "NZ").id
        == "youth_mental_health_nz"
    )
    # Existing recommendations are unchanged.
    assert recommend_subcategory_profile("Mental Health", "NZ").id == "mental_health_nz"
    assert recommend_subcategory_profile("Mental Health", "AU").id == "mental_health_au"


def test_youth_mental_health_nz_declares_gates_follow_up_and_guardian_consent():
    profile = get_subcategory_profile("youth_mental_health_nz")
    assert profile.consent.flow == "proxy_guardian"
    assert profile.consent.proxy_allowed is True
    assert profile.deid.tier == "elevated"
    assert profile.deid.psychotherapy_note_separation is True
    assert profile.content_gates == [
        "crisis_risk_to_self",
        "risk_to_others",
        "child_protection",
        "crisis_mandatory_reporting",
    ]
    assert all(
        gate_severity_for(profile, gate) == "escalate" for gate in profile.content_gates
    )
    assert profile.escalation_follow_up_hours == 24
    # 2.12.0: NZ profiles select the healthcare-nz pack, so the workaround note is gone.
    assert profile.policy_pack == "healthcare-nz"
    assert profile.policy_pack_note == ""
    assert any("Oranga Tamariki" in note for note in profile.jurisdiction_notes)
    assert "nz_oranga_tamariki_s15" in profile.jurisdiction.templates
    assert "nz_mcnz_ai_guidance_2026" in profile.jurisdiction.templates
    runtime_defaults = profile.to_runtime_defaults()
    assert runtime_defaults["escalation_follow_up_hours"] == 24
    assert runtime_defaults["content_gate_policy"]["child_protection"] == "escalate"
    with pytest.raises(KeyError):
        gate_severity_for(profile, "not_declared")


def test_gate_without_policy_defaults_to_acknowledge():
    import dataclasses

    profile = dataclasses.replace(
        get_subcategory_profile("mental_health_nz"), content_gate_policy={}
    )
    assert gate_severity_for(profile, "crisis_mandatory_reporting") == "acknowledge"


def test_adult_mental_health_profiles_gate_risk_and_set_a_follow_up_deadline():
    # 2.13.0: adult mental health gates risk to self and risk to others as well
    # as crisis and mandatory reporting, all at escalate with a 24 hour
    # follow-up. Child protection stays youth only. Consent is unchanged.
    for profile_id in ("mental_health_nz", "mental_health_au"):
        profile = get_subcategory_profile(profile_id)
        assert profile.content_gates == [
            "crisis_risk_to_self",
            "risk_to_others",
            "crisis_mandatory_reporting",
        ]
        assert all(
            gate_severity_for(profile, gate) == "escalate"
            for gate in profile.content_gates
        )
        assert "child_protection" not in profile.content_gates
        assert profile.escalation_follow_up_hours == 24
        assert profile.consent.proxy_allowed is False
