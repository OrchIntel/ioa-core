""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.ioa.governance.detectors.privacy_presidio import PrivacyDetector, PrivacyResult


class TestPrivacyDetector:
    """Test cases for PrivacyDetector."""
    
    def test_initialization(self):
        """Test detector initialization."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "pii_entities": ["PERSON", "EMAIL_ADDRESS"],
            "action": "mask"
        }
        
        detector = PrivacyDetector(config)
        
        assert detector.enabled is True
        assert detector.mode == "monitor"
        assert detector.pii_entities == ["PERSON", "EMAIL_ADDRESS"]
        assert detector.action == "mask"
    
    def test_initialization_disabled(self):
        """Test detector initialization when disabled."""
        config = {"enabled": False}
        
        detector = PrivacyDetector(config)
        
        assert detector.enabled is False
    
    @patch('src.ioa.governance.detectors.privacy_presidio.AnalyzerEngine')
    @patch('src.ioa.governance.detectors.privacy_presidio.AnonymizerEngine')
    def test_detect_and_anonymize_with_pii(self, mock_anonymizer, mock_analyzer):
        """Test PII detection and anonymization."""
        # Mock analyzer results
        mock_result = Mock()
        mock_result.entity_type = "EMAIL_ADDRESS"
        mock_result.start = 10
        mock_result.end = 30
        mock_result.score = 0.95
        
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.analyze.return_value = [mock_result]
        mock_analyzer.return_value = mock_analyzer_instance
        
        # Mock anonymizer results
        mock_anonymized_result = Mock()
        mock_anonymized_result.text = "Contact me at <EMAIL_ADDRESS> for details"
        
        mock_anonymizer_instance = Mock()
        mock_anonymizer_instance.anonymize.return_value = mock_anonymized_result
        mock_anonymizer.return_value = mock_anonymizer_instance
        
        config = {
            "enabled": True,
            "mode": "monitor",
            "pii_entities": ["EMAIL_ADDRESS"],
            "action": "mask"
        }
        
        detector = PrivacyDetector(config)
        result = detector.detect_and_anonymize("Contact me at john@example.com for details")
        
        assert result.has_pii is True
        assert len(result.entities_found) == 1
        assert result.entities_found[0]["entity_type"] == "EMAIL_ADDRESS"
        assert result.entities_found[0]["text"] == "john@example.com"
        assert result.anonymized_text == "Contact me at <EMAIL_ADDRESS> for details"
        assert result.action_taken == "masked"
    
    @patch('src.ioa.governance.detectors.privacy_presidio.AnalyzerEngine')
    def test_detect_and_anonymize_no_pii(self, mock_analyzer):
        """Test detection when no PII is found."""
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.analyze.return_value = []
        mock_analyzer.return_value = mock_analyzer_instance
        
        config = {
            "enabled": True,
            "mode": "monitor",
            "pii_entities": ["EMAIL_ADDRESS"],
            "action": "mask"
        }
        
        detector = PrivacyDetector(config)
        result = detector.detect_and_anonymize("This is a normal text without PII")
        
        assert result.has_pii is False
        assert len(result.entities_found) == 0
        assert result.anonymized_text == "This is a normal text without PII"
        assert result.action_taken == "none"
    
    def test_detect_and_anonymize_disabled(self):
        """Test detection when detector is disabled."""
        config = {"enabled": False}
        
        detector = PrivacyDetector(config)
        result = detector.detect_and_anonymize("Some text with john@example.com")
        
        assert result.has_pii is False
        assert result.anonymized_text == "Some text with john@example.com"
        assert result.action_taken == "disabled"
    
    def test_detect_and_anonymize_presidio_not_available(self):
        """Test detection when Presidio is not available."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "pii_entities": ["EMAIL_ADDRESS"],
            "action": "mask"
        }
        
        detector = PrivacyDetector(config)
        detector._initialized = False
        
        with patch('src.ioa.governance.detectors.privacy_presidio.AnalyzerEngine', side_effect=ImportError):
            result = detector.detect_and_anonymize("Some text")
            
            assert result.has_pii is False
            assert result.error == "Presidio not available"
            assert result.action_taken == "error"
    
    def test_get_evidence(self):
        """Test evidence generation."""
        config = {"enabled": True, "mode": "monitor"}
        detector = PrivacyDetector(config)
        
        result = PrivacyResult(
            has_pii=True,
            entities_found=[{"entity_type": "EMAIL_ADDRESS", "text": "test@example.com"}],
            anonymized_text="<EMAIL_ADDRESS>",
            action_taken="masked",
            confidence_scores={"EMAIL_ADDRESS": 0.95},
            processing_time_ms=1.5
        )
        
        evidence = detector.get_evidence(result)
        
        assert "privacy" in evidence
        assert evidence["privacy"]["enabled"] is True
        assert evidence["privacy"]["has_pii"] is True
        assert evidence["privacy"]["entities_detected"] == 1
        assert evidence["privacy"]["action_taken"] == "masked"
        assert evidence["privacy"]["processing_time_ms"] == 1.5
    
    def test_should_block_monitor_mode(self):
        """Test blocking decision in monitor mode."""
        config = {"enabled": True, "mode": "monitor"}
        detector = PrivacyDetector(config)
        
        result = PrivacyResult(has_pii=True, entities_found=[])
        
        assert detector.should_block(result) is False
    
    def test_should_block_strict_mode(self):
        """Test blocking decision in strict mode."""
        config = {"enabled": True, "mode": "strict"}
        detector = PrivacyDetector(config)
        
        result = PrivacyResult(has_pii=True, entities_found=[])
        
        assert detector.should_block(result) is True
    
    def test_should_block_no_pii(self):
        """Test blocking decision when no PII found."""
        config = {"enabled": True, "mode": "strict"}
        detector = PrivacyDetector(config)
        
        result = PrivacyResult(has_pii=False, entities_found=[])
        
        assert detector.should_block(result) is False
    
    def test_get_status(self):
        """Test status reporting."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "pii_entities": ["PERSON", "EMAIL_ADDRESS"],
            "action": "mask"
        }
        
        detector = PrivacyDetector(config)
        status = detector.get_status()
        
        assert status["name"] == "PrivacyDetector"
        assert status["enabled"] is True
        assert status["mode"] == "monitor"
        assert status["pii_entities"] == ["PERSON", "EMAIL_ADDRESS"]
        assert status["action"] == "mask"
        assert status["version"] == "v2.5.0"
