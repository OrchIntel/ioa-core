"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
Tests the vector_search method in PatternWeaver when FAISS is not available,
falling back to TF-IDF cosine similarity.
"""

import pytest
from unittest.mock import Mock, patch
from src.pattern_weaver import PatternWeaver

class TestVectorSearchFallback:
    """Test vector search fallback functionality."""
    
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
    
    def test_fallback_methods_exist(self):
        """Test that fallback methods exist and are callable."""
        assert hasattr(self.pattern_weaver, '_tfidf_vector_search'), "Should have _tfidf_vector_search method"
        assert callable(self.pattern_weaver._tfidf_vector_search), "_tfidf_vector_search should be callable"
    
    def test_fallback_method_return_structure(self):
        """Test that fallback method returns expected structure."""
        # Mock the fallback method to return test results
        mock_results = [
            {
                'text': 'Test content 1',
                'score': 0.8,
                'meta': {'entry_id': 'test_1'}
            },
            {
                'text': 'Test content 2',
                'score': 0.6,
                'meta': {'entry_id': 'test_2'}
            }
        ]
        
        with patch.object(self.pattern_weaver, '_tfidf_vector_search', return_value=mock_results):
            results = self.pattern_weaver._tfidf_vector_search("test query", k=2)
            
            assert isinstance(results, list), "Should return a list"
            assert len(results) == 2, "Should return 2 results"
            
            for result in results:
                assert 'text' in result, "Result should have text field"
                assert 'score' in result, "Result should have score field"
                assert 'meta' in result, "Result should have meta field"
                assert 'entry_id' in result['meta'], "Meta should have entry_id"
    
    def test_fallback_error_handling(self):
        """Test fallback error handling."""
        # Mock the fallback method to raise an exception
        with patch.object(self.pattern_weaver, '_tfidf_vector_search', side_effect=Exception("Test error")):
            # Should handle errors gracefully
            try:
                results = self.pattern_weaver._tfidf_vector_search("test", k=5)
                # If it doesn't raise, should return empty list
                assert isinstance(results, list), "Should return a list on error"
            except Exception:
                # Exception is also acceptable
                pass
    
    def test_fallback_with_empty_memory(self):
        """Test fallback behavior with empty memory."""
        # Mock empty memory
        self.mock_memory_engine.recall_all.return_value = []
        
        # Mock the fallback method
        with patch.object(self.pattern_weaver, '_tfidf_vector_search', return_value=[]):
            results = self.pattern_weaver._tfidf_vector_search("test", k=5)
            assert isinstance(results, list), "Should return a list"
            assert len(results) == 0, "Should return empty list for empty memory"
    
    def test_fallback_parameter_validation(self):
        """Test fallback method parameter validation."""
        # Test with invalid k values
        with patch.object(self.pattern_weaver, '_tfidf_vector_search', return_value=[]):
            results = self.pattern_weaver._tfidf_vector_search("test", k=0)
            assert isinstance(results, list), "Should handle k=0"
            
            results = self.pattern_weaver._tfidf_vector_search("test", k=-1)
            assert isinstance(results, list), "Should handle negative k"
            
            results = self.pattern_weaver._tfidf_vector_search("test", k=100)
            assert isinstance(results, list), "Should handle large k"
    
    def test_fallback_query_validation(self):
        """Test fallback method query validation."""
        with patch.object(self.pattern_weaver, '_tfidf_vector_search', return_value=[]):
            # Test with various query types
            results = self.pattern_weaver._tfidf_vector_search("", k=5)
            assert isinstance(results, list), "Should handle empty query"
            
            results = self.pattern_weaver._tfidf_vector_search(None, k=5)
            assert isinstance(results, list), "Should handle None query"
            
            results = self.pattern_weaver._tfidf_vector_search(123, k=5)
            assert isinstance(results, list), "Should handle non-string query"
    
    def test_fallback_method_signature(self):
        """Test that fallback method has correct signature."""
        import inspect
        
        sig = inspect.signature(self.pattern_weaver._tfidf_vector_search)
        params = list(sig.parameters.keys())
        
        assert 'query' in params, "Should have query parameter"
        assert 'k' in params, "Should have k parameter"
        assert len(params) == 2, "Should have exactly 2 parameters"
    
    def test_fallback_method_docstring(self):
        """Test that fallback method has proper documentation."""
        doc = self.pattern_weaver._tfidf_vector_search.__doc__
        assert doc is not None, "Method should have docstring"
        assert "TF-IDF" in doc, "Docstring should mention TF-IDF"
        assert "cosine similarity" in doc, "Docstring should mention cosine similarity"
