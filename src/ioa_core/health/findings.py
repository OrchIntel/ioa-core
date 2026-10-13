# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Source-aware findings for QiXMind, for synthetic evaluation only.

This module is not used by the live content gates
(:mod:`ioa_core.health.content_gates`). It answers, for each gate declared by a
care profile:

* where the signal appeared: the model input, the model output, or both;
* in what context: ``affirmed``, ``negated``, ``historical``, ``third_person``
  or ``uncertain``.

Design rules (QiXMind source-aware gates design, 14 October 2026):

* Detection is separate from action. Nothing here decides acknowledgement,
  escalation or follow-up; a versioned, clinically approved policy does.
* A finding is never downgraded because it appears only in the input, and an
  input finding is kept when the output omits it (``omitted_in_output``).
* One finding per gate: matches in the input and output are merged.
* Nothing is cleared automatically. ``negated`` is still a finding for a
  clinician to dispose of, and anything the rules cannot classify is
  ``uncertain``.
* No matched text, offsets or excerpts are kept, only gate names, sources,
  contexts and versions.

The context rules are deterministic phrase rules over the sentence that
contains each match. They are a starting point for clinician adjudication,
not a validated classifier.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from importlib import resources
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .content_gates import (
    GATE_DEFINITIONS,
    ContentGateError,
    _load_lexicon,
    assess_review_output,
    sha256_text,
)
from .registry import gate_severity_for, get_subcategory_profile

DETECTOR_NAME = "ioa_core.health.findings"
DETECTOR_VERSION = "0.2.0"
# 0.2.0 is frozen for independent held-out evaluation (14 October 2026). The 43
# synthetic cases used so far are development data. A change informed by a
# held-out run makes that set development data too and needs a fresh one.
FROZEN_FOR_HELDOUT = True
CONTEXT_RULES_VERSION = "2026.10.2-eval"
STATUS = "evaluation_only"

CONTEXTS: Tuple[str, ...] = (
    "affirmed",
    "uncertain",
    "historical",
    "third_person",
    "negated",
)
# When one gate is matched in several contexts, the finding takes the most
# concerning one: an affirmed match anywhere outweighs a negated one elsewhere.
_CONTEXT_PRIORITY = {name: index for index, name in enumerate(CONTEXTS)}

