""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Modular content digestion pipeline for memory processing
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
Digestor Module - Modular Content Processing Pipeline

Provides a clean, modular approach to content digestion that breaks down the
monolithic digest_entry() function into testable, reusable components.

Pipeline Stages:
1. Pattern Analysis - Detection and confidence scoring
2. Metadata Generation - Comprehensive context extraction  
3. Sentiment Analysis - VAD mapping with contextual awareness
4. Content Compaction - Pattern compression and duplicate linking
5. Storage Assessment - Tier recommendation and optimization
6. Evolution Triggers - Pattern learning and governance

Key Features:
- Modular design for improved testability
- Configurable pipeline stages
- Comprehensive error handling with fallbacks
- Performance monitoring and metrics
- Full backward compatibility with existing memory engine
"""

import json
import datetime
import re
import time
from typing import Dict, List, Any, Optional, Union, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from refinery_utils import map_sentience

# Avoid circular imports while maintaining type hints
if TYPE_CHECKING:
    from .memory_engine import MemoryEngine
    from .pattern_governance import PatternGovernance
    from .pattern_weaver import PatternWeaver


class ProcessingStage(Enum):
    """Enumeration of digestion pipeline stages."""
    PATTERN_ANALYSIS = "pattern_analysis"
    METADATA_GENERATION = "metadata_generation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CONTENT_COMPACTION = "content_compaction"
    STORAGE_ASSESSMENT = "storage_assessment"
    EVOLUTION_TRIGGERS = "evolution_triggers"


@dataclass
class DigestorConfig:
    """Configuration for digestor pipeline."""
    enable_sentiment_mapping: bool = True
    enable_pattern_compaction: bool = True
    enable_storage_assessment: bool = True
    enable_evolution_triggers: bool = True
    confidence_threshold: float = 0.5
    max_content_length: int = 10000
    fallback_on_errors: bool = True


@dataclass
class ProcessingMetrics:
    """Metrics for digestion pipeline performance."""
    total_processing_time: float = 0.0
    stage_times: Dict[str, float] = field(default_factory=dict)
    errors_encountered: List[str] = field(default_factory=list)
    fallbacks_used: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class DigestResult:
    """Complete digestion result with metadata."""
    compacted_entry: Dict[str, Any]
    processing_metrics: ProcessingMetrics
    recommendations: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class DigestorError(Exception):
    """Base exception for digestor operations."""
    pass


class PatternAnalysisError(DigestorError):
    """Raised when pattern analysis fails."""
    pass


class MetadataGenerationError(DigestorError):
    """Raised when metadata generation fails."""
    pass


class SentimentAnalysisError(DigestorError):
    """Raised when sentiment analysis fails."""
    pass


class ProcessingStageError(DigestorError):
    """Raised when a processing stage fails."""
    pass


class PatternAnalyzer:
    """
    Handles pattern detection and confidence scoring for memory entries.
    
    Analyzes raw content against known patterns, calculates confidence scores,
    and provides detailed analysis results including alternative matches.
    """
    
    def __init__(self, patterns: List[Dict[str, Any]]):
        """
        Initialize pattern analyzer with available patterns.
        
        Args:
            patterns: List of pattern definitions
        """
        self.patterns = patterns
        self._pattern_cache = {}
    
    def analyze_patterns(self, raw_entry: str) -> Dict[str, Any]:
        """
        Perform comprehensive pattern analysis with confidence scoring.
        
        Args:
            raw_entry: Raw text content to analyze
            
        Returns:
            Pattern analysis results with confidence metrics
            
        Raises:
            PatternAnalysisError: If analysis fails critically
        """
        try:
            entry_lower = raw_entry.lower()
            entry_tokens = set(entry_lower.split())
            pattern_candidates = []
            
            for pattern in self.patterns:
                # Calculate pattern match confidence
                keywords = pattern.get("keywords", [])
                keyword_matches = sum(1 for kw in keywords if kw.lower() in entry_lower)
                
                if keyword_matches > 0:
                    # Multi-factor confidence calculation
                    keyword_coverage = keyword_matches / len(keywords) if keywords else 0
                    content_relevance = self._calculate_content_relevance(raw_entry, pattern)
                    schema_completeness = self._assess_schema_completeness(raw_entry, pattern.get('schema', []))
                    
                    confidence = (
                        keyword_coverage * 0.4 +
                        content_relevance * 0.4 +
                        schema_completeness * 0.2
                    )
                    
                    pattern_candidates.append({
                        'pattern': pattern,
                        'confidence': confidence,
                        'keyword_matches': keyword_matches,
                        'keyword_coverage': keyword_coverage,
                        'content_relevance': content_relevance,
                        'schema_completeness': schema_completeness
                    })
            
            # Sort by confidence and select best match
            pattern_candidates.sort(key=lambda x: x['confidence'], reverse=True)
            
            if pattern_candidates and pattern_candidates[0]['confidence'] > 0.3:
                best_match = pattern_candidates[0]
                return {
                    'matched_pattern': best_match['pattern'],
                    'confidence': best_match['confidence'],
                    'alternatives': pattern_candidates[1:3],
                    'analysis_quality': 'high' if best_match['confidence'] > 0.7 else 'medium'
                }
            else:
                return {
                    'matched_pattern': None,
                    'confidence': 0.0,
                    'alternatives': pattern_candidates[:3],
                    'analysis_quality': 'low'
                }
                
        except Exception as e:
            raise PatternAnalysisError(f"Pattern analysis failed: {e}") from e
    
    def _calculate_content_relevance(self, raw_entry: str, pattern: Dict[str, Any]) -> float:
        """Calculate content relevance beyond keyword matching."""
        try:
            pattern_desc = pattern.get('description', '').lower()
            pattern_name = pattern.get('name', '').lower()
            entry_lower = raw_entry.lower()
            relevance_score = 0.0
            
            # Description word overlap
            if pattern_desc:
                desc_words = set(pattern_desc.split())
                entry_words = set(entry_lower.split())
                common_words = desc_words.intersection(entry_words)
                if desc_words:
                    relevance_score += len(common_words) / len(desc_words) * 0.5
            
            # Pattern name presence
            if pattern_name and pattern_name in entry_lower:
                relevance_score += 0.3
            
            # Length appropriateness
            expected_length = pattern.get('expected_length', 'medium')
            entry_length = len(raw_entry)
            if expected_length == 'short' and entry_length < 100:
                relevance_score += 0.2
            elif expected_length == 'medium' and 100 <= entry_length <= 500:
                relevance_score += 0.2
            elif expected_length == 'long' and entry_length > 500:
                relevance_score += 0.2
            
            return min(relevance_score, 1.0)
        except Exception:
            return 0.0
    
    def _assess_schema_completeness(self, raw_entry: str, schema: List[str]) -> float:
        """Assess how well entry can populate schema fields."""
        if not schema:
            return 1.0
        
        try:
            entry_lower = raw_entry.lower()
            extractable_fields = 0
            
            for field in schema:
                if field == 'name' and any(indicator in entry_lower for indicator in ['name', 'called', 'is']):
                    extractable_fields += 1
                elif field == 'age' and any(indicator in entry_lower for indicator in ['age', 'old', 'years']):
                    extractable_fields += 1
                elif field == 'location' and any(indicator in entry_lower for indicator in ['at', 'in', 'location']):
                    extractable_fields += 1
                elif field == 'time' and any(indicator in entry_lower for indicator in ['time', 'when', 'at']):
                    extractable_fields += 1
                elif field in entry_lower:
                    extractable_fields += 1
            
            return extractable_fields / len(schema)
        except Exception:
            return 0.0


class VariableExtractor:
    """
    Handles intelligent variable extraction from content based on patterns.
    
    Provides multiple extraction strategies with confidence-based processing
    and fallback mechanisms for robust data extraction.
    """
    
    def extract_variables(self, raw_entry: str, schema: List[str], confidence: float) -> Dict[str, str]:
        """
        Extract variables using appropriate strategy based on confidence.
        
        Args:
            raw_entry: Raw content to extract from
            schema: Expected schema fields
            confidence: Pattern match confidence
            
        Returns:
            Dictionary of extracted variables
        """
        try:
            variables = {}
            entry_lower = raw_entry.lower()
            words = entry_lower.split()
            use_advanced_extraction = confidence > 0.6
            
            for field in schema:
                extracted_value = None
                
                if field == "name":
                    extracted_value = self._extract_name_field(raw_entry, words, use_advanced_extraction)
                elif field == "age":
                    extracted_value = self._extract_age_field(raw_entry, words, use_advanced_extraction)
                elif field == "location":
                    extracted_value = self._extract_location_field(raw_entry, words, use_advanced_extraction)
                elif field == "time" or field == "timestamp":
                    extracted_value = self._extract_time_field(raw_entry, words, use_advanced_extraction)
                elif field == "emotion" or field == "feeling":
                    extracted_value = self._extract_emotion_field(raw_entry, words, use_advanced_extraction)
                else:
                    extracted_value = self._extract_generic_field(field, raw_entry, words, use_advanced_extraction)
                
                variables[field] = extracted_value or "unknown"
            
            return variables
        except Exception as e:
            print(f"[VariableExtractor] Extraction failed: {e}")
            return {field: "unknown" for field in schema}
    
    def _extract_name_field(self, raw_entry: str, words: List[str], advanced: bool) -> Optional[str]:
        """Extract name field using pattern matching."""
        try:
            name_patterns = [
                r"(?:my name is|i am|i'm|called)\s+([A-Za-z]+)",
                r"name:\s*([A-Za-z]+)",
                r"([A-Z][a-z]+)\s+(?:said|says|thinks|believes)"
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, raw_entry, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            if advanced:
                # Advanced extraction using capitalization
                capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', raw_entry)
                if capitalized_words:
                    common_words = {'The', 'This', 'That', 'When', 'Where', 'How', 'Why', 'What'}
                    potential_names = [w for w in capitalized_words if w not in common_words]
                    if potential_names:
                        return potential_names[0]
            
            return None
        except Exception:
            return None
    
    def _extract_age_field(self, raw_entry: str, words: List[str], advanced: bool) -> Optional[str]:
        """Extract age field using pattern matching."""
        try:
            age_patterns = [
                r'(\d{1,3})\s*(?:years?\s+old|yrs?\s+old|y\.?o\.?)',
                r'(?:age|aged)\s*:?\s*(\d{1,3})',
                r'(?:i am|i\'m)\s*(\d{1,3})',
                r'(\d{1,3})\s*(?:year|yr)s?\s*(?:old)?'
            ]
            
            for pattern in age_patterns:
                match = re.search(pattern, raw_entry, re.IGNORECASE)
                if match:
                    age = int(match.group(1))
                    if 0 < age < 150:
                        return str(age)
            
            if advanced:
                # Context-based age estimation
                age_contexts = {
                    'baby': '1', 'toddler': '3', 'child': '8', 'kid': '10',
                    'teenager': '16', 'teen': '17', 'adult': '30', 'elderly': '70'
                }
                entry_lower = raw_entry.lower()
                for context, age in age_contexts.items():
                    if context in entry_lower:
                        return age
            
            return None
        except Exception:
            return None
    
    def _extract_location_field(self, raw_entry: str, words: List[str], advanced: bool) -> Optional[str]:
        """Extract location field using pattern matching."""
        try:
            location_patterns = [
                r'(?:at|in|from|located in|based in)\s+([A-Za-z\s]+?)(?:\.|,|$)',
                r'location:\s*([A-Za-z\s]+?)(?:\.|,|$)',
                r'(?:city|town|country|state):\s*([A-Za-z\s]+?)(?:\.|,|$)'
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, raw_entry, re.IGNORECASE)
                if match:
                    location = match.group(1).strip()
                    if len(location) > 1:
                        return location
            
            return None
        except Exception:
            return None
    
    def _extract_time_field(self, raw_entry: str, words: List[str], advanced: bool) -> Optional[str]:
        """Extract time field using pattern matching."""
        try:
            time_patterns = [
                r'(?:at|on|during)\s+(\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?)',
                r'(?:time|when):\s*([^\.,\n]+)',
                r'(\d{4}-\d{2}-\d{2})',
                r'((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[^\.,\n]*)',
                r'((?:January|February|March|April|May|June|July|August|September|October|November|December)[^\.,\n]*)'
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, raw_entry, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            return None
        except Exception:
            return None
    
    def _extract_emotion_field(self, raw_entry: str, words: List[str], advanced: bool) -> Optional[str]:
        """Extract emotion field using keyword mapping."""
        try:
            emotions = {
                'happy': ['happy', 'joy', 'joyful', 'glad', 'pleased', 'excited'],
                'sad': ['sad', 'unhappy', 'depressed', 'down', 'blue'],
                'angry': ['angry', 'mad', 'furious', 'irritated', 'annoyed'],
                'scared': ['scared', 'afraid', 'frightened', 'worried', 'anxious'],
                'surprised': ['surprised', 'shocked', 'amazed', 'astonished']
            }
            
            entry_lower = raw_entry.lower()
            for emotion, keywords in emotions.items():
                if any(keyword in entry_lower for keyword in keywords):
                    return emotion
            
            return None
        except Exception:
            return None
    
    def _extract_generic_field(self, field_name: str, raw_entry: str, words: List[str], advanced: bool) -> Optional[str]:
        """Extract generic field using pattern matching."""
        try:
            # Try structured field pattern
            field_pattern = rf'{field_name}:\s*([^\.,\n]+)'
            match = re.search(field_pattern, raw_entry, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            # Try context-based extraction
            if field_name.lower() in raw_entry.lower():
                words_list = raw_entry.split()
                for i, word in enumerate(words_list):
                    if field_name.lower() in word.lower():
                        if i + 1 < len(words_list):
                            next_word = words_list[i + 1]
                            if len(next_word) > 2 and not next_word.lower() in ['is', 'the', 'a', 'an']:
                                return next_word
            
            return None
        except Exception:
            return None


class MetadataGenerator:
    """
    Generates comprehensive metadata for memory entries.
    
    Creates rich contextual metadata including conversation analysis,
    processing quality metrics, and system tracking information.
    """
    
        """
        Initialize metadata generator.
        
        Args:
        """
        self.version = version
    
    def generate_metadata(
        self, 
        raw_entry: str, 
        context: Dict[str, Any], 
        role_analysis: Dict[str, Any], 
        pattern_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive metadata combining all analysis results.
        
        Args:
            raw_entry: Original content
            context: Processing context
            role_analysis: Role detection results
            pattern_analysis: Pattern analysis results
            
        Returns:
            Complete metadata dictionary
            
        Raises:
            MetadataGenerationError: If metadata generation fails
        """
        try:
            metadata = {
                "speaker": role_analysis.get('speaker', 'unknown'),
                "agent": role_analysis.get('agent'),
                "recipient": role_analysis.get('recipient'),
                "conversation_type": role_analysis.get('conversation_type', 'unknown'),
                "timestamp": datetime.datetime.now().isoformat(),
                "processing_version": self.version,
                "digest_version": "2.3.0",
                "content_length": len(raw_entry),
                "word_count": len(raw_entry.split()),
                "tone": self._detect_tone(raw_entry),
                "language": self._detect_language(raw_entry),
                "complexity": self._assess_content_complexity(raw_entry),
                "pattern_match_confidence": pattern_analysis.get('confidence', 0.0),
                "role_detection_confidence": role_analysis.get('role_confidence', 0.0),
                "processing_quality": self._assess_processing_quality(pattern_analysis, role_analysis),
                "context_available": bool(context),
                "context_keys": list(context.keys()) if context else [],
                "processing_node": "digestor_pipeline",
                "session_id": context.get('session_id', 'unknown'),
                "thread_id": context.get('thread_id', 'unknown')
            }
            
            # Add pattern-specific metadata if available
            if pattern_analysis.get('matched_pattern'):
                pattern = pattern_analysis['matched_pattern']
                metadata.update({
                    "pattern_name": pattern.get('name', 'unnamed'),
                    "pattern_category": pattern.get('category', 'general'),
                    "pattern_version": pattern.get('version', '1.0')
                })
            
            return metadata
            
        except Exception as e:
            raise MetadataGenerationError(f"Metadata generation failed: {e}") from e
    
    def detect_conversation_roles(self, raw_entry: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect speaker, agent, and recipient roles from content.
        
        Args:
            raw_entry: Content to analyze
            context: Processing context
            
        Returns:
            Role analysis results
        """
        try:
            role_analysis = {
                'speaker': 'unknown',
                'agent': None,
                'recipient': None,
                'conversation_type': 'monologue',
                'role_confidence': 0.0,
                'detected_patterns': []
            }
            
            entry_lower = raw_entry.lower()
            
            # Speaker pattern detection
            speaker_patterns = {
                'user': ['i am', 'i\'m', 'my name', 'i think', 'i feel', 'i want', 'i need'],
                'system': ['system:', 'error:', 'warning:', 'info:', 'debug:'],
                'agent': ['as an ai', 'i can help', 'let me assist', 'i understand'],
                'character': ['character:', 'says:', 'thinks:', 'believes:']
            }
            
            detected_speaker = 'unknown'
            max_matches = 0
            
            for speaker_type, patterns in speaker_patterns.items():
                matches = sum(1 for pattern in patterns if pattern in entry_lower)
                if matches > max_matches:
                    max_matches = matches
                    detected_speaker = speaker_type
            
            role_analysis['speaker'] = detected_speaker
            role_analysis['role_confidence'] = min(max_matches / 3.0, 1.0)
            
            # Conversation type detection
            if any(indicator in entry_lower for indicator in ['you', 'your', 'can you', 'please']):
                role_analysis['conversation_type'] = 'dialogue'
                role_analysis['recipient'] = 'addressed_entity'
            
            # Agent detection
            agent_indicators = ['assistant', 'ai', 'bot', 'system']
            if any(indicator in entry_lower for indicator in agent_indicators):
                role_analysis['agent'] = 'ai_assistant'
            
            # Context override
            if context:
                context_speaker = context.get('speaker')
                if context_speaker:
                    role_analysis['speaker'] = context_speaker
                    role_analysis['role_confidence'] = max(role_analysis['role_confidence'], 0.8)
            
            return role_analysis
            
        except Exception as e:
            print(f"[MetadataGenerator] Role detection failed: {e}")
            return {
                'speaker': 'unknown',
                'agent': None,
                'recipient': None,
                'conversation_type': 'unknown',
                'role_confidence': 0.0,
                'detected_patterns': []
            }
    
    def _detect_tone(self, raw_entry: str) -> str:
        """Detect overall tone of content."""
        try:
            entry_lower = raw_entry.lower()
            tone_patterns = {
                'positive': ['happy', 'great', 'excellent', 'wonderful', 'amazing', 'love', 'like'],
                'negative': ['sad', 'bad', 'terrible', 'awful', 'hate', 'dislike', 'wrong'],
                'questioning': ['?', 'how', 'what', 'when', 'where', 'why', 'which'],
                'urgent': ['!', 'urgent', 'immediately', 'asap', 'quickly', 'hurry'],
                'formal': ['therefore', 'furthermore', 'moreover', 'consequently'],
                'casual': ['gonna', 'wanna', 'yeah', 'ok', 'cool', 'awesome']
            }
            
            tone_scores = {}
            for tone, patterns in tone_patterns.items():
                score = sum(1 for pattern in patterns if pattern in entry_lower)
                if score > 0:
                    tone_scores[tone] = score
            
            return max(tone_scores, key=tone_scores.get) if tone_scores else 'neutral'
        except Exception:
            return 'neutral'
    
    def _detect_language(self, raw_entry: str) -> str:
        """Detect content language."""
        try:
            if re.search(r'[а-яё]', raw_entry, re.IGNORECASE):
                return 'russian'
            elif re.search(r'[äöüß]', raw_entry, re.IGNORECASE):
                return 'german'
            elif re.search(r'[àáâãäåæçèéêëìíîïðñòóôõöøùúûüý]', raw_entry, re.IGNORECASE):
                return 'european'
            else:
                return 'english'
        except Exception:
            return 'unknown'
    
    def _assess_content_complexity(self, raw_entry: str) -> str:
        """Assess content complexity level."""
        try:
            word_count = len(raw_entry.split())
            sentence_count = len([s for s in raw_entry.split('.') if s.strip()])
            avg_word_length = sum(len(word) for word in raw_entry.split()) / word_count if word_count > 0 else 0
            
            if word_count < 10 and avg_word_length < 5:
                return 'simple'
            elif word_count < 50 and avg_word_length < 7:
                return 'moderate'
            else:
                return 'complex'
        except Exception:
            return 'unknown'
    
    def _assess_processing_quality(self, pattern_analysis: Dict[str, Any], role_analysis: Dict[str, Any]) -> str:
        """Assess overall processing quality."""
        try:
            pattern_conf = pattern_analysis.get('confidence', 0.0)
            role_conf = role_analysis.get('role_confidence', 0.0)
            avg_confidence = (pattern_conf + role_conf) / 2
            
            if avg_confidence > 0.8:
                return 'high'
            elif avg_confidence > 0.5:
                return 'medium'
            elif avg_confidence > 0.2:
                return 'low'
            else:
                return 'poor'
        except Exception:
            return 'unknown'


class SentimentAnalyzer:
    """
    Handles sentiment analysis with contextual awareness.
    
    Provides VAD (Valence-Arousal-Dominance) sentiment mapping with
    role and context consideration for enhanced accuracy.
    """
    
    def __init__(self, enable_sentiment_mapping: bool = True):
        """
        Initialize sentiment analyzer.
        
        Args:
            enable_sentiment_mapping: Whether to enable sentiment analysis
        """
        self.enable_sentiment_mapping = enable_sentiment_mapping
    
    def analyze_sentiment(
        self, 
        raw_entry: str, 
        role_analysis: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Perform contextual sentiment analysis.
        
        Args:
            raw_entry: Content to analyze
            role_analysis: Role detection results
            context: Processing context
            
        Returns:
            VAD sentiment scores
            
        Raises:
            SentimentAnalysisError: If sentiment analysis fails
        """
        if not self.enable_sentiment_mapping:
            return {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}
        
        try:
            # Get base sentiment
            base_sentiment = self._map_sentiment_safely(raw_entry)
            
            # Apply contextual adjustments
            adjusted_sentiment = self._apply_contextual_adjustments(
                base_sentiment, role_analysis, context
            )
            
            # Ensure values are within valid range
            for key in adjusted_sentiment:
                adjusted_sentiment[key] = max(-1.0, min(1.0, adjusted_sentiment[key]))
            
            return adjusted_sentiment
            
        except Exception as e:
            raise SentimentAnalysisError(f"Sentiment analysis failed: {e}") from e
    
    def _map_sentiment_safely(self, text: str) -> Dict[str, float]:
        """Map sentiment with error handling fallback."""
        try:
            return map_sentience(text)
        except Exception as e:
            print(f"[SentimentAnalyzer] Sentiment mapping failed: {e}")
            return {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}
    
    def _apply_contextual_adjustments(
        self, 
        base_sentiment: Dict[str, float], 
        role_analysis: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Apply contextual adjustments to base sentiment."""
        adjusted = base_sentiment.copy()
        
        speaker = role_analysis.get('speaker', 'unknown')
        conversation_type = role_analysis.get('conversation_type', 'unknown')
        
        # Speaker-based adjustments
        if speaker == 'system':
            adjusted['valence'] *= 0.5
            adjusted['arousal'] *= 0.7
        elif speaker == 'agent':
            adjusted['valence'] = max(adjusted['valence'], 0.1)
            adjusted['dominance'] = max(adjusted['dominance'], 0.2)
        
        # Conversation type adjustments
        if conversation_type == 'dialogue':
            adjusted['arousal'] = min(adjusted['arousal'] + 0.1, 1.0)
        
        # Context-based adjustments
        if context:
            context_emotion = context.get('emotional_context', 'neutral')
            if context_emotion == 'stressed':
                adjusted['arousal'] = min(adjusted['arousal'] + 0.2, 1.0)
                adjusted['valence'] = max(adjusted['valence'] - 0.1, -1.0)
            elif context_emotion == 'calm':
                adjusted['arousal'] = max(adjusted['arousal'] - 0.2, -1.0)
        
        return adjusted


class ContentCompactor:
    """
    Handles content compaction and duplicate detection.
    
    Performs pattern-based compression, identifies similar content,
    and creates efficient storage representations.
    """
    
    def __init__(self, memory_engine: 'MemoryEngine'):
        """
        Initialize content compactor.
        
        Args:
            memory_engine: Reference to memory system for duplicate detection
        """
        self.memory_engine = memory_engine
    
    def perform_compaction(
        self, 
        raw_entry: str, 
        pattern_id: str, 
        variables: Dict[str, str], 
        confidence: float
    ) -> Dict[str, Any]:
        """
        Perform comprehensive content compaction.
        
        Args:
            raw_entry: Original content
            pattern_id: Matched pattern identifier
            variables: Extracted variables
            confidence: Pattern match confidence
            
        Returns:
            Compaction results with metrics
        """
        try:
            compaction_result = {
                'original_size': len(raw_entry),
                'compacted_size': 0,
                'compression_ratio': 0.0,
                'duplicate_links': [],
                'compaction_strategy': 'none',
                'efficiency_score': 0.0
            }
            
            # Find similar entries for duplicate detection
            if pattern_id != "UNCLASSIFIED":
                similar_entries = self._find_similar_entries(pattern_id, variables, confidence)
                compaction_result['duplicate_links'] = similar_entries
            
            # Determine compaction strategy
            compacted_content = raw_entry
            
            if len(raw_entry) > 1000:
                compaction_strategy = 'summarization'
                compacted_content = self._create_content_summary(raw_entry, variables)
            elif confidence > 0.8 and variables:
                compaction_strategy = 'variable_extraction'
                compacted_content = self._create_variable_representation(variables, pattern_id)
            elif len(compaction_result['duplicate_links']) > 0:
                compaction_strategy = 'reference_linking'
                compacted_content = self._create_reference_link(compaction_result['duplicate_links'][0])
            else:
                compaction_strategy = 'minimal'
            
            # Update result
            compaction_result.update({
                'compacted_content': compacted_content,
                'compacted_size': len(str(compacted_content)),
                'compaction_strategy': compaction_strategy
            })
            
            # Calculate metrics
            if compaction_result['original_size'] > 0:
                compaction_result['compression_ratio'] = (
                    1.0 - compaction_result['compacted_size'] / compaction_result['original_size']
                )
            
            compaction_result['efficiency_score'] = self._calculate_compaction_efficiency(
                compaction_result, confidence
            )
            
            return compaction_result
            
        except Exception as e:
            print(f"[ContentCompactor] Compaction failed: {e}")
            return {
                'original_size': len(raw_entry),
                'compacted_size': len(raw_entry),
                'compression_ratio': 0.0,
                'duplicate_links': [],
                'compaction_strategy': 'error',
                'efficiency_score': 0.0,
                'error': str(e)
            }
    
    def _find_similar_entries(self, pattern_id: str, variables: Dict[str, str], confidence: float) -> List[Dict[str, Any]]:
        """Find similar entries for duplicate detection."""
        try:
            similar_entries = []
            existing_entries = self.memory_engine.recall('pattern_id', pattern_id)
            
            for entry in existing_entries[:10]:  # Limit search
                similarity_score = self._calculate_entry_similarity(entry, variables)
                if similarity_score > 0.7:
                    similar_entries.append({
                        'entry_id': entry.get('id', 'unknown'),
                        'similarity_score': similarity_score,
                        'variables': entry.get('variables', {}),
                        'timestamp': entry.get('metadata', {}).get('timestamp')
                    })
            
            similar_entries.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_entries[:3]  # Top 3 matches
            
        except Exception as e:
            print(f"[ContentCompactor] Similar entry search failed: {e}")
            return []
    
    def _calculate_entry_similarity(self, entry: Dict[str, Any], variables: Dict[str, str]) -> float:
        """Calculate similarity between entries based on variables."""
        try:
            entry_variables = entry.get('variables', {})
            if not entry_variables or not variables:
                return 0.0
            
            common_keys = set(entry_variables.keys()) & set(variables.keys())
            if not common_keys:
                return 0.0
            
            matching_values = 0
            for key in common_keys:
                if entry_variables[key] == variables[key] and variables[key] != 'unknown':
                    matching_values += 1
            
            return matching_values / len(common_keys)
        except Exception:
            return 0.0
    
    def _create_content_summary(self, raw_entry: str, variables: Dict[str, str]) -> str:
        """Create summarized content representation."""
        try:
            sentences = [s.strip() for s in raw_entry.split('.') if s.strip()]
            if len(sentences) <= 2:
                return raw_entry
            
            summary_parts = []
            summary_parts.append(sentences[0])
            if len(sentences) > 1:
                summary_parts.append(sentences[-1])
            
            if variables and any(v != 'unknown' for v in variables.values()):
                var_summary = ', '.join(f"{k}: {v}" for k, v in variables.items() if v != 'unknown')
                summary_parts.append(f"Key details: {var_summary}")
            
            return '. '.join(summary_parts) + '.'
        except Exception:
            return raw_entry[:200] + '...' if len(raw_entry) > 200 else raw_entry
    
    def _create_variable_representation(self, variables: Dict[str, str], pattern_id: str) -> Dict[str, str]:
        """Create variable-based representation."""
        try:
            known_variables = {k: v for k, v in variables.items() if v != 'unknown'}
            return {
                'type': 'variable_representation',
                'pattern': pattern_id,
                'variables': known_variables,
                'representation': f"{pattern_id}({', '.join(f'{k}={v}' for k, v in known_variables.items())})"
            }
        except Exception:
            return {'type': 'variable_representation', 'error': 'creation_failed'}
    
    def _create_reference_link(self, similar_entry: Dict[str, Any]) -> Dict[str, str]:
        """Create reference link to similar content."""
        return {
            'type': 'reference_link',
            'reference_id': similar_entry.get('entry_id'),
            'similarity_score': similar_entry.get('similarity_score'),
            'link_type': 'duplicate_content'
        }
    
    def _calculate_compaction_efficiency(self, compaction_result: Dict[str, Any], confidence: float) -> float:
        """Calculate overall compaction efficiency score."""
        try:
            compression_score = compaction_result.get('compression_ratio', 0.0)
            strategy_scores = {
                'summarization': 0.8,
                'variable_extraction': 0.9,
                'reference_linking': 0.95,
                'minimal': 0.1,
                'error': 0.0
            }
            strategy = compaction_result.get('compaction_strategy', 'minimal')
            strategy_score = strategy_scores.get(strategy, 0.1)
            
            efficiency = (compression_score * 0.6 + strategy_score * 0.4) * confidence
            return min(efficiency, 1.0)
        except Exception:
            return 0.0


class StorageAssessor:
    """
    Assesses storage requirements and provides tier recommendations.
    
    Analyzes content characteristics to determine optimal storage strategy
    including hot/cold storage routing and preservation recommendations.
    """
    
    def __init__(self, config: DigestorConfig):
        """
        Initialize storage assessor.
        
        Args:
            config: Digestor configuration
        """
        self.config = config
    
    def assess_storage_requirements(
        self, 
        raw_entry: str, 
        confidence: float, 
        compaction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess storage requirements and provide recommendations.
        
        Args:
            raw_entry: Original content
            confidence: Pattern match confidence
            compaction_result: Compaction analysis results
            
        Returns:
            Storage assessment with recommendations
        """
        try:
            storage_assessment = {
                'recommended_tier': 'hot',
                'preservation_recommended': False,
                'compaction_recommended': True,
                'cold_storage_candidate': False,
                'reasoning': [],
                'priority_score': 0.5
            }
            
            content_size = len(raw_entry)
            compression_ratio = compaction_result.get('compression_ratio', 0.0)
            
            # Size-based assessment
            if content_size > 5000:
                storage_assessment['preservation_recommended'] = True
                storage_assessment['reasoning'].append('large_content_size')
            
            # Confidence-based routing
            if content_size < 100 and confidence < 0.3:
                storage_assessment['cold_storage_candidate'] = True
                storage_assessment['recommended_tier'] = 'cold'
                storage_assessment['reasoning'].append('small_low_confidence')
            
            # Priority scoring
            if confidence > 0.8:
                storage_assessment['priority_score'] = 0.9
                storage_assessment['reasoning'].append('high_confidence')
            elif confidence < 0.3:
                storage_assessment['priority_score'] = 0.2
                storage_assessment['cold_storage_candidate'] = True
                storage_assessment['reasoning'].append('low_confidence')
            
            # Compression potential
            if compression_ratio > 0.5:
                storage_assessment['compaction_recommended'] = True
                storage_assessment['reasoning'].append('high_compression_potential')
            
            # Format-based preservation
            if self._detect_preservable_format(raw_entry):
                storage_assessment['preservation_recommended'] = True
                storage_assessment['compaction_recommended'] = False
                storage_assessment['reasoning'].append('preservable_format_detected')
            
            # Duplicate handling
            if len(compaction_result.get('duplicate_links', [])) > 0:
                storage_assessment['compaction_recommended'] = True
                storage_assessment['reasoning'].append('duplicate_content_found')
            
            return storage_assessment
            
        except Exception as e:
            print(f"[StorageAssessor] Assessment failed: {e}")
            return {
                'recommended_tier': 'hot',
                'preservation_recommended': False,
                'compaction_recommended': False,
                'cold_storage_candidate': False,
                'reasoning': ['assessment_failed'],
                'priority_score': 0.5,
                'error': str(e)
            }
    
    def _detect_preservable_format(self, content: str) -> bool:
        """Detect if content should be preserved in original format."""
        # Code blocks
        if re.search(r'```.*```', content, re.DOTALL):
            return True
        
        # Screenplay format
        screenplay_patterns = [
            r'^(INT\.|EXT\.)',
            r'^[A-Z\s]+$',
            r'^\s*\(.*\)',
        ]
        if any(re.search(pattern, content, re.MULTILINE) for pattern in screenplay_patterns):
            return True
        
        # Legal documents
        legal_patterns = [
            r'\bWHEREAS\b',
            r'^\s*\d+\.',
            r'\b(?:shall|hereby|herein|thereof)\b'
        ]
        if any(re.search(pattern, content, re.MULTILINE | re.IGNORECASE) for pattern in legal_patterns):
            return True
        
        return False


class DigestorCore:
    """
    Main digestor orchestration class that coordinates all processing stages.
    
    Provides the primary interface for content digestion with comprehensive
    error handling, fallback mechanisms, and performance monitoring.
    """
    
    def __init__(
        self, 
        memory_engine: 'MemoryEngine', 
        patterns: List[Dict[str, Any]], 
        config: Optional[DigestorConfig] = None
    ):
        """
        Initialize digestor core with all processing components.
        
        Args:
            memory_engine: Reference to memory system
            patterns: Available pattern definitions
            config: Optional configuration override
        """
        self.memory_engine = memory_engine
        self.patterns = patterns
        self.version = version
        self.config = config or DigestorConfig()
        
        # Initialize processing components
        self.pattern_analyzer = PatternAnalyzer(patterns)
        self.variable_extractor = VariableExtractor()
        self.metadata_generator = MetadataGenerator(version)
        self.sentiment_analyzer = SentimentAnalyzer(self.config.enable_sentiment_mapping)
        self.content_compactor = ContentCompactor(memory_engine)
        self.storage_assessor = StorageAssessor(self.config)
    
    def digest_entry(self, raw_entry: str, context: Optional[Dict[str, Any]] = None) -> DigestResult:
        """
        Main entry point for content digestion pipeline.
        
        Args:
            raw_entry: Raw content to process
            context: Optional processing context
            
        Returns:
            Complete digestion result
        """
        start_time = time.time()
        context = context or {}
        metrics = ProcessingMetrics()
        
        try:
            # Validate and sanitize input
            if len(raw_entry) > self.config.max_content_length:
                raw_entry = raw_entry[:self.config.max_content_length] + "..."
                metrics.fallbacks_used.append('content_truncation')
            
            # Stage 1: Pattern Analysis
            stage_start = time.time()
            try:
                pattern_analysis = self.pattern_analyzer.analyze_patterns(raw_entry)
                metrics.confidence_scores['pattern_analysis'] = pattern_analysis.get('confidence', 0.0)
            except PatternAnalysisError as e:
                if self.config.fallback_on_errors:
                    pattern_analysis = {'matched_pattern': None, 'confidence': 0.0}
                    metrics.errors_encountered.append(f"pattern_analysis: {e}")
                    metrics.fallbacks_used.append('pattern_analysis_fallback')
                else:
                    raise
            metrics.stage_times['pattern_analysis'] = time.time() - stage_start
            
            # Stage 2: Variable Extraction
            stage_start = time.time()
            if pattern_analysis['matched_pattern']:
                pattern_id = pattern_analysis['matched_pattern']['pattern_id']
                schema = pattern_analysis['matched_pattern']['schema']
                confidence = pattern_analysis['confidence']
                variables = self.variable_extractor.extract_variables(raw_entry, schema, confidence)
            else:
                pattern_id = "UNCLASSIFIED"
                confidence = 0.0
                variables = {}
            metrics.stage_times['variable_extraction'] = time.time() - stage_start
            
            # Stage 3: Role and Metadata Analysis
            stage_start = time.time()
            try:
                role_analysis = self.metadata_generator.detect_conversation_roles(raw_entry, context)
                metadata = self.metadata_generator.generate_metadata(
                    raw_entry, context, role_analysis, pattern_analysis
                )
            except MetadataGenerationError as e:
                if self.config.fallback_on_errors:
                    role_analysis = {'speaker': 'unknown', 'role_confidence': 0.0}
                    metadata = {
                        'speaker': 'unknown',
                        'timestamp': datetime.datetime.now().isoformat(),
                        'processing_version': self.version,
                        'error': 'metadata_generation_failed'
                    }
                    metrics.errors_encountered.append(f"metadata_generation: {e}")
                    metrics.fallbacks_used.append('metadata_generation_fallback')
                else:
                    raise
            metrics.stage_times['metadata_generation'] = time.time() - stage_start
            
            # Stage 4: Sentiment Analysis
            stage_start = time.time()
            try:
                feeling = self.sentiment_analyzer.analyze_sentiment(raw_entry, role_analysis, context)
            except SentimentAnalysisError as e:
                if self.config.fallback_on_errors:
                    feeling = {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}
                    metrics.errors_encountered.append(f"sentiment_analysis: {e}")
                    metrics.fallbacks_used.append('sentiment_analysis_fallback')
                else:
                    raise
            metrics.stage_times['sentiment_analysis'] = time.time() - stage_start
            
            # Stage 5: Content Compaction
            stage_start = time.time()
            if self.config.enable_pattern_compaction:
                compaction_result = self.content_compactor.perform_compaction(
                    raw_entry, pattern_id, variables, confidence
                )
            else:
                compaction_result = {
                    'original_size': len(raw_entry),
                    'compacted_size': len(raw_entry),
                    'compression_ratio': 0.0,
                    'duplicate_links': [],
                    'compaction_strategy': 'disabled'
                }
            metrics.stage_times['content_compaction'] = time.time() - stage_start
            
            # Stage 6: Storage Assessment
            stage_start = time.time()
            if self.config.enable_storage_assessment:
                storage_recommendation = self.storage_assessor.assess_storage_requirements(
                    raw_entry, confidence, compaction_result
                )
            else:
                storage_recommendation = {
                    'recommended_tier': 'hot',
                    'preservation_recommended': False,
                    'compaction_recommended': False
                }
            metrics.stage_times['storage_assessment'] = time.time() - stage_start
            
            # Stage 7: Trigger Evolution
            stage_start = time.time()
            if self.config.enable_evolution_triggers:
                self._trigger_pattern_evolution(pattern_id, confidence)
            metrics.stage_times['evolution_triggers'] = time.time() - stage_start
            
            # Construct final result
            compacted_entry = {
                "pattern_id": pattern_id,
                "pattern_confidence": confidence,
                "variables": variables,
                "metadata": metadata,
                "feeling": feeling,
                "raw_ref": raw_entry,
                "compaction": compaction_result,
                "storage_recommendation": storage_recommendation,
                "processing_metrics": {
                    "digest_version": "2.3.0",
                    "processing_time": time.time() - start_time,
                    "stages_completed": list(metrics.stage_times.keys()),
                    "errors_count": len(metrics.errors_encountered),
                    "fallbacks_count": len(metrics.fallbacks_used)
                }
            }
            
            # Apply fallback metadata
            compacted_entry = self._apply_fallback_metadata(compacted_entry)
            
            # Finalize metrics
            metrics.total_processing_time = time.time() - start_time
            
            return DigestResult(
                compacted_entry=compacted_entry,
                processing_metrics=metrics,
                recommendations={
                    'storage_tier': storage_recommendation.get('recommended_tier', 'hot'),
                    'preservation': storage_recommendation.get('preservation_recommended', False),
                    'compaction': storage_recommendation.get('compaction_recommended', True)
                },
                success=True
            )
            
        except Exception as e:
            # Critical error fallback
            fallback_entry = {
                "pattern_id": "PROCESSING_ERROR",
                "variables": {},
                "metadata": {
                    "speaker": "unknown",
                    "tone": "error",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "processing_version": self.version,
                    "error": str(e)
                },
                "feeling": {"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
                "raw_ref": raw_entry,
                "digest_version": "2.3.0",
                "fallback_mode": True
            }
            
            metrics.total_processing_time = time.time() - start_time
            metrics.errors_encountered.append(f"critical_error: {e}")
            
            return DigestResult(
                compacted_entry=fallback_entry,
                processing_metrics=metrics,
                recommendations={},
                success=False,
                error_message=str(e)
            )
    
    def _trigger_pattern_evolution(self, pattern_id: str, confidence: float) -> None:
        """Trigger pattern evolution processes if needed."""
        try:
            # Trigger PatternWeaver for unclassified entries
            if pattern_id == "UNCLASSIFIED" and hasattr(self.memory_engine, 'weaver'):
                unclassified_count = len(self.memory_engine.recall('pattern_id', 'UNCLASSIFIED'))
                if unclassified_count >= 10:  # Configurable threshold
                    try:
                        self.memory_engine.weaver.run_batch()
                    except Exception as e:
                        print(f"[DigestorCore] Pattern weaver failed: {e}")
            
            # High confidence pattern analysis
            if confidence > 0.9 and pattern_id != "UNCLASSIFIED":
                try:
                    similar_count = len(self.memory_engine.recall('pattern_id', pattern_id))
                    if similar_count < 5:
                        print(f"[DigestorCore] High confidence pattern variant detected: {pattern_id}")
                except Exception as e:
                    print(f"[DigestorCore] Pattern analysis failed: {e}")
                    
        except Exception as e:
            print(f"[DigestorCore] Pattern evolution trigger failed: {e}")
    
    def _apply_fallback_metadata(self, compacted: Dict[str, Any]) -> Dict[str, Any]:
        """Apply fallback metadata for missing fields."""
        try:
            # Ensure required fields exist
            if 'metadata' not in compacted:
                compacted['metadata'] = {}
            
            metadata = compacted['metadata']
            defaults = {
                'speaker': 'unknown',
                'tone': 'neutral',
                'timestamp': datetime.datetime.now().isoformat(),
                'processing_version': self.version
            }
            
            for key, default_value in defaults.items():
                if key not in metadata:
                    metadata[key] = default_value
            
            if 'feeling' not in compacted:
                compacted['feeling'] = {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}
            
            if 'variables' not in compacted:
                compacted['variables'] = {}
            
            return compacted
        except Exception as e:
            print(f"[DigestorCore] Fallback metadata failed: {e}")
            return compacted


# Factory function for creating digestor instances
def create_digestor(
    memory_engine: 'MemoryEngine', 
    patterns: List[Dict[str, Any]], 
    config: Optional[DigestorConfig] = None
) -> DigestorCore:
    """
    Factory function to create digestor instance.
    
    Args:
        memory_engine: Memory system reference
        patterns: Pattern definitions
        config: Optional configuration
        
    Returns:
        Configured DigestorCore instance
    """
    return DigestorCore(memory_engine, patterns, version, config)

