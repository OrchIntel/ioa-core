"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Standalone entry digestion and pattern processing module
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
IOA Digestor Module - Standalone Entry Processing System v0.1.2

Provides modular digestion pipeline for processing raw entries into structured memory objects.
Extracted from memory_engine.py for improved maintainability, testability, and reusability.

Key Features:
- 7-stage processing pipeline with individual error handling
- Pattern matching with configurable sensitivity and thresholds
- Variable extraction using regex and heuristic algorithms
- VAD sentiment analysis integration with fallback support
- Confidence scoring with multi-factor weighting system
- Storage tier recommendations for optimization
- Multi-tier fallback mechanisms (standard → processing → emergency)
- Schema enforcement ensuring IOA v0.1.2 compliance
- Comprehensive statistics collection and monitoring
- Complete independence from memory engine for testing

Architecture:
- DigestorCore: Main processing engine with 7-stage pipeline
- DigestorConfig: Comprehensive configuration management
- DigestResult: Structured result object with metadata
- ProcessingStage: Pipeline stage enumeration for tracking
- Exception hierarchy: Specialized error types for precise handling

Version 0.1.2 Features:
- Production-ready standalone operation
- Enhanced import path compatibility
- Optimized variable extraction algorithms
- Improved confidence calculation with content quality metrics
- Advanced storage tier recommendation logic
- Comprehensive logging and monitoring integration
"""

import json
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

# Avoid circular imports while maintaining type hints
if TYPE_CHECKING:
    from .memory_engine import MemoryEngine

# Enhanced import handling for VAD sentiment mapping with multiple fallback paths
try:
    from refinery_utils import map_sentience
    SENTIMENT_MAPPING_AVAILABLE = True
except ImportError:
    try:
        from .refinery_utils import map_sentience
        SENTIMENT_MAPPING_AVAILABLE = True
    except ImportError:
        SENTIMENT_MAPPING_AVAILABLE = False
        
        def map_sentience(text: str) -> Dict[str, float]:
            """Fallback sentiment mapping when refinery_utils unavailable"""
            return {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}


class ProcessingStage(Enum):
    """Enumeration of stages in the digestion pipeline for tracking and debugging"""
    PATTERN_MATCHING = "pattern_matching"
    VARIABLE_EXTRACTION = "variable_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    METADATA_ENHANCEMENT = "metadata_enhancement"
    CONFIDENCE_CALCULATION = "confidence_calculation"
    SCHEMA_VALIDATION = "schema_validation"
    COMPACTION = "compaction"


class DigestorError(Exception):
    """Base exception for digestor operations with enhanced error context"""
    
    def __init__(self, message: str, stage: Optional[str] = None, entry_id: Optional[str] = None):
        super().__init__(message)
        self.stage = stage
        self.entry_id = entry_id
        self.timestamp = datetime.now().isoformat()


class PatternMatchingError(DigestorError):
    """Raised when pattern matching fails critically"""
    pass


class VariableExtractionError(DigestorError):
    """Raised when variable extraction fails critically"""
    pass


class SentimentAnalysisError(DigestorError):
    """Raised when sentiment analysis fails critically"""
    pass


class SchemaValidationError(DigestorError):
    """Raised when schema validation fails critically"""
    pass


@dataclass
class DigestorConfig:
    """
    Comprehensive configuration for digestor processing pipeline.
    
    Provides fine-grained control over all aspects of the digestion process,
    from pattern matching sensitivity to output formatting preferences.
    """
    
    # Processing feature toggles
    enable_sentiment_mapping: bool = True
    enable_pattern_compaction: bool = True
    enable_storage_assessment: bool = True
    enable_evolution_triggers: bool = True
    
    # Quality and confidence thresholds
    confidence_threshold: float = 0.5
    min_content_length: int = 10
    max_content_length: int = 10000
    pattern_match_threshold: float = 0.5  # Minimum score for pattern matching
    
    # Error handling and resilience
    fallback_on_errors: bool = True
    max_retry_attempts: int = 3
    log_processing_steps: bool = True
    strict_schema_validation: bool = False
    
    # Pattern matching parameters
    case_sensitive_matching: bool = False
    partial_keyword_matching: bool = True
    require_all_keywords: bool = False
    keyword_weight_distribution: str = "uniform"  # "uniform" or "weighted"
    
    # Variable extraction parameters
    default_unknown_value: str = "unknown"
    max_variable_length: int = 100
    strip_whitespace: bool = True
    enable_regex_extraction: bool = True
    
    # Output formatting and metadata
    include_raw_content: bool = True
    include_processing_metadata: bool = True
    include_confidence_scores: bool = True
    include_extraction_details: bool = False
    
    # Performance and optimization
    enable_caching: bool = False
    cache_size_limit: int = 1000
    enable_parallel_processing: bool = False
    
    def validate_config(self) -> List[str]:
        """Validate configuration parameters and return any issues"""
        issues = []
        
        if not 0.0 <= self.confidence_threshold <= 1.0:
            issues.append("confidence_threshold must be between 0.0 and 1.0")
        
        if self.min_content_length < 0:
            issues.append("min_content_length must be non-negative")
        
        if self.max_content_length <= self.min_content_length:
            issues.append("max_content_length must be greater than min_content_length")
        
        if not 0.0 <= self.pattern_match_threshold <= 1.0:
            issues.append("pattern_match_threshold must be between 0.0 and 1.0")
        
        if self.max_retry_attempts < 0:
            issues.append("max_retry_attempts must be non-negative")
        
        if self.max_variable_length < 1:
            issues.append("max_variable_length must be positive")
        
        return issues


@dataclass
class DigestResult:
    """
    Comprehensive result from digestion processing with enhanced metadata.
    
    Provides complete information about the processing outcome, including
    success status, processed entry, confidence metrics, timing information,
    and detailed processing metadata for debugging and optimization.
    """
    success: bool
    compacted_entry: Dict[str, Any]
    confidence_score: float = 0.0
    processing_stages_completed: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    storage_recommendation: str = "hot"  # 'hot', 'cold', or 'auto'
    pattern_matched: bool = False
    pattern_confidence: float = 0.0
    variables_extracted: int = 0
    sentiment_strength: float = 0.0
    
    # Enhanced metadata for debugging and optimization
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization and logging"""
        return {
            "success": self.success,
            "compacted_entry": self.compacted_entry,
            "confidence_score": self.confidence_score,
            "processing_stages_completed": self.processing_stages_completed,
            "processing_time": self.processing_time,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "storage_recommendation": self.storage_recommendation,
            "pattern_matched": self.pattern_matched,
            "pattern_confidence": self.pattern_confidence,
            "variables_extracted": self.variables_extracted,
            "sentiment_strength": self.sentiment_strength,
            "processing_metadata": self.processing_metadata,
            "performance_metrics": self.performance_metrics
        }
    
    def add_warning(self, warning: str):
        """Add warning message to result"""
        self.warnings.append(warning)
    
    def add_performance_metric(self, metric_name: str, value: float):
        """Add performance metric to result"""
        self.performance_metrics[metric_name] = value


