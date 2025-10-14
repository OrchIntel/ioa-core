"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BiasResult:
    """Result of bias detection."""
    has_bias: bool
    bias_found: List[Dict[str, Any]]
    bias_categories: List[str]
    risk_level: str
    action_taken: Optional[str] = None
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class BiasDetector:
    """
    Bias detector for fairness compliance.
    
    Implements Law 5 (Fairness & Non-Discrimination) for bias detection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize bias detector with configuration.
        
        Args:
            config: Bias detection configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.mode = config.get("mode", "monitor")
        self.action = config.get("action", "flag")
        self.lexicon_path = config.get("lexicon_path", "configs/lexicons/bias.json")
        
        # Load bias patterns
        self._patterns = {}
        self._compiled_patterns = {}
        self._bias_categories = {}
        self._initialized = False
        
        logger.info(f"BiasDetector initialized: enabled={self.enabled}, mode={self.mode}")
    
    def _ensure_initialized(self) -> bool:
        """Ensure bias patterns are loaded and compiled."""
        if self._initialized:
            return True
        
        try:
            # Load bias lexicon
            lexicon_path = Path(__file__).parent.parent.parent.parent.parent / self.lexicon_path
            
            if lexicon_path.exists():
                with open(lexicon_path, 'r') as f:
                    lexicon_data = json.load(f)
                    self._patterns = lexicon_data
                    
                    # Compile regex patterns
                    patterns = []
                    if "patterns" in lexicon_data:
                        for pattern in lexicon_data["patterns"]:
                            try:
                                compiled = re.compile(pattern, re.IGNORECASE)
                                patterns.append({
                                    "pattern": pattern,
                                    "compiled": compiled,
                                    "type": "regex"
                                })
                            except re.error as e:
                                logger.warning(f"Invalid regex pattern: {pattern} - {e}")
                    
                    if "words" in lexicon_data:
                        for word in lexicon_data["words"]:
                            # Use word boundary matching
                            pattern = r'\b' + re.escape(word) + r'\b'
                            try:
                                compiled = re.compile(pattern, re.IGNORECASE)
                                patterns.append({
                                    "pattern": pattern,
                                    "compiled": compiled,
                                    "type": "word",
                                    "original": word
                                })
                            except re.error as e:
                                logger.warning(f"Invalid word pattern: {word} - {e}")
                    
                    self._compiled_patterns = patterns
                    
                    # Load bias categories
                    if "metadata" in lexicon_data and "bias_categories" in lexicon_data["metadata"]:
                        self._bias_categories = lexicon_data["metadata"]["bias_categories"]
                    
                    logger.info(f"Loaded bias patterns: {len(patterns)} patterns")
            else:
                logger.warning(f"Bias lexicon file not found: {lexicon_path}")
                return False
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize bias detector: {e}")
            return False
    
    def detect_bias(self, text: str) -> BiasResult:
        """
        Detect bias in text.
        
        Args:
            text: Input text to scan for bias
            
        Returns:
            BiasResult with detection results
        """
        start_time = datetime.now()
        
        if not self.enabled:
            return BiasResult(
                has_bias=False,
                bias_found=[],
                bias_categories=[],
                risk_level="none",
                action_taken="disabled",
                processing_time_ms=0.0
            )
        
        if not self._ensure_initialized():
            return BiasResult(
                has_bias=False,
                bias_found=[],
                bias_categories=[],
                risk_level="none",
                action_taken="error",
                error="Bias patterns not available",
                processing_time_ms=0.0
            )
        
        try:
            bias_found = []
            bias_categories = set()
            
            # Check each pattern
            for pattern_info in self._compiled_patterns:
                pattern = pattern_info["compiled"]
                matches = pattern.finditer(text)
                
                for match in matches:
                    bias_item = {
                        "type": self._classify_bias_type(pattern_info, match.group()),
                        "pattern": pattern_info["pattern"],
                        "start": match.start(),
                        "end": match.end(),
                        "text": match.group(),
                        "severity": self._get_severity(pattern_info, match.group()),
                        "category": self._get_bias_category(pattern_info, match.group())
                    }
                    bias_found.append(bias_item)
                    
                    if bias_item["category"]:
                        bias_categories.add(bias_item["category"])
            
            has_bias = len(bias_found) > 0
            risk_level = self._calculate_risk_level(bias_found)
            
            # Determine action taken
            action_taken = "none"
            if has_bias:
                if self.mode == "monitor":
                    action_taken = "logged"
                elif self.mode == "strict":
                    if self.action == "flag":
                        action_taken = "flagged"
                    elif self.action == "block":
                        action_taken = "blocked"
                    else:
                        action_taken = "warned"
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return BiasResult(
                has_bias=has_bias,
                bias_found=bias_found,
                bias_categories=list(bias_categories),
                risk_level=risk_level,
                action_taken=action_taken,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Bias detection error: {e}")
            return BiasResult(
                has_bias=False,
                bias_found=[],
                bias_categories=[],
                risk_level="none",
                action_taken="error",
                error=str(e),
                processing_time_ms=0.0
            )
    
    def _classify_bias_type(self, pattern_info: Dict[str, Any], matched_text: str) -> str:
        """Classify the type of bias detected."""
        pattern = pattern_info["pattern"]
        text_lower = matched_text.lower()
        
        # Gender bias
        if any(term in text_lower for term in ["men", "women", "male", "female", "masculine", "feminine"]):
            return "gender_bias"
        
        # Racial bias
        if any(term in text_lower for term in ["black", "white", "asian", "hispanic", "african", "caucasian"]):
            return "racial_bias"
        
        # Religious bias
        if any(term in text_lower for term in ["muslim", "jewish", "christian", "hindu", "buddhist", "atheist"]):
            return "religious_bias"
        
        # Disability bias
        if any(term in text_lower for term in ["disabled", "handicapped", "crippled", "retarded"]):
            return "disability_bias"
        
        # Age bias
        if any(term in text_lower for term in ["elderly", "old", "young", "teenager", "senior"]):
            return "age_bias"
        
        # Sexual orientation bias
        if any(term in text_lower for term in ["gay", "lesbian", "straight", "bisexual", "transgender"]):
            return "sexual_orientation_bias"
        
        # Socioeconomic bias
        if any(term in text_lower for term in ["poor", "rich", "wealthy", "poverty", "affluent"]):
            return "socioeconomic_bias"
        
        # General bias terms
        if any(term in text_lower for term in ["stereotype", "prejudice", "discrimination", "bias"]):
            return "general_bias"
        
        return "unknown_bias"
    
    def _get_bias_category(self, pattern_info: Dict[str, Any], matched_text: str) -> Optional[str]:
        """Get the bias category for detected bias."""
        if not self._bias_categories:
            return None
        
        text_lower = matched_text.lower()
        
        for category, terms in self._bias_categories.items():
            if any(term.lower() in text_lower for term in terms):
                return category
        
        return None
    
    def _get_severity(self, pattern_info: Dict[str, Any], matched_text: str) -> str:
        """Get severity level for detected bias."""
        # Check severity levels from metadata
        if "metadata" in self._patterns and "severity_levels" in self._patterns["metadata"]:
            severity_levels = self._patterns["metadata"]["severity_levels"]
            
            for severity, words in severity_levels.items():
                if pattern_info.get("original") in words:
                    return severity
        
        # Default severity based on bias type
        bias_type = self._classify_bias_type(pattern_info, matched_text)
        if bias_type in ["racial_bias", "religious_bias", "disability_bias"]:
            return "severe"
        elif bias_type in ["gender_bias", "sexual_orientation_bias"]:
            return "moderate"
        else:
            return "mild"
    
    def _calculate_risk_level(self, bias_found: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level based on detected bias."""
        if not bias_found:
            return "none"
        
        # Count by severity
        severity_counts = {"mild": 0, "moderate": 0, "severe": 0, "extreme": 0}
        for bias in bias_found:
            severity = bias.get("severity", "mild")
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Count by category
        category_counts = {}
        for bias in bias_found:
            category = bias.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Determine risk level
        if severity_counts["extreme"] > 0 or severity_counts["severe"] > 2:
            return "high"
        elif severity_counts["severe"] > 0 or severity_counts["moderate"] > 3:
            return "medium"
        elif severity_counts["moderate"] > 0 or len(category_counts) > 2:
            return "low"
        else:
            return "minimal"
    
    def get_bias_summary(self, bias_result: BiasResult) -> Dict[str, Any]:
        """Get a summary of detected bias."""
        if not bias_result.has_bias:
            return {"total_bias": 0, "categories": [], "severity_breakdown": {}}
        
        # Count by category
        category_counts = {}
        for bias in bias_result.bias_found:
            category = bias.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Count by severity
        severity_counts = {}
        for bias in bias_result.bias_found:
            severity = bias.get("severity", "mild")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_bias": len(bias_result.bias_found),
            "categories": list(category_counts.keys()),
            "category_counts": category_counts,
            "severity_breakdown": severity_counts,
            "risk_level": bias_result.risk_level
        }
