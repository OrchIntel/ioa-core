""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Test IOA Agent Router: Domain Schema Validation

Verifies that domain profiles correctly validate against the schema template.
"""

import json
from jsonschema import validate
from pathlib import Path

def test_domain_profile_schema_examples(tmp_path: Path):
    """Test that example domain profiles validate against the schema."""
    schema = json.loads(Path("config/domain_profile_template.json").read_text())
    writer = {"domain": "writer.ioa", "capabilities": ["summarize","edit"], "compliance": {"gdpr": True, "hipaa": False}}
    law = {"domain": "law.ioa", "capabilities": ["cite","reason"], "compliance": {"gdpr": True, "hipaa": True}}
    validate(writer, schema)
    validate(law, schema)
