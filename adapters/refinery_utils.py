"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Heuristic-based emotional analysis utilities for VAD mapping with multilingual support
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
Refinery Utils Module - Heuristic VAD Sentiment Analysis

Provides VAD (Valence-Arousal-Dominance) emotional mapping using lightweight heuristic 
approaches with no external dependencies. Designed for fallback scenarios in memory_engine
digestion pipeline when LLM-based analysis is unavailable.

Key Features:
- Heuristic sentiment lexicon-based VAD scoring
- Basic multilingual language detection (character set analysis)
- Configurable thresholds and sentiment multipliers
- Comprehensive fallback strategies with graceful degradation
- Memory-efficient processing with caching support
- Integration-ready for digestor.py and pattern_weaver.py workflows
"""

import json
import re
import time
import logging
import math
from typing import Dict, Optional, Tuple, Any, Union, List, Set
from functools import lru_cache
from dataclasses import dataclass
from enum import Enum
from collections import Counter

# Configure module logger
logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """Fallback strategies for VAD mapping failures"""
    NEUTRAL = "neutral"
    WEIGHTED = "weighted" 
    PREVIOUS = "previous"
    CONTEXTUAL = "contextual"


class LanguageHint(Enum):
    """Detected language hints for VAD processing"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    ARABIC = "ar"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    UNKNOWN = "unknown"


class RefineryError(Exception):
    """Base exception for refinery utilities"""
    pass


class VADMappingError(RefineryError):
    """Raised when VAD mapping fails after retries"""
    pass


