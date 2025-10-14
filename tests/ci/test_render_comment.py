"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.ci.render_comment import (
    load_summary, load_template, transform_summary, main
)


class TestRenderComment(unittest.TestCase):
    """Test cases for comment renderer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.template_dir = Path(self.temp_dir) / "templates"
        self.template_dir.mkdir()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_summary_success(self):
        """Test loading summary from valid JSON file."""
        summary_data = {
            "profile": "pr",
            "mode": "monitor",
            "duration": 1.5,
            "results": [
                {
                    "name": "governance",
                    "status": "pass",
                    "message": "All checks passed",
                    "duration": 0.5
                }
            ]
        }
        
        summary_file = Path(self.temp_dir) / "summary.json"
        summary_file.write_text(json.dumps(summary_data))
        
        result = load_summary(str(summary_file))
        self.assertEqual(result["profile"], "pr")
        self.assertEqual(result["mode"], "monitor")
        self.assertEqual(len(result["results"]), 1)
    
    def test_load_summary_file_not_found(self):
        """Test loading summary when file doesn't exist."""
        with patch('sys.exit') as mock_exit:
            load_summary("nonexistent.json")
            mock_exit.assert_called_with(1)
    
    def test_load_summary_invalid_json(self):
        """Test loading summary with invalid JSON."""
        summary_file = Path(self.temp_dir) / "invalid.json"
        summary_file.write_text("invalid json content")
        
        with patch('sys.exit') as mock_exit:
            load_summary(str(summary_file))
            mock_exit.assert_called_with(1)
    
    def test_load_template_success(self):
        """Test loading template successfully."""
        template_content = "Hello {{ name }}!"
        template_file = self.template_dir / "test.j2"
        template_file.write_text(template_content)
        
        template = load_template(str(template_file))
        self.assertIsNotNone(template)
        
        # Test rendering
        result = template.render(name="World")
        self.assertEqual(result, "Hello World!")
    
    def test_load_template_not_found(self):
        """Test loading template when file doesn't exist."""
        with patch('sys.exit') as mock_exit:
            load_template("nonexistent.j2")
            mock_exit.assert_called_with(1)
    
    def test_transform_summary(self):
        """Test transforming summary data for template."""
        summary = {
            "profile": "pr",
            "mode": "monitor",
            "duration": 1.5,
            "total_gates": 4,
            "passed": 3,
            "warned": 1,
            "failed": 0,
            "skipped": 0,
            "artifacts_dir": "artifacts/lens/gates",
            "results": [
                {
                    "name": "governance",
                    "status": "pass",
                    "message": "All checks passed",
                    "duration": 0.5,
                    "details": {"laws_checked": 7}
                },
                {
                    "name": "security",
                    "status": "warn",
                    "message": "Some warnings found",
                    "duration": 0.3,
                    "details": {"issues": 2}
                }
            ]
        }
        
        result = transform_summary(summary)
        
        # Check basic fields
        self.assertEqual(result["profile"], "pr")
        self.assertEqual(result["mode"], "monitor")
        self.assertEqual(result["duration"], 1.5)
        self.assertEqual(result["total_gates"], 4)
        self.assertEqual(result["passed"], 3)
        
        # Check results transformation
        self.assertIn("governance", result["results"])
        self.assertIn("security", result["results"])
        
        governance = result["results"]["governance"]
        self.assertTrue(governance["ok"])
        self.assertEqual(governance["status"], "pass")
        self.assertEqual(governance["message"], "All checks passed")
        self.assertEqual(governance["details"], {"laws_checked": 7})
        
        security = result["results"]["security"]
        self.assertFalse(security["ok"])
        self.assertEqual(security["status"], "warn")
        self.assertEqual(security["message"], "Some warnings found")
        self.assertEqual(security["details"], {"issues": 2})
        
        # Check artifact links
        self.assertGreater(len(governance["links"]), 0)
        self.assertGreater(len(security["links"]), 0)
    
    def test_transform_summary_minimal(self):
        """Test transforming minimal summary data."""
        summary = {
            "profile": "pr",
            "mode": "monitor",
            "results": []
        }
        
        result = transform_summary(summary)
        
        self.assertEqual(result["profile"], "pr")
        self.assertEqual(result["mode"], "monitor")
        self.assertEqual(result["total_gates"], 0)
        self.assertEqual(result["passed"], 0)
        self.assertEqual(len(result["results"]), 0)
    
    @patch('sys.argv', ['render_comment.py', '--summary', 'test_summary.json', '--template', 'test_template.j2'])
    @patch('tools.ci.render_comment.load_summary')
    @patch('tools.ci.render_comment.load_template')
    @patch('tools.ci.render_comment.transform_summary')
    def test_main_success(self, mock_transform, mock_load_template, mock_load_summary):
        """Test main function with successful rendering."""
        # Mock data
        mock_summary = {"profile": "pr", "results": []}
        mock_load_summary.return_value = mock_summary
        
        mock_template = mock_load_template.return_value
        mock_template.render.return_value = "Rendered comment"
        
        mock_transform.return_value = {"profile": "pr", "results": {}}
        
        with patch('sys.stdout') as mock_stdout:
            main()
            
            # Verify the functions were called
            mock_load_summary.assert_called_once_with('test_summary.json')
            mock_load_template.assert_called_once_with('test_template.j2')
            mock_transform.assert_called_once_with(mock_summary)
            mock_template.render.assert_called_once_with(profile='pr', results={})
            
            # Check that rendered content was written to stdout
            # Debug: print all calls
            calls = mock_stdout.write.call_args_list
            print(f"All calls: {calls}")
            if calls:
                print(f"Last call: {calls[-1]}")
            
            # Check that the rendered content was written
            self.assertTrue(any("Rendered comment" in str(call) for call in calls))
    
    @patch('sys.argv', ['render_comment.py', '--summary', 'test_summary.json', '--output', 'output.md'])
    @patch('tools.ci.render_comment.load_summary')
    @patch('tools.ci.render_comment.load_template')
    @patch('tools.ci.render_comment.transform_summary')
    def test_main_with_output_file(self, mock_transform, mock_load_template, mock_load_summary):
        """Test main function with output file."""
        # Mock data
        mock_summary = {"profile": "pr", "results": []}
        mock_load_summary.return_value = mock_summary
        
        mock_template = mock_load_template.return_value
        mock_template.render.return_value = "Rendered comment"
        
        mock_transform.return_value = {"profile": "pr", "results": {}}
        
        with patch('builtins.open', mock_open()) as mock_file:
            main()
            
            # Check that file was written
            mock_file.assert_called_with('output.md', 'w')
            mock_file.return_value.write.assert_called_with("Rendered comment")
    
    @patch('sys.argv', ['render_comment.py'])
    @patch('tools.ci.render_comment.load_summary')
    def test_main_render_error(self, mock_load_summary):
        """Test main function with render error."""
        mock_load_summary.return_value = {"profile": "pr", "results": []}
        
        with patch('tools.ci.render_comment.load_template') as mock_load_template:
            mock_template = mock_load_template.return_value
            mock_template.render.side_effect = Exception("Render error")
            
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_with(1)


if __name__ == '__main__':
    unittest.main()
