""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
NLP Module

Last Updated: 2025-08-12
License: IOA Dev Confidential – Internal Use Only

This module provides a lightweight NLP processor for the IOA Core.  It
supports configurable sentiment analysis, regex‑based language
detection and simple entity extraction (names and email addresses).
"""

import re
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml
from audit_logger import AuditLogger  # REFACTOR: Claude-2025-08-12

# REFACTOR: Claude-2025-08-12 - Standardized logging setup
logger = logging.getLogger(__name__)
audit_logger = AuditLogger()

class NLPProcessor:
    """
    Lightweight NLP processor with configurable sentiment analysis and language detection.
    
    ENHANCED FEATURES (v2.4.9):
    - Configurable sentiment words via external YAML configuration
    - Robust regex-based language detection with mixed-language handling
    - Pluggable detection modules for future SpaCy/NLTK integration
    - Enhanced error handling and logging for production environments
    - Support for custom sentiment dictionaries and detection patterns
    
    PATCH: Gemini-2025-08-11 - Made sentiment_words configurable
    REFACTOR: Claude-2025-08-12 - Moved to config file, added pluggable detection
    """
    
    def __init__(self, sentiment_config_path: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize NLP processor with configurable sentiment analysis.
        
        Args:
            sentiment_config_path: Path to sentiment.yaml config file
            config: Direct configuration dict (overrides file config)
        """
        self.sentiment_config_path = sentiment_config_path or "config/sentiment.yaml"
        self.custom_config = config
        self.sentiment_words = self._load_sentiment_config()
        self.detection_hooks = []  # REFACTOR: Claude-2025-08-12 - Pluggable detection
        
        logger.info(f"NLPProcessor v2.4.9 initialized with {len(self.sentiment_words.get('positive', []))} positive and {len(self.sentiment_words.get('negative', []))} negative sentiment words")
        audit_logger.log_system_event("nlp_processor_init", {
            "sentiment_config_path": self.sentiment_config_path,
            "positive_words_count": len(self.sentiment_words.get('positive', [])),
            "negative_words_count": len(self.sentiment_words.get('negative', []))
        })

    def _load_sentiment_config(self) -> Dict[str, List[str]]:
        """
        Load sentiment configuration from YAML file or use defaults.
        
        REFACTOR: Claude-2025-08-12 - Moved sentiment_words to config/sentiment.yaml
        
        Returns:
            Dict with 'positive' and 'negative' word lists
        """
        # Use custom config if provided
        if self.custom_config and 'sentiment_words' in self.custom_config:
            return self.custom_config['sentiment_words']
        
        # Try to load from file
        config_path = Path(self.sentiment_config_path)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config.get('sentiment_words', self._get_default_sentiment_words())
            except Exception as e:
                logger.warning(f"Failed to load sentiment config from {config_path}: {e}")
                audit_logger.log_error("sentiment_config_load_failure", {
                    "path": str(config_path),
                    "error": str(e)
                })
        
        # Create default config file if it doesn't exist
        try:
            self._create_default_sentiment_config(config_path)
        except Exception as e:
            logger.warning(f"Failed to create default sentiment config: {e}")
        
        return self._get_default_sentiment_words()

    def _get_default_sentiment_words(self) -> Dict[str, List[str]]:
        """Get default sentiment word lists."""
        return {
            'positive': [
                'happy', 'good', 'positive', 'excellent', 'great', 'wonderful',
                'amazing', 'fantastic', 'brilliant', 'outstanding', 'perfect',
                'love', 'joy', 'beautiful', 'success', 'win', 'victory'
            ],
            'negative': [
                'sad', 'bad', 'negative', 'terrible', 'awful', 'horrible',
                'hate', 'angry', 'furious', 'disgusting', 'fail', 'failure',
                'disappointed', 'frustrated', 'annoyed', 'upset', 'worried'
            ]
        }

    def _create_default_sentiment_config(self, config_path: Path):
        """
        Create default sentiment configuration file.
        
        REFACTOR: Claude-2025-08-12 - Auto-generate config file
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            'sentiment_words': self._get_default_sentiment_words(),
            'language_patterns': {
                'en': r'[a-zA-Z\s]+',
                'es': r'[a-zA-Záéíóúñ\s]+',
                'fa': r'[\u0600-\u06FF\s]+',
                'zh': r'[\u4E00-\u9FFF\s]+'
            },
            'config_version': '2.4.9',
            'last_updated': '2025-08-11'
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Created default sentiment config at {config_path}")

    def add_detection_hook(self, hook_func):
        """
        Add pluggable detection hook for future extensions.
        
        REFACTOR: Claude-2025-08-12 - Prepare for SpaCy/NLTK integration
        
        Args:
            hook_func: Function that takes (text, metadata) and returns enhanced metadata
        """
        self.detection_hooks.append(hook_func)
        logger.info(f"Added detection hook: {hook_func.__name__}")

    def enrich_metadata(self, text: str) -> Dict[str, Any]:
        """
        Enrich text with language, sentiment and entity metadata.

        This method performs lightweight natural language processing to
        detect the language of the input, analyse its sentiment and
        extract simple entities such as names (capitalised first and last
        names) and e‑mail addresses.  In cases where the language
        detector reports ``mixed`` or ``unknown`` the text is noted in
        ``remediation_test.log`` for further analysis.

        Returns a mapping containing the detected language, sentiment
        scores, entity list and basic text statistics.

        Args:
            text: Input text to analyse.

        Returns:
            Dict[str, Any]: Enriched metadata.
        """
        try:
            # Language detection with improved robustness
            language = self._detect_language(text)
            # Sentiment analysis using configurable word lists
            sentiment = self._analyze_sentiment(text)
            # Extract entities (names and emails) using simple regexes
            entities = re.findall(r"([A-Z][a-z]+ [A-Z][a-z]+|[\w\.-]+@[\w\.-]+)", text)
            # Base metadata
            metadata: Dict[str, Any] = {
                "language": language,
                "sentiment": sentiment,
                "entities": entities,
                "text_length": len(text),
                "word_count": len(text.split()),
                "processing_version": "2.5.0"
            }
            # If unsupported language or mixed content, log to remediation_test.log
            if language in {"mixed", "unknown"}:
                try:
                    with open("remediation_test.log", "a", encoding="utf-8") as remed_log:
                        remed_log.write(f"Unsupported language detected ({language}): {text[:100]}\n")
                except Exception as log_err:
                    # Log error via audit logger; do not raise
                    logger.warning(f"Failed to write remediation log: {log_err}")
            # Apply detection hooks for extensibility
            for hook in self.detection_hooks:
                try:
                    metadata = hook(text, metadata)
                except Exception as e:
                    logger.warning(f"Detection hook {hook.__name__} failed: {e}")
            logger.debug(f"Enriched metadata for text (length={len(text)}): {metadata}")
            return metadata
        except Exception as e:
            logger.error(f"Failed to enrich metadata for text: {e}")
            audit_logger.log_error("nlp_enrichment_failure", {"error": str(e)})
            # Return minimal metadata on failure
            return {
                "language": "unknown",
                "sentiment": {"valence": 0.0, "arousal": 0.5, "dominance": 0.5},
                "entities": [],
                "error": str(e)
            }

    def _detect_language(self, text: str) -> str:
        """
        Detect language using regex patterns with mixed-language handling.
        
        REFACTOR: Claude-2025-08-12 - Enhanced robustness for mixed-language text
        
        Args:
            text: Input text
            
        Returns:
            Language code (en, es, fa, zh, mixed, unknown)
        """
        # Language patterns with improved coverage
        lang_patterns = {
            "en": r'[a-zA-Z\s]+',
            "es": r'[a-zA-Záéíóúñ\s]+',
            "fa": r'[\u0600-\u06FF\s]+',
            "zh": r'[\u4E00-\u9FFF\s]+'
        }
        
        # Calculate match percentages for each language
        language_scores = {}
        text_length = len(text.replace(' ', ''))  # Exclude spaces from length calculation
        
        if text_length == 0:
            return "unknown"
        
        for lang, pattern in lang_patterns.items():
            matches = re.findall(pattern, text)
            match_length = sum(len(match.replace(' ', '')) for match in matches)
            language_scores[lang] = match_length / text_length
        
        # Find the dominant language
        max_lang = max(language_scores, key=language_scores.get)
        max_score = language_scores[max_lang]
        
        # Check for mixed-language content
        significant_languages = [lang for lang, score in language_scores.items() if score > 0.2]
        
        if len(significant_languages) > 1:
            return "mixed"
        elif max_score > 0.5:
            return max_lang
        else:
            return "unknown"

    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using configurable word lists.
        
        PATCH: Gemini-2025-08-11 - Use configurable sentiment_words
        REFACTOR: Claude-2025-08-12 - Enhanced VAD calculation
        
        Args:
            text: Input text
            
        Returns:
            Dict with valence, arousal, and dominance scores
        """
        text_lower = text.lower()
        
        # Count positive and negative words
        positive_words = self.sentiment_words.get('positive', [])
        negative_words = self.sentiment_words.get('negative', [])
        
        positive_count = sum(
            len(re.findall(rf'\b{re.escape(word)}\b', text_lower)) 
            for word in positive_words
        )
        
        negative_count = sum(
            len(re.findall(rf'\b{re.escape(word)}\b', text_lower)) 
            for word in negative_words
        )
        
        # Calculate valence (positive vs negative sentiment)
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words > 0:
            valence = (positive_count - negative_count) / total_sentiment_words
        else:
            valence = 0.0
        
        # Enhanced arousal calculation based on word intensity and punctuation
        arousal = self._calculate_arousal(text, positive_count, negative_count)
        
        # Enhanced dominance calculation based on text characteristics
        dominance = self._calculate_dominance(text)
        
        return {
            "valence": max(-1.0, min(1.0, valence)),  # Clamp to [-1, 1]
            "arousal": max(0.0, min(1.0, arousal)),   # Clamp to [0, 1]
            "dominance": max(0.0, min(1.0, dominance)), # Clamp to [0, 1]
            "positive_count": positive_count,
            "negative_count": negative_count
        }

    def _calculate_arousal(self, text: str, positive_count: int, negative_count: int) -> float:
        """
        Calculate arousal (emotional intensity) based on text characteristics.
        
        REFACTOR: Claude-2025-08-12 - Enhanced arousal calculation
        
        Args:
            text: Input text
            positive_count: Number of positive sentiment words
            negative_count: Number of negative sentiment words
            
        Returns:
            Arousal score between 0.0 and 1.0
        """
        base_arousal = 0.3  # Neutral baseline
        
        # Sentiment word intensity
        sentiment_intensity = (positive_count + negative_count) / max(len(text.split()), 1)
        
        # Punctuation intensity (exclamation marks, question marks)
        punctuation_intensity = (text.count('!') + text.count('?')) / max(len(text), 1)
        
        # Capitalization intensity
        caps_intensity = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        # Combine factors
        arousal = base_arousal + (sentiment_intensity * 0.4) + (punctuation_intensity * 0.2) + (caps_intensity * 0.1)
        
        return min(1.0, arousal)

    def _calculate_dominance(self, text: str) -> float:
        """
        Calculate dominance (sense of control) based on text characteristics.
        
        REFACTOR: Claude-2025-08-12 - Enhanced dominance calculation
        
        Args:
            text: Input text
            
        Returns:
            Dominance score between 0.0 and 1.0
        """
        base_dominance = 0.5  # Neutral baseline
        
        # Length-based confidence (longer texts suggest more control)
        length_factor = min(len(text.split()) / 50.0, 0.2)  # Cap at 0.2
        
        # First-person pronouns suggest personal control
        first_person_count = len(re.findall(r'\b(I|me|my|mine|myself)\b', text, re.IGNORECASE))
        first_person_factor = min(first_person_count / max(len(text.split()), 1) * 0.3, 0.2)
        
        # Declarative vs questioning tone
        statements = text.count('.')
        questions = text.count('?')
        declarative_factor = (statements - questions) / max(statements + questions, 1) * 0.1
        
        dominance = base_dominance + length_factor + first_person_factor + declarative_factor
        
        return max(0.0, min(1.0, dominance))

    def redact_phi(self, text: str) -> str:
        """
        Redact Protected Health Information (PHI) from text for HIPAA compliance.
        
        Args:
            text: Input text that may contain PHI
            
        Returns:
            Text with PHI tokens masked
        """
        try:
            if not text:
                return text
            
            # Common PHI patterns
            phi_patterns = [
                # Social Security Numbers (XXX-XX-XXXX)
                (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
                # Phone numbers (various formats)
                (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
                # Email addresses
                (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
                # Dates (MM/DD/YYYY or YYYY-MM-DD)
                (r'\b\d{1,2}/\d{1,2}/\d{4}\b', '[DATE]'),
                (r'\b\d{4}-\d{1,2}-\d{1,2}\b', '[DATE]'),
                # Medical record numbers (MRN)
                (r'\bMRN[:\s]*\d+\b', '[MRN]'),
                # Patient IDs
                (r'\bPatient[:\s]*ID[:\s]*\d+\b', '[PATIENT_ID]'),
                # Names (basic pattern - could be enhanced)
                (r'\b(Dr\.|Dr|Mr\.|Mr|Mrs\.|Mrs|Ms\.|Ms)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b', '[NAME]'),
                # Addresses (basic pattern)
                (r'\b\d+\s+[A-Za-z\s]+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr)\b', '[ADDRESS]'),
                # Insurance numbers
                (r'\b(Insurance|Policy)[:\s]*#?\d+\b', '[INSURANCE]'),
                # Diagnosis codes (ICD-10)
                (r'\b[A-Z]\d{2}\.\d+\b', '[DIAGNOSIS_CODE]'),
                # Procedure codes (CPT)
                (r'\b\d{5}\b', '[PROCEDURE_CODE]')
            ]
            
            redacted_text = text
            
            # Apply each pattern
            for pattern, replacement in phi_patterns:
                redacted_text = re.sub(pattern, replacement, redacted_text, flags=re.IGNORECASE)
            
            # Log redaction activity
            audit_logger.log_system_event("phi_redaction", {
                "original_length": len(text),
                "redacted_length": len(redacted_text),
                "patterns_applied": len(phi_patterns)
            })
            
            return redacted_text
            
        except Exception as e:
            logger.error(f"PHI redaction failed: {e}")
            audit_logger.log_error("phi_redaction_failure", {"error": str(e)})
            # Return original text if redaction fails
            return text

    def reload_sentiment_config(self):
        """
        Reload sentiment configuration from file.
        
        REFACTOR: Claude-2025-08-12 - Runtime config reloading
        """
        try:
            old_config = self.sentiment_words.copy()
            self.sentiment_words = self._load_sentiment_config()
            
            logger.info("Sentiment configuration reloaded successfully")
            audit_logger.log_system_event("sentiment_config_reloaded", {
                "old_positive_count": len(old_config.get('positive', [])),
                "new_positive_count": len(self.sentiment_words.get('positive', [])),
                "old_negative_count": len(old_config.get('negative', [])),
                "new_negative_count": len(self.sentiment_words.get('negative', []))
            })
            
        except Exception as e:
            logger.error(f"Failed to reload sentiment configuration: {e}")
            audit_logger.log_error("sentiment_config_reload_failure", {"error": str(e)})
            raise

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.
        
        REFACTOR: Claude-2025-08-12 - Utility method for language support
        
        Returns:
            List of supported language codes
        """
        return ["en", "es", "fa", "zh", "mixed", "unknown"]

    def validate_text_quality(self, text: str) -> Dict[str, Any]:
        """
        Validate text quality and provide recommendations.
        
        REFACTOR: Claude-2025-08-12 - Quality assessment utility
        
        Args:
            text: Input text to validate
            
        Returns:
            Dict with quality metrics and recommendations
        """
        try:
            quality_metrics = {
                "length_score": min(len(text) / 100.0, 1.0),  # Prefer 100+ chars
                "word_count": len(text.split()),
                "avg_word_length": sum(len(word) for word in text.split()) / max(len(text.split()), 1),
                "punctuation_ratio": sum(1 for c in text if c in '.,!?;:') / max(len(text), 1),
                "caps_ratio": sum(1 for c in text if c.isupper()) / max(len(text), 1)
            }
            
            # Calculate overall quality score
            quality_score = (
                quality_metrics["length_score"] * 0.3 +
                min(quality_metrics["word_count"] / 20.0, 1.0) * 0.3 +
                min(quality_metrics["avg_word_length"] / 6.0, 1.0) * 0.2 +
                min(quality_metrics["punctuation_ratio"] * 10, 1.0) * 0.2
            )
            
            # Generate recommendations
            recommendations = []
            if quality_metrics["length_score"] < 0.3:
                recommendations.append("Consider providing more detailed text")
            if quality_metrics["word_count"] < 5:
                recommendations.append("Text appears too short for reliable analysis")
            if quality_metrics["caps_ratio"] > 0.3:
                recommendations.append("Excessive capitalization detected")
            
            return {
                "quality_score": quality_score,
                "metrics": quality_metrics,
                "recommendations": recommendations,
                "is_suitable": quality_score > 0.4 and len(recommendations) < 2
            }
            
        except Exception as e:
            logger.error(f"Failed to validate text quality: {e}")
            return {
                "quality_score": 0.0,
                "error": str(e),
                "is_suitable": False
            }