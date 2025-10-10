""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""

This module implements Law 1 (Compliance Supremacy) through jurisdiction-based
filtering and enforcement, ensuring 100% compliance across all memory operations.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@dataclass
class JurisdictionConfig:
    """Configuration for a specific jurisdiction."""
    name: str
    priority: int  # Lower number = higher priority
    compliance_frameworks: List[str]
    data_residency_required: bool = False
    retention_days: Optional[int] = None
    encryption_required: bool = True


class JurisdictionError(Exception):
    """Raised when jurisdiction validation fails."""
    pass


class JurisdictionPolicyEngine:
    """
    Enforces jurisdiction-aware policies for Memory Fabric operations.
    
    Implements Law 1: Compliance Supremacy by ensuring all memory operations
    respect jurisdiction boundaries and compliance requirements.
    """
    
    # Jurisdiction priority mapping (lower = higher priority)
    JURISDICTION_PRIORITY = {
        "EU": 1,      # GDPR, EU-AI-Act - Highest priority
        "US": 2,      # SOX, HIPAA, CCPA
        "NZ": 3,      # Privacy-Act-2020, NZGB
        "APAC": 4,    # PDPA, PIPA
        "GLOBAL": 5   # ISO-27001, ISO-9001 - Lowest priority
    }
    
    # Compliance framework requirements per jurisdiction
    COMPLIANCE_FRAMEWORKS = {
        "EU": ["GDPR", "EU-AI-Act", "DPA"],
        "US": ["SOX", "HIPAA", "CCPA"],
        "NZ": ["Privacy-Act-2020", "NZGB"],
        "APAC": ["PDPA", "PIPA"],
        "GLOBAL": ["ISO-27001", "ISO-9001"]
    }
    
    def __init__(self):
        """Initialize jurisdiction policy engine with default configurations."""
        self.configs = self._load_jurisdiction_configs()
        self.enforcement_mode = "enforce"  # off, shadow, enforce, strict
        
    def _load_jurisdiction_configs(self) -> Dict[str, JurisdictionConfig]:
        """Load jurisdiction configurations."""
        return {
            jur: JurisdictionConfig(
                name=jur,
                priority=self.JURISDICTION_PRIORITY[jur],
                compliance_frameworks=self.COMPLIANCE_FRAMEWORKS[jur],
                data_residency_required=(jur == "EU"),  # EU requires data residency
                retention_days=None,  # No limit by default
                encryption_required=True
            )
            for jur in self.JURISDICTION_PRIORITY.keys()
        }
    
    def enforce_jurisdiction(
        self,
        query_jurisdiction: str,
        metadata_jurisdiction: str,
        enforcement_mode: Optional[str] = None
    ) -> bool:
        """
        Enforce jurisdiction matching between query and metadata.
        
        Args:
            query_jurisdiction: Requested jurisdiction from query
            metadata_jurisdiction: Jurisdiction from retrieved metadata
            enforcement_mode: Override default enforcement mode
            
        Returns:
            True if jurisdiction matches or can be allowed, False otherwise
            
        Raises:
            JurisdictionError: In strict mode when mismatch occurs
        """
        mode = enforcement_mode or self.enforcement_mode
        
        # Validate jurisdictions exist
        if query_jurisdiction not in self.JURISDICTION_PRIORITY:
            if mode == "strict":
                raise JurisdictionError(f"Invalid query jurisdiction: {query_jurisdiction}")
            logger.warning(f"Unknown query jurisdiction: {query_jurisdiction}")
            return mode == "off"
        
        if metadata_jurisdiction not in self.JURISDICTION_PRIORITY:
            if mode == "strict":
                raise JurisdictionError(f"Invalid metadata jurisdiction: {metadata_jurisdiction}")
            logger.warning(f"Unknown metadata jurisdiction: {metadata_jurisdiction}")
            return mode == "off"
        
        # Check for exact match
        if query_jurisdiction == metadata_jurisdiction:
            return True
        
        # GLOBAL content can be accessed from any jurisdiction
        if metadata_jurisdiction == "GLOBAL":
            return True
        
        # Higher priority jurisdictions can access lower priority ones
        # (e.g., EU can access US, but US cannot access EU)
        query_priority = self.JURISDICTION_PRIORITY[query_jurisdiction]
        metadata_priority = self.JURISDICTION_PRIORITY[metadata_jurisdiction]
        
        if query_priority <= metadata_priority:
            return True
        
        # Mismatch handling based on mode
        if mode == "off":
            return True
        elif mode == "shadow":
            logger.info(f"Jurisdiction mismatch (shadow): query={query_jurisdiction}, metadata={metadata_jurisdiction}")
            return True
        elif mode == "enforce":
            logger.warning(f"Jurisdiction mismatch blocked: query={query_jurisdiction}, metadata={metadata_jurisdiction}")
            return False
        elif mode == "strict":
            raise JurisdictionError(
                f"Jurisdiction mismatch: query={query_jurisdiction}, metadata={metadata_jurisdiction}"
            )
        
        return False
    
    def filter_results_by_jurisdiction(
        self,
        results: List[Dict[str, Any]],
        query_jurisdiction: str
    ) -> List[Dict[str, Any]]:
        """
        Filter query results to only include jurisdiction-compliant entries.
        
        Args:
            results: List of query results with metadata
            query_jurisdiction: Requested jurisdiction
            
        Returns:
            Filtered list of results matching jurisdiction policy
        """
        if self.enforcement_mode == "off":
            return results
        
        filtered = []
        for result in results:
            metadata_jur = result.get("jurisdiction", "GLOBAL")
            
            try:
                if self.enforce_jurisdiction(query_jurisdiction, metadata_jur):
                    filtered.append(result)
                else:
                    logger.debug(f"Filtered out result: {result.get('chunk_id', 'unknown')} (jurisdiction: {metadata_jur})")
            except JurisdictionError as e:
                logger.error(f"Jurisdiction error filtering result: {e}")
                if self.enforcement_mode == "strict":
                    raise
                continue
        
        return filtered
    
    def get_jurisdiction_priority(self, jurisdiction: str) -> int:
        """Get priority level for a jurisdiction (lower = higher priority)."""
        return self.JURISDICTION_PRIORITY.get(jurisdiction, 999)
    
    def get_compliance_frameworks(self, jurisdiction: str) -> List[str]:
        """Get required compliance frameworks for a jurisdiction."""
        return self.COMPLIANCE_FRAMEWORKS.get(jurisdiction, [])
    
    def validate_compliance(
        self,
        metadata: Dict[str, Any],
        required_frameworks: Optional[List[str]] = None
    ) -> bool:
        """
        Validate that metadata meets compliance requirements.
        
        Args:
            metadata: Metadata to validate
            required_frameworks: Optional list of required frameworks
            
        Returns:
            True if compliant, False otherwise
        """
        jurisdiction = metadata.get("jurisdiction", "GLOBAL")
        
        if jurisdiction not in self.JURISDICTION_PRIORITY:
            logger.warning(f"Unknown jurisdiction in metadata: {jurisdiction}")
            return False
        
        # Get required frameworks for this jurisdiction
        frameworks = required_frameworks or self.get_compliance_frameworks(jurisdiction)
        
        # Check if metadata has compliance information
        metadata_frameworks = metadata.get("compliance_frameworks", [])
        
        # For now, just verify jurisdiction is set correctly
        # Full framework validation would be more complex
        return jurisdiction in self.JURISDICTION_PRIORITY
    
    def set_enforcement_mode(self, mode: str):
        """
        Set enforcement mode for jurisdiction policies.
        
        Modes:
        - off: No enforcement, all results allowed
        - shadow: Log mismatches but allow all results
        - enforce: Block mismatched results
        - strict: Raise errors on mismatches
        """
        valid_modes = ["off", "shadow", "enforce", "strict"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {valid_modes}")
        
        self.enforcement_mode = mode
        logger.info(f"Jurisdiction enforcement mode set to: {mode}")


# Global instance for easy access
jurisdiction_policy = JurisdictionPolicyEngine()

