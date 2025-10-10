""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Configuration helper for Reinforcement Policy Framework
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
Configuration helper for Reinforcement Policy Framework
Handles registry path resolution and environment setup

Location: src/ioa/governance/reinforcement_config.py
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional


class ReinforcementConfig:
    """Configuration manager for Reinforcement Policy Framework"""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.env = os.getenv('IOA_ENV', 'development')
    
    def get_registry_path(self, custom_path: Optional[str] = None) -> str:
        """
        Get the appropriate registry path based on environment and configuration
        
        Priority:
        1. Custom path (if provided)
        2. Environment variable IOA_REGISTRY_PATH
        3. Environment-specific default
        4. Fallback default
        """
        if custom_path:
            # Resolve custom path relative to base_dir to avoid relative path issues
            return str((self.base_dir / custom_path).resolve())
        
        # Check environment variable
        env_path = os.getenv('IOA_REGISTRY_PATH')
        if env_path:
            return str(Path(env_path).resolve())
        
        # Environment-specific defaults
        env_paths = {
            'development': 'data/agent_trust_registry.json',
            'testing': 'data/test_agent_trust_registry.json',
            'staging': 'var/staging_agent_trust_registry.json',
            'production': 'var/agent_trust_registry.json'
        }
        
        registry_path = env_paths.get(self.env, 'data/agent_trust_registry.json')
        # Return an absolute path resolved from base_dir
        return str((self.base_dir / registry_path).resolve())
    
    def ensure_registry_directory(self, registry_path: str) -> bool:
        """Ensure the registry directory exists"""
        try:
            registry_file = Path(registry_path)
            registry_file.parent.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Failed to create registry directory: {e}")
            return False
    
    def get_default_framework_config(self) -> Dict:
        """Get default framework configuration for current environment"""
        registry_path = self.get_registry_path()
        self.ensure_registry_directory(registry_path)
        
        # Environment-specific configurations
        configs = {
            'development': {
                'registry_path': registry_path,
                'reward_config': {
                    'base_satisfaction_boost': 0.1,
                    'base_heat_multiplier': 1.2
                },
                'punishment_config': {
                    'base_stress_increase': 0.15,
                    'base_heat_decay': 0.8
                },
                'credential_config': {
                    'promotion_evaluation_interval': 'every_cycle'  # More frequent for dev
                }
            },
            'testing': {
                'registry_path': registry_path,
                'reward_config': {
                    'base_satisfaction_boost': 0.2,  # Faster for testing
                    'base_heat_multiplier': 1.5
                },
                'punishment_config': {
                    'base_stress_increase': 0.3,  # More dramatic for testing
                    'base_heat_decay': 0.6
                }
            },
            'production': {
                'registry_path': registry_path,
                'reward_config': {
                    'base_satisfaction_boost': 0.05,  # More conservative
                    'base_heat_multiplier': 1.1
                },
                'punishment_config': {
                    'base_stress_increase': 0.1,
                    'base_heat_decay': 0.9
                },
                'credential_config': {
                    'promotion_evaluation_interval': 'daily'
                }
            }
        }
        
        return configs.get(self.env, configs['development'])
    
    def initialize_registry_if_needed(self, registry_path: str) -> bool:
        """Initialize registry file if it doesn't exist"""
        registry_file = Path(registry_path)
        
        if registry_file.exists():
            return True
        
        # Create initial registry structure
        initial_registry = {
            "metadata": {
                "version": "1.0",
                "created": "2024-07-29T12:00:00.000Z",
                "environment": self.env,
                "description": "Agent Trust Registry for IOA Ethical Learning System",
                "schema_version": "ETH-RL-003"
            },
            "configuration": {
                "max_agents": 1000,
                "promotion_evaluation_interval": "daily",
                "credential_expiry_enabled": False,
                "audit_trail_retention_days": 365
            },
            "agents": {},
            "statistics": {
                "total_agents": 0,
                "credential_distribution": {
                    "basic": 0,
                    "ethics_level_1": 0,
                    "ethics_level_2": 0,
                    "trusted_operator": 0,
                    "senior_council": 0
                },
                "average_satisfaction": 0.5,
                "average_stress": 0.0,
                "promotion_rate": 0.0,
                "last_updated": "2024-07-29T12:00:00.000Z"
            },
            "audit_trail": []
        }
        
        try:
            with open(registry_path, 'w') as f:
                json.dump(initial_registry, f, indent=2)
            print(f"Initialized registry at: {registry_path}")
            return True
        except Exception as e:
            print(f"Failed to initialize registry: {e}")
            return False


# Convenience function for easy framework setup
def create_reinforcement_framework(custom_config: Optional[Dict] = None, 
                                 base_dir: Optional[str] = None) -> 'ReinforcementPolicyFramework':
    """
    Create a properly configured ReinforcementPolicyFramework
    
    Args:
        custom_config: Optional custom configuration overrides
        base_dir: Optional base directory (defaults to current working directory)
    
    Returns:
        Configured ReinforcementPolicyFramework instance
    """
    from .reinforcement_policy import ReinforcementPolicyFramework
    
    config_manager = ReinforcementConfig(base_dir)
    default_config = config_manager.get_default_framework_config()
    
    # Merge custom config if provided
    if custom_config:
        default_config.update(custom_config)
    
    # Initialize registry if needed
    config_manager.initialize_registry_if_needed(default_config['registry_path'])
    
    return ReinforcementPolicyFramework(default_config)


# Environment setup utilities
def setup_directories(base_dir: Optional[str] = None):
    """Set up recommended directory structure"""
    base = Path(base_dir) if base_dir else Path.cwd()
    
    directories = [
        'data',
        'var',
        'var/backups',
        'var/logs',
        'config',
        'environments/development',
        'environments/testing', 
        'environments/staging',
        'environments/production'
    ]
    
    created = []
    for dir_path in directories:
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created.append(str(full_path))
    
    # Create .gitignore for var directory
    gitignore_path = base / 'var' / '.gitignore'
    if not gitignore_path.exists():
        with open(gitignore_path, 'w') as f:
            f.write("# Runtime data - do not commit\n")
            f.write("*.json\n")
            f.write("*.log\n")
            f.write("*.backup\n")
    
    print(f"Created directories: {', '.join(created)}")
    return created


if __name__ == "__main__":
    # Setup script - run this to initialize directory structure
    print("Setting up IOA Reinforcement Policy directories...")
    setup_directories()
    
    # Test configuration
    config = ReinforcementConfig()
    print(f"Environment: {config.env}")
    print(f"Registry path: {config.get_registry_path()}")
    
    # Initialize framework
    framework = create_reinforcement_framework()
    print("✅ Reinforcement Policy Framework ready!")