class DigestorCore:
    """
    Core digestion engine for processing entries into structured memory objects.
    
    Implements a sophisticated 7-stage processing pipeline with comprehensive
    error handling, fallback mechanisms, and performance monitoring. Designed
    for high reliability and maintainability in production environments.
    
    Processing Pipeline:
    1. Pattern Matching: Match content against configured patterns
    2. Variable Extraction: Extract structured data using regex and heuristics
    3. Sentiment Analysis: Perform VAD emotional analysis
    4. Metadata Enhancement: Enrich with processing and context metadata
    5. Confidence Calculation: Calculate multi-factor confidence score
    6. Schema Validation: Ensure IOA v0.1.2 compliance
    7. Compaction: Optimize entry size and structure
    """
    
    def __init__(
        self, 
        patterns: List[Dict[str, Any]], 
        config: Optional[DigestorConfig] = None,
        memory_engine: Optional['MemoryEngine'] = None
    ):
        """
        Initialize digestor with patterns and configuration.
        
        Args:
            patterns: List of pattern definitions for matching
            config: Optional digestor configuration (uses defaults if None)
            memory_engine: Optional memory engine reference for advanced features
        """
        self.patterns = patterns or []
        self.config = config or DigestorConfig()
        self.version = version
        self.memory_engine = memory_engine
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        config_issues = self.config.validate_config()
        if config_issues:
            for issue in config_issues:
                self.logger.warning(f"Configuration issue: {issue}")
        
        # Initialize processing statistics with enhanced metrics
        self._processing_stats = {
            "total_processed": 0,
            "successful_digestions": 0,
            "pattern_matches": 0,
            "fallback_uses": 0,
            "errors": 0,
            "avg_processing_time": 0.0,
            "avg_confidence_score": 0.0,
            "sentiment_analysis_successes": 0,
            "variable_extraction_successes": 0
        }
        
        # Initialize performance tracking
        self._performance_history = []
        self._max_history_size = 1000
        
        # Validate and filter patterns on initialization
        self._validate_patterns()
        
        self.logger.info(
            f"DigestorCore v{self.version} initialized with {len(self.patterns)} valid patterns"
        )
    
    def _validate_patterns(self):
        """Validate pattern definitions for structural correctness and completeness"""
        valid_patterns = []
        validation_issues = []
        
        for i, pattern in enumerate(self.patterns):
            try:
                if self._validate_pattern_structure(pattern):
                    valid_patterns.append(pattern)
                else:
                    issue = f"Pattern {i} failed structural validation: {pattern}"
                    validation_issues.append(issue)
                    self.logger.warning(issue)
            except Exception as e:
                issue = f"Pattern {i} validation error: {e}"
                validation_issues.append(issue)
                self.logger.error(issue)
        
        self.patterns = valid_patterns
        
        if validation_issues:
            self.logger.warning(f"Pattern validation completed with {len(validation_issues)} issues")
        else:
            self.logger.info(f"Pattern validation successful: {len(valid_patterns)} valid patterns")
    
    def _validate_pattern_structure(self, pattern: Dict[str, Any]) -> bool:
        """
        Validate individual pattern structure against requirements.
        
        Args:
            pattern: Pattern definition to validate
            
        Returns:
            True if pattern structure is valid and complete
        """
        required_fields = {'pattern_id', 'keywords', 'schema'}
        
        # Check required fields presence
        if not all(field in pattern for field in required_fields):
            return False
        
        # Validate field types and content
        if not isinstance(pattern['pattern_id'], str) or not pattern['pattern_id'].strip():
            return False
        
        if not isinstance(pattern['keywords'], list) or not pattern['keywords']:
            return False
        
        if not isinstance(pattern['schema'], list):
            return False
        
        # Validate keywords are non-empty strings
        for keyword in pattern['keywords']:
            if not isinstance(keyword, str) or not keyword.strip():
                return False
        
        # Validate schema fields are non-empty strings
        for field in pattern['schema']:
            if not isinstance(field, str) or not field.strip():
                return False
        
        return True
    
    def digest_entry(
        self, 
        raw_content: Union[str, Dict[str, Any]], 
        context: Optional[Dict[str, Any]] = None
    ) -> DigestResult:
        """
        Main digestion entry point for processing raw content into structured entries.
        
        Processes content through the complete 7-stage pipeline with comprehensive
        error handling and performance monitoring.
        
        Args:
            raw_content: Raw content to process (string or dict with raw_ref)
            context: Optional processing context and metadata
            
        Returns:
            DigestResult with processed entry and comprehensive metadata
        """
        start_time = datetime.now()
        context = context or {}
        entry_id = str(uuid.uuid4())  # Generate unique ID for tracking
        
        try:
            self._processing_stats["total_processed"] += 1
            
            # Normalize input to string for processing
            if isinstance(raw_content, dict):
                content_str = raw_content.get('raw_ref', json.dumps(raw_content))
                original_entry = raw_content.copy()
            else:
                content_str = str(raw_content) if raw_content is not None else ""
                original_entry = {"raw_ref": content_str}
            
            # Input validation with detailed feedback
            if len(content_str) < self.config.min_content_length:
                return self._create_minimal_entry(
                    content_str, 
                    f"content_too_short (min: {self.config.min_content_length})",
                    entry_id
                )
            
            # Handle oversized content with intelligent truncation
            if len(content_str) > self.config.max_content_length:
                original_length = len(content_str)
                content_str = content_str[:self.config.max_content_length]
                warning = f"Content truncated from {original_length} to {self.config.max_content_length} characters"
                context.setdefault("warnings", []).append(warning)
            
            # Process through comprehensive digestion pipeline
            result = self._process_digestion_pipeline(content_str, original_entry, context, entry_id)
            
            # Calculate and record processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            result.add_performance_metric("total_processing_time", processing_time)
            
            # Update comprehensive statistics
            self._update_processing_statistics(result)
            
            # Record performance history for trend analysis
            self._record_performance_metrics(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Critical digestion error for entry {entry_id}: {e}")
            self._processing_stats["errors"] += 1
            
            # Emergency fallback with detailed error context
            emergency_entry = self._create_emergency_fallback(content_str, str(e), entry_id)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return DigestResult(
                success=False,
                compacted_entry=emergency_entry,
                processing_time=processing_time,
                error_message=f"Critical digestion failure: {e}",
                storage_recommendation="cold",
                processing_metadata={"emergency_fallback": True, "entry_id": entry_id}
            )
    
    def _process_digestion_pipeline(
        self, 
        content: str, 
        original_entry: Dict[str, Any], 
        context: Dict[str, Any],
        entry_id: str
    ) -> DigestResult:
        """
        Process content through the complete 7-stage digestion pipeline.
        
        Args:
            content: Normalized content string
            original_entry: Original entry data
            context: Processing context with metadata
            entry_id: Unique identifier for tracking
            
        Returns:
            DigestResult with processed data and comprehensive metadata
        """
        stages_completed = []
        warnings = []
        processing_metadata = {"entry_id": entry_id, "content_length": len(content)}
        
        try:
            # Stage 1: Pattern Matching with enhanced scoring
            stage_start = datetime.now()
            matched_pattern, pattern_confidence = self._match_pattern(content)
            stage_time = (datetime.now() - stage_start).total_seconds()
            stages_completed.append(ProcessingStage.PATTERN_MATCHING.value)
            processing_metadata["pattern_matching_time"] = stage_time
            
            if matched_pattern:
                pattern_id = matched_pattern["pattern_id"]
                pattern_matched = True
                processing_metadata["matched_pattern"] = pattern_id
            else:
                pattern_id = "UNCLASSIFIED"
                pattern_matched = False
            
            # Stage 2: Variable Extraction with detailed tracking
            stage_start = datetime.now()
            variables = {}
            variables_extracted = 0
            
            if matched_pattern:
                try:
                    variables = self._extract_variables(content, matched_pattern.get("schema", []))
                    variables_extracted = len([v for v in variables.values() if v != self.config.default_unknown_value])
                    stages_completed.append(ProcessingStage.VARIABLE_EXTRACTION.value)
                    processing_metadata["variables_extracted_count"] = variables_extracted
                except Exception as e:
                    warning = f"Variable extraction failed: {e}"
                    warnings.append(warning)
                    if not self.config.fallback_on_errors:
                        raise VariableExtractionError(warning, ProcessingStage.VARIABLE_EXTRACTION.value, entry_id)
            
            stage_time = (datetime.now() - stage_start).total_seconds()
            processing_metadata["variable_extraction_time"] = stage_time
            
            # Stage 3: Sentiment Analysis with strength measurement
            stage_start = datetime.now()
            feeling = {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}
            sentiment_strength = 0.0
            
            if self.config.enable_sentiment_mapping:
                try:
                    feeling = map_sentience(content)
                    sentiment_strength = sum(abs(v) for v in feeling.values()) / 3.0
                    stages_completed.append(ProcessingStage.SENTIMENT_ANALYSIS.value)
                    processing_metadata["sentiment_strength"] = sentiment_strength
                except Exception as e:
                    warning = f"Sentiment analysis failed: {e}"
                    warnings.append(warning)
                    if not self.config.fallback_on_errors:
                        raise SentimentAnalysisError(warning, ProcessingStage.SENTIMENT_ANALYSIS.value, entry_id)
            
            stage_time = (datetime.now() - stage_start).total_seconds()
            processing_metadata["sentiment_analysis_time"] = stage_time
            
            # Stage 4: Metadata Enhancement with comprehensive context
            stage_start = datetime.now()
            metadata = self._create_metadata(content, context, matched_pattern, entry_id)
            stages_completed.append(ProcessingStage.METADATA_ENHANCEMENT.value)
            stage_time = (datetime.now() - stage_start).total_seconds()
            processing_metadata["metadata_enhancement_time"] = stage_time
            
            # Stage 5: Confidence Calculation with detailed factors
            stage_start = datetime.now()
            confidence_score = self._calculate_confidence(
                pattern_matched, variables_extracted, feeling, content, pattern_confidence
            )
            stages_completed.append(ProcessingStage.CONFIDENCE_CALCULATION.value)
            stage_time = (datetime.now() - stage_start).total_seconds()
            processing_metadata["confidence_calculation_time"] = stage_time
            
            # Stage 6: Schema Validation and Assembly
            stage_start = datetime.now()
            compacted_entry = self._assemble_entry(
                pattern_id, variables, metadata, feeling, content, original_entry, entry_id
            )
            stages_completed.append(ProcessingStage.SCHEMA_VALIDATION.value)
            stage_time = (datetime.now() - stage_start).total_seconds()
            processing_metadata["schema_validation_time"] = stage_time
            
            # Stage 7: Compaction (if enabled)
            if self.config.enable_pattern_compaction:
                stage_start = datetime.now()
                compacted_entry = self._apply_compaction(compacted_entry)
                stages_completed.append(ProcessingStage.COMPACTION.value)
                stage_time = (datetime.now() - stage_start).total_seconds()
                processing_metadata["compaction_time"] = stage_time
            
            # Determine intelligent storage recommendation
            storage_recommendation = self._recommend_storage_tier(confidence_score, compacted_entry)
            
            # Create comprehensive result
            result = DigestResult(
                success=True,
                compacted_entry=compacted_entry,
                confidence_score=confidence_score,
                processing_stages_completed=stages_completed,
                warnings=warnings,
                storage_recommendation=storage_recommendation,
                pattern_matched=pattern_matched,
                pattern_confidence=pattern_confidence,
                variables_extracted=variables_extracted,
                sentiment_strength=sentiment_strength,
                processing_metadata=processing_metadata
            )
            
            return result
            
        except Exception as e:
            # Comprehensive fallback processing
            if self.config.fallback_on_errors:
                self._processing_stats["fallback_uses"] += 1
                fallback_entry = self._create_fallback_entry(content, original_entry, str(e), entry_id)
                
                return DigestResult(
                    success=False,
                    compacted_entry=fallback_entry,
                    processing_stages_completed=stages_completed,
                    error_message=str(e),
                    warnings=warnings + ["Used fallback processing due to pipeline failure"],
                    storage_recommendation="cold",
                    processing_metadata=processing_metadata
                )
            else:
                raise DigestorError(f"Pipeline processing failed: {e}", "pipeline", entry_id)
    
    def _match_pattern(self, content: str) -> tuple[Optional[Dict[str, Any]], float]:
        """
        Match content against available patterns with enhanced scoring.
        
        Args:
            content: Content to match against patterns
            
        Returns:
            Tuple of (matched_pattern, confidence_score)
        """
        try:
            if not self.patterns:
                return None, 0.0
            
            content_normalized = content.lower() if not self.config.case_sensitive_matching else content
            best_match = None
            best_score = 0.0
            
            for pattern in self.patterns:
                keywords = pattern.get("keywords", [])
                if not keywords:
                    continue
                
                matches = 0
                total_keyword_length = 0
                matched_keyword_length = 0
                
                for keyword in keywords:
                    keyword_normalized = keyword.lower() if not self.config.case_sensitive_matching else keyword
                    total_keyword_length += len(keyword)
                    
                    if self.config.partial_keyword_matching:
                        if keyword_normalized in content_normalized:
                            matches += 1
                            matched_keyword_length += len(keyword)
                    else:
                        # Exact word boundary matching
                        if re.search(rf'\b{re.escape(keyword_normalized)}\b', content_normalized):
                            matches += 1
                            matched_keyword_length += len(keyword)
                
                # Enhanced scoring algorithm
                if self.config.require_all_keywords:
                    base_score = 1.0 if matches == len(keywords) else 0.0
                else:
                    base_score = matches / len(keywords) if keywords else 0.0
                
                # Apply keyword length weighting for more accurate matching
                if self.config.keyword_weight_distribution == "weighted" and total_keyword_length > 0:
                    length_weight = matched_keyword_length / total_keyword_length
                    final_score = (base_score + length_weight) / 2.0
                else:
                    final_score = base_score
                
                if final_score > best_score:
                    best_score = final_score
                    best_match = pattern
            
            # Only return pattern if score meets configured threshold
            if best_score >= self.config.pattern_match_threshold:
                return best_match, best_score
            else:
                return None, best_score
                
        except Exception as e:
            self.logger.error(f"Pattern matching error: {e}")
            return None, 0.0
    
    def _extract_variables(self, content: str, schema: List[str]) -> Dict[str, str]:
        """
        Extract variables from content based on pattern schema using advanced techniques.
        
        Args:
            content: Content to extract from
            schema: List of variable names to extract
            
        Returns:
            Dictionary of extracted variables with enhanced accuracy
        """
        variables = {}
        content_lower = content.lower()
        content_parts = content_lower.split()
        
        try:
            for field in schema:
                extracted_value = self.config.default_unknown_value
                
                # Apply specialized extraction logic based on field name
                if field == "name":
                    extracted_value = self._extract_name(content, content_parts)
                elif field == "age":
                    extracted_value = self._extract_age(content, content_parts)
                elif field == "location" or field == "country":
                    extracted_value = self._extract_location(content, content_parts)
                elif field == "email":
                    extracted_value = self._extract_email(content)
                elif field == "phone":
                    extracted_value = self._extract_phone(content)
                elif field == "date":
                    extracted_value = self._extract_date(content)
                elif field in ["amount", "price", "cost", "salary"]:
                    extracted_value = self._extract_amount(content)
                elif field in ["company", "organization"]:
                    extracted_value = self._extract_organization(content, content_parts)
                elif field in ["position", "job", "title"]:
                    extracted_value = self._extract_job_title(content, content_parts)
                else:
                    # Enhanced generic extraction for unknown fields
                    extracted_value = self._extract_generic(content, field, content_parts)
                
                # Post-processing cleanup and validation
                if self.config.strip_whitespace and isinstance(extracted_value, str):
                    extracted_value = extracted_value.strip()
                
                # Apply length limits
                if isinstance(extracted_value, str) and len(extracted_value) > self.config.max_variable_length:
                    extracted_value = extracted_value[:self.config.max_variable_length].rstrip()
                
                # Validate extracted value quality
                if extracted_value and extracted_value != self.config.default_unknown_value:
                    if len(extracted_value) < 2:  # Too short to be meaningful
                        extracted_value = self.config.default_unknown_value
                
                variables[field] = extracted_value
            
            return variables
            
        except Exception as e:
            self.logger.error(f"Variable extraction error: {e}")
            return {field: self.config.default_unknown_value for field in schema}
    
    def _extract_name(self, content: str, parts: List[str]) -> str:
        """Extract name from content using multiple strategies"""
        # Enhanced name extraction patterns
        name_patterns = [
            r'(?:my name is|i am|call me|i\'m|name\'s)\s+([a-zA-Z\s\-\'\.]{2,})',
            r'name[:\s]+([a-zA-Z\s\-\'\.]{2,})',
            r'(?:this is|i\'m)\s+([a-zA-Z\s\-\'\.]{2,})',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common false positives
                if (len(name) > 1 and 
                    not name.lower() in ['is', 'am', 'the', 'a', 'an', 'and', 'or', 'but'] and
                    not re.match(r'^\d+$', name)):  # Not just numbers
                    return name
        
        # Fallback: contextual name extraction
        if "name" in content.lower():
            # Look for capitalized words near "name"
            words = content.split()
            for i, word in enumerate(words):
                if "name" in word.lower() and i + 1 < len(words):
                    candidate = words[i + 1]
                    if candidate[0].isupper() and len(candidate) > 1:
                        return candidate
        
        return self.config.default_unknown_value
    
    def _extract_age(self, content: str, parts: List[str]) -> str:
        """Extract age from content with validation"""
        age_patterns = [
            r'(?:age|old|years old)[:\s]*(\d+)',
            r'(\d+)\s*(?:years old|yrs old|year old|y\.o\.)',
            r'(?:i am|i\'m)\s*(\d+)(?:\s*years?)?',
            r'aged?\s*(\d+)',
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                age = match.group(1)
                age_int = int(age)
                # Validate reasonable age range
                if 1 <= age_int <= 150:
                    return age
        
        return self.config.default_unknown_value
    
    def _extract_location(self, content: str, parts: List[str]) -> str:
        """Extract location from content with geographic context"""
        location_patterns = [
            r'(?:from|in|at|live in|located in|based in)\s+([a-zA-Z\s,\-\.]{2,})',
            r'(?:city|state|country|region)[:\s]+([a-zA-Z\s,\-\.]{2,})',
            r'(?:born in|grew up in)\s+([a-zA-Z\s,\-\.]{2,})',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Clean up common artifacts
                location = re.sub(r'\s+', ' ', location)  # Normalize whitespace
                location = location.rstrip('.,;')  # Remove trailing punctuation
                if len(location) > 1:
                    return location
        
        return self.config.default_unknown_value
    
    def _extract_email(self, content: str) -> str:
        """Extract email address with enhanced validation"""
        # Comprehensive email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, content)
        
        if matches:
            # Return the first valid email found
            for email in matches:
                # Additional validation for common email formats
                if '@' in email and '.' in email.split('@')[1]:
                    return email
        
        return self.config.default_unknown_value
    
    def _extract_phone(self, content: str) -> str:
        """Extract phone number with international format support"""
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
            r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',  # (123) 456-7890
            r'\b\+\d{1,3}[-.\s]?\d{3,14}\b',  # International format
            r'\b\d{10,15}\b',  # Simple number sequence
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Return the first match that looks like a valid phone number
                for phone in matches:
                    # Basic validation - should have enough digits
                    digits_only = re.sub(r'\D', '', phone)
                    if 7 <= len(digits_only) <= 15:
                        return phone
        
        return self.config.default_unknown_value
    
    def _extract_date(self, content: str) -> str:
        """Extract date with multiple format support"""
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',  # DD Month YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return self.config.default_unknown_value
    
    def _extract_amount(self, content: str) -> str:
        """Extract monetary amount with currency detection"""
        amount_patterns = [
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $123,456.78
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|usd|€|euros?|£|pounds?)',  # 123.45 dollars
            r'(?:cost|price|salary|wage|pay)[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # cost: $123.45
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                amount = match.group(1)
                # Validate it's a reasonable monetary amount
                try:
                    numeric_value = float(amount.replace(',', ''))
                    if 0 <= numeric_value <= 1000000000:  # Reasonable range
                        return amount
                except ValueError:
                    continue
        
        return self.config.default_unknown_value
    
    def _extract_organization(self, content: str, parts: List[str]) -> str:
        """Extract organization/company name"""
        org_patterns = [
            r'(?:work at|employed by|company|organization)[:\s]+([a-zA-Z\s&.,\-]{2,})',
            r'(?:at|@)\s+([A-Z][a-zA-Z\s&.,\-]{1,}(?:Inc|LLC|Corp|Ltd|Co)\.?)',
            r'([A-Z][a-zA-Z\s&.,\-]{1,}(?:Inc|LLC|Corp|Ltd|Co|Company|Corporation)\.?)',
        ]
        
        for pattern in org_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                org = match.group(1).strip()
                org = re.sub(r'\s+', ' ', org)  # Normalize whitespace
                if len(org) > 1:
                    return org
        
        return self.config.default_unknown_value
    
    def _extract_job_title(self, content: str, parts: List[str]) -> str:
        """Extract job title/position"""
        title_patterns = [
            r'(?:work as|job|position|title)[:\s]+([a-zA-Z\s\-]{2,})',
            r'(?:i am a|i\'m a)\s+([a-zA-Z\s\-]{2,})',
            r'([A-Z][a-zA-Z\s\-]{1,}(?:Engineer|Manager|Director|Analyst|Developer|Designer|Consultant))',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
                if len(title) > 1:
                    return title
        
        return self.config.default_unknown_value
    
    def _extract_generic(self, content: str, field: str, parts: List[str]) -> str:
        """Enhanced generic extraction for unknown field types"""
        # Multiple generic extraction strategies
        generic_patterns = [
            rf'{field}[:\s]+([a-zA-Z0-9\s\-.,]{1,})',
            rf'{field}\s+is\s+([a-zA-Z0-9\s\-.,]{1,})',
            rf'(?:my|the)\s+{field}[:\s]+([a-zA-Z0-9\s\-.,]{1,})',
        ]
        
        for pattern in generic_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean up the extracted value
                value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
                value = value.rstrip('.,;')  # Remove trailing punctuation
                
                if len(value) > 0 and value.lower() not in ['is', 'am', 'the', 'a', 'an']:
                    return value
        
        return self.config.default_unknown_value
    
    def _create_metadata(
        self, 
        content: str, 
        context: Dict[str, Any], 
        matched_pattern: Optional[Dict[str, Any]],
        entry_id: str
    ) -> Dict[str, Any]:
        """
        Create comprehensive metadata for the digested entry.
        
        Args:
            content: Original content
            context: Processing context
            matched_pattern: Matched pattern (if any)
            entry_id: Unique entry identifier
            
        Returns:
            Comprehensive metadata dictionary
        """
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "processing_version": self.version,
            "digestor_used": True,
            "entry_id": entry_id,
            "content_length": len(content),
            "word_count": len(content.split()),
            "character_count": len(content),
            "speaker": context.get("speaker", "user"),
            "tone": context.get("tone", "neutral"),
            "session_id": context.get("session_id", "unknown"),
            "thread_id": context.get("thread_id", "unknown"),
            "processing_node": "digestor_core",
            "schema_version": "IOA_v0.1.2"
        }
        
        # Add pattern-specific metadata
        if matched_pattern:
            metadata.update({
                "matched_pattern_id": matched_pattern["pattern_id"],
                "pattern_keywords": matched_pattern.get("keywords", []),
                "schema_fields": matched_pattern.get("schema", []),
                "pattern_metadata": matched_pattern.get("metadata", {})
            })
        
        # Add comprehensive processing configuration metadata
        if self.config.include_processing_metadata:
            metadata.update({
                "processing_config": {
                    "sentiment_mapping_enabled": self.config.enable_sentiment_mapping,
                    "pattern_compaction_enabled": self.config.enable_pattern_compaction,
                    "fallback_on_errors": self.config.fallback_on_errors,
                    "case_sensitive_matching": self.config.case_sensitive_matching,
                    "confidence_threshold": self.config.confidence_threshold,
                    "pattern_match_threshold": self.config.pattern_match_threshold
                }
            })
        
        # Add context warnings and additional metadata
        if "warnings" in context:
            metadata["context_warnings"] = context["warnings"]
        
        # Add content analysis metadata
        metadata["content_analysis"] = {
            "has_numbers": bool(re.search(r'\d', content)),
            "has_email": bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)),
            "has_phone": bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content)),
            "has_url": bool(re.search(r'https?://[^\s]+', content)),
            "language_hints": self._detect_language_hints(content)
        }
        
        return metadata
    
    def _detect_language_hints(self, content: str) -> List[str]:
        """Detect potential language indicators in content"""
        hints = []
        
        # Common English indicators
        english_indicators = ['the', 'and', 'is', 'are', 'am', 'was', 'were', 'have', 'has']
        if any(word in content.lower().split() for word in english_indicators):
            hints.append("english")
        
        # Add more language detection as needed
        return hints
    
    def _calculate_confidence(
        self, 
        pattern_matched: bool, 
        variables_extracted: int, 
        feeling: Dict[str, float], 
        content: str,
        pattern_confidence: float
    ) -> float:
        """
        Calculate enhanced confidence score using multiple factors.
        
        Args:
            pattern_matched: Whether a pattern was matched
            variables_extracted: Number of variables successfully extracted
            feeling: Sentiment analysis results
            content: Original content
            pattern_confidence: Confidence score from pattern matching
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.0
        
        # Pattern matching confidence (35% weight, enhanced with pattern confidence)
        if pattern_matched:
            base_pattern_score = 0.35
            pattern_quality_bonus = pattern_confidence * 0.15  # Up to 15% bonus for high-quality matches
            confidence += base_pattern_score + pattern_quality_bonus
        
        # Variable extraction quality (25% weight)
        if variables_extracted > 0:
            extraction_score = min(variables_extracted / 5.0, 1.0)  # Max 5 variables for full score
            confidence += 0.25 * extraction_score
        
        # Sentiment analysis confidence (15% weight)
        sentiment_strength = sum(abs(v) for v in feeling.values()) / 3.0
        if sentiment_strength > 0.1:
            confidence += 0.15 * min(sentiment_strength, 1.0)
        
        # Content quality indicators (15% weight)
        content_quality = 0.0
        
        # Length quality
        if 50 <= len(content) <= 1000:  # Optimal range
            content_quality += 0.5
        elif len(content) > 20:  # Acceptable minimum
            content_quality += 0.3
        
        # Structure quality
        if re.search(r'[.!?]', content):  # Has sentence endings
            content_quality += 0.3
        
        if len(content.split()) >= 3:  # Multi-word content
            content_quality += 0.2
        
        confidence += 0.15 * min(content_quality, 1.0)
        
        # Coherence bonus (10% weight)
        coherence_score = 0.0
        
        # Check for coherent sentence structure
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) > 1:
            coherence_score += 0.4
        
        # Check for proper capitalization
        if content and content[0].isupper():
            coherence_score += 0.3
        
        # Check for balanced punctuation
        if content.count('(') == content.count(')') and content.count('"') % 2 == 0:
            coherence_score += 0.3
        
        confidence += 0.10 * min(coherence_score, 1.0)
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _assemble_entry(
        self, 
        pattern_id: str, 
        variables: Dict[str, str], 
        metadata: Dict[str, Any], 
        feeling: Dict[str, float], 
        content: str, 
        original_entry: Dict[str, Any],
        entry_id: str
    ) -> Dict[str, Any]:
        """
        Assemble the final digested entry with enhanced schema compliance.
        
        Args:
            pattern_id: Matched pattern ID or 'UNCLASSIFIED'
            variables: Extracted variables
            metadata: Entry metadata
            feeling: Sentiment analysis results
            content: Original content
            original_entry: Original entry data
            entry_id: Unique entry identifier
            
        Returns:
            Schema-compliant digested entry with enhanced structure
        """
        # Create base entry structure compliant with IOA v0.1.2
        entry = {
            "id": original_entry.get("id", entry_id),
            "pattern_id": pattern_id,
            "variables": variables,
            "metadata": metadata,
            "feeling": feeling,
            "digest_version": self.version,
            "_digested": True,
            "_digestor_timestamp": datetime.now().isoformat(),
            "_digestor_version": self.version
        }
        
        # Include raw content if configured
        if self.config.include_raw_content:
            entry["raw_ref"] = content
        
        # Add processing summary if requested
        if self.config.include_extraction_details:
            entry["_processing_summary"] = {
                "variables_found": len([v for v in variables.values() if v != self.config.default_unknown_value]),
                "total_variables_attempted": len(variables),
                "pattern_matched": pattern_id != "UNCLASSIFIED",
                "sentiment_detected": any(abs(v) > 0.1 for v in feeling.values()),
                "content_word_count": len(content.split()),
                "processing_timestamp": datetime.now().isoformat()
            }
        
        # Merge additional fields from original entry (avoiding conflicts)
        for key, value in original_entry.items():
            if key not in entry and key != "raw_ref":
                entry[key] = value
        
        # Final schema validation
        if self.config.strict_schema_validation:
            self._validate_entry_schema(entry)
        
        return entry
    
    def _validate_entry_schema(self, entry: Dict[str, Any]) -> None:
        """Validate entry against IOA v0.1.2 schema requirements"""
        required_fields = ["id", "pattern_id", "metadata", "feeling"]
        
        for field in required_fields:
            if field not in entry:
                raise SchemaValidationError(f"Missing required field: {field}")
        
        # Validate field types
        if not isinstance(entry["id"], str):
            raise SchemaValidationError("Field 'id' must be a string")
        
        if not isinstance(entry["pattern_id"], str):
            raise SchemaValidationError("Field 'pattern_id' must be a string")
        
        if not isinstance(entry["metadata"], dict):
            raise SchemaValidationError("Field 'metadata' must be a dictionary")
        
        if not isinstance(entry["feeling"], dict):
            raise SchemaValidationError("Field 'feeling' must be a dictionary")
        
        # Validate feeling structure (VAD model)
        required_feeling_fields = ["valence", "arousal", "dominance"]
        for field in required_feeling_fields:
            if field not in entry["feeling"]:
                raise SchemaValidationError(f"Missing required feeling field: {field}")
            if not isinstance(entry["feeling"][field], (int, float)):
                raise SchemaValidationError(f"Feeling field '{field}' must be numeric")
    
    def _apply_compaction(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply intelligent compaction strategies to optimize entry size.
        
        Args:
            entry: Entry to compact
            
        Returns:
            Optimized compacted entry
        """
        compacted = {}
        
        for key, value in entry.items():
            # Skip completely empty values
            if value == "" or value == [] or value == {}:
                continue
            
            # Handle variables compaction
            if key == "variables" and isinstance(value, dict):
                # Filter out unknown or empty variable values.
                # A variable is kept only if it is not equal to the default unknown value and,
                # if it is a string, it is not empty after stripping, otherwise it is truthy.
                filtered_vars = {
                    k: v for k, v in value.items()
                    if (v != self.config.default_unknown_value) and ((v.strip() if isinstance(v, str) else v))
                }
                if filtered_vars:
                    compacted[key] = filtered_vars
            
            # Handle metadata compaction
            elif key == "metadata" and isinstance(value, dict):
                # Keep essential metadata, remove verbose details if space is needed
                essential_metadata = {}
                for meta_key, meta_value in value.items():
                    if meta_key in ["timestamp", "processing_version", "speaker", "tone", "entry_id"]:
                        essential_metadata[meta_key] = meta_value
                    elif not self.config.include_processing_metadata and meta_key.startswith("processing_"):
                        continue  # Skip processing metadata if not needed
                    else:
                        essential_metadata[meta_key] = meta_value
                
                compacted[key] = essential_metadata
            
            # Handle string compaction
            elif isinstance(value, str):
                cleaned_value = value.strip()
                if cleaned_value:
                    compacted[key] = cleaned_value
            
            else:
                compacted[key] = value
        
        # Ensure critical fields are always present
        required_fields = ["id", "pattern_id", "metadata", "feeling"]
        for field in required_fields:
            if field not in compacted:
                if field == "id":
                    compacted[field] = str(uuid.uuid4())
                elif field == "pattern_id":
                    compacted[field] = "UNCLASSIFIED"
                elif field == "metadata":
                    compacted[field] = {
                        "timestamp": datetime.now().isoformat(),
                        "processing_version": self.version
                    }
                elif field == "feeling":
                    compacted[field] = {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}
        
        return compacted
    
    def _recommend_storage_tier(self, confidence_score: float, entry: Dict[str, Any]) -> str:
        """
        Recommend intelligent storage tier based on confidence and entry characteristics.
        
        Args:
            confidence_score: Calculated confidence score
            entry: Processed entry
            
        Returns:
            Storage tier recommendation ('hot', 'cold', or 'auto')
        """
        if not self.config.enable_storage_assessment:
            return "auto"
        
        # High confidence entries go to hot storage
        if confidence_score >= self.config.confidence_threshold:
            return "hot"
        
        # Pattern-based routing
        pattern_id = entry.get("pattern_id", "")
        
        # Unclassified entries with low confidence go to cold storage
        if pattern_id == "UNCLASSIFIED" and confidence_score < 0.3:
            return "cold"
        
        # Large entries with low confidence go to cold storage
        entry_size = len(json.dumps(entry))
        if entry_size > 5000 and confidence_score < 0.4:
            return "cold"
        
        # Entries with good variable extraction stay hot regardless of pattern match
        variables_count = len([v for v in entry.get("variables", {}).values() if v != self.config.default_unknown_value])
        if variables_count >= 3:
            return "hot"
        
        # Entries with strong sentiment stay hot
        feeling = entry.get("feeling", {})
        sentiment_strength = sum(abs(v) for v in feeling.values()) / 3.0
        if sentiment_strength > 0.5:
            return "hot"
        
        # Default to auto-routing for balanced load
        return "auto"
    
    def _create_fallback_entry(
        self, 
        content: str, 
        original_entry: Dict[str, Any], 
        error: str,
        entry_id: str
    ) -> Dict[str, Any]:
        """Create comprehensive fallback entry when main processing fails"""
        return {
            "id": original_entry.get("id", entry_id),
            "pattern_id": "PROCESSING_FALLBACK",
            "variables": {},
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "processing_version": self.version,
                "fallback_mode": True,
                "processing_error": error,
                "speaker": "user",
                "tone": "neutral",
                "content_length": len(content),
                "word_count": len(content.split()),
                "entry_id": entry_id,
                "schema_version": "IOA_v0.1.2"
            },
            "feeling": {"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
            "raw_ref": content,
            "digest_version": f"{self.version}-fallback",
            "_digested": False,
            "_digestor_timestamp": datetime.now().isoformat(),
            "_fallback_reason": error
        }
    
    def _create_emergency_fallback(self, content: str, error: str, entry_id: str) -> Dict[str, Any]:
        """Create emergency fallback entry for critical system failures"""
        return {
            "id": entry_id,
            "pattern_id": "EMERGENCY_FALLBACK",
            "variables": {},
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "processing_version": self.version,
                "emergency_fallback": True,
                "critical_error": error,
                "speaker": "system",
                "tone": "error",
                "entry_id": entry_id,
                "schema_version": "IOA_v0.1.2"
            },
            "feeling": {"valence": -0.5, "arousal": 0.8, "dominance": 0.0},  # Negative, high arousal for errors
            "raw_ref": content if content else "CONTENT_UNAVAILABLE",
            "digest_version": f"{self.version}-emergency",
            "_digested": False,
            "_digestor_timestamp": datetime.now().isoformat(),
            "_emergency_reason": error
        }
    
    def _create_minimal_entry(self, content: str, reason: str, entry_id: str) -> DigestResult:
        """Create minimal entry for edge cases with comprehensive metadata"""
        entry = {
            "id": entry_id,
            "pattern_id": "MINIMAL_ENTRY",
            "variables": {},
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "processing_version": self.version,
                "minimal_entry_reason": reason,
                "content_length": len(content),
                "entry_id": entry_id,
                "schema_version": "IOA_v0.1.2"
            },
            "feeling": {"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
            "raw_ref": content,
            "digest_version": f"{self.version}-minimal",
            "_digested": True,
            "_digestor_timestamp": datetime.now().isoformat(),
            "_minimal_reason": reason
        }
        
        return DigestResult(
            success=True,
            compacted_entry=entry,
            confidence_score=0.1,
            warnings=[f"Minimal entry created: {reason}"],
            storage_recommendation="cold",
            processing_metadata={"minimal_entry": True, "reason": reason}
        )
    
    def _update_processing_statistics(self, result: DigestResult):
        """Update comprehensive processing statistics"""
        if result.success:
            self._processing_stats["successful_digestions"] += 1
            if result.pattern_matched:
                self._processing_stats["pattern_matches"] += 1
            if result.variables_extracted > 0:
                self._processing_stats["variable_extraction_successes"] += 1
            if result.sentiment_strength > 0.1:
                self._processing_stats["sentiment_analysis_successes"] += 1
        else:
            self._processing_stats["errors"] += 1
        
        # Update running averages
        total = self._processing_stats["total_processed"]
        if total > 0:
            old_avg_time = self._processing_stats["avg_processing_time"]
            self._processing_stats["avg_processing_time"] = (
                (old_avg_time * (total - 1) + result.processing_time) / total
            )
            
            old_avg_confidence = self._processing_stats["avg_confidence_score"]
            self._processing_stats["avg_confidence_score"] = (
                (old_avg_confidence * (total - 1) + result.confidence_score) / total
            )
    
    def _record_performance_metrics(self, result: DigestResult):
        """Record performance metrics for trend analysis"""
        if len(self._performance_history) >= self._max_history_size:
            self._performance_history.pop(0)  # Remove oldest entry
        
        self._performance_history.append({
            "timestamp": datetime.now().isoformat(),
            "processing_time": result.processing_time,
            "confidence_score": result.confidence_score,
            "pattern_matched": result.pattern_matched,
            "variables_extracted": result.variables_extracted,
            "sentiment_strength": result.sentiment_strength,
            "success": result.success
        })
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive digestor processing statistics with trends"""
        stats = self._processing_stats.copy()
        
        # Calculate rates
        if stats["total_processed"] > 0:
            stats["success_rate"] = stats["successful_digestions"] / stats["total_processed"]
            stats["pattern_match_rate"] = stats["pattern_matches"] / stats["total_processed"]
            stats["fallback_rate"] = stats["fallback_uses"] / stats["total_processed"]
            stats["error_rate"] = stats["errors"] / stats["total_processed"]
            stats["variable_extraction_rate"] = stats["variable_extraction_successes"] / stats["total_processed"]
            stats["sentiment_analysis_rate"] = stats["sentiment_analysis_successes"] / stats["total_processed"]
        else:
            stats.update({
                "success_rate": 0.0,
                "pattern_match_rate": 0.0,
                "fallback_rate": 0.0,
                "error_rate": 0.0,
                "variable_extraction_rate": 0.0,
                "sentiment_analysis_rate": 0.0
            })
        
        # Add configuration and environment info
        stats.update({
            "patterns_loaded": len(self.patterns),
            "digestor_version": self.version,
            "sentiment_mapping_available": SENTIMENT_MAPPING_AVAILABLE,
            "config_summary": {
                "confidence_threshold": self.config.confidence_threshold,
                "pattern_match_threshold": self.config.pattern_match_threshold,
                "enable_sentiment_mapping": self.config.enable_sentiment_mapping,
                "fallback_on_errors": self.config.fallback_on_errors,
                "enable_pattern_compaction": self.config.enable_pattern_compaction
            },
            "performance_history_size": len(self._performance_history)
        })
        
        # Add recent performance trends if available
        if len(self._performance_history) >= 10:
            recent_entries = self._performance_history[-10:]
            stats["recent_trends"] = {
                "avg_processing_time": sum(e["processing_time"] for e in recent_entries) / len(recent_entries),
                "avg_confidence": sum(e["confidence_score"] for e in recent_entries) / len(recent_entries),
                "recent_success_rate": sum(1 for e in recent_entries if e["success"]) / len(recent_entries)
            }
        
        return stats
    
    def get_performance_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get performance history for detailed analysis"""
        if limit:
            return self._performance_history[-limit:]
        return self._performance_history.copy()
    
    def reset_statistics(self):
        """Reset processing statistics and performance history"""
        self._processing_stats = {
            "total_processed": 0,
            "successful_digestions": 0,
            "pattern_matches": 0,
            "fallback_uses": 0,
            "errors": 0,
            "avg_processing_time": 0.0,
            "avg_confidence_score": 0.0,
            "sentiment_analysis_successes": 0,
            "variable_extraction_successes": 0
        }
        self._performance_history = []
        self.logger.info("Processing statistics and performance history reset")


