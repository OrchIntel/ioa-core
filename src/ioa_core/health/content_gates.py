# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Content gates for health subcategory profiles.

A content gate is a declared safeguard on a subcategory profile (for example
``crisis_risk_to_self`` on a youth mental health profile). This module makes
those declarations enforceable: it screens model output (and optionally the
de-identified input) against packaged lexicons and returns an ordered record of
which gates fired, at what severity, and what the caller must do next.

Design rules:

* Fail closed. If a declared gate's lexicon cannot be loaded, construction
  raises ``ContentGateError`` and callers use ``fail_closed_report`` so the
  output is held rather than committed.
* Record no content. A ``GateResult`` carries the gate name, whether it fired,
  the severity and the lexicon's category. It never carries matched text,
  patterns or offsets, so results are safe to place in signed evidence.
* Lexicons are package data under ``ioa_core.health.lexicons`` so they load
  identically from a source checkout and an installed wheel.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from importlib import resources
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .registry import (
    SubcategoryContextProfile,
    gate_severity_for,
    get_subcategory_profile,
)

DETECTOR_NAME = "ioa_core.health.content_gates"
DETECTOR_VERSION = "1.0.0"

SEVERITY_ORDER: Tuple[str, ...] = ("info", "flag", "acknowledge", "escalate", "hold")
_OVERALL_ACTION_FOR_SEVERITY = {
    "info": "pass",
    "flag": "pass",
    "acknowledge": "acknowledge",
    "escalate": "escalate",
    "hold": "hold",
}
_ESCALATE_INDEX = SEVERITY_ORDER.index("escalate")


class ContentGateError(ValueError):
    """Raised when a gate cannot be evaluated safely."""


@dataclass(frozen=True)
class GateDefinition:
    name: str
    lexicon: str
    category: str
    default_severity: str
    applies_to: Tuple[str, ...]
    description: str


GATE_DEFINITIONS: Dict[str, GateDefinition] = {
    "crisis_risk_to_self": GateDefinition(
        name="crisis_risk_to_self",
        lexicon="crisis_risk_to_self",
        category="risk_to_self",
        default_severity="escalate",
        applies_to=("output",),
        description=(
            "Language consistent with suicidal ideation, self-harm or intent to "
            "end life appearing in model output."
        ),
    ),
    "risk_to_others": GateDefinition(
        name="risk_to_others",
        lexicon="risk_to_others",
        category="risk_to_others",
        default_severity="escalate",
        applies_to=("output",),
        description=(
            "Language consistent with intent or threat to harm another person "
            "appearing in model output."
        ),
    ),
    "child_protection": GateDefinition(
        name="child_protection",
        lexicon="child_protection",
        category="child_protection",
        default_severity="escalate",
        applies_to=("output",),
        description=(
            "Language consistent with abuse, neglect or an unsafe home environment "
            "appearing in model output. Reporting obligations depend on the "
            "jurisdiction (see the jurisdiction templates shown with the gate): the "
            "gate records the signal and obliges acknowledgement and follow-up; it "
            "does not report and does not determine whether a legal duty applies."
        ),
    ),
    "crisis_mandatory_reporting": GateDefinition(
        name="crisis_mandatory_reporting",
        lexicon="crisis_mandatory_reporting",
        category="mandatory_reporting_consideration",
        default_severity="escalate",
        applies_to=("output",),
        description=(
            "Language indicating imminent danger or a reporting consideration "
            "appearing in model output."
        ),
    ),
}


@dataclass(frozen=True)
class GateResult:
    """One gate's outcome. Deliberately carries no matched text or offsets."""

    order: int
    gate: str
    evaluated: bool
    fired: bool
    severity: str
    matched_category: Optional[str]
    lexicon_version: Optional[str]
    applies_to: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContentGateReport:
    profile_id: str
    evaluated_at: str
    detector: str
    detector_version: str
    detector_status: (
        str  # "ok", "partial" (declared gates without lexicons), "unavailable"
    )
    results: List[GateResult]
    overall_action: str  # "pass", "acknowledge", "escalate", "hold"
    output_sha256: Optional[str]
    input_sha256: Optional[str]
    unavailable_reason: Optional[str] = None
    lexicon_versions: Dict[str, str] = field(default_factory=dict)
    # Set when the caller asked whether a review was produced at all
    # (see assess_review_output); None when that check was not requested.
    review_output: Optional[Dict[str, str]] = None

    def fired_gates(self) -> List[GateResult]:
        return [result for result in self.results if result.fired]

    def requires_follow_up(self) -> bool:
        return (
            any(
                SEVERITY_ORDER.index(result.severity) >= _ESCALATE_INDEX
                for result in self.fired_gates()
            )
            or self.overall_action == "hold"
        )

    def is_held(self) -> bool:
        return self.overall_action == "hold"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["results"] = [result.to_dict() for result in self.results]
        return data


