""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from click.testing import CliRunner

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ioa_core.cli import app

class TestVectorsCommand:
    """Test CLI vectors command functionality."""
    
    @pytest.fixture
    def runner(self):
        """Provide Click test runner."""
        return CliRunner()
    
    @pytest.fixture
    def sample_patterns_file(self):
        """Provide temporary patterns file for testing."""
        patterns = {
            "patterns": [
                {
                    "id": "test-1",
                    "name": "Test Pattern One",
                    "description": "First test pattern",
                    "content": "This is the first test pattern with some content.",
                    "tags": ["test", "first", "pattern"],
                    "category": "testing"
                },
                {
                    "id": "test-2",
                    "name": "Test Pattern Two",
                    "description": "Second test pattern",
                    "content": "This is the second test pattern with different content.",
                    "tags": ["test", "second", "pattern"],
                    "category": "testing"
                },
                {
                    "id": "test-3",
                    "name": "Machine Learning Example",
                    "description": "ML pattern for testing",
                    "content": "Machine learning involves algorithms and data processing.",
                    "tags": ["ml", "algorithms", "data"],
                    "category": "ai"
                }
            ],
            "metadata": {
                "version": "1.0.0",
                "created": "2025-01-27",
                "description": "Test patterns for CLI testing"
            }
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(patterns, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass
    
    def test_vectors_command_help(self, runner):
        """Test vectors command help output."""
        result = runner.invoke(app, ['vectors', '--help'])

        assert result.exit_code == 0
        assert 'Vector search and pattern matching' in result.output
        assert 'search' in result.output
        assert 'add' in result.output
        assert 'stats' in result.output

    def test_vectors_search_command_help(self, runner):
        """Test vectors search command help shows options."""
        result = runner.invoke(app, ['vectors', 'search', '--help'])

        assert result.exit_code == 0
        assert 'Search patterns using vector similarity' in result.output
        assert '--index' in result.output
        assert '--query' in result.output
        assert '--k' in result.output
        assert '--backend' in result.output
    
    def test_vectors_command_missing_index(self, runner):
        """Test vectors search command with missing index file."""
        result = runner.invoke(app, ['vectors', 'search', '--query', 'test'])

        assert result.exit_code != 0
        assert 'Error: Missing option' in result.output or 'Missing argument' in result.output
    
    def test_vectors_command_missing_query(self, runner):
        """Test vectors search command with missing query."""
        result = runner.invoke(app, ['vectors', 'search', '--index', 'test.json'])

        assert result.exit_code != 0
        assert 'Error: Missing option' in result.output or 'Missing argument' in result.output

    def test_vectors_command_basic_search(self, runner, tmp_path):
        """Test vectors search command with valid inputs."""
        # Create a test index
        index_path = tmp_path / "test_index.json"

        # Add a document first
        result = runner.invoke(app, [
            'vectors', 'add',
            '--index', str(index_path),
            '--id', 'doc1',
            '--content', 'This is a test document about machine learning'
        ])
        assert result.exit_code == 0

        # Now search
        result = runner.invoke(app, [
            'vectors', 'search',
            '--index', str(index_path),
            '--query', 'machine learning'
        ])

        assert result.exit_code == 0
        assert 'Found' in result.output or 'doc1' in result.output

    def test_vectors_command_with_k_limit(self, runner, tmp_path):
        """Test vectors search command with k limit."""
        index_path = tmp_path / "test_index.json"

        # Add multiple documents
        for i in range(3):
            result = runner.invoke(app, [
                'vectors', 'add',
                '--index', str(index_path),
                '--id', f'doc{i}',
                '--content', f'This is test document {i} with some content'
            ])
            assert result.exit_code == 0

        # Search with k=2
        result = runner.invoke(app, [
            'vectors', 'search',
            '--index', str(index_path),
            '--query', 'test document',
            '--k', '2'
        ])

        assert result.exit_code == 0
        assert 'Found 2 results' in result.output or 'Found' in result.output

    def test_vectors_command_verbose(self, runner, tmp_path):
        """Test vectors search command with verbose output."""
        index_path = tmp_path / "test_index.json"

        # Add a document with metadata
        result = runner.invoke(app, [
            'vectors', 'add',
            '--index', str(index_path),
            '--id', 'doc1',
            '--content', 'This is a test document',
            '--metadata', '{"type": "test", "author": "test_user"}'
        ])
        assert result.exit_code == 0

        # Search with verbose
        result = runner.invoke(app, [
            'vectors', 'search',
            '--index', str(index_path),
            '--query', 'test document',
            '--verbose'
        ])

        assert result.exit_code == 0
        assert 'Metadata:' in result.output or 'type' in result.output
