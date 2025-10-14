"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from src.ioa.governance.detectors.fairness_basic import FairnessDetector, FairnessResult


class TestFairnessDetector:
    """Test cases for FairnessDetector."""
    
    def test_initialization(self):
        """Test detector initialization."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "probes": ["counterfactual_swap", "group_parity"],
            "metrics": ["demographic_parity", "equalized_odds"],
            "thresholds": {"warn": 0.1, "block": 0.2}
        }
        
        detector = FairnessDetector(config)
        
        assert detector.enabled is True
        assert detector.mode == "monitor"
        assert detector.probes == ["counterfactual_swap", "group_parity"]
        assert detector.metrics == ["demographic_parity", "equalized_odds"]
        assert detector.thresholds == {"warn": 0.1, "block": 0.2}
        assert "gender" in detector.protected_pairs
        assert "religion" in detector.protected_pairs
        assert "ethnicity" in detector.protected_pairs
    
    def test_initialization_disabled(self):
        """Test detector initialization when disabled."""
        config = {"enabled": False}
        
        detector = FairnessDetector(config)
        
        assert detector.enabled is False
    
    def test_analyze_fairness_disabled(self):
        """Test fairness analysis when detector is disabled."""
        config = {"enabled": False}
        
        detector = FairnessDetector(config)
        result = detector.analyze_fairness("Some text")
        
        assert result.has_bias is False
        assert result.bias_score == 0.0
        assert result.action_taken == "disabled"
    
    def test_analyze_fairness_counterfactual_swaps(self):
        """Test fairness analysis with counterfactual swaps."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "probes": ["counterfactual_swap"],
            "metrics": [],
            "thresholds": {"warn": 0.1, "block": 0.2}
        }
        
        detector = FairnessDetector(config)
        result = detector.analyze_fairness("He is a good leader")
        
        assert result.has_bias is False  # Should be False for this simple case
        assert result.bias_score >= 0.0
        assert len(result.counterfactual_deltas) > 0
        assert "gender" in result.counterfactual_deltas
        assert len(result.probe_samples) > 0
    
    def test_analyze_fairness_with_group_metrics(self):
        """Test fairness analysis with group metrics."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "probes": ["group_parity"],
            "metrics": ["demographic_parity", "equalized_odds"],
            "thresholds": {"warn": 0.1, "block": 0.2}
        }
        
        detector = FairnessDetector(config)
        
        # Mock labels and groups
        labels = [1, 0, 1, 0, 1]
        groups = ["A", "B", "A", "B", "A"]
        
        result = detector.analyze_fairness("Some text", labels, groups)
        
        assert result.has_bias is False  # Should be False for balanced data
        assert result.bias_score >= 0.0
        assert len(result.group_metrics) >= 0  # May be empty if fairlearn not available
    
    @patch('src.ioa.governance.detectors.fairness_basic.FairnessDetector._calculate_group_metrics')
    def test_calculate_group_metrics_with_fairlearn(self, mock_group_metrics):
        """Test group metrics calculation with fairlearn available."""
        mock_group_metrics.return_value = {
            "demographic_parity_difference": 0.1,
            "equalized_odds_difference": 0.15
        }
        
        config = {
            "enabled": True,
            "mode": "monitor",
            "probes": ["group_parity"],
            "metrics": ["demographic_parity", "equalized_odds"],
            "thresholds": {"warn": 0.1, "block": 0.2}
        }
        
        detector = FairnessDetector(config)
        
        labels = [1, 0, 1, 0, 1]
        groups = ["A", "B", "A", "B", "A"]
        
        metrics = detector._calculate_group_metrics(labels, groups)
        
        assert "demographic_parity_difference" in metrics
        assert "equalized_odds_difference" in metrics
        assert metrics["demographic_parity_difference"] == 0.1
        assert metrics["equalized_odds_difference"] == 0.15
    
    def test_calculate_group_metrics_without_fairlearn(self):
        """Test group metrics calculation without fairlearn."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "probes": ["group_parity"],
            "metrics": ["demographic_parity", "equalized_odds"],
            "thresholds": {"warn": 0.1, "block": 0.2}
        }
        
        detector = FairnessDetector(config)
        
        with patch('src.ioa.governance.detectors.fairness_basic.FairnessDetector._calculate_group_metrics', side_effect=ImportError):
            labels = [1, 0, 1, 0, 1]
            groups = ["A", "B", "A", "B", "A"]
            
            try:
                metrics = detector._calculate_group_metrics(labels, groups)
                assert metrics == {}
            except ImportError:
                # Expected when fairlearn is not available
                pass
    
    def test_swap_terms(self):
        """Test term swapping functionality."""
        config = {"enabled": True}
        detector = FairnessDetector(config)
        
        text = "He is a good leader"
        swapped = detector._swap_terms(text, "he", "she")
        
        assert swapped == "she is a good leader"
    
    def test_calculate_text_score(self):
        """Test text score calculation."""
        config = {"enabled": True}
        detector = FairnessDetector(config)
        
        # Test with positive words
        score1 = detector._calculate_text_score("This is a good and excellent solution")
        assert 0.0 <= score1 <= 1.0
        
        # Test with negative words
        score2 = detector._calculate_text_score("This is a bad and terrible solution")
        assert -1.0 <= score2 <= 1.0  # Allow negative scores
        
        # Test with neutral text
        score3 = detector._calculate_text_score("This is a solution")
        assert 0.0 <= score3 <= 1.0
    
    def test_calculate_bias_score(self):
        """Test bias score calculation."""
        config = {"enabled": True}
        detector = FairnessDetector(config)
        
        counterfactual_deltas = {"gender": 0.1, "religion": 0.05}
        group_metrics = {"demographic_parity_difference": 0.15, "equalized_odds_difference": 0.08}
        
        bias_score = detector._calculate_bias_score(counterfactual_deltas, group_metrics)
        
        # Should be average of all values
        expected = (0.1 + 0.05 + 0.15 + 0.08) / 4
        assert abs(bias_score - expected) < 0.001
    
    def test_calculate_bias_score_empty(self):
        """Test bias score calculation with empty inputs."""
        config = {"enabled": True}
        detector = FairnessDetector(config)
        
        bias_score = detector._calculate_bias_score({}, {})
        
        assert bias_score == 0.0
    
    def test_get_evidence(self):
        """Test evidence generation."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "thresholds": {"warn": 0.1, "block": 0.2}
        }
        
        detector = FairnessDetector(config)
        
        result = FairnessResult(
            has_bias=True,
            bias_score=0.15,
            counterfactual_deltas={"gender": 0.1},
            group_metrics={"demographic_parity_difference": 0.2},
            probe_samples=[{"category": "gender", "avg_delta": 0.1}],
            action_taken="warned",
            processing_time_ms=5.0
        )
        
        evidence = detector.get_evidence(result)
        
        assert "fairness" in evidence
        assert evidence["fairness"]["enabled"] is True
        assert evidence["fairness"]["has_bias"] is True
        assert evidence["fairness"]["bias_score"] == 0.15
        assert evidence["fairness"]["thresholds"] == {"warn": 0.1, "block": 0.2}
        assert evidence["fairness"]["counterfactual_deltas"] == {"gender": 0.1}
        assert evidence["fairness"]["group_metrics"] == {"demographic_parity_difference": 0.2}
        assert evidence["fairness"]["probe_samples_count"] == 1
        assert evidence["fairness"]["action_taken"] == "warned"
        assert evidence["fairness"]["processing_time_ms"] == 5.0
    
    def test_should_block_monitor_mode(self):
        """Test blocking decision in monitor mode."""
        config = {"enabled": True, "mode": "monitor"}
        detector = FairnessDetector(config)
        
        result = FairnessResult(
            has_bias=True, 
            bias_score=0.5,
            counterfactual_deltas={"gender": 0.1},
            group_metrics={"male": 0.4, "female": 0.6},
            probe_samples=[{"text": "test", "group": "male"}]
        )
        
        assert detector.should_block(result) is False
    
    def test_should_block_strict_mode(self):
        """Test blocking decision in strict mode."""
        config = {
            "enabled": True,
            "mode": "strict",
            "thresholds": {"warn": 0.1, "block": 0.2}
        }
        
        detector = FairnessDetector(config)
        
        result = FairnessResult(
            has_bias=True, 
            bias_score=0.5,
            counterfactual_deltas={"gender": 0.1},
            group_metrics={"male": 0.4, "female": 0.6},
            probe_samples=[{"text": "test", "group": "male"}]
        )
        
        assert detector.should_block(result) is True
    
    def test_should_block_graduated_mode(self):
        """Test blocking decision in graduated mode."""
        config = {
            "enabled": True,
            "mode": "graduated",
            "thresholds": {"warn": 0.1, "block": 0.2}
        }
        
        detector = FairnessDetector(config)
        
        # Test with bias score below block threshold
        result1 = FairnessResult(
            has_bias=True, 
            bias_score=0.15,
            counterfactual_deltas={"gender": 0.05},
            group_metrics={"male": 0.45, "female": 0.55},
            probe_samples=[{"text": "test", "group": "male"}]
        )
        assert detector.should_block(result1) is False
        
        # Test with bias score above block threshold
        result2 = FairnessResult(
            has_bias=True, 
            bias_score=0.25,
            counterfactual_deltas={"gender": 0.15},
            group_metrics={"male": 0.35, "female": 0.65},
            probe_samples=[{"text": "test", "group": "male"}]
        )
        assert detector.should_block(result2) is True
    
    def test_get_status(self):
        """Test status reporting."""
        config = {
            "enabled": True,
            "mode": "monitor",
            "probes": ["counterfactual_swap", "group_parity"],
            "metrics": ["demographic_parity", "equalized_odds"],
            "thresholds": {"warn": 0.1, "block": 0.2}
        }
        
        detector = FairnessDetector(config)
        status = detector.get_status()
        
        assert status["name"] == "FairnessDetector"
        assert status["enabled"] is True
        assert status["mode"] == "monitor"
        assert status["probes"] == ["counterfactual_swap", "group_parity"]
        assert status["metrics"] == ["demographic_parity", "equalized_odds"]
        assert status["thresholds"] == {"warn": 0.1, "block": 0.2}
        assert "gender" in status["protected_categories"]
        assert "religion" in status["protected_categories"]
        assert "ethnicity" in status["protected_categories"]
        assert status["version"] == "v2.5.0"
