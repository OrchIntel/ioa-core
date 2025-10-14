"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.ci.forbidden_patterns import (
    load_config, should_ignore_path, find_matching_files, main
)


class TestForbiddenPatterns(unittest.TestCase):
    """Test cases for forbidden patterns checker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_config_default(self):
        """Test loading default config when file doesn't exist."""
        config = load_config("nonexistent.yml")
        self.assertIn('hygiene', config)
        self.assertIn('forbidden_patterns', config['hygiene'])
        self.assertEqual(config['mode'], 'monitor')
    
    def test_load_config_file(self):
        """Test loading config from file."""
        config_content = """
mode: strict
hygiene:
  forbidden_patterns: ["**/*.pem", "**/.env*"]
"""
        config_file = Path(self.temp_dir) / "test_config.yml"
        config_file.write_text(config_content)
        
        config = load_config(str(config_file))
        self.assertEqual(config['mode'], 'strict')
        self.assertEqual(config['hygiene']['forbidden_patterns'], ["**/*.pem", "**/.env*"])
    
    def test_should_ignore_path(self):
        """Test path ignoring logic."""
        # Should ignore
        self.assertTrue(should_ignore_path('.git/'))
        self.assertTrue(should_ignore_path('venv/'))
        self.assertTrue(should_ignore_path('artifacts/'))
        self.assertTrue(should_ignore_path('__pycache__/'))
        self.assertTrue(should_ignore_path('test/.git/'))
        self.assertTrue(should_ignore_path('test/venv/'))
        
        # Should not ignore
        self.assertFalse(should_ignore_path('src/main.py'))
        self.assertFalse(should_ignore_path('test.py'))
        self.assertFalse(should_ignore_path('config.yaml'))
    
    def test_find_matching_files(self):
        """Test finding files matching patterns."""
        # Create test files
        test_files = [
            'test.pem',
            '.env',
            '.env.local',
            'my_private_key.txt',
            'id_rsa',
            'normal_file.py',
            'subdir/test.pem',
            'subdir/.env.prod'
        ]
        
        for file_path in test_files:
            full_path = Path(self.temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("test content")
        
        patterns = ["**/*.pem", "**/.env*", "**/*_private_key*", "**/id_rsa*"]
        matches = find_matching_files(patterns, self.temp_dir)
        
        # Convert to relative paths for comparison
        rel_matches = [os.path.relpath(m, self.temp_dir) for m in matches]
        
        expected = [
            'test.pem',
            '.env',
            '.env.local',
            'my_private_key.txt',
            'id_rsa',
            'subdir/test.pem',
            'subdir/.env.prod'
        ]
        
        # Check that we found the expected number of matches
        self.assertEqual(len(rel_matches), len(expected))
        
        # Check that all expected files are found (order may vary)
        # Extract just the filename or relative path for comparison
        for expected_file in expected:
            found = False
            for match in rel_matches:
                if match.endswith(expected_file) or match == expected_file:
                    found = True
                    break
            self.assertTrue(found, f"Expected file {expected_file} not found in {rel_matches}")
        
        # Should not match normal files
        self.assertNotIn('normal_file.py', rel_matches)
    
    def test_find_matching_files_with_ignores(self):
        """Test that ignored paths are not matched."""
        # Create test files in ignored directories
        ignored_dirs = ['.git', 'venv', 'artifacts', '__pycache__']
        for ignored_dir in ignored_dirs:
            ignored_path = Path(self.temp_dir) / ignored_dir
            ignored_path.mkdir()
            (ignored_path / 'test.pem').write_text("test")
            (ignored_path / '.env').write_text("test")
        
        patterns = ["**/*.pem", "**/.env*"]
        matches = find_matching_files(patterns, self.temp_dir)
        
        # Should be empty since all files are in ignored directories
        self.assertEqual(len(matches), 0)
    
    @patch('sys.argv', ['forbidden_patterns.py', '--json'])
    @patch('tools.ci.forbidden_patterns.load_config')
    @patch('tools.ci.forbidden_patterns.find_matching_files')
    def test_main_json_output(self, mock_find, mock_load_config):
        """Test main function with JSON output."""
        mock_load_config.return_value = {
            'hygiene': {'forbidden_patterns': ['**/*.pem']},
            'mode': 'monitor'
        }
        mock_find.return_value = ['test.pem', 'another.pem']
        
        with patch('sys.stdout') as mock_stdout, patch('sys.exit') as mock_exit:
            main()
            
            # Check that JSON was written to stdout
            mock_stdout.write.assert_called()
            output = ''.join(call[0][0] for call in mock_stdout.write.call_args_list)
            result = json.loads(output)
            
            self.assertEqual(result['count'], 2)
            self.assertEqual(result['mode'], 'monitor')
            self.assertIn('test.pem', result['matches'])
            mock_exit.assert_called_with(0)
    
    @patch('sys.argv', ['forbidden_patterns.py'])
    @patch('tools.ci.forbidden_patterns.load_config')
    @patch('tools.ci.forbidden_patterns.find_matching_files')
    def test_main_strict_mode_with_matches(self, mock_find, mock_load_config):
        """Test main function in strict mode with matches."""
        mock_load_config.return_value = {
            'hygiene': {'forbidden_patterns': ['**/*.pem']},
            'mode': 'strict'
        }
        mock_find.return_value = ['test.pem']
        
        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_with(1)
    
    @patch('sys.argv', ['forbidden_patterns.py'])
    @patch('tools.ci.forbidden_patterns.load_config')
    @patch('tools.ci.forbidden_patterns.find_matching_files')
    def test_main_monitor_mode_with_matches(self, mock_find, mock_load_config):
        """Test main function in monitor mode with matches."""
        mock_load_config.return_value = {
            'hygiene': {'forbidden_patterns': ['**/*.pem']},
            'mode': 'monitor'
        }
        mock_find.return_value = ['test.pem']
        
        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_with(0)


if __name__ == '__main__':
    unittest.main()