# Gates where a third party is the expected subject of the signal (for example
# a parent who hurts the child). Third-person phrasing is not discounted there.
_THIRD_PARTY_SUBJECT_GATES = frozenset(
    {"child_protection", "crisis_mandatory_reporting"}
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+|\n+")

_NEGATION_BEFORE = re.compile(
    r"\b(?:no|not|nil|never|none|denies|denied|denying|without|negative\s+for|"
    r"free\s+of|absence\s+of|absent|ruled\s+out|rules\s+out|no\s+evidence\s+of|"
    r"no\s+current|no\s+active|did\s+not\s+report|does\s+not\s+report|"
    r"didn'?t\s+report|doesn'?t\s+report|not\s+endorsing|does\s+not\s+endorse)\b"
    r"(?:\W+\w+){0,5}\W*$",
    re.IGNORECASE,
)
_NEGATION_AFTER = re.compile(
    r"^\W*(?:\w+\W+){0,3}?(?:denied|was\s+denied|were\s+denied|not\s+reported|"
    r"not\s+present|absent|ruled\s+out|nil)\b",
    re.IGNORECASE,
)
_HISTORICAL = re.compile(
    r"\b(?:history\s+of|hx\s+of|h/o|previous(?:ly)?|prior|past|in\s+the\s+past|"
    r"years?\s+ago|months?\s+ago|last\s+year|as\s+a\s+child|when\s+(?:she|he|they)\s+was|"
    r"when\s+(?:she|he|they)\s+were|former(?:ly)?|historical|in\s+(?:19|20)\d\d)\b",
    re.IGNORECASE,
)
_UNCERTAIN = re.compile(
    r"(?:\b(?:possible|possibly|query|queried|unclear|uncertain|unsure|may\s+have|"
    r"might|maybe|perhaps|suspected|suspect|cannot\s+rule\s+out|can'?t\s+rule\s+out|"
    r"not\s+sure|reportedly|ambiguous|equivocal|hinted|implied)\b|\?)",
    re.IGNORECASE,
)
_THIRD_PERSON = re.compile(
    r"\b(?:(?:his|her|their|my)\s+)?(?:mother|father|mum|mom|dad|brother|sister|"
    r"friend|friends|partner|cousin|uncle|aunt|grandmother|grandfather|peer|"
    r"classmate|teammate|neighbour|neighbor|family\s+member)(?:'s)?\b",
    re.IGNORECASE,
)
_FAMILY_HISTORY = re.compile(r"\bfamily\s+history\s+of\b", re.IGNORECASE)
# A third party who reports on the patient is a reporter, not the subject:
# "Mum reports that he has been cutting himself" is the patient's own risk.
_REPORTER = re.compile(
    r"\b(?:mother|father|mum|mom|dad|brother|sister|friend|partner|parent|parents|"
    r"carer|caregiver|teacher|school|family)\s+(?:reports?|reported|says?|said|"
    r"states?|stated|told|tells|describes?|described|is\s+worried|are\s+worried|"
    r"noticed|notices|found)\b",
    re.IGNORECASE,
)
# The third party must be the subject, not someone the patient spoke to.
_TO_THIRD_PARTY = re.compile(
    r"\b(?:to|with|told|texted|messaged|asked|showed|sent)\s+(?:a\s+|an\s+|the\s+|"
    r"his\s+|her\s+|their\s+|my\s+)?(?:mother|father|mum|mom|dad|brother|sister|"
    r"friend|friends|partner|cousin|uncle|aunt|peer|classmate|teammate)\b",
    re.IGNORECASE,
)


class FindingsError(ValueError):
    """Raised when the evaluation lexicons cannot be loaded."""


@dataclass(frozen=True)
class Finding:
    """One gate's signal across the input and output. Carries no matched text."""

    gate: str
    category: str
    sources: Tuple[str, ...]  # subset of ("input", "output"), sorted
    context: str  # the most concerning context observed
    contexts_observed: Tuple[str, ...]
    match_count: int
    omitted_in_output: bool  # in the input with concern, absent from the output
    default_severity: str
    lexicon_version: str
    # Every distinct (source, context, rule) seen for this gate, with a count.
    # The headline fields above are a summary for presentation; disposition and
    # audit work from these groups, so distinct concerns are never merged away.
    occurrences: Tuple["Occurrence", ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["sources"] = list(self.sources)
        data["contexts_observed"] = list(self.contexts_observed)
        data["occurrences"] = [item.to_dict() for item in self.occurrences]
        return data


@dataclass(frozen=True)
class Occurrence:
    """One distinct signal within a gate. Identifies the rule, never the text."""

    source: str  # "input" or "output"
    context: str
    entry: str
    count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FindingsReport:
    profile_id: str
    evaluated_at: str
    detector: str
    detector_version: str
    context_rules_version: str
    status: str
    gates: Tuple[str, ...]
    findings: Tuple[Finding, ...]
    input_sha256: Optional[str]
    output_sha256: Optional[str]
    review_output: Optional[Dict[str, Any]]
    lexicon_versions: Dict[str, str] = field(default_factory=dict)
    ruleset_sha256: Optional[str] = None

    def finding(self, gate: str) -> Optional[Finding]:
        for item in self.findings:
            if item.gate == gate:
                return item
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "evaluated_at": self.evaluated_at,
            "detector": self.detector,
            "detector_version": self.detector_version,
            "context_rules_version": self.context_rules_version,
            "status": self.status,
            "gates": list(self.gates),
            "findings": [item.to_dict() for item in self.findings],
            "input_sha256": self.input_sha256,
            "output_sha256": self.output_sha256,
            "review_output": self.review_output,
            "lexicon_versions": dict(self.lexicon_versions),
            "ruleset_sha256": self.ruleset_sha256,
        }


@dataclass(frozen=True)
class _EvalLexicon:
    gate: str
    category: str
    version: str
    # (entry id, compiled pattern). Entry ids name the rule that matched
    # ("<lexicon>@<version>:L<n>" for live entries, ":E<n>" for evaluation
    # additions), never the text it matched.
    entries: Tuple[Tuple[str, "re.Pattern[str]"], ...]


@lru_cache(maxsize=16)
def _load_eval_lexicon(gate: str) -> _EvalLexicon:
    """The live lexicon for ``gate`` plus its evaluation-only additions."""
    definition = GATE_DEFINITIONS.get(gate)
    if definition is None:
        raise FindingsError(f"Unknown gate: {gate}")
    try:
        base = _load_lexicon(definition.lexicon)
    except ContentGateError as exc:
        raise FindingsError(str(exc)) from exc
    entries: List[Tuple[str, "re.Pattern[str]"]] = [
        (f"{definition.lexicon}@{base.version}:L{index}", pattern)
        for index, pattern in enumerate(base.patterns)
    ]
    version = base.version
    added: List["re.Pattern[str]"] = []
    try:
        with (
            resources.files("ioa_core.health.lexicons.eval")
            .joinpath(f"{definition.lexicon}.json")
            .open("r", encoding="utf-8") as handle
        ):
            extra = json.load(handle)
    except (FileNotFoundError, ModuleNotFoundError):
        extra = None
    except (OSError, json.JSONDecodeError) as exc:
        raise FindingsError(f"Evaluation lexicon unreadable: {gate}") from exc
    if isinstance(extra, Mapping):
        for word in extra.get("words") or []:
            text = str(word or "").strip()
            if text:
                added.append(re.compile(r"\b" + re.escape(text) + r"\b", re.IGNORECASE))
        for pattern in extra.get("patterns") or []:
            text = str(pattern or "").strip()
            if text:
                added.append(re.compile(text, re.IGNORECASE))
        version = str(extra.get("version") or version)
        entries.extend(
            (f"{definition.lexicon}@{version}:E{index}", pattern)
            for index, pattern in enumerate(added)
        )
    return _EvalLexicon(
        gate=gate,
        category=base.category,
        version=version,
        entries=tuple(entries),
    )


def _sentences(text: str) -> Iterable[Tuple[int, str]]:
    start = 0
    for part in _SENTENCE_SPLIT.split(text):
        index = text.find(part, start)
        if index < 0:
            index = start
        yield index, part
        start = index + len(part)


def _classify(gate: str, sentence: str, start: int, end: int) -> str:
    """Context of one match, from the sentence that contains it."""
    before = sentence[:start]
    after = sentence[end:]
    if _UNCERTAIN.search(sentence):
        return "uncertain"
    negated = bool(_NEGATION_BEFORE.search(before) or _NEGATION_AFTER.search(after))
    historical = bool(_HISTORICAL.search(sentence))
    third_party_named = bool(_THIRD_PERSON.search(before)) and not (
        _REPORTER.search(sentence) or _TO_THIRD_PARTY.search(before)
    )
    third_person = gate not in _THIRD_PARTY_SUBJECT_GATES and bool(
        _FAMILY_HISTORY.search(sentence) or third_party_named
    )
    if negated and (historical or third_person):
        # "No history of ..." or "her friend denies ...": not a negation of the
        # patient's current state that the rules can trust.
        return "uncertain"
    if negated:
        return "negated"
    if third_person:
        return "third_person"
    if historical:
        return "historical"
    return "affirmed"


def _scan(
    gate: str, lexicon: _EvalLexicon, text: Optional[str]
) -> List[Tuple[str, str]]:
    """(context, entry id) for every match of ``gate`` in ``text``; no text."""
    if not text:
        return []
    hits: List[Tuple[str, str]] = []
    for _offset, sentence in _sentences(str(text)):
        seen: List[Tuple[int, int]] = []
        for entry_id, pattern in lexicon.entries:
            for match in pattern.finditer(sentence):
                span = match.span()
                if any(span[0] < other[1] and other[0] < span[1] for other in seen):
                    continue  # overlapping entries describe the same phrase
                seen.append(span)
                hits.append((_classify(gate, sentence, span[0], span[1]), entry_id))
    return hits


def ruleset_fingerprint() -> str:
    """Fingerprint of the findings detector: versions, context rules and every
    live and evaluation lexicon file, byte for byte."""
    digest = hashlib.sha256()
    digest.update(
        f"{DETECTOR_NAME}|{DETECTOR_VERSION}|{CONTEXT_RULES_VERSION}\n".encode()
    )
    for rule in (
        _SENTENCE_SPLIT,
        _NEGATION_BEFORE,
        _NEGATION_AFTER,
        _HISTORICAL,
        _UNCERTAIN,
        _THIRD_PERSON,
        _FAMILY_HISTORY,
        _REPORTER,
        _TO_THIRD_PARTY,
    ):
        digest.update(rule.pattern.encode("utf-8") + b"\n")
    digest.update(",".join(sorted(_THIRD_PARTY_SUBJECT_GATES)).encode() + b"\n")
    for gate in sorted(GATE_DEFINITIONS):
        lexicon = GATE_DEFINITIONS[gate].lexicon
        for package in ("ioa_core.health.lexicons", "ioa_core.health.lexicons.eval"):
            try:
                data = resources.files(package).joinpath(f"{lexicon}.json").read_bytes()
            except FileNotFoundError:
                data = b""
            digest.update(f"{package}/{lexicon}\n".encode() + data + b"\n")
    return "sha256:" + digest.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def detect_findings(
    *,
    profile_id: str,
    input_text: Optional[str],
    output_text: Optional[str],
    gates: Optional[Sequence[str]] = None,
) -> FindingsReport:
    """Source-aware findings for a care profile's declared gates.

    ``input_text`` should be the de-identified text sent to the model and
    ``output_text`` the model's output. Either may be empty, for example when
    generation was refused: input findings are still reported.
    """
    try:
        profile = get_subcategory_profile(profile_id)
    except Exception:  # noqa: BLE001 - explicit gates may name no known profile
        if gates is None:
            raise
        profile = None
    if gates is None:
        gates = tuple(getattr(profile, "content_gates", ()) or ())
    gate_list = tuple(str(gate) for gate in gates)
    findings: List[Finding] = []
    versions: Dict[str, str] = {}
    for gate in gate_list:
        lexicon = _load_eval_lexicon(gate)
        versions[gate] = lexicon.version
        input_hits = _scan(gate, lexicon, input_text)
        output_hits = _scan(gate, lexicon, output_text)
        input_contexts = [context for context, _entry in input_hits]
        output_contexts = [context for context, _entry in output_hits]
        grouped: Dict[Tuple[str, str, str], int] = {}
        for source, hits in (("input", input_hits), ("output", output_hits)):
            for context, entry in hits:
                key = (source, context, entry)
                grouped[key] = grouped.get(key, 0) + 1
        occurrences = tuple(
            Occurrence(source=source, context=context, entry=entry, count=count)
            for (source, context, entry), count in sorted(
                grouped.items(),
                key=lambda item: (
                    item[0][0],
                    _CONTEXT_PRIORITY[item[0][1]],
                    item[0][2],
                ),
            )
        )
        if not input_contexts and not output_contexts:
            continue
        observed = sorted(
            set(input_contexts) | set(output_contexts),
            key=lambda name: _CONTEXT_PRIORITY[name],
        )
        sources = tuple(
            name
            for name, found in (("input", input_contexts), ("output", output_contexts))
            if found
        )
        concerning_in_input = any(
            context in ("affirmed", "uncertain") for context in input_contexts
        )
        try:
            severity = gate_severity_for(profile, gate)
        except Exception:  # noqa: BLE001 - gate not declared on this profile
            severity = GATE_DEFINITIONS[gate].default_severity
        findings.append(
            Finding(
                gate=gate,
                category=lexicon.category,
                sources=sources,
                context=observed[0],
                contexts_observed=tuple(observed),
                match_count=len(input_contexts) + len(output_contexts),
                omitted_in_output=(
                    output_text is not None
                    and concerning_in_input
                    and not output_contexts
                ),
                default_severity=severity,
                lexicon_version=lexicon.version,
                occurrences=occurrences,
            )
        )
    review = (
        assess_review_output(output_text).to_dict() if output_text is not None else None
    )
    return FindingsReport(
        profile_id=str(profile_id),
        evaluated_at=_now(),
        detector=DETECTOR_NAME,
        detector_version=DETECTOR_VERSION,
        context_rules_version=CONTEXT_RULES_VERSION,
        status=STATUS,
        gates=gate_list,
        findings=tuple(findings),
        input_sha256=sha256_text(input_text) if input_text is not None else None,
        output_sha256=sha256_text(output_text) if output_text is not None else None,
        review_output=review,
        lexicon_versions=versions,
        ruleset_sha256=ruleset_fingerprint(),
    )


__all__ = [
    "CONTEXTS",
    "CONTEXT_RULES_VERSION",
    "DETECTOR_NAME",
    "DETECTOR_VERSION",
    "FROZEN_FOR_HELDOUT",
    "Finding",
    "FindingsError",
    "Occurrence",
    "FindingsReport",
    "detect_findings",
    "ruleset_fingerprint",
]
