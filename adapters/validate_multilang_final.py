"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Multilingual validation for IOA entries with ONBOARD-001 integration
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
Multilingual Validation Module - Final Production Version

Provides comprehensive validation for IOA memory entries including:
- UTF-8 encoding validation with error recovery
- IOA schema v0.1.2 compliance checking
- Heuristic language detection for multiple languages
- Content quality assessment with confidence scoring
- ONBOARD-001 tenant isolation support

✅ ONBOARD-001 Features:
- Tenant-aware validation with isolation
- Enhanced error reporting and recovery
- Performance metrics integration
- Multi-language confidence scoring
"""

__version__ = "1.0.0"

import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ValidationConfig:
    """Configuration for multilingual validation with ONBOARD-001 support."""
    supported_languages: Set[str]
    strict_schema_validation: bool = True
    enable_content_analysis: bool = True
    log_validation_errors: bool = True
    max_error_details: int = 10
    tenant_isolation_enabled: bool = True


@dataclass
class LanguageDetectionResult:
    """Detailed language detection result."""
    detected_language: str
    confidence: float
    detected_scripts: List[str]
    character_analysis: Dict[str, int]


class ValidationError(Exception):
    """Base exception for validation operations."""
    pass


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails."""
    pass


class EncodingValidationError(ValidationError):
    """Raised when encoding validation fails."""
    pass


