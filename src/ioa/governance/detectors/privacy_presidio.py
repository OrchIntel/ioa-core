# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""
IOA Module: src/ioa/governance/detectors/privacy_presidio.py
Version: v2.6.2
Last-Updated: 2026-10-05
Summary: Privacy detector using Presidio for PII detection and anonymization (Laws 1, 3)

A detector that cannot run must say so. Earlier versions replaced a missing
Presidio import with empty placeholder classes, accepted them as
"initialized", reported ``presidio_available: True`` and then returned a
"no PII" result with an error attached. Callers that only read ``has_pii``
certified text as clean. This version:

- imports the analyzer and the anonymizer separately and records why each
  is unavailable;
- never treats a placeholder as an engine; ``_ensure_initialized`` verifies
  that the analyzer exposes ``analyze`` and the anonymizer ``anonymize``;
- requires the analyzer to check text at all, and treats a missing
  anonymizer as "detected but could not mask" (``action_taken ==
  "mask_unavailable"``), never as a clean result;
- labels every result with a ``status`` (``checked``, ``unavailable``,
  ``error``, ``disabled``) that evidence and status reporting carry through;
- fails closed in strict mode when the detector is unavailable or errors.
"""

import logging
from functools import lru_cache
from threading import RLock
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

VERSION = "v2.6.2"

# Module-level engine symbols so tests can patch them. They are None, never a
# stand-in class, when the dependency is missing.
ANALYZER_IMPORT_ERROR: Optional[str] = None
ANONYMIZER_IMPORT_ERROR: Optional[str] = None
try:
    from presidio_analyzer import AnalyzerEngine  # type: ignore
except Exception as _exc:  # pragma: no cover - depends on the environment
    AnalyzerEngine = None  # type: ignore
    ANALYZER_IMPORT_ERROR = f"{type(_exc).__name__}: {_exc}"
try:
    from presidio_anonymizer import AnonymizerEngine  # type: ignore
except Exception as _exc:  # pragma: no cover - depends on the environment
    AnonymizerEngine = None  # type: ignore
    ANONYMIZER_IMPORT_ERROR = f"{type(_exc).__name__}: {_exc}"


STATUS_CHECKED = "checked"
STATUS_UNAVAILABLE = "unavailable"
STATUS_ERROR = "error"
STATUS_DISABLED = "disabled"

_analyzer_lock = RLock()


@lru_cache(maxsize=1)
def _analyzer_for_factory(factory):
    """Load one NLP model per process, keyed by the actual engine factory.

    Call only while holding _analyzer_lock: lru_cache alone can initialize
    twice when cold calls overlap. Exceptions are never cached as success.
    Factory identity also isolates alternate engines used by callers/tests.
    """
    analyzer = factory()
    if not callable(getattr(analyzer, "analyze", None)):
        raise RuntimeError("presidio AnalyzerEngine has no usable analyze()")
    return analyzer


def get_shared_analyzer():
    """Canonical analyzer shared by privacy checks and clinical extraction.

    Registry and NLP configuration are read-only after initialization. Callers
    must not mutate shared recognizers. Different requested detection entities
    and score thresholds remain per-call arguments, not shared mutable state.
    """
    if AnalyzerEngine is None:
        raise RuntimeError(f"presidio_analyzer not importable ({ANALYZER_IMPORT_ERROR})")
    with _analyzer_lock:
        return _analyzer_for_factory(AnalyzerEngine)


@dataclass
class PrivacyResult:
    """Result of privacy detection and anonymization.

    ``has_pii`` is only meaningful when ``status == "checked"``. For any other
    status the text was not analyzed and must not be treated as clean.
    """
    has_pii: bool
    entities_found: List[Dict[str, Any]]
    anonymized_text: Optional[str] = None
    action_taken: Optional[str] = None
    confidence_scores: Dict[str, float] = None
    processing_time_ms: float = 0.0
    error: Optional[str] = None
    status: str = STATUS_CHECKED
    unavailable_reason: Optional[str] = None
    masking_error: Optional[str] = None

    @property
    def checked(self) -> bool:
        return self.status == STATUS_CHECKED


class PrivacyDetector:
    """
    Privacy detector using Presidio for PII detection and anonymization.

    Implements Laws 1 (Compliance Supremacy) and 3 (Auditability) for privacy protection.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize privacy detector with configuration.

        Args:
            config: Privacy configuration from ethics_pack_v0.json
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.mode = config.get("mode", "monitor")
        self.pii_entities = config.get("pii_entities", ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN"])
        self.action = config.get("action", "mask")

        self._analyzer = None
        self._anonymizer = None
        self._initialized = False
        self.unavailable_reason: Optional[str] = None
        self.anonymizer_unavailable_reason: Optional[str] = None

        logger.info(f"PrivacyDetector initialized: enabled={self.enabled}, mode={self.mode}")

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    @property
    def requires_anonymizer(self) -> bool:
        """Masking needs the anonymizer; detection alone does not."""
        return self.action == "mask"

    @staticmethod
    def _usable(engine: Any, method: str) -> bool:
        return engine is not None and callable(getattr(engine, method, None))

    def _ensure_initialized(self) -> bool:
        """Create the Presidio engines and verify they can do the work.

        The analyzer is required: without a usable ``analyze`` nothing can be
        checked and this returns False with ``unavailable_reason`` set. The
        anonymizer is attempted when masking is configured; if it is missing
        or unusable, detection still runs and results carry
        ``masking_error`` so callers know PII was found but not masked. A
        placeholder is never accepted as an engine.
        """
        if self._initialized:
            return True

        if AnalyzerEngine is None:
            self.unavailable_reason = f"presidio_analyzer not importable ({ANALYZER_IMPORT_ERROR})"
            logger.error("Presidio analyzer unavailable: %s", self.unavailable_reason)
            return False
        try:
            analyzer = get_shared_analyzer()
        except Exception as e:
            self.unavailable_reason = f"Presidio initialization failed: {type(e).__name__}: {e}"
            logger.error("Failed to initialize Presidio: %s", e)
            return False
        if not self._usable(analyzer, "analyze"):
            self.unavailable_reason = "presidio AnalyzerEngine has no usable analyze()"
            logger.error("Presidio analyzer unusable: %s", self.unavailable_reason)
            return False

        anonymizer = None
        self.anonymizer_unavailable_reason = None
        if self.requires_anonymizer:
            if AnonymizerEngine is None:
                self.anonymizer_unavailable_reason = f"presidio_anonymizer not importable ({ANONYMIZER_IMPORT_ERROR})"
            else:
                try:
                    anonymizer = AnonymizerEngine()  # type: ignore[misc]
                except Exception as e:
                    self.anonymizer_unavailable_reason = f"Presidio anonymizer initialization failed: {type(e).__name__}: {e}"
                if anonymizer is not None and not self._usable(anonymizer, "anonymize"):
                    anonymizer = None
                    self.anonymizer_unavailable_reason = "presidio AnonymizerEngine has no usable anonymize()"
            if self.anonymizer_unavailable_reason:
                logger.error("Presidio anonymizer unavailable, PII will be detected but not masked: %s", self.anonymizer_unavailable_reason)

        self._analyzer = analyzer
        self._anonymizer = anonymizer
        self._initialized = True
        self.unavailable_reason = None
        logger.info("Presidio components initialized successfully (masking %s)", "enabled" if anonymizer or not self.requires_anonymizer else "unavailable")
        return True

    @property
    def available(self) -> bool:
        """True only when the analyzer exists and has been verified usable."""
        return self._initialized or self._ensure_initialized()

    @property
    def masking_available(self) -> bool:
        """True when masking is configured and the anonymizer is usable, or masking is off."""
        if not self.available:
            return False
        if not self.requires_anonymizer:
            return True
        return self._anonymizer is not None

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def detect_and_anonymize(self, text: str) -> PrivacyResult:
        """
        Detect PII in text and optionally anonymize it.

        Args:
            text: Input text to analyze

        Returns:
            PrivacyResult. Check ``status`` before trusting ``has_pii``.
        """
        start_time = datetime.now()

        if not self.enabled:
            return PrivacyResult(
                has_pii=False,
                entities_found=[],
                anonymized_text=text,
                action_taken="disabled",
                status=STATUS_DISABLED,
                processing_time_ms=0.0,
            )

        if not self._ensure_initialized():
            return PrivacyResult(
                has_pii=False,
                entities_found=[],
                anonymized_text=text,
                action_taken="error",
                error="Presidio not available",
                status=STATUS_UNAVAILABLE,
                unavailable_reason=self.unavailable_reason,
                processing_time_ms=0.0,
            )

        try:
            results = self._analyzer.analyze(
                text=text,
                entities=self.pii_entities,
                language='en'
            )

            entities_found = []
            for result in results:
                raw_span = text[result.start:result.end]
                span = raw_span.strip()
                # Heuristic: if span contains email with leading filler like "at ",
                # pick the token containing '@' to match expected entity text.
                if "@" in span and span != "" and " " in span:
                    for token in span.split():
                        if "@" in token:
                            span = token
                            break
                entities_found.append({
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": span,
                })

            has_pii = len(entities_found) > 0

            anonymized_text = text
            action_taken = "none"
            masking_error = None
            if has_pii and self.action == "mask":
                if self._anonymizer is None:
                    # Detected, could not mask: say so rather than returning the raw text as "masked".
                    action_taken = "mask_unavailable"
                    masking_error = self.anonymizer_unavailable_reason or "anonymizer unavailable"
                else:
                    anonymized_result = self._anonymizer.anonymize(
                        text=text,
                        analyzer_results=results
                    )
                    anonymized_text = anonymized_result.text
                    action_taken = "masked"

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            confidence_scores: Dict[str, List[float]] = {}
            for entity in entities_found:
                confidence_scores.setdefault(entity["entity_type"], []).append(entity["score"])
            avg_confidence = {k: sum(v) / len(v) for k, v in confidence_scores.items()}

            return PrivacyResult(
                has_pii=has_pii,
                entities_found=entities_found,
                anonymized_text=anonymized_text,
                action_taken=action_taken,
                confidence_scores=avg_confidence,
                processing_time_ms=processing_time,
                status=STATUS_CHECKED,
                masking_error=masking_error,
            )

        except Exception as e:
            logger.error(f"Privacy detection failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return PrivacyResult(
                has_pii=False,
                entities_found=[],
                anonymized_text=text,
                action_taken="error",
                error=str(e),
                status=STATUS_ERROR,
                processing_time_ms=processing_time,
            )

    # ------------------------------------------------------------------
    # Evidence and decisions
    # ------------------------------------------------------------------

    def get_evidence(self, result: PrivacyResult) -> Dict[str, Any]:
        """
        Generate evidence for audit trail.

        ``checked`` is False whenever the text was not actually analyzed, so a
        reader cannot mistake an unavailable detector for a clean result.
        """
        return {
            "privacy": {
                "enabled": self.enabled,
                "mode": self.mode,
                "status": result.status,
                "checked": result.checked,
                "has_pii": result.has_pii if result.checked else None,
                "entities_detected": len(result.entities_found),
                "entity_types": sorted({str(e.get("entity_type")) for e in result.entities_found}),
                "action_taken": result.action_taken,
                "masked": result.action_taken == "masked",
                "masking_error": result.masking_error,
                "confidence_scores": result.confidence_scores or {},
                "processing_time_ms": result.processing_time_ms,
                "error": result.error,
                "unavailable_reason": result.unavailable_reason,
                "detector_version": VERSION,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    def should_block(self, result: PrivacyResult) -> bool:
        """
        Determine if action should be blocked based on privacy result.

        Monitor mode never blocks; it records. Strict mode blocks on detected
        PII and also when the detector could not check the text (unavailable
        or error), because an unchecked text cannot be certified clean.
        """
        if not self.enabled or self.mode == "monitor":
            return False

        if self.mode == "strict":
            if not result.checked:
                return True
            return bool(result.has_pii)

        return False

    def get_status(self) -> Dict[str, Any]:
        """Get detector status for diagnostics. Reflects the real engines."""
        available = self.available
        return {
            "name": "PrivacyDetector",
            "enabled": self.enabled,
            "mode": self.mode,
            "pii_entities": self.pii_entities,
            "action": self.action,
            "presidio_available": available,
            "analyzer_available": available,
            "anonymizer_available": self._anonymizer is not None,
            "anonymizer_required": self.requires_anonymizer,
            "masking_available": self.masking_available,
            "unavailable_reason": None if available else self.unavailable_reason,
            "anonymizer_unavailable_reason": self.anonymizer_unavailable_reason if self.requires_anonymizer else None,
            "version": VERSION,
        }