@dataclass(frozen=True)
class _CompiledLexicon:
    name: str
    version: str
    category: str
    patterns: Tuple["re.Pattern[str]", ...]


def sha256_text(text: Optional[str]) -> Optional[str]:
    """Return ``sha256:<hex>`` for text, matching the QiXHealth runtime format."""
    if text is None:
        return None
    return "sha256:" + hashlib.sha256(str(text).encode("utf-8")).hexdigest()


REVIEW_OUTPUT_DETECTOR_VERSION = "2026.10.1"

# Refusal wording near the start of an output. Matched only in the opening
# window and only when the output has almost no review structure, so a full
# review that says "I cannot diagnose" is not treated as a refusal.
_REFUSAL_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bI(?:'|\u2019)?m\s+(?:sorry|unable|not\s+able)\b",
        r"\bI\s+am\s+(?:sorry|unable|not\s+able)\b",
        r"\bI\s+(?:can(?:'|\u2019)?t|cannot|won(?:'|\u2019)?t|will\s+not)\s+"
        r"(?:help|assist|provide|create|generate|complete|comply|produce|write|support|do\s+that)\b",
        r"\bI(?:'|\u2019)?m\s+not\s+(?:permitted|allowed)\s+to\b",
        r"\bas\s+an\s+ai\b",
    )
)
_REFUSAL_WINDOW = 400
_MIN_REVIEW_CHARS = 20
_SECTION_LINE = re.compile(
    r"^\s*(?:#{1,4}\s+\S|[A-Z][A-Za-z0-9 ,/&()'\u2019-]{2,80}:)", re.MULTILINE
)


@dataclass(frozen=True)
class ReviewOutputAssessment:
    """Whether the model produced a review at all. Carries no output text."""

    status: str  # "produced", "empty", "refused"
    reason_code: Optional[str]
    detector_version: str = REVIEW_OUTPUT_DETECTOR_VERSION

    @property
    def produced(self) -> bool:
        return self.status == "produced"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def assess_review_output(output_text: Optional[str]) -> ReviewOutputAssessment:
    """Classify an output as a produced review, empty, or a refusal.

    A refused or empty output must never be treated as a review that passed
    its checks: there is nothing for the gates to have found and nothing for a
    clinician to sign off.
    """
    text = str(output_text or "").strip()
    if len(re.sub(r"\s+", "", text)) < _MIN_REVIEW_CHARS:
        return ReviewOutputAssessment(status="empty", reason_code="empty_output")
    opening = text[:_REFUSAL_WINDOW]
    if any(pattern.search(opening) for pattern in _REFUSAL_PATTERNS):
        if len(_SECTION_LINE.findall(text)) < 2:
            return ReviewOutputAssessment(
                status="refused", reason_code="refusal_language"
            )
    return ReviewOutputAssessment(status="produced", reason_code=None)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_severity(value: Any, fallback: str) -> str:
    """Return a known severity; an unrecognised configured value is a defect."""
    text = str(value or "").strip().lower()
    if text in SEVERITY_ORDER:
        return text
    if text:
        raise ContentGateError(f"Unknown gate severity: {text!r}")
    if fallback in SEVERITY_ORDER:
        return fallback
    raise ContentGateError(f"Unknown gate severity fallback: {fallback!r}")


