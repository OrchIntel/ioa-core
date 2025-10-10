""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# PATCH: Cursor-2025-01-27 DISPATCH-GPT-20250825-031 <memory engine modularization>

@dataclass
class RedactionRule:
    """Redaction rule configuration."""
    name: str
    pattern: str
    replacement: str = "[REDACTED]"
    description: str = ""
    enabled: bool = True
    priority: int = 0  # Higher priority rules are applied first

@dataclass
class RedactionResult:
    """Result of redaction operation."""
    original_content: str
    redacted_content: str
    redactions_applied: List[Dict[str, Any]]
    redaction_score: float  # 0.0 to 1.0, higher means more redaction

class RedactionEngine:
    """Engine for redacting PII/PHI from content."""
    
    def __init__(self, enable_hipaa: bool = True, enable_gdpr: bool = True):
        """
        Initialize redaction engine.
        
        Args:
            enable_hipaa: Enable HIPAA-compliant redaction
            enable_gdpr: Enable GDPR-compliant redaction
        """
        self.logger = logging.getLogger(__name__)
        self.enable_hipaa = enable_hipaa
        self.enable_gdpr = enable_gdpr
        
        # Initialize redaction rules
        self._rules: List[RedactionRule] = []
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize default redaction rules."""
        # HIPAA rules
        if self.enable_hipaa:
            self._add_hipaa_rules()
        
        # GDPR rules
        if self.enable_gdpr:
            self._add_gdpr_rules()
        
        # Compile patterns for efficiency
        self._compile_patterns()
    
    def _add_hipaa_rules(self):
        """Add HIPAA-compliant redaction rules."""
        hipaa_rules = [
            RedactionRule(
                name="ssn",
                pattern=r"\b\d{3}-\d{2}-\d{4}\b",
                replacement="***-**-****",
                description="Social Security Number",
                priority=100
            ),
            RedactionRule(
                name="phone",
                pattern=r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
                replacement="***-***-****",
                description="Phone number",
                priority=90
            ),
            RedactionRule(
                name="email",
                pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                replacement="***@***.***",
                description="Email address",
                priority=80
            ),
            RedactionRule(
                name="credit_card",
                pattern=r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
                replacement="****-****-****-****",
                description="Credit card number",
                priority=95
            ),
            RedactionRule(
                name="date_of_birth",
                pattern=r"\b(?:birth|born|DOB|date of birth)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
                replacement="[DATE OF BIRTH]",
                description="Date of birth",
                priority=85
            ),
            RedactionRule(
                name="medical_record",
                pattern=r"\b(?:MRN|medical record|patient ID)[:\s]+(\d+)\b",
                replacement="[MEDICAL RECORD]",
                description="Medical record number",
                priority=75
            )
        ]
        
        for rule in hipaa_rules:
            self._rules.append(rule)
    
    def _add_gdpr_rules(self):
        """Add GDPR-compliant redaction rules."""
        gdpr_rules = [
            RedactionRule(
                name="ip_address",
                pattern=r"\b(?:IPv4|IP)[:\s]+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b",
                replacement="[IP ADDRESS]",
                description="IP address",
                priority=70
            ),
            RedactionRule(
                name="location",
                pattern=r"\b(?:address|location|GPS)[:\s]+([A-Za-z0-9\s,.-]+)\b",
                replacement="[LOCATION]",
                description="Physical location",
                priority=65
            ),
            RedactionRule(
                name="biometric",
                pattern=r"\b(?:fingerprint|retina|face|voice|gait)[:\s]+(\w+)\b",
                replacement="[BIOMETRIC DATA]",
                description="Biometric data",
                priority=60
            ),
            RedactionRule(
                name="national_id",
                pattern=r"\b(?:passport|national ID|driver license)[:\s]+([A-Z0-9]+)\b",
                replacement="[NATIONAL ID]",
                description="National identification",
                priority=85
            )
        ]
        
        for rule in gdpr_rules:
            self._rules.append(rule)
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        for rule in self._rules:
            if rule.enabled:
                try:
                    self._compiled_patterns[rule.name] = re.compile(rule.pattern, re.IGNORECASE)
                except re.error as e:
                    self.logger.warning(f"Invalid regex pattern for rule {rule.name}: {e}")
    
    def add_rule(self, rule: RedactionRule):
        """Add a custom redaction rule."""
        self._rules.append(rule)
        
        # Recompile patterns
        if rule.enabled:
            try:
                self._compiled_patterns[rule.name] = re.compile(rule.pattern, re.IGNORECASE)
            except re.error as e:
                self.logger.warning(f"Invalid regex pattern for custom rule {rule.name}: {e}")
    
    def redact_content(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> RedactionResult:
        """
        Redact PII/PHI from content.
        
        Args:
            content: Content to redact
            metadata: Optional metadata for context
            
        Returns:
            RedactionResult with redacted content and details
        """
        if not content:
            return RedactionResult(
                original_content=content,
                redacted_content=content,
                redactions_applied=[],
                redaction_score=0.0
            )
        
        redacted_content = content
        redactions_applied = []
        
        # Sort rules by priority (highest first)
        sorted_rules = sorted(self._rules, key=lambda x: x.priority, reverse=True)
        
        for rule in sorted_rules:
            if not rule.enabled or rule.name not in self._compiled_patterns:
                continue
            
            pattern = self._compiled_patterns[rule.name]
            matches = list(pattern.finditer(redacted_content))
            
            if matches:
                # Apply redaction
                for match in reversed(matches):  # Reverse to maintain positions
                    start, end = match.span()
                    redacted_content = (
                        redacted_content[:start] + 
                        rule.replacement + 
                        redacted_content[end:]
                    )
                
                # Record redaction
                redactions_applied.append({
                    "rule_name": rule.name,
                    "pattern": rule.pattern,
                    "replacement": rule.replacement,
                    "description": rule.description,
                    "matches_found": len(matches),
                    "priority": rule.priority
                })
        
        # Calculate redaction score
        redaction_score = self._calculate_redaction_score(content, redacted_content, redactions_applied)
        
        return RedactionResult(
            original_content=content,
            redacted_content=redacted_content,
            redactions_applied=redactions_applied,
            redaction_score=redaction_score
        )
    
    def _calculate_redaction_score(self, original: str, redacted: str, redactions: List[Dict[str, Any]]) -> float:
        """Calculate redaction score (0.0 to 1.0)."""
        if not redactions:
            return 0.0
        
        # Base score from number of redactions
        base_score = min(len(redactions) / 10.0, 1.0)
        
        # Bonus for high-priority redactions
        priority_bonus = sum(
            redaction["priority"] / 100.0 
            for redaction in redactions
        ) / len(redactions)
        
        # Content change ratio
        if len(original) > 0:
            change_ratio = abs(len(redacted) - len(original)) / len(original)
            change_score = min(change_ratio * 2, 1.0)
        else:
            change_score = 0.0
        
        # Combine scores
        final_score = (base_score * 0.4 + priority_bonus * 0.3 + change_score * 0.3)
        return min(final_score, 1.0)
    
    def get_redaction_summary(self, content: str) -> Dict[str, Any]:
        """Get a summary of potential redactions without applying them."""
        summary = {
            "content_length": len(content),
            "potential_redactions": [],
            "risk_level": "low"
        }
        
        total_risk = 0
        
        for rule in self._rules:
            if not rule.enabled or rule.name not in self._compiled_patterns:
                continue
            
            pattern = self._compiled_patterns[rule.name]
            matches = list(pattern.finditer(content))
            
            if matches:
                risk_score = rule.priority / 100.0
                total_risk += risk_score * len(matches)
                
                summary["potential_redactions"].append({
                    "rule_name": rule.name,
                    "description": rule.description,
                    "matches_found": len(matches),
                    "risk_score": risk_score
                })
        
        # Determine overall risk level
        if total_risk > 5.0:
            summary["risk_level"] = "high"
        elif total_risk > 2.0:
            summary["risk_level"] = "medium"
        
        summary["total_risk_score"] = total_risk
        
        return summary
    
    def enable_rule(self, rule_name: str):
        """Enable a redaction rule."""
        for rule in self._rules:
            if rule.name == rule_name:
                rule.enabled = True
                if rule.name not in self._compiled_patterns:
                    try:
                        self._compiled_patterns[rule.name] = re.compile(rule.pattern, re.IGNORECASE)
                    except re.error as e:
                        self.logger.warning(f"Invalid regex pattern for rule {rule.name}: {e}")
                break
    
    def disable_rule(self, rule_name: str):
        """Disable a redaction rule."""
        for rule in self._rules:
            if rule.name == rule_name:
                rule.enabled = False
                if rule.name in self._compiled_patterns:
                    del self._compiled_patterns[rule.name]
                break
    
    def list_rules(self) -> List[Dict[str, Any]]:
        """List all redaction rules with their status."""
        return [
            {
                "name": rule.name,
                "pattern": rule.pattern,
                "replacement": rule.replacement,
                "description": rule.description,
                "enabled": rule.enabled,
                "priority": rule.priority
            }
            for rule in self._rules
        ]
