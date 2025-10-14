"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Proposes draft pattern from unclassified entry (mock: keyword clustering).
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


# pattern_governance.py
# Governance for pattern proposals, validation, versioning, deprecation.
# "Pattern Court" – Ensures quality/non-redundant patterns.

import json
import datetime
from typing import Dict, List, Any
import os  # Added for file ops

class PatternGovernance:
    def __init__(self, registry_file: str = 'pattern_registry.json'):
        self.registry_file = registry_file
        self.registry = self._load_registry()

    def _load_registry(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return []

    def _save_registry(self):
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=4)

    def propose_pattern(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Proposes draft pattern from unclassified entry (mock: keyword clustering)."""
        raw = entry.get('raw_ref', '')
        # Simple mock: Extract potential keywords/schema (future: LLM/Weaver)
        keywords = [word for word in raw.lower().split() if len(word) > 3]  # Placeholder
        schema = ["field1", "field2"]  # Mock; derive from content
        proposal = {
            "pattern_id": f"P{len(self.registry) + 1:03d}",
            "name": "Auto-Proposed Pattern",
            "schema": schema,
            "keywords": keywords[:3],  # Limit
            "description": f"From entry: {raw[:50]}...",
            "author": "PatternWeaver",  # Future model
            "status": "under_review"
        }
        return proposal

    def validate_pattern(self, proposal: Dict[str, Any]) -> bool:
        """Validates: No duplicates (keyword overlap <50%), not too generic, clear schema."""
        # Check duplicates
        for existing in self.registry:
            overlap = len(set(proposal['keywords']) & set(existing['keywords'])) / len(proposal['keywords']) if proposal['keywords'] else 0
            if overlap > 0.5:
                print(f"Validation failed: Duplicate overlap with {existing['pattern_id']}")
                return False
        # Generic check (edge: too broad keywords)
        generic_keywords = ['the', 'and', 'is']
        if any(kw in proposal['keywords'] for kw in generic_keywords):
            print("Warning: Generic keywords flagged.")
            # Continue but log; future reject
        # Schema clear (non-empty)
        if not proposal['schema']:
            print("Validation failed: Empty schema.")
            return False
        return True

    def version_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Adds version/timestamp/status metadata."""
        pattern['version'] = 1.0  # Initial
        pattern['creation_timestamp'] = datetime.datetime.now().isoformat()
        pattern['status'] = "active"
        pattern['linked_examples'] = []  # Future append entry IDs
        return pattern

    def deprecate_pattern(self, pattern_id: str):
        """Marks pattern obsolete; prevents future use."""
        for pattern in self.registry:
            if pattern['pattern_id'] == pattern_id:
                pattern['status'] = "deprecated"
                self._save_registry()
                print(f"Pattern {pattern_id} deprecated.")
                return
        print(f"Pattern {pattern_id} not found.")

    def add_to_registry(self, pattern: Dict[str, Any]):
        self.registry.append(pattern)
        self._save_registry()
