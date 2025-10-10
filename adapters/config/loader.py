""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class FeatureLoader:
    """Loads and manages feature toggle configuration with environment variable overrides."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize feature loader with optional config path."""
        self.config_path = config_path or "src/config/features.yaml"
        self._features: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    self._features = config.get('features', {})
            else:
                # Fallback to defaults if file doesn't exist
                self._features = self._get_default_features()
        except Exception as e:
            # Fallback to defaults on any error
            self._features = self._get_default_features()
    
    def _get_default_features(self) -> Dict[str, str]:
        """Return default feature configuration."""
        return {
            "vector_search": "faiss",
            "gdpr_hooks": "on",
            "hipaa_redaction": "on",
            "cold_storage_encryption": "on",
            "policy_gate": "on",
            "benchmarks": "on"
        }
    
    def get_feature(self, feature_name: str, default: str = "off") -> str:
        """Get feature value with environment variable override precedence."""
        # Environment variable override (highest precedence)
        env_var = f"IOA_FEATURE_{feature_name.upper()}"
        if env_var in os.environ:
            return os.environ[env_var].lower()
        
        # Config file value
        return self._features.get(feature_name, default)
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        value = self.get_feature(feature_name)
        return value != "off" and value is not None
    
    def get_all_features(self) -> Dict[str, str]:
        """Get all feature values with environment variable overrides applied."""
        return {
            name: self.get_feature(name)
            for name in self._features.keys()
        }
    
    def set_feature(self, feature_name: str, value: str) -> None:
        """Set a feature value (runtime only, doesn't persist to file)."""
        self._features[feature_name] = value

# Global feature loader instance
feature_loader = FeatureLoader()

# Convenience functions
def get_feature(feature_name: str, default: str = "off") -> str:
    """Get feature value using global loader."""
    return feature_loader.get_feature(feature_name, default)

def is_feature_enabled(feature_name: str) -> bool:
    """Check if feature is enabled using global loader."""
    return feature_loader.is_feature_enabled(feature_name)

def get_all_features() -> Dict[str, str]:
    """Get all feature values using global loader."""
    return feature_loader.get_all_features()