class MultilingualValidator:
    """
    Comprehensive multilingual validator for IOA entries with ONBOARD-001 integration.
    
    Validates content against IOA schema v0.1.2 requirements,
    performs UTF-8 encoding validation, and provides heuristic
    language detection with quality assessment and tenant isolation.
    
    ✅ ONBOARD-001 Features:
    - Tenant-aware validation processing
    - Enhanced error context and recovery
    - Performance metrics integration
    - Multi-tenant isolation support
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """Initialize multilingual validator with ONBOARD-001 support."""
        self.logger = logging.getLogger(__name__)
        
        # ONBOARD-001: Enhanced configuration
        self.config = config or ValidationConfig(
            supported_languages={"en", "es", "fa", "zh"},
            strict_schema_validation=True,
            enable_content_analysis=True,
            log_validation_errors=True,
            tenant_isolation_enabled=True
        )
        
        # IOA schema v0.1.2 required fields
        self.required_fields = {
            "id", "pattern_id", "variables", "metadata", 
            "feeling", "raw_ref"
        }
        
        # Enhanced language detection patterns for ONBOARD-001
        self.language_patterns = {
            "es": {
                "chars": "ñáéíóúü¿¡",
                "words": {"el", "la", "de", "que", "y", "en", "un", "es", "se", "no", "te"},
                "confidence_boost": 0.2
            },
            "fa": {
                "char_ranges": [(0x600, 0x6FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
                "words": {"و", "در", "به", "از", "که", "این", "با", "را", "بر"},
                "rtl": True,
                "confidence_boost": 0.3
            },
            "zh": {
                "char_ranges": [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x20000, 0x2A6DF)],
                "confidence_boost": 0.4
            },
            "en": {
                "words": {"the", "be", "to", "of", "and", "a", "in", "that", "have", "it"},
                "confidence_boost": 0.1
            }
        }
        
        # ONBOARD-001: Validation statistics with tenant tracking
        self.stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "language_detections": {},
            "common_errors": {},
            "tenant_stats": {}
        }

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of IOA memory entry with ONBOARD-001 enhancements.

        Args:
            entry: Dictionary representing IOA memory entry (may include tenant_id)

        Returns:
            Dictionary containing validation results with structure:
            {
                "is_valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "lang_detected": str,
                "lang_confidence": float,
                "quality_score": float,
                "validation_metadata": Dict[str, Any],
                "tenant_id": Optional[str]  # ONBOARD-001
            }
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "lang_detected": "unknown",
            "lang_confidence": 0.0,
            "quality_score": 1.0,
            "validation_metadata": {
                "timestamp": datetime.now().isoformat(),
                "validator_version": __version__,
                "validation_id": f"val_{id(entry)}",
                "onboard_001_enabled": True
            }
        }
        
        # ONBOARD-001: Extract tenant information
        tenant_id = entry.get("tenant_id") or entry.get("metadata", {}).get("tenant_id")
        if tenant_id:
            result["tenant_id"] = tenant_id
            result["validation_metadata"]["tenant_id"] = tenant_id
        
        try:
            self.stats["total_validations"] += 1
            
            # ONBOARD-001: Track tenant-specific stats
            if tenant_id:
                if tenant_id not in self.stats["tenant_stats"]:
                    self.stats["tenant_stats"][tenant_id] = {
                        "total": 0, "valid": 0, "invalid": 0
                    }
                self.stats["tenant_stats"][tenant_id]["total"] += 1
            
            # 1. UTF-8 Encoding Validation
            encoding_result = self._validate_encoding(entry)
            if not encoding_result["valid"]:
                result["errors"].extend(encoding_result["errors"])
                result["is_valid"] = False
            
            # 2. Schema Validation
            schema_result = self._validate_schema(entry)
            if not schema_result["valid"]:
                result["errors"].extend(schema_result["errors"])
                result["is_valid"] = False
            
            # 3. Enhanced Language Detection with ONBOARD-001 features
            if result["is_valid"] or not self.config.strict_schema_validation:
                lang_result = self._detect_language_enhanced(entry)
                result["lang_detected"] = lang_result["language"]
                result["lang_confidence"] = lang_result["confidence"]
                result["validation_metadata"]["language_analysis"] = lang_result["analysis"]
            
            # 4. Content Quality Assessment
            if self.config.enable_content_analysis:
                quality_result = self._assess_content_quality(entry)
                result["quality_score"] = quality_result["score"]
                result["warnings"].extend(quality_result["warnings"])
            
            # 5. Update Statistics
            if result["is_valid"]:
                self.stats["successful_validations"] += 1
                lang = result["lang_detected"]
                self.stats["language_detections"][lang] = \
                    self.stats["language_detections"].get(lang, 0) + 1
                
                # ONBOARD-001: Update tenant stats
                if tenant_id:
                    self.stats["tenant_stats"][tenant_id]["valid"] += 1
            else:
                self.stats["failed_validations"] += 1
                if tenant_id:
                    self.stats["tenant_stats"][tenant_id]["invalid"] += 1
                
                for error in result["errors"]:
                    error_type = error.split(":")[0]
                    self.stats["common_errors"][error_type] = \
                        self.stats["common_errors"].get(error_type, 0) + 1
            
            # 6. Enhanced Logging for ONBOARD-001
            if self.config.log_validation_errors and result["errors"]:
                entry_id = entry.get('id', 'unknown')
                tenant_context = f" [Tenant: {tenant_id}]" if tenant_id else ""
                self.logger.warning(
                    f"Validation failed for entry {entry_id}{tenant_context}: "
                    f"{'; '.join(result['errors'][:3])}..."
                )
            
            return result
            
        except Exception as e:
            # Handle unexpected validation errors with ONBOARD-001 context
            self.stats["failed_validations"] += 1
            if tenant_id:
                self.stats["tenant_stats"][tenant_id]["invalid"] += 1
            
            error_msg = f"Validation error: {str(e)}"
            
            if self.config.log_validation_errors:
                tenant_context = f" [Tenant: {tenant_id}]" if tenant_id else ""
                self.logger.error(f"Critical validation failure{tenant_context}: {e}")
            
            return {
                "is_valid": False,
                "errors": [error_msg],
                "warnings": [],
                "lang_detected": "unknown",
                "lang_confidence": 0.0,
                "quality_score": 0.0,
                "tenant_id": tenant_id,
                "validation_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "validator_version": __version__,
                    "error": str(e),
                    "onboard_001_enabled": True
                }
            }

    def _validate_encoding(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate UTF-8 encoding with ONBOARD-001 enhancements."""
        result = {"valid": True, "errors": []}
        
        try:
            # Check raw_ref field specifically
            raw_ref = entry.get("raw_ref", "")
            
            if not isinstance(raw_ref, str):
                result["errors"].append("Encoding error: raw_ref must be string type")
                result["valid"] = False
            else:
                # Attempt UTF-8 encoding
                try:
                    raw_ref.encode("utf-8")
                except UnicodeEncodeError as e:
                    result["errors"].append(f"Encoding error: invalid UTF-8 in raw_ref: {e}")
                    result["valid"] = False
            
            # ONBOARD-001: Check additional fields for encoding issues
            string_fields = ["id", "pattern_id"]
            if "tenant_id" in entry:
                string_fields.append("tenant_id")
                
            for field in string_fields:
                if field in entry:
                    value = entry[field]
                    if isinstance(value, str):
                        try:
                            value.encode("utf-8")
                        except UnicodeEncodeError as e:
                            result["errors"].append(f"Encoding error: invalid UTF-8 in {field}: {e}")
                            result["valid"] = False
                            
        except Exception as e:
            result["errors"].append(f"Encoding validation failed: {e}")
            result["valid"] = False
            
        return result

    def _validate_schema(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate IOA schema v0.1.2 compliance with ONBOARD-001 support."""
        result = {"valid": True, "errors": []}
        
        try:
            # Check required fields
            missing_fields = self.required_fields - set(entry.keys())
            if missing_fields:
                result["errors"].append(f"Schema error: missing required fields: {missing_fields}")
                result["valid"] = False
            
            # ONBOARD-001: Enhanced field validation
            if "id" in entry and not isinstance(entry["id"], str):
                result["errors"].append("Schema error: 'id' must be string")
                result["valid"] = False
                
            if "pattern_id" in entry and not isinstance(entry["pattern_id"], str):
                result["errors"].append("Schema error: 'pattern_id' must be string")
                result["valid"] = False
                
            if "variables" in entry and not isinstance(entry["variables"], (dict, list)):
                result["errors"].append("Schema error: 'variables' must be dict or list")
                result["valid"] = False
                
            if "metadata" in entry and not isinstance(entry["metadata"], dict):
                result["errors"].append("Schema error: 'metadata' must be dict")
                result["valid"] = False
            
            # ONBOARD-001: Validate tenant_id if present
            if "tenant_id" in entry and not isinstance(entry["tenant_id"], str):
                result["errors"].append("Schema error: 'tenant_id' must be string")
                result["valid"] = False
                
            # Validate VAD feeling structure
            if "feeling" in entry:
                feeling = entry["feeling"]
                if isinstance(feeling, dict):
                    for vad_dim in ["valence", "arousal", "dominance"]:
                        if vad_dim in feeling:
                            value = feeling[vad_dim]
                            if not isinstance(value, (int, float)) or not (-1 <= value <= 1):
                                result["errors"].append(
                                    f"Schema error: feeling.{vad_dim} must be numeric in range [-1, 1]"
                                )
                                result["valid"] = False
                else:
                    result["errors"].append("Schema error: 'feeling' must be dict")
                    result["valid"] = False
                    
        except Exception as e:
            result["errors"].append(f"Schema validation failed: {e}")
            result["valid"] = False
            
        return result

    def _detect_language_enhanced(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced language detection with ONBOARD-001 confidence scoring."""
        raw_ref = entry.get("raw_ref", "")
        
        if not isinstance(raw_ref, str) or not raw_ref.strip():
            return {
                "language": "unknown",
                "confidence": 0.0,
                "analysis": {"error": "empty or invalid raw_ref"}
            }
        
        text = raw_ref.lower().strip()
        
        # ONBOARD-001: Enhanced character analysis
        char_analysis = {
            "total_chars": len(text),
            "latin_chars": 0,
            "arabic_chars": 0,
            "chinese_chars": 0,
            "numeric_chars": 0,
            "special_chars": 0
        }
        
        detected_scripts = []
        language_scores = {lang: 0.0 for lang in self.config.supported_languages}
        
        # Analyze characters with ONBOARD-001 enhancements
        for char in text:
            ord_val = ord(char)
            
            if char.isalpha():
                if ord_val <= 0x7F:  # ASCII Latin
                    char_analysis["latin_chars"] += 1
                elif 0x600 <= ord_val <= 0x6FF:  # Arabic/Persian
                    char_analysis["arabic_chars"] += 1
                    if "arabic" not in detected_scripts:
                        detected_scripts.append("arabic")
                elif 0x4E00 <= ord_val <= 0x9FFF:  # Chinese
                    char_analysis["chinese_chars"] += 1
                    if "chinese" not in detected_scripts:
                        detected_scripts.append("chinese")
            elif char.isdigit():
                char_analysis["numeric_chars"] += 1
            else:
                char_analysis["special_chars"] += 1
        
        if char_analysis["latin_chars"] > 0 and "latin" not in detected_scripts:
            detected_scripts.append("latin")
        
        # Enhanced language scoring with ONBOARD-001 confidence boosts
        
        # Spanish detection
        if "es" in self.config.supported_languages:
            spanish_chars = sum(1 for c in text if c in self.language_patterns["es"]["chars"])
            spanish_words = sum(1 for word in self.language_patterns["es"]["words"] if word in text)
            base_score = (spanish_chars * 0.3 + spanish_words * 0.7) / max(1, len(text.split()))
            language_scores["es"] = base_score + self.language_patterns["es"]["confidence_boost"] * base_score
        
        # Persian/Farsi detection
        if "fa" in self.config.supported_languages:
            persian_chars = sum(
                1 for char in text 
                for start, end in self.language_patterns["fa"]["char_ranges"]
                if start <= ord(char) <= end
            )
            if char_analysis["total_chars"] > 0:
                base_score = persian_chars / char_analysis["total_chars"]
                language_scores["fa"] = base_score + self.language_patterns["fa"]["confidence_boost"] * base_score
        
        # Chinese detection
        if "zh" in self.config.supported_languages:
            chinese_chars = sum(
                1 for char in text
                for start, end in self.language_patterns["zh"]["char_ranges"]
                if start <= ord(char) <= end
            )
            if char_analysis["total_chars"] > 0:
                base_score = chinese_chars / char_analysis["total_chars"]
                language_scores["zh"] = base_score + self.language_patterns["zh"]["confidence_boost"] * base_score
        
        # English detection (default for Latin script)
        if "en" in self.config.supported_languages:
            english_words = sum(1 for word in self.language_patterns["en"]["words"] if word in text)
            if char_analysis["latin_chars"] > 0:
                base_score = (char_analysis["latin_chars"] * 0.5 + english_words * 0.5) / max(1, len(text.split()))
                language_scores["en"] = base_score + self.language_patterns["en"]["confidence_boost"] * base_score
        
        # Determine best match
        best_language = max(language_scores, key=language_scores.get)
        best_confidence = language_scores[best_language]
        
        # Apply confidence thresholds
        if best_confidence < 0.1:
            best_language = "unknown"
            best_confidence = 0.0
        elif best_confidence > 1.0:
            best_confidence = 1.0
        
        return {
            "language": best_language,
            "confidence": round(best_confidence, 3),
            "analysis": {
                "detected_scripts": detected_scripts,
                "character_analysis": char_analysis,
                "all_scores": {k: round(v, 3) for k, v in language_scores.items()},
                "onboard_001_enhanced": True
            }
        }

    def _assess_content_quality(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Assess content quality with ONBOARD-001 enhancements."""
        warnings = []
        quality_factors = []
        
        # Check content length
        raw_ref = entry.get("raw_ref", "")
        if isinstance(raw_ref, str):
            if len(raw_ref.strip()) < 3:
                warnings.append("Quality warning: content is very short")
                quality_factors.append(0.5)
            elif len(raw_ref) > 10000:
                warnings.append("Quality warning: content is very long")
                quality_factors.append(0.8)
            else:
                quality_factors.append(1.0)
        else:
            quality_factors.append(0.0)
        
        # ONBOARD-001: Enhanced metadata completeness check
        metadata = entry.get("metadata", {})
        if isinstance(metadata, dict):
            expected_metadata = ["speaker", "timestamp", "tone"]
            # ONBOARD-001: Add tenant_id to expected metadata if tenant isolation enabled
            if self.config.tenant_isolation_enabled and "tenant_id" in entry:
                expected_metadata.append("tenant_id")
                
            present_metadata = sum(1 for key in expected_metadata if key in metadata)
            metadata_score = present_metadata / len(expected_metadata)
            quality_factors.append(metadata_score)
            
            if metadata_score < 0.5:
                warnings.append("Quality warning: metadata is incomplete")
        else:
            quality_factors.append(0.0)
        
        # Check VAD feeling completeness
        feeling = entry.get("feeling", {})
        if isinstance(feeling, dict):
            vad_complete = all(dim in feeling for dim in ["valence", "arousal", "dominance"])
            quality_factors.append(1.0 if vad_complete else 0.7)
            
            if not vad_complete:
                warnings.append("Quality warning: VAD feeling incomplete")
        else:
            quality_factors.append(0.0)
        
        # Calculate overall quality score
        overall_score = sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
        
        return {
            "score": round(overall_score, 3),
            "warnings": warnings
        }

    def get_validation_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get validation statistics with ONBOARD-001 tenant filtering."""
        total = self.stats["total_validations"]
        success_rate = self.stats["successful_validations"] / max(1, total)
        
        base_stats = {
            **self.stats,
            "success_rate": round(success_rate, 3),
            "supported_languages": list(self.config.supported_languages),
            "validator_version": __version__,
            "onboard_001_enabled": True
        }
        
        # ONBOARD-001: Filter by tenant if specified
        if tenant_id and tenant_id in self.stats["tenant_stats"]:
            tenant_stats = self.stats["tenant_stats"][tenant_id]
            tenant_success_rate = tenant_stats["valid"] / max(1, tenant_stats["total"])
            
            base_stats["tenant_specific"] = {
                "tenant_id": tenant_id,
                **tenant_stats,
                "success_rate": round(tenant_success_rate, 3)
            }
        
        return base_stats

    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self.stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "language_detections": {},
            "common_errors": {},
            "tenant_stats": {}
        }


def create_validator(config: Optional[ValidationConfig] = None) -> MultilingualValidator:
    """Factory function for ONBOARD-001 integration."""
    return MultilingualValidator(config)


# Utility functions for common validation patterns
def validate_single_field(value: Any, field_name: str, expected_type: type) -> List[str]:
    """
    Validate a single field against expected type.

    Args:
        value: Value to validate
        field_name: Name of the field for error reporting
        expected_type: Expected Python type

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if not isinstance(value, expected_type):
        errors.append(f"Field '{field_name}' must be of type {expected_type.__name__}")
    
    return errors


def validate_vad_score(value: Any, dimension: str) -> List[str]:
    """
    Validate VAD emotional score.

    Args:
        value: Value to validate
        dimension: VAD dimension name

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if not isinstance(value, (int, float)):
        errors.append(f"VAD {dimension} must be numeric")
    elif not (-1 <= value <= 1):
        errors.append(f"VAD {dimension} must be in range [-1, 1]")
    
    return errors


# Export classes for ONBOARD-001
__all__ = [
    'MultilingualValidator',
    'ValidationConfig',
    'LanguageDetectionResult',
    'ValidationError',
    'SchemaValidationError',
    'EncodingValidationError',
    'create_validator',
    'validate_single_field',
    'validate_vad_score'
]
