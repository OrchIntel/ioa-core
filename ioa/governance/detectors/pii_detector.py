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
class PIIResult:
    """Result of PII detection."""
    has_pii: bool
    pii_found: List[Dict[str, Any]]
    risk_level: str
    action_taken: Optional[str] = None
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class PIIDetector:
    """
    PII detector for privacy compliance.
    
    Implements Law 1 (Compliance Supremacy) and Law 3 (Auditability) for PII detection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PII detector with configuration.
        
        Args:
            config: PII detection configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.mode = config.get("mode", "monitor")
        self.action = config.get("action", "redact")
        self.lexicon_path = config.get("lexicon_path", "configs/lexicons/pii.json")
        
        # Load PII patterns
        self._patterns = {}
        self._compiled_patterns = {}
        self._initialized = False
        
        logger.info(f"PIIDetector initialized: enabled={self.enabled}, mode={self.mode}")
    
    def _ensure_initialized(self) -> bool:
        """Ensure PII patterns are loaded and compiled."""
        if self._initialized:
            return True
        
        try:
            # Load PII lexicon
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
                    logger.info(f"Loaded PII patterns: {len(patterns)} patterns")
            else:
                logger.warning(f"PII lexicon file not found: {lexicon_path}")
                return False
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize PII detector: {e}")
            return False
    
    def detect_pii(self, text: str) -> PIIResult:
        """
        Detect PII in text.
        
        Args:
            text: Input text to scan for PII
            
        Returns:
            PIIResult with detection results
        """
        start_time = datetime.now()
        
        if not self.enabled:
            return PIIResult(
                has_pii=False,
                pii_found=[],
                risk_level="none",
                action_taken="disabled",
                processing_time_ms=0.0
            )
        
        if not self._ensure_initialized():
            return PIIResult(
                has_pii=False,
                pii_found=[],
                risk_level="none",
                action_taken="error",
                error="PII patterns not available",
                processing_time_ms=0.0
            )
        
        try:
            pii_found = []
            
            # Check each pattern
            for pattern_info in self._compiled_patterns:
                pattern = pattern_info["compiled"]
                matches = pattern.finditer(text)
                
                for match in matches:
                    pii_item = {
                        "type": self._classify_pii_type(pattern_info),
                        "pattern": pattern_info["pattern"],
                        "start": match.start(),
                        "end": match.end(),
                        "text": match.group(),
                        "severity": self._get_severity(pattern_info, match.group())
                    }
                    pii_found.append(pii_item)
            
            has_pii = len(pii_found) > 0
            risk_level = self._calculate_risk_level(pii_found)
            
            # Determine action taken
            action_taken = "none"
            if has_pii:
                if self.mode == "monitor":
                    action_taken = "logged"
                elif self.mode == "strict":
                    if self.action == "redact":
                        action_taken = "redacted"
                    elif self.action == "block":
                        action_taken = "blocked"
                    else:
                        action_taken = "flagged"
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return PIIResult(
                has_pii=has_pii,
                pii_found=pii_found,
                risk_level=risk_level,
                action_taken=action_taken,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"PII detection error: {e}")
            return PIIResult(
                has_pii=False,
                pii_found=[],
                risk_level="none",
                action_taken="error",
                error=str(e),
                processing_time_ms=0.0
            )
    
    def _classify_pii_type(self, pattern_info: Dict[str, Any]) -> str:
        """Classify the type of PII detected."""
        pattern = pattern_info["pattern"]
        
        # SSN patterns
        if re.search(r'\d{3}[-.\s]?\d{2}[-.\s]?\d{4}', pattern):
            return "ssn"
        
        # Credit card patterns
        if re.search(r'\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}', pattern):
            return "credit_card"
        
        # Email patterns
        if re.search(r'@.*\.', pattern):
            return "email"
        
        # Phone patterns
        if re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', pattern):
            return "phone"
        
        # ZIP code patterns
        if re.search(r'\d{5}(-\d{4})?', pattern):
            return "zip_code"
        
        # IP address patterns
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', pattern):
            return "ip_address"
        
        # Default to word-based classification
        if pattern_info.get("type") == "word":
            return pattern_info.get("original", "unknown")
        
        return "unknown"
    
    def _get_severity(self, pattern_info: Dict[str, Any], matched_text: str) -> str:
        """Get severity level for detected PII."""
        # Check severity levels from metadata
        if "metadata" in self._patterns and "severity_levels" in self._patterns["metadata"]:
            severity_levels = self._patterns["metadata"]["severity_levels"]
            
            for severity, words in severity_levels.items():
                if pattern_info.get("original") in words:
                    return severity
        
        # Default severity based on PII type
        pii_type = self._classify_pii_type(pattern_info)
        if pii_type in ["ssn", "credit_card", "bank_account"]:
            return "severe"
        elif pii_type in ["email", "phone", "zip_code"]:
            return "moderate"
        else:
            return "mild"
    
    def _calculate_risk_level(self, pii_found: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level based on detected PII."""
        if not pii_found:
            return "none"
        
        # Count by severity
        severity_counts = {"mild": 0, "moderate": 0, "severe": 0, "extreme": 0}
        for pii in pii_found:
            severity = pii.get("severity", "mild")
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Determine risk level
        if severity_counts["extreme"] > 0 or severity_counts["severe"] > 2:
            return "high"
        elif severity_counts["severe"] > 0 or severity_counts["moderate"] > 3:
            return "medium"
        elif severity_counts["moderate"] > 0 or severity_counts["mild"] > 5:
            return "low"
        else:
            return "minimal"
    
    def redact_pii(self, text: str, pii_result: PIIResult) -> str:
        """Redact detected PII from text."""
        if not pii_result.has_pii:
            return text
        
        redacted_text = text
        offset = 0
        
        # Sort by position to handle redaction correctly
        sorted_pii = sorted(pii_result.pii_found, key=lambda x: x["start"])
        
        for pii in sorted_pii:
            start = pii["start"] - offset
            end = pii["end"] - offset
            
            # Create redaction based on PII type
            if pii["type"] == "ssn":
                redaction = "XXX-XX-XXXX"
            elif pii["type"] == "credit_card":
                redaction = "XXXX-XXXX-XXXX-XXXX"
            elif pii["type"] == "email":
                redaction = "***@***.***"
            elif pii["type"] == "phone":
                redaction = "XXX-XXX-XXXX"
            else:
                redaction = "***"
            
            redacted_text = redacted_text[:start] + redaction + redacted_text[end:]
            offset += len(pii["text"]) - len(redaction)
        
        return redacted_text
