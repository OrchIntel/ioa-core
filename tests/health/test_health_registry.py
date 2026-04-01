# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

from ioa_core.health import (
    build_health_session_context,
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
    assert recommend_subcategory_profile("Allied Health", "AU").id == "allied_health_au_nz"
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
