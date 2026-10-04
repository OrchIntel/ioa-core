# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""
A privacy detector that cannot run must never look like a clean check (OP-40).

Production incident 2026-10-04: presidio_anonymizer was absent from the
QiXChat image. The detector replaced both engines with placeholders,
reported presidio_available=True, raised on every call and returned
has_pii=False, which downstream evidence recorded as "no PII".
"""

from unittest.mock import Mock, patch

import pytest

from src.ioa.governance.detectors import privacy_presidio as pp
from src.ioa.governance.detectors.privacy_presidio import PrivacyDetector, PrivacyResult

MODULE = "src.ioa.governance.detectors.privacy_presidio"
CONFIG = {"enabled": True, "mode": "monitor", "pii_entities": ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"], "action": "mask"}


def _analyzer_returning(entities):
    engine = Mock()
    engine.analyze.return_value = entities
    return Mock(return_value=engine)


def _anonymizer_returning(text):
    engine = Mock()
    engine.anonymize.return_value = Mock(text=text)
    return Mock(return_value=engine)


def _hit(entity_type, start, end, score=0.9):
    return Mock(entity_type=entity_type, start=start, end=end, score=score)


# --- Missing or broken engines never count as initialized -----------------


def test_missing_anonymizer_detects_but_reports_masking_unavailable():
    """The production incident: analyzer present, anonymizer absent, action=mask."""
    hits = [_hit("EMAIL_ADDRESS", 8, 24)]
    with patch(f"{MODULE}.AnonymizerEngine", None), patch(f"{MODULE}.ANONYMIZER_IMPORT_ERROR", "ModuleNotFoundError"), patch(
        f"{MODULE}.AnalyzerEngine", _analyzer_returning(hits)
    ):
        detector = PrivacyDetector(CONFIG)
        result = detector.detect_and_anonymize("Jane at jane@example.com")
        status = detector.get_status()
        evidence = detector.get_evidence(result)["privacy"]
    assert result.status == "checked" and result.has_pii is True
    assert result.action_taken == "mask_unavailable"
    assert "presidio_anonymizer" in result.masking_error
    assert result.anonymized_text == "Jane at jane@example.com"  # raw text, never claimed masked
    assert evidence["masked"] is False and "presidio_anonymizer" in evidence["masking_error"]
    assert status["presidio_available"] is True
    assert status["anonymizer_available"] is False and status["masking_available"] is False
    assert "presidio_anonymizer" in status["anonymizer_unavailable_reason"]
    # Strict mode still blocks: PII was found and could not be masked.
    assert PrivacyDetector({**CONFIG, "mode": "strict"}).should_block(result) is True


def test_missing_anonymizer_still_detects_when_not_masking():
    with patch(f"{MODULE}.AnonymizerEngine", None), patch(f"{MODULE}.AnalyzerEngine", _analyzer_returning([_hit("EMAIL_ADDRESS", 8, 24)])):
        detector = PrivacyDetector({**CONFIG, "action": "none"})
        result = detector.detect_and_anonymize("Jane at jane@example.com")
    assert result.status == "checked" and result.has_pii is True
    assert result.action_taken == "none"


def test_missing_analyzer_is_unavailable():
    with patch(f"{MODULE}.AnalyzerEngine", None), patch(f"{MODULE}.ANALYZER_IMPORT_ERROR", "ModuleNotFoundError"):
        detector = PrivacyDetector(CONFIG)
        result = detector.detect_and_anonymize("text")
        status = detector.get_status()
    assert result.status == "unavailable"
    assert "presidio_analyzer" in result.unavailable_reason
    assert status["presidio_available"] is False


def test_initialization_failure_is_unavailable():
    with patch(f"{MODULE}.AnalyzerEngine", Mock(side_effect=RuntimeError("spacy model missing"))):
        detector = PrivacyDetector(CONFIG)
        result = detector.detect_and_anonymize("text")
    assert result.status == "unavailable"
    assert "spacy model missing" in result.unavailable_reason
    assert detector._initialized is False


def test_placeholder_engine_without_analyze_is_rejected():
    class Placeholder:  # what the old shim produced
        pass

    with patch(f"{MODULE}.AnalyzerEngine", Placeholder), patch(f"{MODULE}.AnonymizerEngine", Placeholder):
        detector = PrivacyDetector(CONFIG)
        result = detector.detect_and_anonymize("text")
        status = detector.get_status()
    assert result.status == "unavailable"
    assert "analyze" in result.unavailable_reason
    assert status["presidio_available"] is False


def test_runtime_detector_error_is_reported_as_error():
    engine = Mock()
    engine.analyze.side_effect = ValueError("tokenizer exploded")
    with patch(f"{MODULE}.AnalyzerEngine", Mock(return_value=engine)), patch(f"{MODULE}.AnonymizerEngine", _anonymizer_returning("x")):
        detector = PrivacyDetector(CONFIG)
        result = detector.detect_and_anonymize("text")
    assert result.status == "error" and result.checked is False
    assert "tokenizer exploded" in result.error


# --- Evidence and blocking --------------------------------------------------


@pytest.mark.parametrize("status", ["unavailable", "error"])
def test_evidence_never_reads_as_clean_when_not_checked(status):
    detector = PrivacyDetector(CONFIG)
    result = PrivacyResult(has_pii=False, entities_found=[], status=status, error="boom", unavailable_reason="why")
    privacy = detector.get_evidence(result)["privacy"]
    assert privacy["checked"] is False
    assert privacy["has_pii"] is None
    assert privacy["status"] == status
    assert privacy["error"] == "boom"


def test_evidence_for_a_real_check():
    detector = PrivacyDetector(CONFIG)
    result = PrivacyResult(has_pii=True, entities_found=[{"entity_type": "EMAIL_ADDRESS", "text": "a@b.c"}], status="checked")
    privacy = detector.get_evidence(result)["privacy"]
    assert privacy["checked"] is True and privacy["has_pii"] is True
    assert privacy["detector_version"] == pp.VERSION


@pytest.mark.parametrize("status", ["unavailable", "error"])
def test_strict_mode_fails_closed_when_detector_cannot_check(status):
    detector = PrivacyDetector({**CONFIG, "mode": "strict"})
    assert detector.should_block(PrivacyResult(has_pii=False, entities_found=[], status=status, error="boom")) is True


def test_strict_mode_blocks_pii_and_allows_clean():
    detector = PrivacyDetector({**CONFIG, "mode": "strict"})
    assert detector.should_block(PrivacyResult(has_pii=True, entities_found=[{}], status="checked")) is True
    assert detector.should_block(PrivacyResult(has_pii=False, entities_found=[], status="checked")) is False


@pytest.mark.parametrize("status", ["unavailable", "error", "checked"])
def test_monitor_mode_never_blocks_but_records(status):
    detector = PrivacyDetector(CONFIG)
    result = PrivacyResult(has_pii=True, entities_found=[{"entity_type": "PERSON"}], status=status, error=None if status == "checked" else "boom")
    assert detector.should_block(result) is False
    assert detector.get_evidence(result)["privacy"]["status"] == status


# --- Real detection of synthetic values ------------------------------------


def test_detects_synthetic_name_email_and_phone_with_mocked_engines():
    text = "Contact Jane Doe at jane.doe@example.com or +64 21 555 0101."
    hits = [_hit("PERSON", 8, 16), _hit("EMAIL_ADDRESS", 20, 40), _hit("PHONE_NUMBER", 44, 59)]
    with patch(f"{MODULE}.AnalyzerEngine", _analyzer_returning(hits)), patch(
        f"{MODULE}.AnonymizerEngine", _anonymizer_returning("Contact <PERSON> at <EMAIL_ADDRESS> or <PHONE_NUMBER>.")
    ):
        detector = PrivacyDetector(CONFIG)
        result = detector.detect_and_anonymize(text)
    assert result.status == "checked" and result.has_pii is True
    assert {e["entity_type"] for e in result.entities_found} == {"PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"}
    assert result.action_taken == "masked"
    assert "jane.doe@example.com" not in result.anonymized_text


@pytest.mark.skipif(pp.AnalyzerEngine is None or pp.AnonymizerEngine is None, reason="presidio not installed")
def test_detects_synthetic_values_with_real_presidio():
    detector = PrivacyDetector(CONFIG)
    result = detector.detect_and_anonymize("Contact Jane Doe at jane.doe@example.com or call 415-555-0101.")
    assert result.status == "checked", result.unavailable_reason or result.error
    assert result.has_pii is True
    assert "EMAIL_ADDRESS" in {e["entity_type"] for e in result.entities_found}
    assert "jane.doe@example.com" not in result.anonymized_text
    assert detector.get_status()["presidio_available"] is True
