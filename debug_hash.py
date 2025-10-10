""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from src.audit.canonical import compute_hash

# Create test data like in the test
entry_data = {
    "event_id": "evt_001",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "prev_hash": "0" * 64,
    "hash": "",  # Will be computed
    "payload": {
        "event_type": "test_event_1",
        "data": "test_data_1"
    },
    "writer": "test_service"
}

print("Original data:")
print(json.dumps(entry_data, indent=2))

# Compute hash on data without hash field
hash_data = entry_data.copy()
hash_data.pop('hash', None)
computed_hash = compute_hash(hash_data)
entry_data["hash"] = computed_hash
print(f"\nComputed hash: {computed_hash}")

# Now simulate what happens when we read it back
print("\nSimulating read from file...")

# Write to file and read back
with open("test_entry.json", "w") as f:
    json.dump(entry_data, f, indent=2)

with open("test_entry.json", "r") as f:
    loaded_data = json.load(f)

print("Loaded data:")
print(json.dumps(loaded_data, indent=2))

# Compute hash on loaded data (without hash field)
hash_data_loaded = loaded_data.copy()
hash_data_loaded.pop('hash', None)
recomputed_hash = compute_hash(hash_data_loaded)
print(f"\nRecomputed hash: {recomputed_hash}")
print(f"Original hash:   {computed_hash}")
print(f"Match: {recomputed_hash == computed_hash}")

# Now test with AuditEntry model
from src.audit.models import AuditEntry

# Create AuditEntry from loaded data
entry = AuditEntry(**loaded_data)
print(f"\nAuditEntry timestamp type: {type(entry.timestamp)}")
print(f"AuditEntry timestamp: {entry.timestamp}")

# Test hash verification exactly like in the verification code
entry_dict = entry.model_dump()
print(f"model_dump() timestamp: {entry_dict['timestamp']}")
print(f"model_dump() timestamp type: {type(entry_dict['timestamp'])}")

if 'timestamp' in entry_dict and isinstance(entry_dict['timestamp'], datetime):
    entry_dict['timestamp'] = entry_dict['timestamp'].isoformat()
    print(f"After isoformat(): {entry_dict['timestamp']}")

# Remove fields that shouldn't be included in hash computation (like in verification)
entry_dict.pop('hash', None)
entry_dict.pop('signature', None)
entry_dict.pop('pubkey', None)

final_hash = compute_hash(entry_dict)
print(f"Final computed hash: {final_hash}")
print(f"Match: {final_hash == computed_hash}")

# Let's also test the canonical JSON directly
from src.audit.canonical import canonicalize_json
print(f"\nCanonical JSON of original: {canonicalize_json(hash_data_loaded)}")
print(f"Canonical JSON of model_dump: {canonicalize_json(entry_dict)}")
