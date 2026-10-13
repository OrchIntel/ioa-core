# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""QiXHealth subcategory profiles and jurisdiction template registries."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import re
from functools import lru_cache
from importlib import resources
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


@dataclass(frozen=True)
class ConsentFlowConfig:
    flow: str
    renewal_days: Optional[int]
    in_session_confirm: bool
    pre_session_sms: bool
    proxy_allowed: bool


@dataclass(frozen=True)
class DeIdentificationConfig:
    tier: str
    psychotherapy_note_separation: bool
    incapacitated_patient_flag: bool


@dataclass(frozen=True)
class RoundtableConfig:
    enabled: bool
    trigger: str


@dataclass(frozen=True)
class JurisdictionBinding:
    primary: str
    templates: List[str]


@dataclass(frozen=True)
class SubcategoryContextProfile:
    id: str
    label: str
    subcategory: str
    jurisdiction: JurisdictionBinding
    consent: ConsentFlowConfig
    deid: DeIdentificationConfig
    content_gates: List[str]
    roles: List[str]
    roundtable: RoundtableConfig
    governance_pack_id: str
    policy_pack: str
    default_governance_mode: str
    aliases: List[str]
    # Gate name -> severity policy ("info", "flag", "acknowledge", "escalate",
    # "hold"). Gates listed in content_gates without a policy entry default to
    # "acknowledge" (see gate_severity_for).
    content_gate_policy: Dict[str, str] = field(default_factory=dict)
    # Hours allowed to confirm follow-up after a gate fires at "escalate" or
    # above. None means the profile does not create follow-up obligations.
    escalation_follow_up_hours: Optional[int] = None
    policy_pack_note: str = ""
    jurisdiction_notes: List[str] = field(default_factory=list)
    # Sub-national codes (for example AU-NSW) whose templates layer under this
    # profile when the patient jurisdiction names them.
    supported_sub_jurisdictions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_runtime_defaults(self) -> Dict[str, Any]:
        return {
            "subcategory_profile_id": self.id,
            "subcategory": self.subcategory,
            "jurisdiction": self.jurisdiction.primary,
            "governance_pack_id": self.governance_pack_id,
            "policy_pack": self.policy_pack,
            "default_governance_mode": self.default_governance_mode,
            "consent": asdict(self.consent),
            "deid": asdict(self.deid),
            "content_gates": list(self.content_gates),
            "content_gate_policy": dict(self.content_gate_policy),
            "escalation_follow_up_hours": self.escalation_follow_up_hours,
            "supported_sub_jurisdictions": list(self.supported_sub_jurisdictions),
            "roles": list(self.roles),
            "roundtable": asdict(self.roundtable),
            "jurisdiction_templates": list(self.jurisdiction.templates),
        }


DEFAULT_GATE_SEVERITY = "acknowledge"


def gate_severity_for(profile: SubcategoryContextProfile, gate_name: str) -> str:
    """Return the severity policy for a gate declared on a profile.

    A gate listed in ``content_gates`` without an entry in
    ``content_gate_policy`` defaults to ``acknowledge`` so that a declared gate
    can never fire silently.
    """
    name = str(gate_name or "").strip()
    if name not in profile.content_gates:
        raise KeyError(f"Gate {name!r} is not declared on profile {profile.id!r}")
    return str(profile.content_gate_policy.get(name) or DEFAULT_GATE_SEVERITY).strip()


