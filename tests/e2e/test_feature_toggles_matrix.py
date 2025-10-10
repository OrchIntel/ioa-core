""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


import pytest
import os
import sys
from typing import Dict, List, Tuple
from itertools import combinations

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from config.loader import FeatureLoader, get_feature, is_feature_enabled, get_all_features

class TestFeatureToggleMatrix:
    """Test matrix to validate feature independence and system-agnostic behavior."""
    
    @pytest.fixture
    def feature_loader(self):
        """Provide a clean feature loader instance."""
        return FeatureLoader()
    
    @pytest.fixture
    def core_features(self):
        """List of core features to test."""
        return [
            "vector_search",
            "gdpr_hooks", 
            "hipaa_redaction",
            "cold_storage_encryption",
            "policy_gate",
            "benchmarks"
        ]
    
    def test_feature_loader_defaults(self, feature_loader):
        """Test that feature loader provides sensible defaults."""
        features = feature_loader.get_all_features()
        assert "vector_search" in features
        assert "gdpr_hooks" in features
        assert "hipaa_redaction" in features
        assert "cold_storage_encryption" in features
        assert "policy_gate" in features
        assert "benchmarks" in features
    
    def test_environment_variable_override(self, feature_loader):
        """Test that environment variables override config file values."""
        # Set environment variable
        os.environ["IOA_FEATURE_VECTOR_SEARCH"] = "off"
        
        try:
            assert feature_loader.get_feature("vector_search") == "off"
            assert not feature_loader.is_feature_enabled("vector_search")
        finally:
            # Clean up
            del os.environ["IOA_FEATURE_VECTOR_SEARCH"]
    
    def test_feature_independence_single_toggle(self, feature_loader, core_features):
        """Test that toggling one feature doesn't affect others."""
        for feature in core_features:
            # Toggle feature off
            original_value = feature_loader.get_feature(feature)
            feature_loader.set_feature(feature, "off")
            
            # Verify other features remain unchanged
            for other_feature in core_features:
                if other_feature != feature:
                    other_original = feature_loader.get_feature(other_feature)
                    assert other_original != "off"  # Should still be enabled
            
            # Restore original value
            feature_loader.set_feature(feature, original_value)
    
    def test_feature_toggle_combinations(self, feature_loader, core_features):
        """Test pairwise combinations of feature toggles."""
        # Test all pairs of features
        for feature1, feature2 in combinations(core_features, 2):
            # Store original values
            orig1 = feature_loader.get_feature(feature1)
            orig2 = feature_loader.get_feature(feature2)
            
            try:
                # Toggle both off
                feature_loader.set_feature(feature1, "off")
                feature_loader.set_feature(feature2, "off")
                
                # Verify both are off
                assert not feature_loader.is_feature_enabled(feature1)
                assert not feature_loader.is_feature_enabled(feature2)
                
                # Verify other features remain enabled
                for other_feature in core_features:
                    if other_feature not in [feature1, feature2]:
                        assert feature_loader.is_feature_enabled(other_feature)
                
            finally:
                # Restore original values
                feature_loader.set_feature(feature1, orig1)
                feature_loader.set_feature(feature2, orig2)
    
    def test_feature_toggle_all_off(self, feature_loader, core_features):
        """Test that all features can be disabled simultaneously."""
        # Store original values
        original_values = {}
        for feature in core_features:
            original_values[feature] = feature_loader.get_feature(feature)
        
        try:
            # Toggle all off
            for feature in core_features:
                feature_loader.set_feature(feature, "off")
            
            # Verify all are off
            for feature in core_features:
                assert not feature_loader.is_feature_enabled(feature)
            
        finally:
            # Restore original values
            for feature in core_features:
                feature_loader.set_feature(feature, original_values[feature])
    
    def test_feature_toggle_all_on(self, feature_loader, core_features):
        """Test that all features can be enabled simultaneously."""
        # Store original values
        original_values = {}
        for feature in core_features:
            original_values[feature] = feature_loader.get_feature(feature)
        
        try:
            # Toggle all on
            for feature in core_features:
                feature_loader.set_feature(feature, "on")
            
            # Verify all are on
            for feature in core_features:
                assert feature_loader.is_feature_enabled(feature)
            
        finally:
            # Restore original values
            for feature in core_features:
                feature_loader.set_feature(feature, original_values[feature])
    
    def test_global_functions(self):
        """Test global convenience functions."""
        # Test get_feature
        assert get_feature("vector_search") in ["faiss", "tfidf", "off"]
        
        # Test is_feature_enabled
        assert isinstance(is_feature_enabled("vector_search"), bool)
        
        # Test get_all_features
        all_features = get_all_features()
        assert isinstance(all_features, dict)
        assert "vector_search" in all_features
    
    def test_feature_loader_persistence(self, feature_loader):
        """Test that runtime changes don't persist to file."""
        original_value = feature_loader.get_feature("vector_search")
        
        # Change value
        feature_loader.set_feature("vector_search", "off")
        assert feature_loader.get_feature("vector_search") == "off"
        
        # Create new loader instance (should read from file, not memory)
        new_loader = FeatureLoader()
        assert new_loader.get_feature("vector_search") == original_value
