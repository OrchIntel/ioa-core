"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
This module provides a basic classifier for EU AI Act compliance, categorizing
AI systems into risk levels (minimal, limited, high, unacceptable) based on
use case characteristics and technical capabilities.
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """EU AI Act risk levels."""
    MINIMAL = "minimal"
    LIMITED = "limited"
    HIGH = "high"
    UNACCEPTABLE = "unacceptable"

@dataclass
class RiskAssessment:
    """Result of AI Act risk assessment."""
    risk_level: RiskLevel
    confidence: float
    factors: List[str]
    recommendations: List[str]
    compliance_requirements: List[str]

class EUAIActClassifier:
    """
    Basic EU AI Act compliance classifier.
    
    Provides risk assessment for AI systems based on use case characteristics,
    technical capabilities, and deployment context.
    """
    
    def __init__(self):
        """Initialize the EU AI Act classifier."""
        self.risk_patterns = self._initialize_risk_patterns()
        logger.info("EU AI Act Classifier initialized")
    
    def _initialize_risk_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize risk assessment patterns."""
        return {
            "unacceptable": {
                "patterns": [
                    "social_scoring",
                    "real_time_biometric_identification",
                    "manipulative_behavior",
                    "emotion_recognition_workplace",
                    "predictive_policing"
                ],
                "requirements": [
                    "Prohibited under EU AI Act",
                    "Cannot be deployed in EU",
                    "Requires immediate cessation"
                ]
            },
            "high": {
                "patterns": [
                    "critical_infrastructure",
                    "education",
                    "employment",
                    "essential_services",
                    "law_enforcement",
                    "migration_control"
                ],
                "requirements": [
                    "Conformity assessment required",
                    "Risk management system",
                    "Quality management system",
                    "Post-market monitoring",
                    "Human oversight"
                ]
            },
            "limited": {
                "patterns": [
                    "chatbots",
                    "deepfakes",
                    "emotion_recognition",
                    "biometric_categorization"
                ],
                "requirements": [
                    "Transparency obligations",
                    "User notification",
                    "Human oversight option"
                ]
            },
            "minimal": {
                "patterns": [
                    "spam_filters",
                    "recommendation_systems",
                    "video_games",
                    "general_purpose_ai"
                ],
                "requirements": [
                    "Basic transparency",
                    "Code of conduct adherence"
                ]
            }
        }
    
    def classify_system(self, 
                       use_case: str,
                       technical_capabilities: List[str],
                       deployment_context: str,
                       user_impact: str) -> RiskAssessment:
        """
        Classify an AI system according to EU AI Act risk levels.
        
        Args:
            use_case: Description of the AI system's use case
            technical_capabilities: List of technical capabilities
            deployment_context: Where/how the system is deployed
            user_impact: Impact on end users
            
        Returns:
            RiskAssessment with risk level and compliance requirements
        """
        try:
            # Analyze risk factors
            risk_factors = []
            recommendations = []
            
            # Check for unacceptable patterns
            if any(pattern in use_case.lower() for pattern in self.risk_patterns["unacceptable"]["patterns"]):
                risk_level = RiskLevel.UNACCEPTABLE
                compliance_requirements = self.risk_patterns["unacceptable"]["requirements"]
                risk_factors.append("Matches prohibited use case patterns")
                recommendations.append("Immediate cessation required")
            
            # Check for high-risk patterns
            elif any(pattern in use_case.lower() for pattern in self.risk_patterns["high"]["patterns"]):
                risk_level = RiskLevel.HIGH
                compliance_requirements = self.risk_patterns["high"]["requirements"]
                risk_factors.append("Critical infrastructure or essential services")
                recommendations.append("Implement comprehensive compliance framework")
            
            # Check for limited-risk patterns
            elif any(pattern in use_case.lower() for pattern in self.risk_patterns["limited"]["patterns"]):
                risk_level = RiskLevel.LIMITED
                compliance_requirements = self.risk_patterns["limited"]["requirements"]
                risk_factors.append("Specific transparency and oversight requirements")
                recommendations.append("Implement transparency measures")
            
            # Default to minimal risk
            else:
                risk_level = RiskLevel.MINIMAL
                compliance_requirements = self.risk_patterns["minimal"]["requirements"]
                risk_factors.append("Standard AI system with minimal risk")
                recommendations.append("Follow basic transparency guidelines")
            
            # Additional context-based factors
            if "healthcare" in use_case.lower() or "medical" in use_case.lower():
                risk_factors.append("Healthcare domain - additional compliance requirements")
                recommendations.append("Review healthcare-specific regulations")
            
            if "financial" in use_case.lower() or "banking" in use_case.lower():
                risk_factors.append("Financial services domain")
                recommendations.append("Review financial services compliance requirements")
            
            # Calculate confidence based on pattern matching
            confidence = min(0.95, 0.7 + (len(risk_factors) * 0.05))
            
            assessment = RiskAssessment(
                risk_level=risk_level,
                confidence=confidence,
                factors=risk_factors,
                recommendations=recommendations,
                compliance_requirements=compliance_requirements
            )
            
            logger.info(f"AI Act classification: {risk_level.value} risk (confidence: {confidence:.2f})")
            return assessment
            
        except Exception as e:
            logger.error(f"AI Act classification failed: {e}")
            # Return minimal risk as safe fallback
            return RiskAssessment(
                risk_level=RiskLevel.MINIMAL,
                confidence=0.5,
                factors=["Classification failed - using safe fallback"],
                recommendations=["Review system manually for compliance"],
                compliance_requirements=self.risk_patterns["minimal"]["requirements"]
            )
    
    def get_compliance_checklist(self, risk_level: RiskLevel) -> Dict[str, Any]:
        """
        Get compliance checklist for a specific risk level.
        
        Args:
            risk_level: Risk level to get checklist for
            
        Returns:
            Compliance checklist with requirements and deadlines
        """
        checklists = {
            RiskLevel.UNACCEPTABLE: {
                "status": "Prohibited",
                "action": "Immediate cessation",
                "deadline": "Immediate",
                "penalties": "Up to 7% of global annual turnover"
            },
            RiskLevel.HIGH: {
                "status": "High compliance required",
                "action": "Implement comprehensive framework",
                "deadline": "Before market deployment",
                "penalties": "Up to 6% of global annual turnover"
            },
            RiskLevel.LIMITED: {
                "status": "Limited compliance required",
                "action": "Implement transparency measures",
                "deadline": "Before market deployment",
                "penalties": "Up to 4% of global annual turnover"
            },
            RiskLevel.MINIMAL: {
                "status": "Minimal compliance required",
                "action": "Follow transparency guidelines",
                "deadline": "Ongoing",
                "penalties": "Up to 2% of global annual turnover"
            }
        }
        
        return checklists.get(risk_level, checklists[RiskLevel.MINIMAL])

# Factory function
def create_ai_act_classifier() -> EUAIActClassifier:
    """Create an EU AI Act classifier instance."""
    return EUAIActClassifier()

# Export key classes
__all__ = [
    "EUAIActClassifier",
    "RiskLevel", 
    "RiskAssessment",
    "create_ai_act_classifier"
]