@dataclass(frozen=True)
class JurisdictionTemplate:
    template_id: str
    version: str
    effective_date: str
    jurisdiction: str
    language: str
    title: str
    body: str
    requires_explicit_confirm: bool
    auto_renew_days: Optional[int]
    audit_field: str
    # One-line statement (<= 300 chars) used for gate acknowledgement labels
    # and evidence cards. Bodies are long; summaries are what the clinician
    # sees next to a fired gate. Receipts record template ids only.
    summary: str = ""
    # "reviewed", "draft_pending_legal_review" or "unspecified" (legacy entries).
    review_status: str = "unspecified"
    # Care settings (profile subcategories) the template applies to. Empty
    # means every care setting. Used when a jurisdiction layers templates onto
    # a profile, so a youth mental health session never lists the Aged Care
    # Act and a dental clinic never lists a Mental Health Act.
    care_settings: List[str] = field(default_factory=list)

    def applies_to(self, care_setting: Optional[str]) -> bool:
        if not self.care_settings or not care_setting:
            return True
        return str(care_setting).strip().lower() in self.care_settings

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class JurisdictionTemplateRegistry:
    """Registry for consent/disclosure templates keyed by jurisdiction and template id."""

    def __init__(self, templates: Mapping[str, JurisdictionTemplate]):
        self._templates = dict(templates)

    @classmethod
    def from_builtin(cls) -> "JurisdictionTemplateRegistry":
        return cls(_load_templates())

    def get(self, template_id: str) -> Optional[JurisdictionTemplate]:
        return self._templates.get(str(template_id or "").strip())

    def require(self, template_id: str) -> JurisdictionTemplate:
        template = self.get(template_id)
        if template is None:
            raise KeyError(f"Unknown jurisdiction template: {template_id}")
        return template

    def list(self) -> List[JurisdictionTemplate]:
        return [self._templates[key] for key in sorted(self._templates)]

    def for_jurisdiction(
        self, jurisdiction: str, *, layered: bool = False
    ) -> List[JurisdictionTemplate]:
        """Templates for a jurisdiction code.

        ``layered=False`` (default) matches the code exactly, as before.
        ``layered=True`` returns the national templates first and then the
        state or territory templates for a sub-national code such as
        ``AU-NSW``; for a national code it is the same as the exact match.
        """
        normalized = _normalize_jurisdiction_code(jurisdiction)
        exact = [
            template
            for template in self.list()
            if _normalize_jurisdiction_code(template.jurisdiction) == normalized
        ]
        if not layered:
            return exact
        country, state = _split_jurisdiction_code(normalized)
        if state is None:
            return exact
        national = [
            template
            for template in self.list()
            if _normalize_jurisdiction_code(template.jurisdiction) == country
        ]
        seen = set()
        ordered: List[JurisdictionTemplate] = []
        for template in national + exact:
            if template.template_id not in seen:
                ordered.append(template)
                seen.add(template.template_id)
        return ordered

    def resolve_template_ids(
        self,
        *,
        profile: Optional[SubcategoryContextProfile] = None,
        jurisdictions: Optional[Iterable[str]] = None,
        include_offshore_disclosure: bool = False,
    ) -> List[str]:
        ordered: List[str] = []
        seen = set()
        if profile is not None:
            for template_id in profile.jurisdiction.templates:
                if template_id not in seen:
                    ordered.append(template_id)
                    seen.add(template_id)
        care_setting = profile.subcategory if profile is not None else None
        for jurisdiction in jurisdictions or []:
            # A patient jurisdiction such as AU-NSW layers the national
            # templates under the state ones, limited to templates that apply
            # to the profile's care setting. The profile's own list is curated
            # and always kept.
            for template in self.for_jurisdiction(jurisdiction, layered=True):
                if not template.applies_to(care_setting):
                    continue
                if template.template_id not in seen:
                    ordered.append(template.template_id)
                    seen.add(template.template_id)
        if (
            include_offshore_disclosure
            and profile
            and profile.jurisdiction.primary == "NZ"
        ):
            offshore_id = "nz_hipc_rule12_offshore"
            if offshore_id not in seen:
                ordered.append(offshore_id)
        return ordered

    def resolve_templates(
        self,
        *,
        profile: Optional[SubcategoryContextProfile] = None,
        jurisdictions: Optional[Iterable[str]] = None,
        include_offshore_disclosure: bool = False,
    ) -> List[JurisdictionTemplate]:
        return [
            self.require(template_id)
            for template_id in self.resolve_template_ids(
                profile=profile,
                jurisdictions=jurisdictions,
                include_offshore_disclosure=include_offshore_disclosure,
            )
        ]