@lru_cache(maxsize=32)
def _load_lexicon(name: str) -> _CompiledLexicon:
    try:
        with (
            resources.files("ioa_core.health.lexicons")
            .joinpath(f"{name}.json")
            .open("r", encoding="utf-8") as handle
        ):
            payload = json.load(handle)
    except (FileNotFoundError, ModuleNotFoundError) as exc:
        raise ContentGateError(f"Lexicon not packaged: {name}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ContentGateError(f"Lexicon unreadable: {name}") from exc
    if not isinstance(payload, Mapping):
        raise ContentGateError(f"Lexicon malformed: {name}")
    version = str(payload.get("version") or "").strip()
    category = str(payload.get("category") or "").strip()
    words = payload.get("words") or []
    patterns = payload.get("patterns") or []
    if not version or not category:
        raise ContentGateError(f"Lexicon missing version or category: {name}")
    if not isinstance(words, list) or not isinstance(patterns, list):
        raise ContentGateError(f"Lexicon words/patterns must be lists: {name}")
    if not words and not patterns:
        raise ContentGateError(f"Lexicon is empty: {name}")
    compiled: List["re.Pattern[str]"] = []
    for word in words:
        text = str(word or "").strip()
        if not text:
            raise ContentGateError(f"Lexicon has an empty word entry: {name}")
        compiled.append(re.compile(r"\b" + re.escape(text) + r"\b", re.IGNORECASE))
    for pattern in patterns:
        text = str(pattern or "").strip()
        if not text:
            raise ContentGateError(f"Lexicon has an empty pattern entry: {name}")
        try:
            compiled.append(re.compile(text, re.IGNORECASE))
        except re.error as exc:
            raise ContentGateError(f"Lexicon pattern invalid in {name}") from exc
    return _CompiledLexicon(
        name=name, version=version, category=category, patterns=tuple(compiled)
    )


class ContentGateEvaluator:
    """Evaluate a profile's declared gates against model text.

    Construction compiles every lexicon eagerly so that a missing or malformed
    lexicon is discovered before any output is screened.
    """

    def __init__(
        self,
        gates: Sequence[str],
        severities: Mapping[str, str],
        *,
        profile_id: str = "",
    ):
        self.profile_id = str(profile_id or "").strip()
        self._gates: List[str] = [
            str(gate).strip() for gate in gates if str(gate).strip()
        ]
        self._severities: Dict[str, str] = {}
        self._lexicons: Dict[str, _CompiledLexicon] = {}
        for gate in self._gates:
            definition = GATE_DEFINITIONS.get(gate)
            fallback = definition.default_severity if definition else "acknowledge"
            self._severities[gate] = _normalize_severity(severities.get(gate), fallback)
            if definition is not None:
                self._lexicons[gate] = _load_lexicon(definition.lexicon)

    @classmethod
    def for_profile(cls, profile_id: str) -> "ContentGateEvaluator":
        profile = get_subcategory_profile(profile_id)
        return cls.from_profile(profile)

    @classmethod
    def from_profile(cls, profile: SubcategoryContextProfile) -> "ContentGateEvaluator":
        severities = {
            gate: gate_severity_for(profile, gate) for gate in profile.content_gates
        }
        return cls(profile.content_gates, severities, profile_id=profile.id)

    @property
    def gates(self) -> List[str]:
        return list(self._gates)

    @property
    def implemented_gates(self) -> List[str]:
        return [gate for gate in self._gates if gate in self._lexicons]

    @property
    def unimplemented_gates(self) -> List[str]:
        return [gate for gate in self._gates if gate not in self._lexicons]

    def lexicon_versions(self) -> Dict[str, str]:
        return {gate: lexicon.version for gate, lexicon in self._lexicons.items()}

    def evaluate(
        self,
        *,
        output_text: str,
        input_text: Optional[str] = None,
        profile_id: Optional[str] = None,
        require_review_output: bool = False,
    ) -> ContentGateReport:
        """Evaluate the declared gates.

        With ``require_review_output`` the output is also checked for whether
        a review was produced at all; an empty or refused output is held
        (``overall_action == "hold"``) with the reason in ``review_output``,
        while every gate result is still recorded.
        """
        if output_text is None:
            raise ContentGateError("output_text is required")
        output = str(output_text)
        results: List[GateResult] = []
        max_severity_index = -1
        for order, gate in enumerate(self._gates):
            severity = self._severities[gate]
            definition = GATE_DEFINITIONS.get(gate)
            lexicon = self._lexicons.get(gate)
            if definition is None or lexicon is None:
                results.append(
                    GateResult(
                        order=order,
                        gate=gate,
                        evaluated=False,
                        fired=False,
                        severity=severity,
                        matched_category=None,
                        lexicon_version=None,
                        applies_to="none",
                    )
                )
                continue
            scopes = ["output"]
            fired = _matches(lexicon, output)
            if "input" in definition.applies_to and input_text is not None:
                scopes.append("input")
                fired = fired or _matches(lexicon, str(input_text))
            if fired:
                max_severity_index = max(
                    max_severity_index, SEVERITY_ORDER.index(severity)
                )
            results.append(
                GateResult(
                    order=order,
                    gate=gate,
                    evaluated=True,
                    fired=fired,
                    severity=severity,
                    matched_category=lexicon.category if fired else None,
                    lexicon_version=lexicon.version,
                    applies_to=",".join(scopes),
                )
            )
        if max_severity_index < 0:
            overall_action = "pass"
        else:
            overall_action = _OVERALL_ACTION_FOR_SEVERITY[
                SEVERITY_ORDER[max_severity_index]
            ]
        status = "ok" if all(result.evaluated for result in results) else "partial"
        review_output = None
        if require_review_output:
            assessment = assess_review_output(output)
            review_output = assessment.to_dict()
            if not assessment.produced:
                overall_action = "hold"
        return ContentGateReport(
            profile_id=str(profile_id or self.profile_id),
            evaluated_at=_now(),
            detector=DETECTOR_NAME,
            detector_version=DETECTOR_VERSION,
            detector_status=status,
            results=results,
            overall_action=overall_action,
            output_sha256=sha256_text(output),
            input_sha256=sha256_text(input_text) if input_text is not None else None,
            lexicon_versions=self.lexicon_versions(),
            review_output=review_output,
        )


def _matches(lexicon: _CompiledLexicon, text: str) -> bool:
    return any(pattern.search(text) for pattern in lexicon.patterns)


def ruleset_fingerprint() -> str:
    """Fingerprint of the live gate rules: detector versions, the refusal rules
    and every packaged live lexicon, byte for byte."""
    digest = hashlib.sha256()
    digest.update(
        f"{DETECTOR_NAME}|{DETECTOR_VERSION}|{REVIEW_OUTPUT_DETECTOR_VERSION}\n".encode()
    )
    for pattern in _REFUSAL_PATTERNS:
        digest.update(pattern.pattern.encode("utf-8") + b"\n")
    for gate in sorted(GATE_DEFINITIONS):
        lexicon = GATE_DEFINITIONS[gate].lexicon
        data = (
            resources.files("ioa_core.health.lexicons")
            .joinpath(f"{lexicon}.json")
            .read_bytes()
        )
        digest.update(f"{lexicon}\n".encode() + data + b"\n")
    return "sha256:" + digest.hexdigest()


def fail_closed_report(
    profile_id: str,
    reason_code: str,
    *,
    output_text: Optional[str] = None,
    input_text: Optional[str] = None,
) -> ContentGateReport:
    """Return the report a caller records when gates could not be evaluated.

    ``reason_code`` must be a short machine code (for example
    ``lexicon_unavailable`` or ``evaluator_error``), never an exception message,
    so that nothing from the clinical text can leak into evidence or logs.
    """
    code = re.sub(r"[^a-z0-9_]+", "_", str(reason_code or "unknown").strip().lower())[
        :64
    ]
    return ContentGateReport(
        profile_id=str(profile_id or "").strip(),
        evaluated_at=_now(),
        detector=DETECTOR_NAME,
        detector_version=DETECTOR_VERSION,
        detector_status="unavailable",
        results=[],
        overall_action="hold",
        output_sha256=sha256_text(output_text) if output_text is not None else None,
        input_sha256=sha256_text(input_text) if input_text is not None else None,
        unavailable_reason=code or "unknown",
    )


__all__ = [
    "DETECTOR_NAME",
    "DETECTOR_VERSION",
    "REVIEW_OUTPUT_DETECTOR_VERSION",
    "ReviewOutputAssessment",
    "assess_review_output",
    "GATE_DEFINITIONS",
    "SEVERITY_ORDER",
    "ContentGateError",
    "ContentGateEvaluator",
    "ContentGateReport",
    "GateDefinition",
    "GateResult",
    "fail_closed_report",
    "ruleset_fingerprint",
    "sha256_text",
]
