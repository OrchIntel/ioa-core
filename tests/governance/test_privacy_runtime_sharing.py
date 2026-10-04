# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""Prove overlapping diagnostics/checks allocate one expensive NLP engine."""
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import time

from ioa.governance.detectors import privacy_presidio as pp


def test_concurrent_detectors_share_one_analyzer(monkeypatch):
    calls = []
    lock = Lock()

    class Analyzer:
        def __init__(self):
            with lock:
                calls.append(1)
            time.sleep(0.02)

        def analyze(self, **kwargs):
            return []

    monkeypatch.setattr(pp, "AnalyzerEngine", Analyzer)
    with ThreadPoolExecutor(max_workers=8) as executor:
        engines = list(executor.map(lambda _: pp.get_shared_analyzer(), range(16)))
    assert len(calls) == 1
    assert all(engine is engines[0] for engine in engines)
    detectors = [pp.PrivacyDetector({"action": "none"}) for _ in range(4)]
    assert all(detector.available for detector in detectors)
    assert all(detector._analyzer is engines[0] for detector in detectors)
    assert len(calls) == 1


def test_failed_initialization_is_not_cached(monkeypatch):
    calls = []

    class Analyzer:
        def __init__(self):
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError("Synthetic initialization failure")

        def analyze(self, **kwargs):
            return []

    monkeypatch.setattr(pp, "AnalyzerEngine", Analyzer)
    first = pp.PrivacyDetector({"action": "none", "mode": "strict"})
    result = first.detect_and_anonymize("Synthetic input")
    assert result.status == "unavailable" and first.should_block(result)
    second = pp.PrivacyDetector({"action": "none"})
    assert second.available and len(calls) == 2