@dataclass
class VADScore:
    """Encapsulates VAD (Valence-Arousal-Dominance) emotional scores"""
    valence: float
    arousal: float
    dominance: float
    confidence: float = 0.5  # Added confidence score for heuristic quality
    
    def __post_init__(self):
        """Validate VAD scores are within expected range"""
        for attr in ['valence', 'arousal', 'dominance']:
            value = getattr(self, attr)
            if not -1.0 <= value <= 1.0:
                setattr(self, attr, max(-1.0, min(1.0, value)))  # Clamp instead of error
        
        # Validate confidence score
        if not 0.0 <= self.confidence <= 1.0:
            self.confidence = max(0.0, min(1.0, self.confidence))
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary format"""
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance
        }
    
    @classmethod
    def neutral(cls) -> 'VADScore':
        """Create neutral VAD score with low confidence"""
        return cls(0.0, 0.0, 0.0, confidence=0.3)


@dataclass
class HeuristicConfig:
    """Configuration for heuristic VAD analysis"""
    min_word_length: int = 3
    max_text_length: int = 2000
    sentiment_threshold: float = 0.1
    arousal_multiplier: float = 1.2
    dominance_base: float = 0.1
    negation_window: int = 3
    punctuation_weight: float = 0.1
    caps_weight: float = 0.15
    enable_language_detection: bool = True
    confidence_decay_factor: float = 0.9


class HeuristicVADMapper:
    """
    Heuristic-based VAD emotional mapping with multilingual support.
    
    Uses lightweight sentiment lexicons and linguistic features to estimate
    emotional content without external dependencies or model downloads.
    """
    
    def __init__(self, 
                 config: Optional[HeuristicConfig] = None,
                 fallback_strategy: FallbackStrategy = FallbackStrategy.NEUTRAL):
        """
        Initialize heuristic VAD mapper.
        
        Args:
            config: Heuristic analysis configuration
            fallback_strategy: Strategy for handling analysis failures
        """
        self.config = config or HeuristicConfig()
        self.fallback_strategy = fallback_strategy
        self._last_valid_score: Optional[VADScore] = None
        self._sentiment_cache: Dict[str, VADScore] = {}
        
        # Initialize sentiment lexicons
        self._load_sentiment_lexicons()
        
        logger.debug(f"HeuristicVADMapper initialized with {fallback_strategy.value} fallback")
    
    def _load_sentiment_lexicons(self) -> None:
        """Load lightweight sentiment lexicons for heuristic analysis"""
        
        # English sentiment lexicon (basic but effective)
        self._english_sentiment = {
            # High positive valence
            'amazing': (0.8, 0.6, 0.3), 'awesome': (0.9, 0.7, 0.4),
            'excellent': (0.8, 0.5, 0.5), 'fantastic': (0.9, 0.7, 0.4),
            'wonderful': (0.8, 0.6, 0.3), 'perfect': (0.9, 0.5, 0.6),
            'brilliant': (0.8, 0.6, 0.5), 'outstanding': (0.9, 0.6, 0.6),
            'superb': (0.8, 0.6, 0.4), 'magnificent': (0.9, 0.7, 0.5),
            
            # Moderate positive valence
            'good': (0.6, 0.3, 0.2), 'nice': (0.5, 0.2, 0.1),
            'happy': (0.7, 0.4, 0.2), 'pleased': (0.6, 0.3, 0.2),
            'satisfied': (0.6, 0.2, 0.3), 'content': (0.5, -0.2, 0.2),
            'glad': (0.6, 0.4, 0.2), 'cheerful': (0.7, 0.5, 0.3),
            'positive': (0.6, 0.3, 0.3), 'optimistic': (0.6, 0.3, 0.4),
            
            # High negative valence
            'terrible': (-0.8, 0.6, -0.3), 'awful': (-0.9, 0.7, -0.4),
            'horrible': (-0.8, 0.7, -0.3), 'disgusting': (-0.9, 0.6, -0.2),
            'devastating': (-0.9, 0.8, -0.4), 'catastrophic': (-0.9, 0.8, -0.5),
            'nightmare': (-0.8, 0.7, -0.4), 'disaster': (-0.8, 0.7, -0.3),
            'tragic': (-0.8, 0.5, -0.4), 'dreadful': (-0.8, 0.6, -0.3),
            
            # Moderate negative valence
            'bad': (-0.6, 0.3, -0.2), 'sad': (-0.6, -0.2, -0.3),
            'angry': (-0.6, 0.8, 0.4), 'upset': (-0.5, 0.4, -0.2),
            'disappointed': (-0.6, 0.2, -0.3), 'frustrated': (-0.5, 0.6, 0.1),
            'annoyed': (-0.4, 0.5, 0.2), 'worried': (-0.4, 0.4, -0.2),
            'concerned': (-0.3, 0.3, -0.1), 'negative': (-0.6, 0.3, -0.3),
            
            # High arousal terms
            'excited': (0.6, 0.9, 0.4), 'thrilled': (0.8, 0.9, 0.5),
            'ecstatic': (0.9, 0.9, 0.6), 'energetic': (0.5, 0.8, 0.4),
            'passionate': (0.6, 0.8, 0.5), 'intense': (0.2, 0.8, 0.3),
            'frantic': (-0.2, 0.9, -0.1), 'chaotic': (-0.4, 0.8, -0.2),
            
            # Low arousal terms
            'calm': (0.3, -0.6, 0.2), 'peaceful': (0.6, -0.7, 0.3),
            'relaxed': (0.5, -0.6, 0.2), 'serene': (0.7, -0.7, 0.4),
            'tranquil': (0.6, -0.8, 0.3), 'quiet': (0.2, -0.5, 0.1),
            'tired': (-0.2, -0.6, -0.2), 'exhausted': (-0.4, -0.7, -0.3),
            
            # High dominance terms
            'powerful': (0.4, 0.6, 0.8), 'strong': (0.4, 0.5, 0.7),
            'confident': (0.6, 0.4, 0.8), 'dominant': (0.2, 0.5, 0.9),
            'control': (0.3, 0.3, 0.8), 'command': (0.3, 0.5, 0.8),
            'leader': (0.4, 0.4, 0.7), 'authority': (0.2, 0.3, 0.8),
            
            # Low dominance terms
            'weak': (-0.4, -0.2, -0.7), 'helpless': (-0.6, 0.2, -0.8),
            'powerless': (-0.5, 0.3, -0.8), 'submissive': (-0.2, -0.1, -0.7),
            'vulnerable': (-0.3, 0.4, -0.6), 'dependent': (-0.2, -0.1, -0.5)
        }
        
        # Basic multilingual sentiment indicators
        self._multilingual_sentiment = {
            # Spanish
            'bueno': (0.6, 0.3, 0.2), 'malo': (-0.6, 0.3, -0.2),
            'excelente': (0.8, 0.5, 0.5), 'terrible': (-0.8, 0.6, -0.3),
            'feliz': (0.7, 0.4, 0.2), 'triste': (-0.6, -0.2, -0.3),
            
            # French  
            'bon': (0.6, 0.3, 0.2), 'mauvais': (-0.6, 0.3, -0.2),
            'excellent': (0.8, 0.5, 0.5), 'terrible': (-0.8, 0.6, -0.3),
            'heureux': (0.7, 0.4, 0.2), 'triste': (-0.6, -0.2, -0.3),
            
            # German
            'gut': (0.6, 0.3, 0.2), 'schlecht': (-0.6, 0.3, -0.2),
            'ausgezeichnet': (0.8, 0.5, 0.5), 'schrecklich': (-0.8, 0.6, -0.3),
            'glücklich': (0.7, 0.4, 0.2), 'traurig': (-0.6, -0.2, -0.3),
        }
        
        # Negation words that flip sentiment
        self._negation_words = {
            'not', 'no', 'never', 'none', 'nothing', 'nobody', 'nowhere',
            'neither', 'nor', 'barely', 'hardly', 'scarcely', "don't", 
            "won't", "can't", "isn't", "aren't", "wasn't", "weren't",
            "shouldn't", "couldn't", "wouldn't", "hasn't", "haven't",
            "hadn't", "doesn't", "didn't"
        }
        
        # Intensifier words that amplify sentiment
        self._intensifiers = {
            'very': 1.3, 'extremely': 1.5, 'incredibly': 1.4, 'absolutely': 1.4,
            'totally': 1.3, 'completely': 1.3, 'utterly': 1.4, 'quite': 1.2,
            'really': 1.2, 'truly': 1.2, 'highly': 1.3, 'deeply': 1.3,
            'strongly': 1.3, 'seriously': 1.2, 'definitely': 1.2
        }
    
    @lru_cache(maxsize=256)
    def detect_language(self, text: str) -> LanguageHint:
        """
        Lightweight language detection using character set analysis.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Detected language hint
        """
        if not text or len(text.strip()) < 10:
            return LanguageHint.UNKNOWN
        
        text_lower = text.lower()
        
        # Character-based detection for non-Latin scripts
        char_counts = Counter(text)
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return LanguageHint.UNKNOWN
        
        # Cyrillic detection
        cyrillic_chars = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        if cyrillic_chars / total_chars > 0.3:
            return LanguageHint.RUSSIAN
        
        # Arabic detection
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if arabic_chars / total_chars > 0.3:
            return LanguageHint.ARABIC
        
        # Chinese detection
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if chinese_chars / total_chars > 0.2:
            return LanguageHint.CHINESE
        
        # Japanese detection (Hiragana/Katakana)
        japanese_chars = sum(1 for c in text if '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff')
        if japanese_chars / total_chars > 0.2:
            return LanguageHint.JAPANESE
        
        # Korean detection
        korean_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7af')
        if korean_chars / total_chars > 0.2:
            return LanguageHint.KOREAN
        
        # Latin script language detection using common words/patterns
        common_words = text_lower.split()[:20]  # Check first 20 words
        
        # Spanish indicators
        spanish_indicators = {'el', 'la', 'de', 'que', 'y', 'es', 'en', 'un', 'ser', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'una', 'tiene', 'él', 'está', 'todo', 'le', 'su', 'ya', 'sí'}
        spanish_score = sum(1 for word in common_words if word in spanish_indicators)
        
        # French indicators  
        french_indicators = {'le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour', 'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus', 'par', 'grand', 'en', 'être', 'à', 'son', 'que'}
        french_score = sum(1 for word in common_words if word in french_indicators)
        
        # German indicators
        german_indicators = {'der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als', 'auch', 'es', 'an', 'werden', 'aus', 'er', 'hat', 'dass', 'sie', 'nach'}
        german_score = sum(1 for word in common_words if word in german_indicators)
        
        # Determine most likely language
        max_score = max(spanish_score, french_score, german_score)
        if max_score >= 2:  # At least 2 indicator words found
            if spanish_score == max_score:
                return LanguageHint.SPANISH
            elif french_score == max_score:
                return LanguageHint.FRENCH
            elif german_score == max_score:
                return LanguageHint.GERMAN
        
        # Default to English for Latin scripts
        return LanguageHint.ENGLISH
    
    def map_sentience(self, text: str) -> Dict[str, float]:
        """
        Map text to VAD emotional scores using heuristic analysis.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with valence, arousal, dominance scores
        """
        try:
            # Validate and sanitize input
            text = self._sanitize_text(text)
            if not text:
                logger.warning("Empty text provided for VAD mapping")
                return self._get_fallback_score().to_dict()
            
            # Check cache first
            cache_key = text[:100]  # Use first 100 chars as cache key
            if cache_key in self._sentiment_cache:
                cached_score = self._sentiment_cache[cache_key]
                logger.debug(f"Using cached VAD score for text snippet")
                return cached_score.to_dict()
            
            # Perform heuristic analysis
            vad_score = self._analyze_text_heuristically(text)
            
            # Cache result
            self._sentiment_cache[cache_key] = vad_score
            if len(self._sentiment_cache) > 1000:  # Prevent memory bloat
                # Remove oldest 50% of entries
                keys_to_remove = list(self._sentiment_cache.keys())[:500]
                for key in keys_to_remove:
                    del self._sentiment_cache[key]
            
            self._last_valid_score = vad_score
            return vad_score.to_dict()
            
        except Exception as e:
            logger.error(f"VAD mapping failed: {e}")
            return self._get_fallback_score().to_dict()
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize input text for analysis.
        
        Args:
            text: Raw input text
            
        Returns:
            Cleaned text
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Truncate if too long
        if len(text) > self.config.max_text_length:
            logger.debug(f"Truncating text from {len(text)} to {self.config.max_text_length} chars")
            text = text[:self.config.max_text_length] + "..."
        
        # Remove problematic characters but preserve punctuation
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    def _analyze_text_heuristically(self, text: str) -> VADScore:
        """
        Perform heuristic VAD analysis on sanitized text.
        
        Args:
            text: Sanitized input text
            
        Returns:
            VADScore with confidence
        """
        # Detect language for appropriate lexicon selection
        language = self.detect_language(text) if self.config.enable_language_detection else LanguageHint.ENGLISH
        
        # Tokenize and clean words
        words = self._tokenize_text(text)
        if not words:
            return VADScore.neutral()
        
        # Initialize accumulators
        total_valence = 0.0
        total_arousal = 0.0
        total_dominance = 0.0
        word_count = 0
        confidence_factors = []
        
        # Analyze linguistic features
        caps_ratio = self._calculate_caps_ratio(text)
        punctuation_intensity = self._calculate_punctuation_intensity(text)
        
        # Process each word with context
        for i, word in enumerate(words):
            word_lower = word.lower()
            
            # Skip very short words
            if len(word_lower) < self.config.min_word_length:
                continue
            
            # Get sentiment scores for word
            v, a, d, conf = self._get_word_sentiment(word_lower, language)
            
            if conf > 0:  # Word found in lexicon
                # Check for negation in nearby context
                negation_multiplier = self._check_negation_context(words, i)
                
                # Check for intensifiers
                intensifier_multiplier = self._check_intensifier_context(words, i)
                
                # Apply modifiers
                v *= negation_multiplier * intensifier_multiplier
                a *= intensifier_multiplier  # Arousal typically increased by intensifiers
                d *= intensifier_multiplier
                
                # Accumulate weighted scores
                total_valence += v * conf
                total_arousal += a * conf
                total_dominance += d * conf
                word_count += conf
                confidence_factors.append(conf)
        
        # Calculate base averages
        if word_count > 0:
            avg_valence = total_valence / word_count
            avg_arousal = total_arousal / word_count
            avg_dominance = total_dominance / word_count
        else:
            # No sentiment words found - use linguistic features only
            avg_valence = 0.0
            avg_arousal = 0.0
            avg_dominance = self.config.dominance_base
        
        # Apply linguistic feature adjustments
        # High caps ratio suggests higher arousal
        avg_arousal += caps_ratio * self.config.caps_weight * self.config.arousal_multiplier
        
        # Punctuation intensity affects arousal
        avg_arousal += punctuation_intensity * self.config.punctuation_weight * self.config.arousal_multiplier
        
        # Calculate overall confidence
        if confidence_factors:
            base_confidence = sum(confidence_factors) / len(confidence_factors)
            # Adjust confidence based on text length and word coverage
            coverage_ratio = len(confidence_factors) / len(words)
            length_factor = min(1.0, len(text) / 100)  # Longer text = higher confidence up to a point
            final_confidence = base_confidence * coverage_ratio * length_factor
        else:
            final_confidence = 0.2  # Low confidence for no-sentiment-word texts
        
        # Clamp final scores
        final_valence = max(-1.0, min(1.0, avg_valence))
        final_arousal = max(-1.0, min(1.0, avg_arousal))
        final_dominance = max(-1.0, min(1.0, avg_dominance))
        
        return VADScore(
            valence=final_valence,
            arousal=final_arousal, 
            dominance=final_dominance,
            confidence=max(0.0, min(1.0, final_confidence))
        )
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Simple but effective tokenization"""
        # Use regex to split on whitespace and punctuation while preserving contractions
        words = re.findall(r"\b[\w']+\b", text)
        return [w for w in words if w and len(w) > 0]
    
    def _get_word_sentiment(self, word: str, language: LanguageHint) -> Tuple[float, float, float, float]:
        """
        Get VAD sentiment scores for a word.
        
        Args:
            word: Word to analyze (lowercase)
            language: Detected language hint
            
        Returns:
            Tuple of (valence, arousal, dominance, confidence)
        """
        # Try primary English lexicon first
        if word in self._english_sentiment:
            v, a, d = self._english_sentiment[word]
            return v, a, d, 0.8
        
        # Try multilingual lexicon
        if word in self._multilingual_sentiment:
            v, a, d = self._multilingual_sentiment[word]
            return v, a, d, 0.7
        
        # Fallback: basic pattern matching for unknown words
        confidence = 0.0
        valence = 0.0
        arousal = 0.0
        dominance = 0.0
        
        # Positive patterns
        if any(pattern in word for pattern in ['good', 'great', 'best', 'love', 'like', 'happy', 'joy']):
            valence = 0.4
            arousal = 0.2
            dominance = 0.1
            confidence = 0.3
        
        # Negative patterns
        elif any(pattern in word for pattern in ['bad', 'hate', 'worst', 'sad', 'pain', 'hurt', 'terrible']):
            valence = -0.4
            arousal = 0.3
            dominance = -0.1
            confidence = 0.3
        
        # High arousal patterns
        if any(pattern in word for pattern in ['excit', 'thrill', 'amaz', 'shock', 'surpris']):
            arousal += 0.3
            confidence = max(confidence, 0.2)
        
        # High dominance patterns
        if any(pattern in word for pattern in ['power', 'control', 'command', 'lead', 'boss', 'manage']):
            dominance += 0.3
            confidence = max(confidence, 0.2)
        
        return valence, arousal, dominance, confidence
    
    def _check_negation_context(self, words: List[str], word_index: int) -> float:
        """
        Check for negation words near the current word.
        
        Args:
            words: List of all words
            word_index: Index of current word
            
        Returns:
            Multiplier for sentiment (1.0 = no negation, -0.8 = negated)
        """
        start_idx = max(0, word_index - self.config.negation_window)
        end_idx = min(len(words), word_index + 1)
        
        context_words = [w.lower() for w in words[start_idx:end_idx]]
        
        # Check for negation words
        negation_count = sum(1 for w in context_words if w in self._negation_words)
        
        if negation_count % 2 == 1:  # Odd number of negations = negated
            return -0.8
        else:
            return 1.0
    
    def _check_intensifier_context(self, words: List[str], word_index: int) -> float:
        """
        Check for intensifier words near the current word.
        
        Args:
            words: List of all words  
            word_index: Index of current word
            
        Returns:
            Multiplier for sentiment intensity
        """
        if word_index == 0:
            return 1.0
        
        # Check previous word for intensifiers
        prev_word = words[word_index - 1].lower()
        return self._intensifiers.get(prev_word, 1.0)
    
    def _calculate_caps_ratio(self, text: str) -> float:
        """Calculate ratio of uppercase characters"""
        if not text:
            return 0.0
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        caps = sum(1 for c in letters if c.isupper())
        return caps / len(letters)
    
    def _calculate_punctuation_intensity(self, text: str) -> float:
        """Calculate intensity based on punctuation patterns"""
        exclamations = text.count('!')
        questions = text.count('?')
        ellipses = text.count('...')
        
        # Normalize by text length
        text_length = len(text.split())
        if text_length == 0:
            return 0.0
        
        intensity = (exclamations * 2 + questions + ellipses * 0.5) / text_length
        return min(1.0, intensity)  # Cap at 1.0
    
    def _get_fallback_score(self) -> VADScore:
        """
        Get fallback VAD score based on configured strategy.
        
        Returns:
            VADScore based on fallback strategy
        """
        if self.fallback_strategy == FallbackStrategy.NEUTRAL:
            return VADScore.neutral()
            
        elif self.fallback_strategy == FallbackStrategy.PREVIOUS:
            if self._last_valid_score:
                logger.debug("Using previous valid score as fallback")
                return self._last_valid_score
            return VADScore.neutral()
            
        elif self.fallback_strategy == FallbackStrategy.WEIGHTED:
            # Slightly negative bias for processing failures
            return VADScore(valence=-0.1, arousal=0.1, dominance=-0.1, confidence=0.2)
            
        else:  # CONTEXTUAL or unknown
            return VADScore.neutral()


