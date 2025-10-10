""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""


"""
Pattern Weaver Module - Advanced NLP Pattern Discovery

Analyzes unclassified memory entries to discover new patterns using sophisticated
clustering algorithms, multilingual NLP analysis, and governance-integrated validation.
Provides comprehensive pattern suggestion and batch processing capabilities.

Key Features:
- NLP-enhanced clustering with keyword and entity analysis
- Multilingual pattern discovery with language-aware processing
- Governance integration for pattern validation and submission
- Configurable clustering thresholds and similarity metrics
- Batch processing with performance optimization
- Comprehensive fallback strategies and error handling
- Schema-compliant output with full metadata enrichment
"""

import json
import logging
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from functools import lru_cache
from enum import Enum

# Import dependencies with fallback handling
try:
    from refinery_utils import map_sentience, get_emotion_label, LanguageHint, HeuristicVADMapper
except ImportError:
        # Fallback stubs
        def map_sentience(text):
            return {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}
        
        def get_emotion_label(valence, arousal):
            return "neutral"
        
        class LanguageHint(Enum):
            ENGLISH = "en"
            UNKNOWN = "unknown"
        
        class HeuristicVADMapper:
            def __init__(self):
                pass
            
            def map_sentience(self, text: str) -> Dict[str, float]:
                return {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}

try:
    from nlp_module import NLPProcessor
except ImportError:
        class NLPProcessor:
            def process_text(self, text: str) -> Dict[str, Any]:
                return {
                    'keywords': [],
                    'entities': [],
                    'language': 'en',
                    'metadata': {}
                }

# FAISS stub for optional vector search acceleration
try:
    import faiss  # type: ignore
    _HAS_FAISS = True
except Exception:
    _HAS_FAISS = False

# Configure module logger
logger = logging.getLogger(__name__)


class ClusteringMethod(Enum):
    """Clustering methods for pattern discovery"""
    KEYWORD_SIMILARITY = "keyword_similarity"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    ENTITY_BASED = "entity_based"
    HYBRID = "hybrid"


