""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

"""
Sandboxed Environment for CLI Command Validation

This module provides a safe sandboxed environment for running CLI commands
during documentation validation. It prevents destructive operations and
provides controlled access to system resources.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager


class SandboxEnvironment:
    """Sandboxed environment for safe command execution."""
    
    def __init__(self, repo_root: Path, live_mode: bool = False):
        self.repo_root = repo_root
        self.live_mode = live_mode
        self.temp_dir: Optional[Path] = None
        self.original_env: Dict[str, str] = {}
        
    def __enter__(self):
        """Enter sandbox context."""
        self.setup_sandbox()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox context."""
        self.cleanup_sandbox()
    
    def setup_sandbox(self):
        """Set up sandboxed environment."""
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ioa_doc_validation_"))
        
        # Save original environment
        self.original_env = os.environ.copy()
        
        # Set up sandboxed environment
        self._setup_environment()
        self._setup_fake_config()
    
    def cleanup_sandbox(self):
        """Clean up sandboxed environment."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Remove temporary directory
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_environment(self):
        """Set up sandboxed environment variables."""
        # Clear potentially dangerous environment variables
        dangerous_vars = [
            'PATH', 'LD_LIBRARY_PATH', 'PYTHONPATH',
            'HOME', 'USER', 'USERNAME', 'SHELL',
            'TMPDIR', 'TMP', 'TEMP'
        ]
        
        for var in dangerous_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Set safe defaults
        os.environ.update({
            'PATH': '/usr/bin:/bin',
            'HOME': str(self.temp_dir),
            'USER': 'sandbox',
            'SHELL': '/bin/bash',
            'TMPDIR': str(self.temp_dir),
            'TMP': str(self.temp_dir),
            'TEMP': str(self.temp_dir),
        })
        
        # IOA-specific environment
        if not self.live_mode:
            os.environ.update({
                'IOA_FAKE_MODE': '1',
                'NO_NETWORK': '1',
                'IOA_OFFLINE': 'true',
                'IOA_SANDBOX': '1',
            })
        
        # Python environment
        os.environ['PYTHONPATH'] = str(self.repo_root / 'src')
        
        # Disable network access unless in live mode
        if not self.live_mode:
            os.environ.update({
                'HTTP_PROXY': '',
                'HTTPS_PROXY': '',
                'NO_PROXY': '*',
                'REQUESTS_CA_BUNDLE': '',
                'CURL_CA_BUNDLE': '',
            })
    
    def _setup_fake_config(self):
        """Set up fake configuration files."""
        # Create fake IOA config directory
        config_dir = self.temp_dir / '.ioa' / 'config'
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create fake provider config
        provider_config = {
            "providers": {
                "openai": {
                    "enabled": True,
                    "api_key": "fake-key-for-testing",
                    "model": "gpt-3.5-turbo"
                },
                "anthropic": {
                    "enabled": True,
                    "api_key": "fake-key-for-testing",
                    "model": "claude-3-sonnet"
                },
                "ollama": {
                    "enabled": True,
                    "host": "http://localhost:11434",
                    "model": "llama2"
                }
            },
            "default_provider": "openai",
            "offline_mode": not self.live_mode
        }
        
        import json
        with open(config_dir / 'providers.json', 'w') as f:
            json.dump(provider_config, f, indent=2)
        
        # Create fake audit log directory
        audit_dir = self.temp_dir / '.ioa' / 'logs'
        audit_dir.mkdir(parents=True, exist_ok=True)
        
        # Create fake audit log
        audit_log = {
            "timestamp": "2025-01-06T00:00:00Z",
            "level": "INFO",
            "message": "Sandboxed validation environment initialized",
            "component": "doc_validator"
        }
        
        with open(audit_dir / 'audit.log', 'w') as f:
            json.dump(audit_log, f, indent=2)
    
    def get_working_directory(self) -> Path:
        """Get the working directory for command execution."""
        return self.temp_dir
    
    def is_live_mode(self) -> bool:
        """Check if running in live mode."""
        return self.live_mode


@contextmanager
def sandboxed_environment(repo_root: Path, live_mode: bool = False):
    """Context manager for sandboxed environment."""
    with SandboxEnvironment(repo_root, live_mode) as sandbox:
        yield sandbox


def create_fake_env_file(repo_root: Path) -> Path:
    """Create a fake .env.local file for testing."""
    env_file = repo_root / '.env.local.example'
    
    env_content = """# IOA Core Environment Configuration
# Copy this file to .env.local and fill in your actual API keys

# OpenAI Configuration
OPENAI_API_KEY=

# Anthropic Configuration  
ANTHROPIC_API_KEY=

# Google Gemini Configuration
GOOGLE_API_KEY=

# DeepSeek Configuration
DEEPSEEK_API_KEY=

# Ollama Configuration (local)
OLLAMA_HOST=http://127.0.0.1:11434

# IOA Configuration
IOA_FAKE_MODE=1
IOA_OFFLINE=true
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    return env_file


if __name__ == "__main__":
    # Test sandbox environment
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        with sandboxed_environment(repo_root, live_mode=False) as sandbox:
            print(f"Sandbox working directory: {sandbox.get_working_directory()}")
            print(f"Live mode: {sandbox.is_live_mode()}")
            print(f"Environment variables:")
            for key, value in os.environ.items():
                if key.startswith('IOA_') or key in ['PATH', 'HOME', 'USER']:
                    print(f"  {key}={value}")