# Module-level convenience functions for backward compatibility
_default_mapper = None

def map_sentience(text: str) -> Dict[str, float]:
    """
    Maps text to VAD scores using default heuristic mapper.
    
    This is the primary interface function that maintains backward compatibility
    with the original memory_engine.py integration while using enhanced heuristic analysis.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary with valence, arousal, dominance scores
        
    Example:
        >>> result = map_sentience("I'm really excited about this amazing project!")
        >>> print(result)
        {'valence': 0.75, 'arousal': 0.82, 'dominance': 0.45}
    """
    global _default_mapper
    if _default_mapper is None:
        _default_mapper = HeuristicVADMapper()
    
    return _default_mapper.map_sentience(text)


@lru_cache(maxsize=128)
def get_emotion_label(valence: float, arousal: float) -> str:
    """
    Convert VAD scores to emotion label using Russell's circumplex model.
    
    Args:
        valence: Valence score (-1 to 1)
        arousal: Arousal score (-1 to 1)
        
    Returns:
        Emotion label string
    """
    # Quadrant-based emotion mapping with enhanced granularity
    if valence > 0.4:
        if arousal > 0.4:
            return "ecstatic" if valence > 0.7 and arousal > 0.7 else "excited"
        elif arousal < -0.4:
            return "content" if valence > 0.6 else "satisfied"
        else:
            return "happy" if valence > 0.6 else "pleased"
    elif valence < -0.4:
        if arousal > 0.4:
            return "furious" if valence < -0.7 and arousal > 0.7 else "angry"
        elif arousal < -0.4:
            return "depressed" if valence < -0.6 else "sad"
        else:
            return "upset" if valence < -0.6 else "disappointed"
    else:
        if arousal > 0.4:
            return "alert" if arousal > 0.6 else "tense"
        elif arousal < -0.4:
            return "calm" if arousal < -0.6 else "relaxed"
        else:
            return "neutral"


