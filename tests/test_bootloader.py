""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Test suite for test_bootloader
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


# test_bootloader.py
# Unit tests for bootloader.py using pytest and mocks (temp dirs).

import pytest
import os
import json
import sys
from unittest.mock import patch

# Add src directory to Python path for imports
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.bootloader import Bootloader
from src.llm_adapter import OpenAIService

@pytest.fixture
def temp_base_path(tmp_path):
    return str(tmp_path / "projects")

@pytest.fixture
def bootloader(temp_base_path):
    return Bootloader(base_path=temp_base_path)

@patch('os.getenv', return_value=None)  # Mock non-interactive check
@patch('sys.stdin.isatty', return_value=True)  # Mock TTY check
@patch('builtins.input', side_effect=['screenwriting', 'TestProj'])
def test_run_wizard_preset(mock_isatty, mock_getenv, mock_input, bootloader):
    bootloader.run_wizard()
    project_path = os.path.join(bootloader.base_path, "TestProj.ioa")
    assert os.path.exists(project_path)

    schema_file = os.path.join(project_path, "schema.json")
    assert os.path.exists(schema_file)
    with open(schema_file, 'r') as f:
        schema = json.load(f)
    assert schema == {"characters": ["name", "bio", "traits"], "scenes": ["id", "title", "content"]}

    boot_file = os.path.join(project_path, "boot_prompt.json")
    assert os.path.exists(boot_file)
    with open(boot_file, 'r') as f:
        boot = json.load(f)
    assert boot["type"] == "screenwriting"
    assert boot["name"] == "TestProj.IOA"
    assert "schema" in boot
    assert boot["agents"] == ["Analyzer", "Editor"]

@patch('os.getenv', return_value=None)  # Mock non-interactive check
@patch('sys.stdin.isatty', return_value=True)  # Mock TTY check
@patch('builtins.input', side_effect=['custom', 'CustomProj', 'case: id, client, facts'])
@patch('src.bootloader.OpenAIService')
def test_run_wizard_custom(mock_openai_service, mock_input, mock_isatty, mock_getenv, bootloader):
    # PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <fix patch target>
    mock_service = mock_openai_service.return_value
    mock_service.execute.return_value = '{"custom": ["id", "client", "facts"]}'
    
    bootloader.run_wizard()
    project_path = os.path.join(bootloader.base_path, "CustomProj.ioa")
    assert os.path.exists(project_path)

    schema_file = os.path.join(project_path, "schema.json")
    with open(schema_file, 'r') as f:
        schema = json.load(f)
    assert schema == {"custom": ["id", "client", "facts"]}
