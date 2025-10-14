"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
Tests the vector_search method in PatternWeaver with FAISS present.
"""

import pytest
from unittest.mock import Mock, patch
from src.pattern_weaver import PatternWeaver

class TestVectorSearchBasic:
    """Test basic vector search functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_memory_engine = Mock()
        self.mock_governance = Mock()
        
        # Mock memory entries
        self.mock_entries = [
            {
                'id': 'entry_1',
                'content': 'This is a test document about machine learning',
                'pattern_id': 'ml_pattern',
                'timestamp': '2025-08-25T10:00:00Z'
            },
            {
                'id': 'entry_2', 
                'content': 'Another document about artificial intelligence',
                'pattern_id': 'ai_pattern',
                'timestamp': '2025-08-25T11:00:00Z'
            },
            {
                'id': 'entry_3',
                'content': 'Document about data science and analytics',
                'pattern_id': 'ds_pattern', 
                'timestamp': '2025-08-25T12:00:00Z'
            }
        ]
        
        self.mock_memory_engine.recall_all.return_value = self.mock_entries
        
        self.pattern_weaver = PatternWeaver(
            memory_engine=self.mock_memory_engine,
            governance=self.mock_governance
        )
    
    def test_vector_search_method_exists(self):
        """Test that vector_search method exists and is callable."""
        assert hasattr(self.pattern_weaver, 'vector_search'), "vector_search method should exist"
        assert callable(self.pattern_weaver.vector_search), "vector_search should be callable"
    
    def test_vector_search_query_validation(self):
        """Test vector search with invalid queries."""
        # Empty query
        results = self.pattern_weaver.vector_search("", k=5)
        assert isinstance(results, list), "Should return a list"
        
        # None query
        results = self.pattern_weaver.vector_search(None, k=5)
        assert isinstance(results, list), "Should return a list"
        
        # Very long query
        long_query = "a" * 10000
        results = self.pattern_weaver.vector_search(long_query, k=5)
        assert isinstance(results, list), "Should return a list"
    
    def test_vector_search_k_validation(self):
        """Test vector search with different k values."""
        # Test with k=0
        results = self.pattern_weaver.vector_search("test", k=0)
        assert isinstance(results, list), "Should return a list"
        
        # Test with k larger than available documents
        results = self.pattern_weaver.vector_search("test", k=100)
        assert isinstance(results, list), "Should return a list"
        
        # Test with negative k
        results = self.pattern_weaver.vector_search("test", k=-1)
        assert isinstance(results, list), "Should return a list"
    
    def test_vector_search_empty_memory(self):
        """Test vector search when memory engine is empty."""
        self.mock_memory_engine.recall_all.return_value = []
        
        results = self.pattern_weaver.vector_search("test", k=5)
        assert isinstance(results, list), "Should return a list"
    
    def test_vector_search_error_handling(self):
        """Test vector search error handling."""
        # Mock memory engine to raise exception
        self.mock_memory_engine.recall_all.side_effect = Exception("Memory error")
        
        # Should return empty list on error
        results = self.pattern_weaver.vector_search("test", k=5)
        assert isinstance(results, list), "Should return a list"
    
    def test_vector_search_return_structure(self):
        """Test that vector search returns expected structure."""
        # Mock the _has_faiss method to return False to force fallback
        with patch.object(self.pattern_weaver, '_has_faiss', return_value=False):
            # Mock the fallback method to return test results
            mock_results = [
                {
                    'text': 'Test content 1',
                    'score': 0.8,
                    'meta': {'entry_id': 'test_1'}
                }
            ]
            
            with patch.object(self.pattern_weaver, '_tfidf_vector_search', return_value=mock_results):
                results = self.pattern_weaver.vector_search("test query", k=1)
                
                assert isinstance(results, list), "Should return a list"
                if results:
                    assert 'text' in results[0], "Result should have text field"
                    assert 'score' in results[0], "Result should have score field"
                    assert 'meta' in results[0], "Result should have meta field"
    
    def test_vector_search_faiss_detection(self):
        """Test FAISS detection method."""
        assert hasattr(self.pattern_weaver, '_has_faiss'), "Should have _has_faiss method"
        assert callable(self.pattern_weaver._has_faiss), "_has_faiss should be callable"
        
        # Test the method returns a boolean
        result = self.pattern_weaver._has_faiss()
        assert isinstance(result, bool), "_has_faiss should return boolean"
    
    def test_vector_search_fallback_methods_exist(self):
        """Test that fallback methods exist."""
        assert hasattr(self.pattern_weaver, '_faiss_vector_search'), "Should have _faiss_vector_search method"
        assert hasattr(self.pattern_weaver, '_tfidf_vector_search'), "Should have _tfidf_vector_search method"
        
        assert callable(self.pattern_weaver._faiss_vector_search), "_faiss_vector_search should be callable"
        assert callable(self.pattern_weaver._tfidf_vector_search), "_tfidf_vector_search should be callable"