class SubcategoryContextProfileRegistry:
    """Registry for QiXHealth subcategory context profiles."""

    def __init__(self, profiles: Mapping[str, SubcategoryContextProfile]):
        self._profiles = dict(profiles)
        self._aliases: Dict[tuple[str, str], str] = {}
        self._alias_scores: Dict[tuple[str, str], int] = {}
        for profile in self._profiles.values():
            keys = {profile.subcategory, *profile.aliases}
            supported_jurisdictions = _supported_jurisdictions(profile)
            primary = _normalize_jurisdiction_code(profile.jurisdiction.primary)
            for key in keys:
                alias = _normalize_alias(key)
                if not alias:
                    continue
                for jurisdiction in supported_jurisdictions:
                    score = _profile_recommendation_score(
                        profile,
                        jurisdiction=jurisdiction,
                        primary_jurisdiction=primary,
                    )
                    current_score = self._alias_scores.get((alias, jurisdiction), -1)
                    if score >= current_score:
                        self._aliases[(alias, jurisdiction)] = profile.id
                        self._alias_scores[(alias, jurisdiction)] = score

    @classmethod
    def from_builtin(cls) -> "SubcategoryContextProfileRegistry":
        return cls(_load_profiles())

    def get(self, profile_id: str) -> Optional[SubcategoryContextProfile]:
        return self._profiles.get(str(profile_id or "").strip())

    def require(self, profile_id: str) -> SubcategoryContextProfile:
        profile = self.get(profile_id)
        if profile is None:
            raise KeyError(f"Unknown subcategory profile: {profile_id}")
        return profile

    def list(self) -> List[SubcategoryContextProfile]:
        return [self._profiles[key] for key in sorted(self._profiles)]

    def recommend(
        self, subcategory: str, jurisdiction: str
    ) -> SubcategoryContextProfile:
        normalized_jurisdiction = _normalize_jurisdiction_code(jurisdiction)
        alias = _normalize_alias(subcategory)
        country, _state = _split_jurisdiction_code(normalized_jurisdiction)
        profile_id = self._aliases.get(
            (alias, normalized_jurisdiction)
        ) or self._aliases.get((alias, country))
        if profile_id:
            return self.require(profile_id)
        # Fallback by country: an Australian state must never land on an NZ
        # general practice profile.
        if country == "AU":
            return self.require("gp_au")
        return self.require("gp_nz")


@lru_cache(maxsize=1)
def _load_profiles() -> Dict[str, SubcategoryContextProfile]:
    raw_profiles = _read_json_resource("subcategory_profiles.json")
    profiles: Dict[str, SubcategoryContextProfile] = {}
    for item in raw_profiles:
        profile = _profile_from_mapping(item)
        profiles[profile.id] = profile
    return profiles


@lru_cache(maxsize=1)
def _load_templates() -> Dict[str, JurisdictionTemplate]:
    raw_templates = _read_json_resource("jurisdiction_templates.json")
    templates: Dict[str, JurisdictionTemplate] = {}
    for item in raw_templates:
        template = _template_from_mapping(item)
        templates[template.template_id] = template
    return templates


def get_subcategory_profile_registry() -> SubcategoryContextProfileRegistry:
    return SubcategoryContextProfileRegistry.from_builtin()


def get_jurisdiction_template_registry() -> JurisdictionTemplateRegistry:
    return JurisdictionTemplateRegistry.from_builtin()


def recommend_subcategory_profile(
    subcategory: str, jurisdiction: str
) -> SubcategoryContextProfile:
    return get_subcategory_profile_registry().recommend(subcategory, jurisdiction)


def get_subcategory_profile(profile_id: str) -> SubcategoryContextProfile:
    return get_subcategory_profile_registry().require(profile_id)


def get_jurisdiction_template(template_id: str) -> JurisdictionTemplate:
    return get_jurisdiction_template_registry().require(template_id)


def build_health_session_context(
    *,
    profile_id: str,
    patient_jurisdiction: Optional[str] = None,
    include_offshore_disclosure: bool = False,
) -> Dict[str, Any]:
    profile = get_subcategory_profile(profile_id)
    registry = get_jurisdiction_template_registry()
    jurisdictions: List[str] = []
    if patient_jurisdiction:
        jurisdictions.append(patient_jurisdiction)
    template_ids = registry.resolve_template_ids(
        profile=profile,
        jurisdictions=jurisdictions,
        include_offshore_disclosure=include_offshore_disclosure,
    )
    templates = [
        registry.require(template_id).to_dict() for template_id in template_ids
    ]
    return {
        "profile": profile.to_dict(),
        "runtime_defaults": profile.to_runtime_defaults(),
        "jurisdiction_templates": templates,
    }


def _read_json_resource(filename: str) -> Sequence[Mapping[str, Any]]:
    with (
        resources.files("ioa_core.health")
        .joinpath(filename)
        .open("r", encoding="utf-8") as handle
    ):
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list payload in {filename}")
    return payload