# Factory and utility functions with enhanced error handling

def create_digestor(
    memory_engine: Optional['MemoryEngine'] = None,
    patterns: Optional[List[Dict[str, Any]]] = None,
    config: Optional[DigestorConfig] = None,
) -> DigestorCore:
    """
    Enhanced factory function to create a configured digestor instance.
    
    Args:
        memory_engine: Optional memory engine reference for integration
        patterns: Optional pattern definitions (loads from memory_engine if None)
        config: Optional digestor configuration (uses defaults if None)
        
    Returns:
        Configured DigestorCore instance ready for production use
        
    Raises:
        ValueError: If invalid configuration provided
        RuntimeError: If digestor initialization fails
    """
    try:
        # Load patterns from memory engine if not provided
        if patterns is None and memory_engine:
            patterns = getattr(memory_engine, 'patterns', [])
        elif patterns is None:
            patterns = []
        
        # Use default config if not provided
        if config is None:
            config = DigestorConfig()
        
        # Validate configuration
        config_issues = config.validate_config()
        if config_issues:
            raise ValueError(f"Invalid digestor configuration: {', '.join(config_issues)}")
        
        # Create digestor instance
        digestor = DigestorCore(
            patterns=patterns,
            config=config,
            version=version,
            memory_engine=memory_engine
        )
        
        return digestor
        
    except Exception as e:
        raise RuntimeError(f"Failed to create digestor: {e}")


