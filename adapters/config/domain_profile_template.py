"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.


"""
Domain Profile Template Module

Provides the JSON schema for validating domain plugin profiles.
Used by the agent router to enforce schema compliance when loading plugins.
"""

import json
from pathlib import Path

# Load the domain profile schema from the JSON file
def _load_domain_schema() -> dict:
    """Load the domain profile schema from the JSON file."""
    schema_path = Path(__file__).parent / "domain_profile_template.json"
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        # Fallback schema if file loading fails
        return {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "minLength": 1},
                "capabilities": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                "compliance": {
                    "type": "object",
                    "properties": {
                        "gdpr": {"type": "boolean"},
                        "hipaa": {"type": "boolean"}
                    },
                    "additionalProperties": False
                }
            },
            "required": ["domain", "capabilities"],
            "additionalProperties": True
        }

# Export the schema
DOMAIN_PROFILE_SCHEMA = _load_domain_schema()
