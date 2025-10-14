# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# Part of IOA Core (Open Source Edition).

"""
Ethics Cartridge (Aletheia-inspired) – IOA Original

NOTE: Inspired by public ethics frameworks such as Aletheia v2.0 (CC BY-ND 4.0).
This is NOT a derivative or implementation of Aletheia; it uses IOA-original criteria names.

This module provides neutral, IOA-original ethics checking functions that can be
used as a starting point for runtime ethics governance in AI systems.

Attribution: Aletheia Framework v2.0 by Rolls-Royce Civil Aerospace (CC BY-ND 4.0)
Reference: https://www.rolls-royce.com/innovation/the-aletheia-framework.aspx
"""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class EthicsDecision:
    """Result of an ethics precheck evaluation."""
    allow: bool
    reasons: List[str]
    confidence: float = 1.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def contains_disallowed_pii(input_payload: Dict[str, Any]) -> bool:
    """
    Check if input contains personally identifiable information.
    
    This is a basic implementation - production systems should use
    specialized PII detection libraries.
    """
    if not isinstance(input_payload, dict):
        return False
    
    # Simple keyword-based PII detection
    pii_keywords = [
        'ssn', 'social security', 'credit card', 'passport',
        'driver license', 'phone number', 'email address'
    ]
    
    text_content = str(input_payload).lower()
    return any(keyword in text_content for keyword in pii_keywords)


def appears_deceptive(input_payload: Dict[str, Any]) -> bool:
    """
    Check if input appears to be attempting to deceive or manipulate.
    
    This is a basic implementation - production systems should use
    more sophisticated deception detection methods.
    """
    if not isinstance(input_payload, dict):
        return False
    
    # Simple deception pattern detection
    deception_patterns = [
        'ignore previous instructions', 'forget everything',
        'pretend to be', 'act as if', 'roleplay as'
    ]
    
    text_content = str(input_payload).lower()
    return any(pattern in text_content for pattern in deception_patterns)


def contains_harmful_content(input_payload: Dict[str, Any]) -> bool:
    """
    Check if input contains potentially harmful or inappropriate content.
    
    This is a basic implementation - production systems should use
    specialized content moderation libraries.
    """
    if not isinstance(input_payload, dict):
        return False
    
    # Simple harmful content detection
    harmful_keywords = [
        'violence', 'hate speech', 'discrimination', 'harassment',
        'illegal activities', 'harmful instructions'
    ]
    
    text_content = str(input_payload).lower()
    return any(keyword in text_content for keyword in harmful_keywords)


def violates_fairness_principles(input_payload: Dict[str, Any]) -> bool:
    """
    Check if input appears to violate fairness principles.
    
    This is a basic implementation - production systems should use
    more sophisticated bias detection methods.
    """
    if not isinstance(input_payload, dict):
        return False
    
    # Simple fairness violation detection
    unfair_patterns = [
        'discriminate against', 'treat differently based on',
        'bias toward', 'unfair advantage'
    ]
    
    text_content = str(input_payload).lower()
    return any(pattern in text_content for pattern in unfair_patterns)


def precheck(input_payload: Dict[str, Any], strict_mode: bool = False) -> EthicsDecision:
    """
    Perform ethics precheck on input payload.
    
    Args:
        input_payload: The input data to evaluate
        strict_mode: If True, use stricter evaluation criteria
        
    Returns:
        EthicsDecision with allow/reject decision and reasons
    """
    reasons = []
    confidence = 1.0
    
    # Check for PII violations
    if contains_disallowed_pii(input_payload):
        reasons.append("PII risk detected")
        confidence *= 0.8
    
    # Check for deception attempts
    if appears_deceptive(input_payload):
        reasons.append("Transparency risk - potential deception")
        confidence *= 0.7
    
    # Check for harmful content
    if contains_harmful_content(input_payload):
        reasons.append("Harmful content detected")
        confidence *= 0.5
    
    # Check for fairness violations
    if violates_fairness_principles(input_payload):
        reasons.append("Fairness principle violation")
        confidence *= 0.6
    
    # In strict mode, any violation blocks the request
    if strict_mode and reasons:
        allow = False
    else:
        # Allow if confidence is above threshold
        allow = confidence >= 0.5
    
    return EthicsDecision(
        allow=allow,
        reasons=reasons,
        confidence=confidence,
        metadata={
            "strict_mode": strict_mode,
            "checks_performed": [
                "pii_detection",
                "deception_detection", 
                "harmful_content_detection",
                "fairness_violation_detection"
            ]
        }
    )


def validate_ethics_policy(policy_config: Dict[str, Any]) -> bool:
    """
    Validate that an ethics policy configuration is properly formed.
    
    Args:
        policy_config: Policy configuration dictionary
        
    Returns:
        True if policy is valid, False otherwise
    """
    required_fields = ["name", "version", "thresholds"]
    
    if not isinstance(policy_config, dict):
        return False
    
    for field in required_fields:
        if field not in policy_config:
            return False
    
    # Validate thresholds are numeric
    thresholds = policy_config.get("thresholds", {})
    if not isinstance(thresholds, dict):
        return False
    
    for key, value in thresholds.items():
        if not isinstance(value, (int, float)) or not (0 <= value <= 1):
            return False
    
    return True