def _profile_from_mapping(item: Mapping[str, Any]) -> SubcategoryContextProfile:
    jurisdiction = (
        item.get("jurisdiction")
        if isinstance(item.get("jurisdiction"), Mapping)
        else {}
    )
    consent = item.get("consent") if isinstance(item.get("consent"), Mapping) else {}
    deid = item.get("deid") if isinstance(item.get("deid"), Mapping) else {}
    roundtable = (
        item.get("roundtable") if isinstance(item.get("roundtable"), Mapping) else {}
    )
    return SubcategoryContextProfile(
        id=str(item.get("id") or "").strip(),
        label=str(item.get("label") or "").strip(),
        subcategory=str(item.get("subcategory") or "").strip(),
        jurisdiction=JurisdictionBinding(
            primary=_normalize_jurisdiction_code(jurisdiction.get("primary")),
            templates=[
                str(template_id).strip()
                for template_id in jurisdiction.get("templates", [])
            ],
        ),
        consent=ConsentFlowConfig(
            flow=str(consent.get("flow") or "in_session").strip(),
            renewal_days=_optional_int(consent.get("renewal_days")),
            in_session_confirm=bool(consent.get("in_session_confirm", False)),
            pre_session_sms=bool(consent.get("pre_session_sms", False)),
            proxy_allowed=bool(consent.get("proxy_allowed", False)),
        ),
        deid=DeIdentificationConfig(
            tier=str(deid.get("tier") or "standard").strip(),
            psychotherapy_note_separation=bool(
                deid.get("psychotherapy_note_separation", False)
            ),
            incapacitated_patient_flag=bool(
                deid.get("incapacitated_patient_flag", False)
            ),
        ),
        content_gates=[
            str(item_name).strip() for item_name in item.get("content_gates", [])
        ],
        roles=[str(role).strip() for role in item.get("roles", [])],
        roundtable=RoundtableConfig(
            enabled=bool(roundtable.get("enabled", False)),
            trigger=str(roundtable.get("trigger") or "disabled").strip(),
        ),
        governance_pack_id=str(item.get("governance_pack_id") or "qix_health").strip(),
        policy_pack=str(item.get("policy_pack") or "healthcare-au").strip(),
        default_governance_mode=str(
            item.get("default_governance_mode") or "enforce"
        ).strip(),
        aliases=[
            str(alias).strip()
            for alias in item.get("aliases", [])
            if str(alias).strip()
        ],
        content_gate_policy={
            str(gate).strip(): str(severity).strip()
            for gate, severity in (
                item.get("content_gate_policy")
                if isinstance(item.get("content_gate_policy"), Mapping)
                else {}
            ).items()
            if str(gate).strip() and str(severity).strip()
        },
        escalation_follow_up_hours=_optional_int(
            item.get("escalation_follow_up_hours")
        ),
        policy_pack_note=str(item.get("policy_pack_note") or "").strip(),
        jurisdiction_notes=[
            str(note).strip()
            for note in item.get("jurisdiction_notes", [])
            if str(note).strip()
        ],
        supported_sub_jurisdictions=[
            _normalize_jurisdiction_code(code)
            for code in item.get("supported_sub_jurisdictions", [])
            if str(code).strip()
        ],
    )


def _template_from_mapping(item: Mapping[str, Any]) -> JurisdictionTemplate:
    return JurisdictionTemplate(
        template_id=str(item.get("template_id") or "").strip(),
        version=str(item.get("version") or "1.0").strip(),
        effective_date=str(item.get("effective_date") or "").strip(),
        jurisdiction=_normalize_jurisdiction_code(item.get("jurisdiction")),
        language=str(item.get("language") or "en").strip(),
        title=str(item.get("title") or "").strip(),
        body=str(item.get("body") or "").strip(),
        requires_explicit_confirm=bool(item.get("requires_explicit_confirm", False)),
        auto_renew_days=_optional_int(item.get("auto_renew_days")),
        audit_field=str(item.get("audit_field") or "").strip(),
        summary=str(item.get("summary") or "").strip()[:300],
        review_status=str(item.get("review_status") or "unspecified").strip(),
        care_settings=[
            str(value).strip().lower()
            for value in (item.get("care_settings") or [])
            if str(value).strip()
        ],
    )