def analyze_emotional_trajectory(vad_history: List[Dict[str, float]]) -> Dict[str, Any]:
    """
    Analyze emotional trajectory over time with enhanced statistical measures.
    
    Args:
        vad_history: List of VAD dictionaries over time
        
    Returns:
        Comprehensive analysis including trends, patterns, and stability metrics
    """
    if not vad_history:
        return {"error": "No emotional history provided"}
    
    if len(vad_history) < 2:
        return {"error": "At least 2 data points required for trajectory analysis"}
    
    # Extract individual dimensions
    valence_trend = [v.get('valence', 0.0) for v in vad_history]
    arousal_trend = [v.get('arousal', 0.0) for v in vad_history]
    dominance_trend = [v.get('dominance', 0.0) for v in vad_history]
    
    def calculate_trend_stats(data: List[float]) -> Dict[str, Any]:
        """Calculate comprehensive trend statistics"""
        if not data:
            return {}
        
        mean_val = sum(data) / len(data)
        variance = sum((x - mean_val) ** 2 for x in data) / len(data)
        std_dev = math.sqrt(variance)
        
        # Linear trend calculation
        n = len(data)
        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = mean_val
        
        numerator = sum((x_vals[i] - x_mean) * (data[i] - y_mean) for i in range(n))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        
        slope = numerator / denominator if denominator != 0 else 0
        
        return {
            "mean": round(mean_val, 3),
            "std_dev": round(std_dev, 3),
            "min": min(data),
            "max": max(data),
            "range": max(data) - min(data),
            "slope": round(slope, 4),
            "trend": "increasing" if slope > 0.01 else ("decreasing" if slope < -0.01 else "stable"),
            "volatility": round(std_dev, 3)
        }
    
    # Simple moving average calculation
    def moving_average(data: List[float], window: int) -> List[float]:
        if len(data) < window:
            return data
        return [sum(data[i:i+window])/window for i in range(len(data)-window+1)]
    
    window_size = min(3, len(vad_history))
    
    return {
        "summary": {
            "total_entries": len(vad_history),
            "analysis_window": window_size,
            "timespan_analyzed": f"{len(vad_history)} data points"
        },
        "valence_analysis": calculate_trend_stats(valence_trend),
        "arousal_analysis": calculate_trend_stats(arousal_trend),
        "dominance_analysis": calculate_trend_stats(dominance_trend),
        "emotional_patterns": {
            "valence_smoothed": moving_average(valence_trend, window_size),
            "arousal_smoothed": moving_average(arousal_trend, window_size),
            "dominance_smoothed": moving_average(dominance_trend, window_size)
        },
        "stability_metrics": {
            "overall_volatility": round(
                (calculate_trend_stats(valence_trend).get('volatility', 0) +
                 calculate_trend_stats(arousal_trend).get('volatility', 0) +
                 calculate_trend_stats(dominance_trend).get('volatility', 0)) / 3, 3
            ),
            "emotional_coherence": round(
                1.0 - (calculate_trend_stats(valence_trend).get('volatility', 0) * 0.5), 3
            )
        },
        "current_state": {
            "latest_emotion": get_emotion_label(valence_trend[-1], arousal_trend[-1]),
            "recent_valence": valence_trend[-1],
            "recent_arousal": arousal_trend[-1], 
            "recent_dominance": dominance_trend[-1]
        }
    }


def create_vad_mapper(config: Optional[HeuristicConfig] = None, 
                     fallback_strategy: FallbackStrategy = FallbackStrategy.NEUTRAL) -> HeuristicVADMapper:
    """
    Factory function to create configured VAD mapper instances.
    
    Args:
        config: Optional heuristic configuration
        fallback_strategy: Fallback strategy for failures
        
    Returns:
        Configured HeuristicVADMapper instance
    """
    return HeuristicVADMapper(config=config, fallback_strategy=fallback_strategy)


# Export key classes and functions for external usage
__all__ = [
    'map_sentience',
    'get_emotion_label', 
    'analyze_emotional_trajectory',
    'create_vad_mapper',
    'HeuristicVADMapper',
    'VADScore',
    'HeuristicConfig',
    'FallbackStrategy',
    'LanguageHint',
    'RefineryError',
    'VADMappingError'
]
