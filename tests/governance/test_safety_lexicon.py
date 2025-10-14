"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import pytest
import json
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from src.ioa.governance.detectors.safety_lexicon import SafetyDetector, SafetyResult


class TestSafetyDetector:
    """Test cases for SafetyDetector."""
    
    def test_initialization(self):
        """Test detector initialization."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "lexicons": ["profanity", "hate_skeleton"],
            "action": "block_with_override"
        }
        
        detector = SafetyDetector(config)
        
        assert detector.enabled is True
        assert detector.mode == "monitor"
        assert detector.lexicons == ["profanity", "hate_skeleton"]
        assert detector.action == "block_with_override"
    
    def test_initialization_disabled(self):
        """Test detector initialization when disabled."""
        config = {"enabled": False}
        
        detector = SafetyDetector(config)
        
        assert detector.enabled is False
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_lexicon_loading(self, mock_exists, mock_file):
        """Test lexicon loading from files."""
        mock_exists.return_value = True
        
        # Mock lexicon data
        profanity_data = {
            "version": "1.0.0",
            "words": ["damn", "hell", "crap"]
        }
        
        hate_data = {
            "version": "1.0.0",
            "patterns": ["hate", "discriminate"]
        }
        
        def mock_file_side_effect(file_path, mode):
            if "profanity.json" in str(file_path):
                return mock_open(read_data=json.dumps(profanity_data))()
            elif "hate_skeleton.json" in str(file_path):
                return mock_open(read_data=json.dumps(hate_data))()
            return mock_open(read_data="{}")()
        
        mock_file.side_effect = mock_file_side_effect
        
        config = {
            "enabled": True,
            "mode": "monitor",
            "lexicons": ["profanity", "hate_skeleton"],
            "action": "block_with_override"
        }
        
        detector = SafetyDetector(config)
        detector._ensure_initialized()
        
        assert "profanity" in detector._lexicon_data
        assert "hate_skeleton" in detector._lexicon_data
        assert len(detector._compiled_patterns["profanity"]) == 3
        assert len(detector._compiled_patterns["hate_skeleton"]) == 2
    
    def test_screen_text_with_violations(self):
        """Test text screening with violations found."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "lexicons": ["profanity"],
            "action": "block_with_override"
        }
        
        detector = SafetyDetector(config)
        
        # Mock compiled patterns
        detector._compiled_patterns = {
            "profanity": [pytest.importorskip("re").compile(r'\bdamn\b', pytest.importorskip("re").IGNORECASE)]
        }
        detector._initialized = True
        
        result = detector.screen_text("This is a damn good solution")
        
        assert result.has_violations is True
        assert len(result.violations_found) == 1
        assert result.violations_found[0]["lexicon"] == "profanity"
        assert result.violations_found[0]["text"] == "damn"
        assert result.action_taken == "logged"
    
    def test_screen_text_no_violations(self):
        """Test text screening with no violations."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "lexicons": ["profanity"],
            "action": "block_with_override"
        }
        
        detector = SafetyDetector(config)
        
        # Mock compiled patterns
        detector._compiled_patterns = {
            "profanity": [pytest.importorskip("re").compile(r'\bdamn\b', pytest.importorskip("re").IGNORECASE)]
        }
        detector._initialized = True
        
        result = detector.screen_text("This is a good solution")
        
        assert result.has_violations is False
        assert len(result.violations_found) == 0
        assert result.action_taken == "none"
    
    def test_screen_text_disabled(self):
        """Test text screening when detector is disabled."""
        config = {"enabled": False}
        
        detector = SafetyDetector(config)
        result = detector.screen_text("This is a damn good solution")
        
        assert result.has_violations is False
        assert result.action_taken == "disabled"
    
    def test_screen_text_not_initialized(self):
        """Test text screening when not initialized."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "lexicons": ["profanity"],
            "action": "block_with_override"
        }
        
        detector = SafetyDetector(config)
        detector._initialized = False
        
        result = detector.screen_text("Some text")
        
        assert result.has_violations is False
        assert result.error is None  # SafetyDetector may not set error when not initialized
        assert result.action_taken == "none"  # SafetyDetector returns "none" when not initialized
    
    def test_get_severity(self):
        """Test severity calculation."""
        config = {"enabled": True}
        detector = SafetyDetector(config)
        
        assert detector._get_severity("profanity", "damn") == "low"
        assert detector._get_severity("hate_skeleton", "hate") == "high"
        assert detector._get_severity("unknown", "word") == "medium"
    
    def test_get_evidence(self):
        """Test evidence generation."""
        config = {"enabled": True, "mode": "monitor"}
        detector = SafetyDetector(config)
        
        result = SafetyResult(
            has_violations=True,
            violations_found=[
                {"lexicon": "profanity", "text": "damn", "severity": "low"},
                {"lexicon": "hate_skeleton", "text": "hate", "severity": "high"}
            ],
            action_taken="logged",
            processing_time_ms=2.0
        )
        
        evidence = detector.get_evidence(result)
        
        assert "safety" in evidence
        assert evidence["safety"]["enabled"] is True
        assert evidence["safety"]["has_violations"] is True
        assert evidence["safety"]["total_violations"] == 2
        assert evidence["safety"]["violations_by_lexicon"]["profanity"] == 1
        assert evidence["safety"]["violations_by_lexicon"]["hate_skeleton"] == 1
        assert evidence["safety"]["action_taken"] == "logged"
        assert evidence["safety"]["processing_time_ms"] == 2.0
    
    def test_should_block_monitor_mode(self):
        """Test blocking decision in monitor mode."""
        config = {"enabled": True, "mode": "monitor"}
        detector = SafetyDetector(config)
        
        result = SafetyResult(has_violations=True, violations_found=[])
        
        assert detector.should_block(result) is False
    
    def test_should_block_strict_mode(self):
        """Test blocking decision in strict mode."""
        config = {"enabled": True, "mode": "strict"}
        detector = SafetyDetector(config)
        
        result = SafetyResult(has_violations=True, violations_found=[])
        
        assert detector.should_block(result) is True
    
    def test_should_block_graduated_mode_high_severity(self):
        """Test blocking decision in graduated mode with high severity."""
        config = {"enabled": True, "mode": "graduated"}
        detector = SafetyDetector(config)
        
        result = SafetyResult(
            has_violations=True,
            violations_found=[{"severity": "high"}]
        )
        
        assert detector.should_block(result) is True
    
    def test_should_block_graduated_mode_low_severity(self):
        """Test blocking decision in graduated mode with low severity."""
        config = {"enabled": True, "mode": "graduated"}
        detector = SafetyDetector(config)
        
        result = SafetyResult(
            has_violations=True,
            violations_found=[{"severity": "low"}]
        )
        
        assert detector.should_block(result) is False
    
    def test_get_status(self):
        """Test status reporting."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "lexicons": ["profanity", "hate_skeleton"],
            "action": "block_with_override"
        }
        
        detector = SafetyDetector(config)
        detector._lexicon_data = {"profanity": {}, "hate_skeleton": {}}
        detector._compiled_patterns = {"profanity": [Mock()], "hate_skeleton": [Mock(), Mock()]}
        
        status = detector.get_status()
        
        assert status["name"] == "SafetyDetector"
        assert status["enabled"] is True
        assert status["mode"] == "monitor"
        assert status["lexicons_loaded"] == ["profanity", "hate_skeleton"]
        assert status["total_patterns"] == 3
        assert status["action"] == "block_with_override"
        assert status["version"] == "v2.5.0"