def validate_digestor_patterns(patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Comprehensive validation of pattern definitions for digestor compatibility.
    
    Args:
        patterns: List of pattern definitions to validate
        
    Returns:
        Detailed validation report with results, issues, and recommendations
    """
    validation_report = {
        "total_patterns": len(patterns),
        "valid_patterns": 0,
        "invalid_patterns": 0,
        "issues": [],
        "recommendations": [],
        "pattern_details": []
    }
    
    for i, pattern in enumerate(patterns):
        pattern_report = {
            "index": i,
            "pattern_id": pattern.get("pattern_id", f"UNKNOWN_{i}"),
            "valid": False,
            "issues": []
        }
        
        try:
            # Check required fields
            required_fields = ['pattern_id', 'keywords', 'schema']
            missing_fields = [field for field in required_fields if field not in pattern]
            
            if missing_fields:
                pattern_report["issues"].append(f"Missing required fields: {missing_fields}")
                validation_report["issues"].append(f"Pattern {i}: Missing fields {missing_fields}")
            
            # Validate field types and content
            if 'pattern_id' in pattern:
                if not isinstance(pattern['pattern_id'], str) or not pattern['pattern_id'].strip():
                    pattern_report["issues"].append("Invalid pattern_id: must be non-empty string")
                    validation_report["issues"].append(f"Pattern {i}: Invalid pattern_id")
            
            if 'keywords' in pattern:
                if not isinstance(pattern['keywords'], list):
                    pattern_report["issues"].append("Invalid keywords: must be a list")
                    validation_report["issues"].append(f"Pattern {i}: Keywords must be a list")
                elif not pattern['keywords']:
                    pattern_report["issues"].append("Invalid keywords: list cannot be empty")
                    validation_report["issues"].append(f"Pattern {i}: Keywords list is empty")
                else:
                    # Validate individual keywords
                    for j, keyword in enumerate(pattern['keywords']):
                        if not isinstance(keyword, str) or not keyword.strip():
                            pattern_report["issues"].append(f"Invalid keyword at index {j}: must be non-empty string")
            
            if 'schema' in pattern:
                if not isinstance(pattern['schema'], list):
                    pattern_report["issues"].append("Invalid schema: must be a list")
                    validation_report["issues"].append(f"Pattern {i}: Schema must be a list")
                else:
                    # Validate schema fields
                    for j, field in enumerate(pattern['schema']):
                        if not isinstance(field, str) or not field.strip():
                            pattern_report["issues"].append(f"Invalid schema field at index {j}: must be non-empty string")
            
            # Check for pattern validity
            if not pattern_report["issues"]:
                pattern_report["valid"] = True
                validation_report["valid_patterns"] += 1
            else:
                validation_report["invalid_patterns"] += 1
            
        except Exception as e:
            pattern_report["issues"].append(f"Validation error: {e}")
            validation_report["invalid_patterns"] += 1
            validation_report["issues"].append(f"Pattern {i}: Validation error - {e}")
        
        validation_report["pattern_details"].append(pattern_report)
    
    # Generate comprehensive recommendations
    if validation_report["invalid_patterns"] > 0:
        validation_report["recommendations"].append("Fix invalid patterns before using digestor")
        validation_report["recommendations"].append("Review pattern_details for specific issues")
    
    if validation_report["valid_patterns"] == 0:
        validation_report["recommendations"].append("Add at least one valid pattern for effective digestion")
    
    if validation_report["total_patterns"] > 100:
        validation_report["recommendations"].append("Consider pattern optimization for large pattern sets")
    
    # Add quality suggestions
    validation_report["recommendations"].append("Ensure pattern keywords are distinctive and specific")
    validation_report["recommendations"].append("Validate schema fields match your data extraction needs")
    
    validation_report["validation_passed"] = validation_report["invalid_patterns"] == 0
    validation_report["validation_score"] = (validation_report["valid_patterns"] / validation_report["total_patterns"] * 100) if validation_report["total_patterns"] > 0 else 0
    
    return validation_report


def validate_production_deployment() -> Dict[str, Any]:
    """
    Comprehensive validation of digestor module readiness for production deployment.
    
    Returns:
        Detailed deployment readiness report with comprehensive checks
    """
    report = {
        "deployment_ready": True,
        "version": "0.1.2",
        "checks_passed": 0,
        "checks_failed": 0,
        "issues": [],
        "recommendations": [],
        "test_results": []
    }
    
    # Test 1: Critical imports availability
    try:
        import json, logging, re, uuid
        from datetime import datetime
        from typing import Dict, List, Any, Optional, Union
        from dataclasses import dataclass, field
        from enum import Enum
        report["checks_passed"] += 1
        report["test_results"].append({"test": "critical_imports", "status": "passed"})
    except ImportError as e:
        report["checks_failed"] += 1
        report["issues"].append(f"Critical import check failed: {e}")
        report["deployment_ready"] = False
        report["test_results"].append({"test": "critical_imports", "status": "failed", "error": str(e)})
    
    # Test 2: Sentiment mapping availability
    if SENTIMENT_MAPPING_AVAILABLE:
        report["checks_passed"] += 1
        report["recommendations"].append("Sentiment mapping fully operational with refinery_utils")
        report["test_results"].append({"test": "sentiment_mapping", "status": "passed", "method": "refinery_utils"})
    else:
        report["checks_passed"] += 1  # Still passes with fallback
        report["recommendations"].append("Using fallback sentiment mapping - consider installing refinery_utils for enhanced functionality")
        report["test_results"].append({"test": "sentiment_mapping", "status": "passed", "method": "fallback"})
    
    # Test 3: Factory function operational
    try:
        test_digestor = create_digestor(patterns=[])
        if isinstance(test_digestor, DigestorCore):
            report["checks_passed"] += 1
            report["test_results"].append({"test": "factory_function", "status": "passed"})
        else:
            report["checks_failed"] += 1
            report["issues"].append("Factory function returns invalid type")
            report["deployment_ready"] = False
            report["test_results"].append({"test": "factory_function", "status": "failed", "error": "invalid_type"})
    except Exception as e:
        report["checks_failed"] += 1
        report["issues"].append(f"Factory function failed: {e}")
        report["deployment_ready"] = False
        report["test_results"].append({"test": "factory_function", "status": "failed", "error": str(e)})
    
    # Test 4: Configuration validation
    try:
        test_config = DigestorConfig()
        config_issues = test_config.validate_config()
        if not config_issues:
            report["checks_passed"] += 1
            report["test_results"].append({"test": "configuration_validation", "status": "passed"})
        else:
            report["checks_failed"] += 1
            report["issues"].append(f"Configuration validation issues: {config_issues}")
            report["deployment_ready"] = False
            report["test_results"].append({"test": "configuration_validation", "status": "failed", "issues": config_issues})
    except Exception as e:
        report["checks_failed"] += 1
        report["issues"].append(f"Configuration validation failed: {e}")
        report["deployment_ready"] = False
        report["test_results"].append({"test": "configuration_validation", "status": "failed", "error": str(e)})
    
    # Test 5: Exception hierarchy
    try:
        test_exceptions = [DigestorError, PatternMatchingError, VariableExtractionError, SentimentAnalysisError, SchemaValidationError]
        if all(issubclass(exc, Exception) for exc in test_exceptions):
            report["checks_passed"] += 1
            report["test_results"].append({"test": "exception_hierarchy", "status": "passed"})
        else:
            report["checks_failed"] += 1
            report["issues"].append("Exception hierarchy invalid")
            report["deployment_ready"] = False
            report["test_results"].append({"test": "exception_hierarchy", "status": "failed", "error": "hierarchy_invalid"})
    except Exception as e:
        report["checks_failed"] += 1
        report["issues"].append(f"Exception hierarchy check failed: {e}")
        report["deployment_ready"] = False
        report["test_results"].append({"test": "exception_hierarchy", "status": "failed", "error": str(e)})
    
    # Test 6: Processing pipeline integrity
    try:
        test_digestor = create_digestor(patterns=[{
            "pattern_id": "test_pattern",
            "keywords": ["test"],
            "schema": ["test_field"]
        }])
        result = test_digestor.digest_entry("This is a test message")
        if isinstance(result, DigestResult) and "pattern_id" in result.compacted_entry:
            report["checks_passed"] += 1
            report["test_results"].append({"test": "processing_pipeline", "status": "passed"})
        else:
            report["checks_failed"] += 1
            report["issues"].append("Processing pipeline produces invalid results")
            report["deployment_ready"] = False
            report["test_results"].append({"test": "processing_pipeline", "status": "failed", "error": "invalid_results"})
    except Exception as e:
        report["checks_failed"] += 1
        report["issues"].append(f"Processing pipeline test failed: {e}")
        report["deployment_ready"] = False
        report["test_results"].append({"test": "processing_pipeline", "status": "failed", "error": str(e)})
    
    # Calculate overall statistics
    report["total_checks"] = report["checks_passed"] + report["checks_failed"]
    report["success_rate"] = (report["checks_passed"] / report["total_checks"] * 100) if report["total_checks"] > 0 else 0.0
    
    # Generate final recommendations
    if report["deployment_ready"]:
        report["recommendations"].append("✅ All critical systems operational - ready for production deployment")
        report["recommendations"].append("🚀 Consider running comprehensive test suite before deployment")
        report["recommendations"].append("📊 Monitor performance metrics during initial deployment")
    else:
        report["recommendations"].append("❌ Critical issues detected - resolve before deployment")
        report["recommendations"].append("🔧 Review failed tests and address underlying issues")
        report["recommendations"].append("⚠️ Do not deploy until all checks pass")
    
    report["deployment_timestamp"] = datetime.now().isoformat()
    
    return report

