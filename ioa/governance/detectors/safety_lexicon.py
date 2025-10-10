""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SafetyResult:
    """Result of safety screening."""
    has_violations: bool
    violations_found: List[Dict[str, Any]]
    action_taken: Optional[str] = None
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class SafetyDetector:
    """
    Safety detector using lexicon-based screening.
    
    Implements Law 4 (Immutable Governance) skeleton for content safety.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize safety detector with configuration.
        
        Args:
            config: Safety configuration from ethics_pack_v0.json
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.mode = config.get("mode", "monitor")
        self.lexicons = config.get("lexicons", ["profanity", "hate_skeleton"])
        self.action = config.get("action", "block_with_override")
        
        # Load lexicons
        self._lexicon_data = {}
        self._compiled_patterns = {}
        self._initialized = False
        
        logger.info(f"SafetyDetector initialized: enabled={self.enabled}, mode={self.mode}")
    
    def _ensure_initialized(self) -> bool:
        """Ensure lexicons are loaded and patterns compiled."""
        if self._initialized:
            return True
        
        try:
            # Load lexicon files
            for lexicon_name in self.lexicons:
                lexicon_path = Path(__file__).parent.parent.parent.parent.parent / "configs" / "lexicons" / f"{lexicon_name}.json"
                
                if lexicon_path.exists():
                    with open(lexicon_path, 'r') as f:
                        lexicon_data = json.load(f)
                        self._lexicon_data[lexicon_name] = lexicon_data
                        
                        # Compile patterns for this lexicon
                        patterns = []
                        if "words" in lexicon_data:
                            for word in lexicon_data["words"]:
                                # Use word boundary matching
                                pattern = r'\b' + re.escape(word) + r'\b'
                                patterns.append(re.compile(pattern, re.IGNORECASE))
                        
                        if "patterns" in lexicon_data:
                            for pattern in lexicon_data["patterns"]:
                                patterns.append(re.compile(pattern, re.IGNORECASE))
                        
                        self._compiled_patterns[lexicon_name] = patterns
                        logger.info(f"Loaded lexicon '{lexicon_name}' with {len(patterns)} patterns")
                else:
                    logger.warning(f"Lexicon file not found: {lexicon_path}")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize safety detector: {e}")
            return False
    
    def screen_text(self, text: str) -> SafetyResult:
        """
        Screen text for safety violations.
        
        Args:
            text: Input text to screen
            
        Returns:
            SafetyResult with screening results
        """
        start_time = datetime.now()
        
        if not self.enabled:
            return SafetyResult(
                has_violations=False,
                violations_found=[],
                action_taken="disabled",
                processing_time_ms=0.0
            )
        
        if not self._ensure_initialized():
            return SafetyResult(
                has_violations=False,
                violations_found=[],
                action_taken="error",
                error="Lexicons not available",
                processing_time_ms=0.0
            )
        
        try:
            violations_found = []
            
            # Check each lexicon
            for lexicon_name, patterns in self._compiled_patterns.items():
                for pattern in patterns:
                    matches = pattern.finditer(text)
                    for match in matches:
                        violation = {
                            "lexicon": lexicon_name,
                            "pattern": pattern.pattern,
                            "start": match.start(),
                            "end": match.end(),
                            "text": match.group(),
                            "severity": self._get_severity(lexicon_name, match.group())
                        }
                        violations_found.append(violation)
            
            has_violations = len(violations_found) > 0
            
            # Determine action taken
            action_taken = "none"
            if has_violations:
                if self.mode == "monitor":
                    action_taken = "logged"
                elif self.mode == "graduated":
                    action_taken = "warned"
                elif self.mode == "strict":
                    action_taken = "blocked"
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return SafetyResult(
                has_violations=has_violations,
                violations_found=violations_found,
                action_taken=action_taken,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Safety screening failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return SafetyResult(
                has_violations=False,
                violations_found=[],
                action_taken="error",
                error=str(e),
                processing_time_ms=processing_time
            )
    
    def _get_severity(self, lexicon_name: str, matched_text: str) -> str:
        """Determine severity of a violation."""
        if lexicon_name == "profanity":
            return "low"
        elif lexicon_name == "hate_skeleton":
            return "high"
        else:
            return "medium"
    
    def get_evidence(self, result: SafetyResult) -> Dict[str, Any]:
        """
        Generate evidence for audit trail.
        
        Args:
            result: Safety screening result
            
        Returns:
            Evidence dictionary for audit chain
        """
        # Group violations by lexicon
        violations_by_lexicon = {}
        for violation in result.violations_found:
            lexicon = violation["lexicon"]
            if lexicon not in violations_by_lexicon:
                violations_by_lexicon[lexicon] = []
            violations_by_lexicon[lexicon].append(violation)
        
        return {
            "safety": {
                "enabled": self.enabled,
                "mode": self.mode,
                "has_violations": result.has_violations,
                "total_violations": len(result.violations_found),
                "violations_by_lexicon": {
                    lexicon: len(violations) 
                    for lexicon, violations in violations_by_lexicon.items()
                },
                "action_taken": result.action_taken,
                "processing_time_ms": result.processing_time_ms,
                "error": result.error,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def should_block(self, result: SafetyResult) -> bool:
        """
        Determine if action should be blocked based on safety result.
        
        Args:
            result: Safety screening result
            
        Returns:
            True if action should be blocked
        """
        if not self.enabled or self.mode == "monitor":
            return False
        
        if result.error:
            return False  # Don't block on errors in monitor mode
        
        # Block if violations found and mode is strict
        if self.mode == "strict" and result.has_violations:
            return True
        
        # Block if high severity violations in graduated mode
        if self.mode == "graduated" and result.has_violations:
            high_severity_violations = [
                v for v in result.violations_found 
                if v.get("severity") == "high"
            ]
            if high_severity_violations:
                return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get detector status for diagnostics."""
        return {
            "name": "SafetyDetector",
            "enabled": self.enabled,
            "mode": self.mode,
            "lexicons_loaded": list(self._lexicon_data.keys()),
            "total_patterns": sum(len(patterns) for patterns in self._compiled_patterns.values()),
            "action": self.action,
            "version": "v2.5.0"
        }