def _normalize_alias(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("&", " and ")
    for token in ("-", "/"):
        text = text.replace(token, " ")
    return "_".join(part for part in text.split() if part)


def _normalize_jurisdiction_code(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text or "NZ"


AU_STATE_CODES = ("NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT")
_AU_STATE_PREFIX = re.compile(r"^au_(nsw|vic|qld|wa|sa|tas|act|nt)_")


def _split_jurisdiction_code(code: str) -> tuple[str, Optional[str]]:
    """Split ``AU-NSW`` into ``("AU", "NSW")``; a national code has no state."""
    normalized = _normalize_jurisdiction_code(code)
    if "-" in normalized:
        country, state = normalized.split("-", 1)
        return country, (state or None)
    return normalized, None


def _template_implied_sub_jurisdiction(template_id: str) -> Optional[str]:
    normalized = str(template_id or "").strip().lower()
    match = _AU_STATE_PREFIX.match(normalized)
    if match:
        return f"AU-{match.group(1).upper()}"
    return None


def _template_implied_jurisdiction(template_id: str) -> Optional[str]:
    normalized = str(template_id or "").strip().lower()
    if normalized.startswith("nz_"):
        return "NZ"
    if normalized.startswith("au_"):
        return "AU"
    if normalized.startswith("us_") or normalized == "hipaa":
        return "US"
    if normalized.startswith("uk_"):
        return "UK"
    if normalized.startswith("eu_"):
        return "EU"
    return None


def _supported_jurisdictions(profile: SubcategoryContextProfile) -> List[str]:
    supported = {_normalize_jurisdiction_code(profile.jurisdiction.primary)}
    for template_id in profile.jurisdiction.templates:
        implied = _template_implied_jurisdiction(template_id)
        if implied:
            supported.add(implied)
        implied_sub = _template_implied_sub_jurisdiction(template_id)
        if implied_sub:
            supported.add(implied_sub)
    supported.update(profile.supported_sub_jurisdictions)
    return sorted(supported)


def _profile_recommendation_score(
    profile: SubcategoryContextProfile,
    *,
    jurisdiction: str,
    primary_jurisdiction: str,
) -> int:
    normalized_id = profile.id.lower()
    score = 0
    if normalized_id.endswith("_au_nz"):
        score += 8
    # A state code scores as its country (AU-NSW matches a primary of AU).
    if (
        jurisdiction == primary_jurisdiction
        or _split_jurisdiction_code(jurisdiction)[0] == primary_jurisdiction
    ):
        score += 4
    if profile.subcategory in {
        "telehealth",
        "allied_health",
        "aged_care",
        "midwifery",
        "dental",
    }:
        score += 2
    if jurisdiction in _supported_jurisdictions(profile):
        score += 1
    return score


def _optional_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# Which jurisdiction template states the reporting position for a gate. The
# evaluator never reads these; the console uses them for the acknowledgement
# label next to a fired gate, and the receipt records the template ids shown.
GATE_JURISDICTION_TEMPLATES: Dict[str, Dict[str, str]] = {
    "child_protection": {
        "NZ": "nz_oranga_tamariki_s15",
        **{
            f"AU-{state}": f"au_{state.lower()}_child_protection_reporting"
            for state in AU_STATE_CODES
        },
    },
    "crisis_mandatory_reporting": {
        "NZ": "nz_mental_health_act_2026_transition",
        **{
            f"AU-{state}": f"au_{state.lower()}_mental_health_act"
            for state in AU_STATE_CODES
        },
    },
}
_AU_NATIONAL_GATE_LINE = (
    "Mandatory reporting is set by state or territory law in Australia; select the "
    "patient's state to see who is mandated to report, what, and to whom."
)


def gate_jurisdiction_template_id(gate_name: str, jurisdiction: str) -> Optional[str]:
    code = _normalize_jurisdiction_code(jurisdiction)
    mapping = GATE_JURISDICTION_TEMPLATES.get(str(gate_name or "").strip(), {})
    return mapping.get(code)


def gate_jurisdiction_text(gate_name: str, jurisdiction: str) -> Optional[str]:
    """One-line jurisdiction statement for a gate, or None when nothing applies.

    For a bare ``AU`` code on a gate that varies by state the line says so
    instead of guessing a state.
    """
    gate = str(gate_name or "").strip()
    code = _normalize_jurisdiction_code(jurisdiction)
    template_id = gate_jurisdiction_template_id(gate, code)
    if template_id:
        template = get_jurisdiction_template_registry().get(template_id)
        if template is not None and template.summary:
            return template.summary
    if gate in GATE_JURISDICTION_TEMPLATES and code == "AU":
        return _AU_NATIONAL_GATE_LINE
    return None


__all__ = [
    "AU_STATE_CODES",
    "ConsentFlowConfig",
    "DEFAULT_GATE_SEVERITY",
    "GATE_JURISDICTION_TEMPLATES",
    "gate_jurisdiction_template_id",
    "gate_jurisdiction_text",
    "DeIdentificationConfig",
    "RoundtableConfig",
    "JurisdictionBinding",
    "SubcategoryContextProfile",
    "gate_severity_for",
    "JurisdictionTemplate",
    "JurisdictionTemplateRegistry",
    "SubcategoryContextProfileRegistry",
    "get_subcategory_profile_registry",
    "get_jurisdiction_template_registry",
    "recommend_subcategory_profile",
    "get_subcategory_profile",
    "get_jurisdiction_template",
    "build_health_session_context",
]
