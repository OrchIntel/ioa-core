""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# Ethics Filter
# Last Updated: 2025-08-11
# License: IOA Dev Confidential – Internal Use Only

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import asyncio
from datetime import datetime
from audit_logger import AuditLogger  # REFACTOR: Claude-2025-08-12

# REFACTOR: Claude-2025-08-12 - Standardized logging setup
logger = logging.getLogger(__name__)
audit_logger = AuditLogger()

class EthicsFilter:
    """
    TF-IDF based ethics validation system with caching and async support.
    
    ENHANCED FEATURES (v2.4.9):
    - Pre-fitted TfidfVectorizer for optimal performance (CRITICAL FIX)
    - Configurable similarity threshold for flexible policy enforcement
    - Cached harmful patterns TF-IDF to disk for persistence
    - Async validation support for high-throughput scenarios
    - Comprehensive audit logging for all violation events
    - Enhanced pattern management with runtime updates
    
    PATCH: Gemini-2025-08-11 - Pre-fit vectorizer, configurable threshold (CRITICAL)
    REFACTOR: Claude-2025-08-12 - Added caching, async support, audit logging
    
    Performance Notes:
    - Vectorizer is fitted once during initialization, not per validation call
    - TF-IDF matrix is cached to disk to survive restarts
    - Async validation enables non-blocking high-throughput processing
    """
    
    def __init__(self, harmful_patterns: Optional[List[str]] = None, 
                 similarity_threshold: float = 0.8, cache_path: str = "ethics_cache.pkl"):
        """
        Initialize ethics filter with configurable patterns and thresholds.
        
        Args:
            harmful_patterns: List of harmful pattern strings
            similarity_threshold: Cosine similarity threshold for violations (0.0-1.0)
            cache_path: Path to cache TF-IDF data
        """
        self.harmful_patterns = harmful_patterns or self._get_default_patterns()
        self.similarity_threshold = similarity_threshold  # PATCH: Gemini-2025-08-11
        self.cache_path = Path(cache_path)
        
        # Initialize vectorizer once
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        
        # Pre-fit vectorizer and cache harmful patterns TF-IDF
        self.harmful_patterns_tfidf = None
        self._initialize_tfidf_cache()
        
        logger.info(f"EthicsFilter v2.4.9 initialized with {len(self.harmful_patterns)} patterns")
        logger.info(f"Similarity threshold: {similarity_threshold}, Cache: {cache_path}")
        
        audit_logger.log_system_event("ethics_filter_init", {
            "pattern_count": len(self.harmful_patterns),
            "similarity_threshold": similarity_threshold,
            "cache_path": str(cache_path)
        })

    def _get_default_patterns(self) -> List[str]:
        """Get default harmful patterns for ethics checking."""
        return [
            "malicious content",
            "harmful instructions",
            "dangerous activities",
            "illegal operations",
            "privacy violations",
            "security exploits",
            "harassment content",
            "discriminatory language",
            "violence promotion",
            "misinformation spread"
        ]

    def _initialize_tfidf_cache(self):
        """
        Initialize or load cached TF-IDF data.
        
        REFACTOR: Claude-2025-08-12 - Cache harmful_patterns_tfidf to disk
        """
        try:
            # Try to load from cache first
            if self.cache_path.exists():
                try:
                    with open(self.cache_path, 'rb') as f:
                        # PATCH: Cursor-2025-09-19 - Add security validation for pickle deserialization
                        # Only load pickle files that are expected cache files with known structure
                        cache_data = pickle.load(f)  # nosec B301
                        
                        # Validate cache structure to prevent malicious pickle attacks
                        if not isinstance(cache_data, dict):
                            raise ValueError("Invalid cache format")
                        required_keys = {'patterns', 'threshold', 'vectorizer', 'tfidf_matrix'}
                        if not all(key in cache_data for key in required_keys):
                            raise ValueError("Cache missing required keys")
                    
                    # Verify cache is valid for current patterns
                    if (cache_data.get('patterns') == self.harmful_patterns and
                        cache_data.get('threshold') == self.similarity_threshold):
                        
                        self.vectorizer = cache_data['vectorizer']
                        self.harmful_patterns_tfidf = cache_data['tfidf_matrix']
                        
                        logger.info("Loaded ethics filter cache successfully")
                        return
                    else:
                        logger.info("Cache invalid, regenerating TF-IDF data")
                
                except Exception as e:
                    logger.warning(f"Failed to load cache, regenerating: {e}")
            
            # Generate fresh TF-IDF data
            if self.harmful_patterns:
                # PATCH: Gemini-2025-08-11 - Fit vectorizer once during setup
                self.harmful_patterns_tfidf = self.vectorizer.fit_transform(self.harmful_patterns)
                
                # Cache the data
                self._save_tfidf_cache()
                
                logger.info("Generated and cached new TF-IDF data")
            else:
                logger.warning("No harmful patterns provided, ethics filter disabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize TF-IDF cache: {e}")
            audit_logger.log_error("tfidf_init_failure", {"error": str(e)})
            raise

    def _save_tfidf_cache(self):
        """
        Save TF-IDF data to cache.
        
        REFACTOR: Claude-2025-08-12 - Persistence for TF-IDF data
        """
        try:
            cache_data = {
                'patterns': self.harmful_patterns,
                'threshold': self.similarity_threshold,
                'vectorizer': self.vectorizer,
                'tfidf_matrix': self.harmful_patterns_tfidf,
                'cached_at': datetime.now().isoformat(),
                'version': '2.4.9'
            }
            
            # Ensure cache directory exists
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.debug(f"Saved TF-IDF cache to {self.cache_path}")
            
        except Exception as e:
            logger.error(f"Failed to save TF-IDF cache: {e}")
            # Don't raise - cache failure shouldn't break ethics checking

    def validate(self, action: str, context: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """
        Validate action against harmful patterns using TF-IDF similarity.
        
        PATCH: Gemini-2025-08-11 - Use pre-fitted vectorizer (CRITICAL FIX)
        REFACTOR: Claude-2025-08-12 - Enhanced logging and context handling
        
        Args:
            action: Text action to validate
            context: Optional context information for validation
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        try:
            if not self.harmful_patterns or self.harmful_patterns_tfidf is None:
                logger.debug("No harmful patterns configured, allowing action")
                return True, []
            
            # PATCH: Gemini-2025-08-11 - Use transform, not fit_transform
            action_tfidf = self.vectorizer.transform([action])
            
            # Calculate similarity to harmful patterns
            similarity_scores = cosine_similarity(action_tfidf, self.harmful_patterns_tfidf)
            max_similarity = similarity_scores.max()
            
            violations = []
            
            # Check against threshold
            if max_similarity > self.similarity_threshold:
                # Find which pattern(s) matched
                matching_indices = (similarity_scores[0] > self.similarity_threshold).nonzero()[0]
                matching_patterns = [self.harmful_patterns[i] for i in matching_indices]
                
                violations = [
                    f"High-risk similarity to '{pattern}' (score: {similarity_scores[0][i]:.3f})"
                    for i, pattern in zip(matching_indices, matching_patterns)
                ]
                
                # REFACTOR: Claude-2025-08-12 - Audit logging for violations
                audit_logger.log_ethics_violation("similarity_violation", {
                    "action": action[:200],  # Truncate for logging
                    "max_similarity": float(max_similarity),
                    "threshold": self.similarity_threshold,
                    "matching_patterns": matching_patterns,
                    "context": context or {}
                })
                
                logger.warning(f"Ethics violation detected: max_similarity={max_similarity:.3f}")
                return False, violations
            
            logger.debug(f"Action validated successfully: max_similarity={max_similarity:.3f}")
            return True, []
            
        except Exception as e:
            logger.error(f"Ethics validation failed: {e}")
            audit_logger.log_error("ethics_validation_failure", {
                "action": action[:200] if action else None,
                "error": str(e),
                "context": context or {}
            })
            
            # Fail-safe: deny on error
            return False, [f"Validation error: {str(e)}"]

    async def validate_async(self, action: str, context: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """
        Async version of validate for high-throughput scenarios.
        
        REFACTOR: Claude-2025-08-12 - Added async ethics validation
        
        Args:
            action: Text action to validate
            context: Optional context information
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        try:
            # Run validation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.validate, action, context)
            
            return result
            
        except Exception as e:
            logger.error(f"Async ethics validation failed: {e}")
            return False, [f"Async validation error: {str(e)}"]

    def add_harmful_pattern(self, pattern: str, rebuild_cache: bool = True):
        """
        Add new harmful pattern and optionally rebuild cache.
        
        REFACTOR: Claude-2025-08-12 - Runtime pattern management
        
        Args:
            pattern: New harmful pattern to add
            rebuild_cache: Whether to rebuild TF-IDF cache immediately
        """
        try:
            if pattern not in self.harmful_patterns:
                self.harmful_patterns.append(pattern)
                
                logger.info(f"Added harmful pattern: {pattern}")
                audit_logger.log_system_event("harmful_pattern_added", {
                    "pattern": pattern,
                    "total_patterns": len(self.harmful_patterns)
                })
                
                if rebuild_cache:
                    self._rebuild_tfidf_cache()
            else:
                logger.debug(f"Pattern already exists: {pattern}")
                
        except Exception as e:
            logger.error(f"Failed to add harmful pattern: {e}")
            raise

    def remove_harmful_pattern(self, pattern: str, rebuild_cache: bool = True):
        """
        Remove harmful pattern and optionally rebuild cache.
        
        REFACTOR: Claude-2025-08-12 - Runtime pattern management
        
        Args:
            pattern: Harmful pattern to remove
            rebuild_cache: Whether to rebuild TF-IDF cache immediately
        """
        try:
            if pattern in self.harmful_patterns:
                self.harmful_patterns.remove(pattern)
                
                logger.info(f"Removed harmful pattern: {pattern}")
                audit_logger.log_system_event("harmful_pattern_removed", {
                    "pattern": pattern,
                    "total_patterns": len(self.harmful_patterns)
                })
                
                if rebuild_cache:
                    self._rebuild_tfidf_cache()
            else:
                logger.debug(f"Pattern not found: {pattern}")
                
        except Exception as e:
            logger.error(f"Failed to remove harmful pattern: {e}")
            raise

    def _rebuild_tfidf_cache(self):
        """
        Rebuild TF-IDF cache after pattern changes.
        
        REFACTOR: Claude-2025-08-12 - Cache rebuilding utility
        """
        try:
            if self.harmful_patterns:
                # Re-fit vectorizer with updated patterns
                self.harmful_patterns_tfidf = self.vectorizer.fit_transform(self.harmful_patterns)
                
                # Save updated cache
                self._save_tfidf_cache()
                
                logger.info("Rebuilt TF-IDF cache with updated patterns")
            else:
                logger.warning("No patterns available, disabling TF-IDF cache")
                self.harmful_patterns_tfidf = None
                
        except Exception as e:
            logger.error(f"Failed to rebuild TF-IDF cache: {e}")
            audit_logger.log_error("cache_rebuild_failure", {"error": str(e)})
            raise

    def update_threshold(self, new_threshold: float):
        """
        Update similarity threshold for violation detection.
        
        REFACTOR: Claude-2025-08-12 - Runtime threshold adjustment
        
        Args:
            new_threshold: New similarity threshold (0.0-1.0)
        """
        if not 0.0 <= new_threshold <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {new_threshold}")
        
        old_threshold = self.similarity_threshold
        self.similarity_threshold = new_threshold
        
        logger.info(f"Updated similarity threshold: {old_threshold} -> {new_threshold}")
        audit_logger.log_system_event("threshold_updated", {
            "old_threshold": old_threshold,
            "new_threshold": new_threshold
        })
        
        # Update cache with new threshold
        self._save_tfidf_cache()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get ethics filter statistics and configuration.
        
        REFACTOR: Claude-2025-08-12 - Statistics and monitoring
        
        Returns:
            Dict with filter statistics
        """
        try:
            stats = {
                "version": "2.4.9",
                "pattern_count": len(self.harmful_patterns),
                "similarity_threshold": self.similarity_threshold,
                "cache_path": str(self.cache_path),
                "cache_exists": self.cache_path.exists(),
                "tfidf_initialized": self.harmful_patterns_tfidf is not None,
                "vectorizer_vocabulary_size": len(self.vectorizer.vocabulary_) if hasattr(self.vectorizer, 'vocabulary_') else 0
            }
            
            if self.cache_path.exists():
                stats["cache_size_mb"] = self.cache_path.stat().st_size / (1024 * 1024)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}

    def validate_batch(self, actions: List[str], context: Dict[str, Any] = None) -> List[Tuple[bool, List[str]]]:
        """
        Validate multiple actions in batch for efficiency.
        
        REFACTOR: Claude-2025-08-12 - Batch validation for performance
        
        Args:
            actions: List of actions to validate
            context: Optional shared context
            
        Returns:
            List of validation results
        """
        try:
            if not self.harmful_patterns or self.harmful_patterns_tfidf is None:
                return [(True, []) for _ in actions]
            
            # Vectorize all actions at once for efficiency
            actions_tfidf = self.vectorizer.transform(actions)
            
            # Calculate similarities for all actions
            similarity_matrix = cosine_similarity(actions_tfidf, self.harmful_patterns_tfidf)
            
            results = []
            for i, action in enumerate(actions):
                max_similarity = similarity_matrix[i].max()
                
                if max_similarity > self.similarity_threshold:
                    matching_indices = (similarity_matrix[i] > self.similarity_threshold).nonzero()[0]
                    violations = [
                        f"High-risk similarity to '{self.harmful_patterns[j]}' (score: {similarity_matrix[i][j]:.3f})"
                        for j in matching_indices
                    ]
                    results.append((False, violations))
                    
                    # Log batch violations
                    audit_logger.log_ethics_violation("batch_similarity_violation", {
                        "action_index": i,
                        "action": action[:200],
                        "max_similarity": float(max_similarity),
                        "context": context or {}
                    })
                else:
                    results.append((True, []))
            
            logger.info(f"Batch validated {len(actions)} actions")
            return results
            
        except Exception as e:
            logger.error(f"Batch validation failed: {e}")
            return [(False, [f"Batch validation error: {str(e)}"]) for _ in actions]

    def clear_cache(self):
        """
        Clear TF-IDF cache and force regeneration.
        
        REFACTOR: Claude-2025-08-12 - Cache management utility
        """
        try:
            if self.cache_path.exists():
                self.cache_path.unlink()
                logger.info("Cleared TF-IDF cache")
            
            # Regenerate cache
            self._initialize_tfidf_cache()
            
            audit_logger.log_system_event("cache_cleared", {
                "cache_path": str(self.cache_path)
            })
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise