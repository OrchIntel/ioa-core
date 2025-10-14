"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import re

logger = logging.getLogger(__name__)


@dataclass
class FairnessResult:
    """Result of fairness analysis."""
    has_bias: bool
    bias_score: float
    counterfactual_deltas: Dict[str, float]
    group_metrics: Dict[str, float]
    probe_samples: List[Dict[str, Any]]
    action_taken: Optional[str] = None
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class FairnessDetector:
    """
    Basic fairness detector with counterfactual swaps and group metrics.
    
    Implements Law 5 (Fairness & Non-Discrimination) for bias detection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize fairness detector with configuration.
        
        Args:
            config: Fairness configuration from ethics_pack_v0.json
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.mode = config.get("mode", "monitor")
        self.probes = config.get("probes", ["counterfactual_swap", "group_parity"])
        self.metrics = config.get("metrics", ["demographic_parity", "equalized_odds"])
        self.thresholds = config.get("thresholds", {"warn": 0.1, "block": 0.2})
        
        # Protected term pairs for counterfactual swaps
        self.protected_pairs = {
            "gender": [
                ("he", "she"), ("him", "her"), ("his", "her"), ("himself", "herself"),
                ("man", "woman"), ("men", "women"), ("boy", "girl"), ("boys", "girls"),
                ("male", "female"), ("masculine", "feminine")
            ],
            "religion": [
                ("Christian", "Muslim"), ("Christianity", "Islam"), ("church", "mosque"),
                ("priest", "imam"), ("baptism", "conversion")
            ],
            "ethnicity": [
                ("white", "black"), ("Caucasian", "African-American"), ("European", "Asian"),
                ("Hispanic", "Latino")
            ]
        }
        
        logger.info(f"FairnessDetector initialized: enabled={self.enabled}, mode={self.mode}")
    
    def analyze_fairness(self, text: str, labels: Optional[List[Any]] = None, 
                        groups: Optional[List[str]] = None) -> FairnessResult:
        """
        Analyze text for fairness and bias.
        
        Args:
            text: Input text to analyze
            labels: Optional labels for group metrics calculation
            groups: Optional group identifiers for each label
            
        Returns:
            FairnessResult with fairness analysis
        """
        start_time = datetime.now()
        
        if not self.enabled:
            return FairnessResult(
                has_bias=False,
                bias_score=0.0,
                counterfactual_deltas={},
                group_metrics={},
                probe_samples=[],
                action_taken="disabled",
                processing_time_ms=0.0
            )
        
        try:
            counterfactual_deltas = {}
            probe_samples = []
            
            # Run counterfactual swap probes
            if "counterfactual_swap" in self.probes:
                counterfactual_deltas, samples = self._run_counterfactual_swaps(text)
                probe_samples.extend(samples)
            
            # Calculate group metrics if labels and groups provided
            group_metrics = {}
            if "group_parity" in self.probes and labels is not None and groups is not None:
                group_metrics = self._calculate_group_metrics(labels, groups)
            
            # Calculate overall bias score
            bias_score = self._calculate_bias_score(counterfactual_deltas, group_metrics)
            has_bias = bias_score > self.thresholds["warn"]
            
            # Determine action taken
            action_taken = "none"
            if has_bias:
                if self.mode == "monitor":
                    action_taken = "logged"
                elif self.mode == "graduated":
                    if bias_score > self.thresholds["block"]:
                        action_taken = "blocked"
                    else:
                        action_taken = "warned"
                elif self.mode == "strict":
                    action_taken = "blocked"
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return FairnessResult(
                has_bias=has_bias,
                bias_score=bias_score,
                counterfactual_deltas=counterfactual_deltas,
                group_metrics=group_metrics,
                probe_samples=probe_samples,
                action_taken=action_taken,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Fairness analysis failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return FairnessResult(
                has_bias=False,
                bias_score=0.0,
                counterfactual_deltas={},
                group_metrics={},
                probe_samples=[],
                action_taken="error",
                error=str(e),
                processing_time_ms=processing_time
            )
    
    def _run_counterfactual_swaps(self, text: str) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
        """
        Run counterfactual swap probes to detect bias.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (deltas by category, sample results)
        """
        deltas = {}
        samples = []
        
        for category, pairs in self.protected_pairs.items():
            category_deltas = []
            
            for term1, term2 in pairs:
                # Create swapped versions
                swapped_text1 = self._swap_terms(text, term1, term2)
                swapped_text2 = self._swap_terms(text, term2, term1)
                
                # Calculate simple similarity scores (placeholder for actual model scoring)
                original_score = self._calculate_text_score(text)
                swapped1_score = self._calculate_text_score(swapped_text1)
                swapped2_score = self._calculate_text_score(swapped_text2)
                
                # Calculate deltas
                delta1 = abs(original_score - swapped1_score)
                delta2 = abs(original_score - swapped2_score)
                avg_delta = (delta1 + delta2) / 2
                
                category_deltas.append(avg_delta)
                
                # Store sample
                samples.append({
                    "category": category,
                    "term1": term1,
                    "term2": term2,
                    "original_score": original_score,
                    "swapped1_score": swapped1_score,
                    "swapped2_score": swapped2_score,
                    "delta1": delta1,
                    "delta2": delta2,
                    "avg_delta": avg_delta
                })
            
            # Average delta for this category
            if category_deltas:
                deltas[category] = sum(category_deltas) / len(category_deltas)
        
        return deltas, samples
    
    def _swap_terms(self, text: str, term1: str, term2: str) -> str:
        """Swap terms in text using word boundary matching."""
        pattern = r'\b' + re.escape(term1) + r'\b'
        return re.sub(pattern, term2, text, flags=re.IGNORECASE)
    
    def _calculate_text_score(self, text: str) -> float:
        """
        Calculate a simple score for text (placeholder for actual model scoring).
        
        In a real implementation, this would call an actual model to score the text.
        For now, we use a simple heuristic based on text characteristics.
        """
        # Simple heuristic: length, word count, sentiment indicators
        words = text.split()
        word_count = len(words)
        
        # Simple sentiment indicators
        positive_words = ["good", "great", "excellent", "positive", "beneficial"]
        negative_words = ["bad", "terrible", "negative", "harmful", "problematic"]
        
        positive_count = sum(1 for word in words if word.lower() in positive_words)
        negative_count = sum(1 for word in words if word.lower() in negative_words)
        
        # Calculate score (0-1 range)
        sentiment_score = (positive_count - negative_count) / max(word_count, 1)
        length_score = min(word_count / 100, 1.0)  # Normalize by 100 words
        
        return (sentiment_score + length_score) / 2
    
    def _calculate_group_metrics(self, labels: List[Any], groups: List[str]) -> Dict[str, float]:
        """
        Calculate group-based fairness metrics.
        
        Args:
            labels: List of labels/predictions
            groups: List of group identifiers for each label
            
        Returns:
            Dictionary of fairness metrics
        """
        try:
            from fairlearn.metrics import demographic_parity_difference, equalized_odds_difference
            
            # Convert to numpy arrays if needed
            import numpy as np
            labels = np.array(labels)
            groups = np.array(groups)
            
            # Calculate demographic parity difference
            if "demographic_parity" in self.metrics:
                dp_diff = demographic_parity_difference(labels, groups)
            else:
                dp_diff = 0.0
            
            # Calculate equalized odds difference
            if "equalized_odds" in self.metrics:
                eo_diff = equalized_odds_difference(labels, groups)
            else:
                eo_diff = 0.0
            
            return {
                "demographic_parity_difference": dp_diff,
                "equalized_odds_difference": eo_diff
            }
            
        except ImportError:
            logger.warning("fairlearn not available - skipping group metrics")
            return {}
        except Exception as e:
            logger.error(f"Group metrics calculation failed: {e}")
            return {}
    
    def _calculate_bias_score(self, counterfactual_deltas: Dict[str, float], 
                            group_metrics: Dict[str, float]) -> float:
        """
        Calculate overall bias score from deltas and group metrics.
        
        Args:
            counterfactual_deltas: Deltas from counterfactual swaps
            group_metrics: Group-based fairness metrics
            
        Returns:
            Overall bias score (0-1)
        """
        scores = []
        
        # Add counterfactual deltas
        for category, delta in counterfactual_deltas.items():
            scores.append(delta)
        
        # Add group metrics
        for metric, value in group_metrics.items():
            scores.append(abs(value))  # Use absolute value
        
        if not scores:
            return 0.0
        
        # Return average score
        return sum(scores) / len(scores)
    
    def get_evidence(self, result: FairnessResult) -> Dict[str, Any]:
        """
        Generate evidence for audit trail.
        
        Args:
            result: Fairness analysis result
            
        Returns:
            Evidence dictionary for audit chain
        """
        return {
            "fairness": {
                "enabled": self.enabled,
                "mode": self.mode,
                "has_bias": result.has_bias,
                "bias_score": result.bias_score,
                "thresholds": self.thresholds,
                "counterfactual_deltas": result.counterfactual_deltas,
                "group_metrics": result.group_metrics,
                "probe_samples_count": len(result.probe_samples),
                "action_taken": result.action_taken,
                "processing_time_ms": result.processing_time_ms,
                "error": result.error,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def should_block(self, result: FairnessResult) -> bool:
        """
        Determine if action should be blocked based on fairness result.
        
        Args:
            result: Fairness analysis result
            
        Returns:
            True if action should be blocked
        """
        if not self.enabled or self.mode == "monitor":
            return False
        
        if result.error:
            return False  # Don't block on errors in monitor mode
        
        # Block if bias score exceeds block threshold
        if result.bias_score > self.thresholds["block"]:
            return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get detector status for diagnostics."""
        return {
            "name": "FairnessDetector",
            "enabled": self.enabled,
            "mode": self.mode,
            "probes": self.probes,
            "metrics": self.metrics,
            "thresholds": self.thresholds,
            "protected_categories": list(self.protected_pairs.keys()),
            "version": "v2.5.0"
        }