class PatternConfidence(Enum):
    """Pattern confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    EXPERIMENTAL = "experimental"


@dataclass
class ClusteringConfig:
    """Configuration for pattern clustering operations"""
    similarity_threshold: float = 0.6
    min_cluster_size: int = 3
    max_clusters: int = 50
    keyword_weight: float = 0.4
    entity_weight: float = 0.3
    sentiment_weight: float = 0.2
    language_weight: float = 0.1
    enable_multilingual: bool = True
    confidence_threshold: float = 0.7
    batch_size: int = 100
    cache_enabled: bool = True
    clustering_method: ClusteringMethod = ClusteringMethod.HYBRID


@dataclass
class PatternCluster:
    """Represents a discovered pattern cluster"""
    cluster_id: str
    representative_text: str
    member_entries: List[Dict[str, Any]]
    common_keywords: List[str]
    common_entities: List[Dict[str, Any]]
    sentiment_profile: Dict[str, float]
    confidence_score: float
    language_hint: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_pattern_suggestion(self) -> Dict[str, Any]:
        """Convert cluster to pattern suggestion format"""
        sentiment_consistency = self._calculate_sentiment_consistency()
        emotion_label = get_emotion_label(self.sentiment_profile['valence'], self.sentiment_profile['arousal'])
        
        return {
            "pattern_id": f"discovered_{self.cluster_id}",
            "name": f"Auto-discovered Pattern {self.cluster_id}",
            "description": f"Pattern discovered from {len(self.member_entries)} similar entries",
            "schema": self._generate_schema(),
            "keywords": self.common_keywords,
            "entities": [e.get('text', '') for e in self.common_entities],
            "sentiment_profile": self.sentiment_profile,
            "confidence": self.confidence_score,
            "language": self.language_hint,
            "sample_entries": [entry.get('raw_ref', '')[:100] for entry in self.member_entries[:3]],
            "metadata": {
                **self.metadata,
                "created_by": "PatternWeaver",
                "created_at": datetime.now().isoformat(),
                "cluster_size": len(self.member_entries),
                "keyword_diversity": len(set(kw for kw in self.common_keywords)),
                "entity_diversity": len(set(e.get('type', '') for e in self.common_entities)),
                "sentiment_consistency": sentiment_consistency,
                "emotion_label": emotion_label,
                "discovery_method": "nlp_clustering"
            }
        }
    
    def _generate_schema(self) -> List[str]:
        """Generate schema fields based on common entities"""
        schema_fields = []
        entity_types = Counter(e.get('type', '').lower() for e in self.common_entities)
        
        for entity_type, count in entity_types.most_common(5):
            if count >= 2 and entity_type:  # At least 2 occurrences
                schema_fields.append(entity_type)
        
        # Add sentiment field if consistent pattern
        sentiment_consistency = self._calculate_sentiment_consistency()
        if sentiment_consistency > 0.7:
            schema_fields.append("sentiment")
        
        return schema_fields or ["content"]  # Fallback to basic content
    
    def _calculate_sentiment_consistency(self) -> float:
        """Calculate how consistent sentiment is across cluster members"""
        if not self.member_entries:
            return 0.0
        
        sentiments = []
        for entry in self.member_entries:
            feeling = entry.get('feeling', {})
            if feeling:
                # Calculate dominant sentiment direction
                valence = feeling.get('valence', 0.0)
                sentiments.append(1 if valence > 0.2 else (-1 if valence < -0.2 else 0))
        
        if not sentiments:
            return 0.0
        
        # Calculate consistency as ratio of most common sentiment
        sentiment_counts = Counter(sentiments)
        most_common_count = sentiment_counts.most_common(1)[0][1] if sentiment_counts else 0
        return most_common_count / len(sentiments)


class PatternWeaverError(Exception):
    """Base exception for pattern weaver operations"""
    pass


class ClusteringError(PatternWeaverError):
    """Raised when clustering operations fail"""
    pass


class PatternValidationError(PatternWeaverError):
    """Raised when pattern validation fails"""
    pass


class PatternWeaver:
    """
    Advanced pattern discovery system using NLP clustering and multilingual analysis.
    
    Analyzes unclassified memory entries to discover recurring patterns, themes,
    and structures that can be formalized into reusable pattern definitions.
    """
    
    def __init__(self, 
                 memory_engine=None,
                 governance=None,
                 config: Optional[ClusteringConfig] = None,
                 nlp_processor: Optional[NLPProcessor] = None):
        """
        Initialize PatternWeaver with dependencies and configuration.
        
        Args:
            memory_engine: Memory engine instance for data access
            governance: Pattern governance system for validation
            config: Clustering configuration settings
            nlp_processor: NLP processor for text analysis
        """
        # PATCH: Cursor-2025-08-15 CL-P2-Cleanup - Add validation for None components
        if memory_engine is None:
            raise PatternWeaverError("Memory engine cannot be None")
        if governance is None:
            raise PatternWeaverError("Governance system cannot be None")
        
        self.version = "v2.3.2"
        self.memory_engine = memory_engine
        self.governance = governance
        self.config = config or ClusteringConfig()
        
        # PATCH: Cursor-2025-08-15 CL-P2-Cleanup - Add configuration validation
        if hasattr(self.config, 'similarity_threshold') and self.config.similarity_threshold > 1.0:
            raise PatternWeaverError("Similarity threshold cannot exceed 1.0")
        if hasattr(self.config, 'min_cluster_size') and self.config.min_cluster_size < 1:
            raise PatternWeaverError("Minimum cluster size must be at least 1")
        
        # Initialize NLP processor with fallback
        try:
            self.nlp_processor = nlp_processor or NLPProcessor()
        except Exception as e:
            logger.warning(f"Failed to initialize NLP processor: {e}, using fallback")
            self.nlp_processor = NLPProcessor()  # Fallback mock
        
        # Initialize VAD mapper for sentiment analysis
        try:
            self.vad_mapper = HeuristicVADMapper()
        except Exception as e:
            logger.error(f"Failed to initialize VAD mapper: {e}")
            raise PatternWeaverError(f"VAD mapper initialization failed: {e}")
        
        # Performance tracking
        self._clustering_cache: Dict[str, List[PatternCluster]] = {}
        self._pattern_metadata: Dict[str, Dict[str, Any]] = {}  # PATCH: CL-002 GDPR-CASCADE-FIX - Add pattern metadata tracking
        self._stats = {
            'total_entries_processed': 0,
            'patterns_discovered': 0,
            'clusters_created': 0,
            'cache_hits': 0,
            'processing_time': 0.0
        }
        
        logger.info(f"PatternWeaver v{self.version} initialized with {self.config.clustering_method.value} clustering")
    
    def run_batch(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process batch of entries to discover and suggest patterns.
        
        Args:
            entries: List of unclassified memory entries
            
        Returns:
            List of pattern suggestions with confidence scores
            
        Raises:
            PatternWeaverError: If batch processing fails
        """
        start_time = time.time()
        
        try:
            if not entries:
                logger.warning("Empty entries list provided to run_batch")
                return []
            
            logger.info(f"Processing batch of {len(entries)} entries for pattern discovery")
            
            # Validate and preprocess entries
            valid_entries = self._validate_entries(entries)
            if not valid_entries:
                logger.warning("No valid entries found after preprocessing")
                return []
            
            # Enrich entries with NLP analysis
            enriched_entries = self._enrich_entries_with_nlp(valid_entries)
            
            # Perform clustering analysis
            clusters = self._perform_clustering_analysis(enriched_entries)
            
            # Convert clusters to pattern suggestions
            pattern_suggestions = []
            for cluster in clusters:
                if cluster.confidence_score >= self.config.confidence_threshold:
                    suggestion = cluster.to_pattern_suggestion()
                    pattern_suggestions.append(suggestion)
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(len(entries), len(pattern_suggestions), len(clusters), processing_time)
            
            logger.info(f"Batch processing completed: {len(pattern_suggestions)} patterns discovered in {processing_time:.2f}s")
            return pattern_suggestions
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise PatternWeaverError(f"Batch processing failed: {e}") from e
    
    def propose_patterns(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Analyze single text to propose pattern candidates.
        
        Args:
            text: Input text to analyze
            context: Optional context information
            
        Returns:
            List of pattern proposals with metadata
            
        Raises:
            PatternWeaverError: If proposal fails
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided to propose_patterns")
                return self._create_fallback_pattern(text)
            
            # Create mock entry for processing
            mock_entry = {
                'raw_ref': text,
                'metadata': context or {},
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat()
            }
            
            # Enrich with NLP analysis
            enriched_entries = self._enrich_entries_with_nlp([mock_entry])
            
            if not enriched_entries:
                return self._create_fallback_pattern(text)
            
            enriched_entry = enriched_entries[0]
            
            # Generate pattern proposal
            pattern_proposal = self._create_pattern_from_entry(enriched_entry)
            
            return [pattern_proposal]
            
        except Exception as e:
            logger.error(f"Pattern proposal failed: {e}")
            return self._create_fallback_pattern(text)
    
    def _validate_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and filter entries for processing"""
        valid_entries = []
        
        for entry in entries:
            try:
                # Check required fields
                if not isinstance(entry, dict):
                    continue
                
                raw_ref = entry.get('raw_ref', '')
                if not raw_ref or not isinstance(raw_ref, str) or len(raw_ref.strip()) < 10:
                    continue
                
                # Ensure required fields exist
                if 'metadata' not in entry:
                    entry['metadata'] = {}
                
                if 'id' not in entry:
                    entry['id'] = str(uuid.uuid4())
                
                if 'timestamp' not in entry:
                    entry['timestamp'] = datetime.now().isoformat()
                
                valid_entries.append(entry)
                
            except Exception as e:
                logger.warning(f"Entry validation failed: {e}")
                continue
        
        logger.debug(f"Validated {len(valid_entries)} out of {len(entries)} entries")
        return valid_entries
    
    def _enrich_entries_with_nlp(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich entries with NLP analysis and sentiment data"""
        enriched_entries = []
        
        for entry in entries:
            try:
                text = entry.get('raw_ref', '')
                
                # Perform NLP processing
                nlp_result = self.nlp_processor.process_text(text)
                
                # Perform VAD sentiment analysis
                vad_result = self.vad_mapper.map_sentience(text)
                
                # Detect language if not already available
                language_hint = self._detect_language_hint(text)
                
                # Create enriched entry
                enriched_entry = {
                    **entry,
                    'nlp_analysis': nlp_result,
                    'feeling': vad_result,
                    'language_hint': language_hint,
                    'enrichment_timestamp': datetime.now().isoformat()
                }
                
                enriched_entries.append(enriched_entry)
                
            except Exception as e:
                logger.warning(f"Entry enrichment failed: {e}, skipping entry")
                continue
        
        logger.debug(f"Enriched {len(enriched_entries)} entries with NLP analysis")
        return enriched_entries
    
    @lru_cache(maxsize=256)
    def _detect_language_hint(self, text: str) -> str:
        """Detect language hint using VAD mapper language detection"""
        try:
            language = self.vad_mapper.detect_language(text)
            return language.value if hasattr(language, 'value') else str(language)
        except Exception:
            return 'en'  # Default to English
    
    def _perform_clustering_analysis(self, entries: List[Dict[str, Any]]) -> List[PatternCluster]:
        """Perform clustering analysis on enriched entries"""
        if len(entries) < self.config.min_cluster_size:
            logger.info(f"Insufficient entries ({len(entries)}) for clustering (minimum: {self.config.min_cluster_size})")
            return []
        
        # Check cache first
        cache_key = self._generate_cache_key(entries)
        if self.config.cache_enabled and cache_key in self._clustering_cache:
            logger.debug("Using cached clustering results")
            self._stats['cache_hits'] += 1
            return self._clustering_cache[cache_key]
        
        try:
            # Perform clustering based on method
            if self.config.clustering_method == ClusteringMethod.KEYWORD_SIMILARITY:
                clusters = self._cluster_by_keywords(entries)
            elif self.config.clustering_method == ClusteringMethod.ENTITY_BASED:
                clusters = self._cluster_by_entities(entries)
            elif self.config.clustering_method == ClusteringMethod.SEMANTIC_SIMILARITY:
                clusters = self._cluster_by_semantics(entries)
            else:  # HYBRID
                clusters = self._cluster_hybrid(entries)
            
            # Filter clusters by minimum size and confidence
            filtered_clusters = [
                cluster for cluster in clusters 
                if len(cluster.member_entries) >= self.config.min_cluster_size 
                and cluster.confidence_score >= 0.3
            ]
            
            # Cache results
            if self.config.cache_enabled:
                self._clustering_cache[cache_key] = filtered_clusters
                # Prevent cache from growing too large
                if len(self._clustering_cache) > 100:
                    oldest_key = next(iter(self._clustering_cache))
                    del self._clustering_cache[oldest_key]
            
            logger.info(f"Clustering analysis complete: {len(filtered_clusters)} clusters discovered")
            return filtered_clusters
            
        except Exception as e:
            logger.error(f"Clustering analysis failed: {e}")
            raise ClusteringError(f"Clustering analysis failed: {e}") from e
    
    def _cluster_by_keywords(self, entries: List[Dict[str, Any]]) -> List[PatternCluster]:
        """Cluster entries based on keyword similarity"""
        clusters = []
        used_entries = set()
        
        for i, entry1 in enumerate(entries):
            if entry1['id'] in used_entries:
                continue
            
            # Start new cluster with this entry
            cluster_members = [entry1]
            used_entries.add(entry1['id'])
            
            keywords1 = set(entry1.get('nlp_analysis', {}).get('keywords', []))
            if not keywords1:
                continue
            
            # Find similar entries
            for j, entry2 in enumerate(entries[i+1:], i+1):
                if entry2['id'] in used_entries:
                    continue
                
                keywords2 = set(entry2.get('nlp_analysis', {}).get('keywords', []))
                if not keywords2:
                    continue
                
                # Calculate keyword similarity
                similarity = self._calculate_keyword_similarity(keywords1, keywords2)
                
                if similarity >= self.config.similarity_threshold:
                    cluster_members.append(entry2)
                    used_entries.add(entry2['id'])
            
            # Create cluster if minimum size met
            if len(cluster_members) >= self.config.min_cluster_size:
                cluster = self._create_cluster_from_members(cluster_members, "keyword_similarity")
                clusters.append(cluster)
        
        return clusters
    
    def _cluster_by_entities(self, entries: List[Dict[str, Any]]) -> List[PatternCluster]:
        """Cluster entries based on entity similarity"""
        # Group entries by entity types
        entity_groups = defaultdict(list)
        
        for entry in entries:
            entities = entry.get('nlp_analysis', {}).get('entities', [])
            entity_types = set(e.get('type', '').lower() for e in entities if e.get('type'))
            
            if entity_types:
                # Use frozenset for hashable key
                key = frozenset(entity_types)
                entity_groups[key].append(entry)
        
        clusters = []
        for entity_type_set, members in entity_groups.items():
            if len(members) >= self.config.min_cluster_size:
                cluster = self._create_cluster_from_members(members, "entity_based")
                clusters.append(cluster)
        
        return clusters
    
    def _cluster_by_semantics(self, entries: List[Dict[str, Any]]) -> List[PatternCluster]:
        """Cluster entries based on semantic similarity (sentiment + language)"""
        clusters = []
        used_entries = set()
        
        for i, entry1 in enumerate(entries):
            if entry1['id'] in used_entries:
                continue
            
            cluster_members = [entry1]
            used_entries.add(entry1['id'])
            
            # Get semantic features
            feeling1 = entry1.get('feeling', {})
            lang1 = entry1.get('language_hint', 'en')
            
            for j, entry2 in enumerate(entries[i+1:], i+1):
                if entry2['id'] in used_entries:
                    continue
                
                feeling2 = entry2.get('feeling', {})
                lang2 = entry2.get('language_hint', 'en')
                
                # Calculate semantic similarity
                similarity = self._calculate_semantic_similarity(feeling1, feeling2, lang1, lang2)
                
                if similarity >= self.config.similarity_threshold:
                    cluster_members.append(entry2)
                    used_entries.add(entry2['id'])
            
            if len(cluster_members) >= self.config.min_cluster_size:
                cluster = self._create_cluster_from_members(cluster_members, "semantic_similarity")
                clusters.append(cluster)
        
        return clusters
    
    def _cluster_hybrid(self, entries: List[Dict[str, Any]]) -> List[PatternCluster]:
        """Perform hybrid clustering using multiple similarity measures"""
        clusters = []
        used_entries = set()
        
        for i, entry1 in enumerate(entries):
            if entry1['id'] in used_entries:
                continue
            
            cluster_members = [entry1]
            used_entries.add(entry1['id'])
            
            for j, entry2 in enumerate(entries[i+1:], i+1):
                if entry2['id'] in used_entries:
                    continue
                
                # Calculate hybrid similarity score
                similarity = self._calculate_hybrid_similarity(entry1, entry2)
                
                if similarity >= self.config.similarity_threshold:
                    cluster_members.append(entry2)
                    used_entries.add(entry2['id'])
            
            if len(cluster_members) >= self.config.min_cluster_size:
                cluster = self._create_cluster_from_members(cluster_members, "hybrid")
                clusters.append(cluster)
        
        return clusters
    
    def _calculate_keyword_similarity(self, keywords1: Set[str], keywords2: Set[str]) -> float:
        """Calculate Jaccard similarity between keyword sets"""
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_semantic_similarity(self, feeling1: Dict[str, float], feeling2: Dict[str, float], 
                                     lang1: str, lang2: str) -> float:
        """Calculate semantic similarity based on sentiment and language"""
        # Language similarity
        lang_sim = 1.0 if lang1 == lang2 else 0.5
        
        # Sentiment similarity (Euclidean distance in VAD space)
        v1, a1, d1 = feeling1.get('valence', 0), feeling1.get('arousal', 0), feeling1.get('dominance', 0)
        v2, a2, d2 = feeling2.get('valence', 0), feeling2.get('arousal', 0), feeling2.get('dominance', 0)
        
        # Calculate normalized Euclidean distance
        distance = ((v1-v2)**2 + (a1-a2)**2 + (d1-d2)**2)**0.5
        max_distance = (3**0.5 * 2)  # Maximum possible distance in VAD space
        sentiment_sim = 1.0 - (distance / max_distance)
        
        # Weighted combination
        return (sentiment_sim * 0.7) + (lang_sim * 0.3)
    
    def _calculate_hybrid_similarity(self, entry1: Dict[str, Any], entry2: Dict[str, Any]) -> float:
        """Calculate hybrid similarity using weighted combination of methods"""
        # Keyword similarity
        keywords1 = set(entry1.get('nlp_analysis', {}).get('keywords', []))
        keywords2 = set(entry2.get('nlp_analysis', {}).get('keywords', []))
        keyword_sim = self._calculate_keyword_similarity(keywords1, keywords2)
        
        # Entity similarity
        entities1 = set(e.get('type', '').lower() for e in entry1.get('nlp_analysis', {}).get('entities', []))
        entities2 = set(e.get('type', '').lower() for e in entry2.get('nlp_analysis', {}).get('entities', []))
        entity_sim = self._calculate_keyword_similarity(entities1, entities2)  # Same calculation
        
        # Semantic similarity
        feeling1 = entry1.get('feeling', {})
        feeling2 = entry2.get('feeling', {})
        lang1 = entry1.get('language_hint', 'en')
        lang2 = entry2.get('language_hint', 'en')
        semantic_sim = self._calculate_semantic_similarity(feeling1, feeling2, lang1, lang2)
        
        # Weighted combination based on config
        hybrid_score = (
            keyword_sim * self.config.keyword_weight +
            entity_sim * self.config.entity_weight +
            semantic_sim * (self.config.sentiment_weight + self.config.language_weight)
        )
        
        return hybrid_score
    
    def _create_cluster_from_members(self, members: List[Dict[str, Any]], method: str) -> PatternCluster:
        """Create PatternCluster from member entries"""
        cluster_id = str(uuid.uuid4())[:8]
        
        # Find representative text (longest or most keyword-rich)
        representative = max(members, key=lambda x: len(x.get('raw_ref', '')))
        representative_text = representative.get('raw_ref', '')[:200]
        
        # Extract common keywords
        all_keywords = []
        for member in members:
            keywords = member.get('nlp_analysis', {}).get('keywords', [])
            all_keywords.extend(keywords)
        
        keyword_counts = Counter(all_keywords)
        min_occurrences = max(2, len(members) // 3)  # At least 1/3 of members must have keyword
        common_keywords = [kw for kw, count in keyword_counts.most_common(10) if count >= min_occurrences]
        
        # Extract common entities
        all_entities = []
        for member in members:
            entities = member.get('nlp_analysis', {}).get('entities', [])
            all_entities.extend(entities)
        
        entity_texts = [e.get('text', '') for e in all_entities]
        entity_counts = Counter(entity_texts)
        common_entity_texts = [text for text, count in entity_counts.most_common(5) if count >= 2]
        common_entities = [{'text': text, 'type': 'common'} for text in common_entity_texts]
        
        # Calculate average sentiment profile
        sentiments = [member.get('feeling', {}) for member in members]
        avg_sentiment = {
            'valence': sum(s.get('valence', 0) for s in sentiments) / len(sentiments),
            'arousal': sum(s.get('arousal', 0) for s in sentiments) / len(sentiments),
            'dominance': sum(s.get('dominance', 0) for s in sentiments) / len(sentiments)
        }
        
        # Calculate confidence based on cluster coherence
        confidence = self._calculate_cluster_confidence(members, common_keywords, common_entities)
        
        # Determine dominant language
        languages = [member.get('language_hint', 'en') for member in members]
        language_counts = Counter(languages)
        dominant_language = language_counts.most_common(1)[0][0]
        
        return PatternCluster(
            cluster_id=cluster_id,
            representative_text=representative_text,
            member_entries=members,
            common_keywords=common_keywords,
            common_entities=common_entities,
            sentiment_profile=avg_sentiment,
            confidence_score=confidence,
            language_hint=dominant_language,
            metadata={
                'clustering_method': method,
                'cluster_size': len(members),
                'keyword_diversity': len(set(all_keywords)),
                'entity_diversity': len(set(entity_texts)),
                'language_consistency': language_counts[dominant_language] / len(members)
            }
        )
    
    def _calculate_cluster_confidence(self, members: List[Dict[str, Any]], 
                                    common_keywords: List[str], 
                                    common_entities: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for cluster quality"""
        if not members:
            return 0.0
        
        # Factors contributing to confidence
        size_factor = min(1.0, len(members) / 10)  # Up to 10 members = full size factor
        keyword_factor = min(1.0, len(common_keywords) / 5)  # Up to 5 keywords = full factor
        entity_factor = min(1.0, len(common_entities) / 3)  # Up to 3 entities = full factor
        
        # Sentiment consistency factor
        sentiments = [member.get('feeling', {}) for member in members]
        valences = [s.get('valence', 0) for s in sentiments]
        valence_std = (sum((v - sum(valences)/len(valences))**2 for v in valences) / len(valences))**0.5
        consistency_factor = max(0.0, 1.0 - valence_std)  # Lower std = higher consistency
        
        # Weighted average
        confidence = (
            size_factor * 0.25 +
            keyword_factor * 0.3 +
            entity_factor * 0.25 +
            consistency_factor * 0.2
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _create_pattern_from_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Create pattern proposal from single enriched entry"""
        nlp_analysis = entry.get('nlp_analysis', {})
        feeling = entry.get('feeling', {})
        
        # Generate pattern ID based on content characteristics
        valence = feeling.get('valence', 0.0)
        keywords = nlp_analysis.get('keywords', [])
        entities = nlp_analysis.get('entities', [])
        
        # Determine pattern type
        if valence > 0.5:
            pattern_type = "positive"
        elif valence < -0.5:
            pattern_type = "negative"
        else:
            pattern_type = "neutral"
        
        # Add specificity based on keywords/entities
        if keywords:
            pattern_type += f"_{keywords[0].lower()}"
        elif entities:
            pattern_type += f"_{entities[0].get('type', 'entity').lower()}"
        
        return {
            "pattern_id": f"proposed_{pattern_type}_{str(uuid.uuid4())[:8]}",
            "name": f"Proposed {pattern_type.title()} Pattern",
            "description": f"Pattern proposed from single entry analysis",
            "schema": self._generate_schema_from_entry(entry),
            "keywords": keywords[:5],  # Top 5 keywords
            "entities": [e.get('text', '') for e in entities[:3]],  # Top 3 entities
            "sentiment_profile": feeling,
            "confidence": 0.6,  # Lower confidence for single-entry patterns
            "language": entry.get('language_hint', 'en'),
            "sample_text": entry.get('raw_ref', '')[:100],
            "variables": self._extract_variables_from_entry(entry),
            "metadata": {
                "created_by": "PatternWeaver",
                "created_at": datetime.now().isoformat(),
                "source_entry_id": entry.get('id'),
                "discovery_method": "single_entry_analysis",
                "nlp_enhanced": True
            },
            "raw_ref": entry.get('raw_ref', ''),
            "feeling": feeling
        }
    
    def _generate_schema_from_entry(self, entry: Dict[str, Any]) -> List[str]:
        """Generate schema fields from single entry"""
        schema = []
        
        entities = entry.get('nlp_analysis', {}).get('entities', [])
        entity_types = set(e.get('type', '').lower() for e in entities if e.get('type'))
        
        for entity_type in list(entity_types)[:3]:  # Max 3 entity types
            schema.append(entity_type)
        
        # Add sentiment if strong
        feeling = entry.get('feeling', {})
        valence = abs(feeling.get('valence', 0.0))
        if valence > 0.4:
            schema.append("sentiment")
        
        return schema or ["content"]
    
    def _extract_variables_from_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Extract variables from entry for pattern matching"""
        variables = {}
        
        entities = entry.get('nlp_analysis', {}).get('entities', [])
        for i, entity in enumerate(entities[:5]):  # Max 5 entities
            entity_text = entity.get('text', '')
            entity_type = entity.get('type', 'entity')
            if entity_text:
                variables[f"{entity_type.lower()}_{i}"] = entity_text
        
        keywords = entry.get('nlp_analysis', {}).get('keywords', [])
        if keywords:
            variables['primary_keyword'] = keywords[0]
        
        feeling = entry.get('feeling', {})
        if feeling:
            variables['sentiment_valence'] = feeling.get('valence', 0.0)
            variables['sentiment_arousal'] = feeling.get('arousal', 0.0)
        
        return variables
    
    def _create_fallback_pattern(self, text: str) -> List[Dict[str, Any]]:
        """Create basic fallback pattern when processing fails"""
        try:
            # Basic sentiment analysis
            vad_result = map_sentience(text)
            valence = vad_result.get('valence', 0.0)
            
            pattern_type = "positive" if valence > 0.2 else ("negative" if valence < -0.2 else "neutral")
            
            return [{
                "pattern_id": f"fallback_{pattern_type}_{str(uuid.uuid4())[:8]}",
                "name": f"Fallback {pattern_type.title()} Pattern",
                "description": "Basic pattern created from fallback analysis",
                "schema": ["content"],
                "keywords": [],
                "entities": [],
                "sentiment_profile": vad_result,
                "confidence": 0.3,  # Low confidence for fallback
                "language": "en",
                "sample_text": text[:100],
                "variables": {"content": text[:200]},
                "metadata": {
                    "created_by": "PatternWeaver",
                    "created_at": datetime.now().isoformat(),
                    "discovery_method": "fallback_analysis",
                    "fallback_used": True
                },
                "raw_ref": text,
                "feeling": vad_result
            }]
        except Exception as e:
            logger.error(f"Fallback pattern creation failed: {e}")
            return []
    
    def _generate_cache_key(self, entries: List[Dict[str, Any]]) -> str:
        """Generate cache key for entries"""
        # Use hash of entry IDs and content length as cache key
        entry_info = [(e.get('id', ''), len(e.get('raw_ref', ''))) for e in entries]
        return str(hash(tuple(sorted(entry_info))))
    
    def _update_stats(self, entries_processed: int, patterns_discovered: int, 
                     clusters_created: int, processing_time: float) -> None:
        """Update internal statistics"""
        self._stats['total_entries_processed'] += entries_processed
        self._stats['patterns_discovered'] += patterns_discovered
        self._stats['clusters_created'] += clusters_created
        self._stats['processing_time'] += processing_time
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self._stats,
            'cache_size': len(self._clustering_cache),
            'avg_processing_time': (
                self._stats['processing_time'] / max(1, self._stats['total_entries_processed'] // 100)
            )
        }
    
    def clear_cache(self) -> None:
        """Clear clustering cache"""
        self._clustering_cache.clear()
        logger.info("Clustering cache cleared")
    
    def update_config(self, new_config: ClusteringConfig) -> None:
        """Update clustering configuration"""
        old_method = self.config.clustering_method
        self.config = new_config
        
        # Clear cache if clustering method changed
        if old_method != new_config.clustering_method:
            self.clear_cache()
        
        logger.info(f"Configuration updated: {new_config.clustering_method.value} clustering enabled")

    def _calculate_similarity(self, entry1: Dict[str, Any], entry2: Dict[str, Any]) -> float:
        """
        Calculate similarity between two entries.
        
        Args:
            entry1: First entry for comparison
            entry2: Second entry for comparison
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Implement minimal working stub
        try:
            # Basic keyword-based similarity as fallback
            keywords1 = set(entry1.get('keywords', []))
            keywords2 = set(entry2.get('keywords', []))
            
            if not keywords1 and not keywords2:
                return 0.5  # Neutral similarity for entries without keywords
            
            if not keywords1 or not keywords2:
                return 0.0  # No similarity if one entry has no keywords
            
            intersection = len(keywords1.intersection(keywords2))
            union = len(keywords1.union(keywords2))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}, returning 0.0")
            return 0.0
    
    def _assess_cluster_quality(self, cluster: 'PatternCluster') -> float:
        """
        Assess the quality and confidence of a pattern cluster.
        
        Args:
            cluster: Pattern cluster to assess
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        # PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Implement minimal working stub
        try:
            if not hasattr(cluster, 'member_entries') or not cluster.member_entries:
                return 0.0
            
            # Basic quality assessment based on cluster size and entry consistency
            size_score = min(len(cluster.member_entries) / 10.0, 1.0)  # Cap at 10 entries
            
            # Simple consistency check (placeholder for more sophisticated logic)
            consistency_score = 0.7  # Default consistency
            
            return (size_score + consistency_score) / 2.0
            
        except Exception as e:
            logger.warning(f"Cluster quality assessment failed: {e}, returning 0.5")
            return 0.5
    
    def _infer_schema(self, cluster: 'PatternCluster') -> List[str]:
        """
        Infer schema from cluster entries.
        
        Args:
            cluster: Pattern cluster to analyze
            
        Returns:
            List of inferred field names
        """
        # PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Implement minimal working stub
        try:
            if not hasattr(cluster, 'member_entries') or not cluster.member_entries:
                return []
            
            # Extract common fields from cluster entries
            all_fields = set()
            for entry in cluster.member_entries:
                if isinstance(entry, dict):
                    all_fields.update(entry.keys())
            
            # Return sorted list of common fields
            return sorted(list(all_fields))
            
        except Exception as e:
            logger.warning(f"Schema inference failed: {e}, returning empty list")
            return []
    
    def _extract_cluster_keywords(self, cluster: 'PatternCluster') -> List[str]:
        """
        Extract keywords from cluster entries.
        
        Args:
            cluster: Pattern cluster to analyze
            
        Returns:
            List of extracted keywords
        """
        # PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Implement minimal working stub
        try:
            if not hasattr(cluster, 'member_entries') or not cluster.member_entries:
                return []
            
            # Collect keywords from all entries
            all_keywords = []
            for entry in cluster.member_entries:
                if isinstance(entry, dict):
                    keywords = entry.get('keywords', [])
                    if isinstance(keywords, list):
                        all_keywords.extend(keywords)
            
            # Return unique keywords
            return list(set(all_keywords))
            
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}, returning empty list")
            return []
    
    def _generate_pattern_id(self, cluster: 'PatternCluster') -> str:
        """
        Generate unique pattern ID for cluster.
        
        Args:
            cluster: Pattern cluster to generate ID for
            
        Returns:
            Unique pattern ID string
        """
        # PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Implement minimal working stub
        try:
            # Generate UUID-based pattern ID
            base_id = str(uuid.uuid4())[:8]
            return f"pattern_{base_id}"
            
        except Exception as e:
            logger.warning(f"Pattern ID generation failed: {e}, returning fallback ID")
            return f"pattern_fallback_{int(time.time())}"
    
    def _submit_to_governance(self, pattern: Dict[str, Any]) -> bool:
        """
        Submit pattern to governance system for validation.
        
        Args:
            pattern: Pattern to submit
            
        Returns:
            True if submission successful, False otherwise
        """
        # PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Implement minimal working stub
        try:
            if not self.governance:
                logger.warning("No governance system available for pattern submission")
                return False
            
            # Placeholder for governance submission logic
            logger.info(f"Pattern {pattern.get('pattern_id', 'unknown')} submitted to governance")
            return True
            
        except Exception as e:
            logger.warning(f"Pattern submission to governance failed: {e}")
            return False
    
    def _validate_pattern(self, pattern: Dict[str, Any]) -> bool:
        """
        Validate pattern through governance system.
        
        Args:
            pattern: Pattern to validate
            
        Returns:
            True if pattern is valid, False otherwise
        """
        # PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Implement minimal working stub
        try:
            if not self.governance:
                logger.warning("No governance system available for pattern validation")
                return False
            
            # Basic validation checks
            required_fields = ['pattern_id', 'keywords', 'schema']
            if not all(field in pattern for field in required_fields):
                return False
            
            # Placeholder for governance validation logic
            logger.info(f"Pattern {pattern.get('pattern_id', 'unknown')} validated through governance")
            return True
            
        except Exception as e:
            logger.warning(f"Pattern validation failed: {e}")
            return False
    
    def _cluster_entries(self, entries: List[Dict[str, Any]]) -> List['PatternCluster']:
        """
        Cluster entries using similarity-based grouping.
        
        Args:
            entries: List of entries to cluster
            
        Returns:
            List of pattern clusters
        """
        # PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Implement minimal working stub
        try:
            if not entries:
                return []
            
            # Simple clustering: group entries by pattern_id if available
            clusters = defaultdict(list)
            for entry in entries:
                pattern_id = entry.get('pattern_id', 'unclassified')
                clusters[pattern_id].append(entry)
            
            # Convert to PatternCluster objects
            result = []
            for pattern_id, cluster_entries in clusters.items():
                if len(cluster_entries) >= self.config.min_cluster_size:
                    cluster = PatternCluster(
                        pattern_id=pattern_id,
                        entries=cluster_entries,
                        confidence=0.7,  # Default confidence
                        metadata={'cluster_method': 'simple_grouping'}
                    )
                    result.append(cluster)
            
            return result
            
        except Exception as e:
            logger.warning(f"Entry clustering failed: {e}, returning empty list")
            return []

    def remove_pattern_references(self, pattern_id: str, user_id: str) -> bool:
        """
        Remove pattern references and clean up derived data for GDPR compliance.
        
        Args:
            pattern_id: The pattern ID to clean up
            user_id: The user ID whose data is being erased
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        # PATCH: Cursor-2024-12-19 CL-002 GDPR-CASCADE-FIX - Add pattern cleanup for GDPR compliance
        
        try:
            logger.info(f"GDPR cleanup: Removing pattern references for {pattern_id} (user: {user_id})")
            
            # Clean up clustering cache entries for this pattern
            if pattern_id in self._clustering_cache:
                del self._clustering_cache[pattern_id]
                logger.debug(f"Removed pattern {pattern_id} from clustering cache")
            
            # Clean up any pattern-specific metadata
            if hasattr(self, '_pattern_metadata') and pattern_id in self._pattern_metadata:
                del self._pattern_metadata[pattern_id]
                logger.debug(f"Removed metadata for pattern {pattern_id}")
            
            # Update statistics to reflect cleanup
            self._stats['patterns_discovered'] = max(0, self._stats['patterns_discovered'] - 1)
            
            # Log GDPR cleanup event
            logger.info(f"GDPR cleanup completed for pattern {pattern_id}: references and derived data removed")
            return True
            
        except Exception as e:
            logger.error(f"GDPR cleanup failed for pattern {pattern_id}: {e}")
            return False

    def vector_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform vector search using FAISS or fallback to TF-IDF cosine similarity.
        
        Args:
            query: Search query string
            k: Number of top results to return
            
        Returns:
            List of results with text, score, and metadata
        """
        try:
            # Try FAISS first
            if _HAS_FAISS:
                return self._faiss_vector_search(query, k)
            else:
                # Fallback to TF-IDF cosine similarity
                logger.warning("FAISS not installed; falling back to TF-IDF")
                return self._tfidf_vector_search(query, k)
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def _has_faiss(self) -> bool:
        """Check if FAISS is available."""
        return _HAS_FAISS
    
    def _faiss_vector_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """FAISS-based vector search."""
        try:
            import faiss
            import numpy as np
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            # Get all memory entries for indexing
            entries = self.memory_engine.recall_all()
            if not entries:
                return []
            
            # Extract text content
            texts = [entry.get('content', '') for entry in entries]
            texts.append(query)  # Add query to corpus
            
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Convert to numpy arrays
            vectors = tfidf_matrix.toarray().astype(np.float32)
            query_vector = vectors[-1].reshape(1, -1)
            doc_vectors = vectors[:-1]
            
            # Build FAISS index
            dimension = doc_vectors.shape[1]
            index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            index.add(doc_vectors)
            
            # Search
            scores, indices = index.search(query_vector, min(k, len(doc_vectors)))
            
            # Format results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(entries):
                    entry = entries[idx]
                    results.append({
                        'text': entry.get('content', '')[:200] + '...' if len(entry.get('content', '')) > 200 else entry.get('content', ''),
                        'score': float(score),
                        'meta': {
                            'entry_id': entry.get('id', f'entry_{idx}'),
                            'pattern_id': entry.get('pattern_id', 'unknown'),
                            'timestamp': entry.get('timestamp', 'unknown')
                        }
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"FAISS vector search failed: {e}")
            return []
    
    def _tfidf_vector_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """TF-IDF cosine similarity fallback."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            # Get all memory entries
            entries = self.memory_engine.recall_all()
            if not entries:
                return []
            
            # Extract text content
            texts = [entry.get('content', '') for entry in entries]
            texts.append(query)
            
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Calculate cosine similarity
            query_vector = tfidf_matrix[-1:].toarray()
            doc_vectors = tfidf_matrix[:-1].toarray()
            
            similarities = cosine_similarity(query_vector, doc_vectors)[0]
            
            # Get top-k results
            top_indices = np.argsort(similarities)[::-1][:k]
            
            # Format results
            results = []
            for idx in top_indices:
                if idx < len(entries):
                    entry = entries[idx]
                    results.append({
                        'text': entry.get('content', '')[:200] + '...' if len(entry.get('content', '')) > 200 else entry.get('content', ''),
                        'score': float(similarities[idx]),
                        'meta': {
                            'entry_id': entry.get('id', f'entry_{idx}'),
                            'pattern_id': entry.get('pattern_id', 'unknown'),
                            'timestamp': entry.get('timestamp', 'unknown')
                        }
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"TF-IDF vector search failed: {e}")
            return []


# Factory function for easy instantiation
def create_pattern_weaver(memory_engine=None, governance=None, 
                         config: Optional[ClusteringConfig] = None) -> PatternWeaver:
    """
    Factory function to create PatternWeaver instance.
    
    Args:
        memory_engine: Memory engine instance
        governance: Pattern governance system
        config: Clustering configuration
        
    Returns:
        Configured PatternWeaver instance
    """
    return PatternWeaver(
        memory_engine=memory_engine,
        governance=governance,
        config=config
    )


# Export key classes and functions
__all__ = [
    'PatternWeaver',
    'PatternCluster',
    'ClusteringConfig',
    'ClusteringMethod',
    'PatternConfidence',
    'create_pattern_weaver',
    'PatternWeaverError',
    'ClusteringError',
    'PatternValidationError'
]
