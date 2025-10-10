""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""

Migrates audit chains from the old format to the new standardized format:
- Old: logs/audit_chain-YYYYMMDD-HHMMSS-<hash>.jsonl
- New: audit_chain/YYYYMMDD/run_<id>.jsonl + audit_chain/YYYYMMDD/run_<id>_receipt.json
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import hashlib

def migrate_audit_chains():
    """Migrate existing audit chains to standardized format."""
    logs_dir = Path("logs")
    audit_chain_dir = Path("audit_chain")
    
    # Create new directory structure
    audit_chain_dir.mkdir(exist_ok=True)
    
    # Find all audit chain files
    audit_files = list(logs_dir.glob("audit_chain*.jsonl"))
    
    print(f"Found {len(audit_files)} audit chain files to migrate")
    
    for audit_file in sorted(audit_files):
        print(f"Migrating {audit_file.name}")
        
        # Parse date from filename
        if audit_file.name == "audit_chain.jsonl":
            # Use current date for the main file
            date_str = datetime.now().strftime("%Y%m%d")
        else:
            # Extract date from filename like audit_chain-20250820-075914-dcfc17c04178.jsonl
            try:
                parts = audit_file.stem.split("-")
                if len(parts) >= 3:
                    date_str = parts[1]  # 20250820
                else:
                    date_str = datetime.now().strftime("%Y%m%d")
            except:
                date_str = datetime.now().strftime("%Y%m%d")
        
        # Create date directory
        date_dir = audit_chain_dir / date_str
        date_dir.mkdir(exist_ok=True)
        
        # Generate run ID (use hash of original filename for uniqueness)
        run_id = hashlib.md5(audit_file.name.encode()).hexdigest()[:8]
        
        # Copy the JSONL file
        new_jsonl_path = date_dir / f"run_{run_id}.jsonl"
        shutil.copy2(audit_file, new_jsonl_path)
        
        # Create receipt file
        receipt_data = create_receipt(audit_file, run_id)
        receipt_path = date_dir / f"run_{run_id}_receipt.json"
        with receipt_path.open('w') as f:
            json.dump(receipt_data, f, indent=2)
        
        print(f"  -> {new_jsonl_path}")
        print(f"  -> {receipt_path}")

def create_receipt(audit_file: Path, run_id: str) -> Dict[str, Any]:
    """Create a receipt file for an audit chain."""
    # Read the audit chain to get metadata
    entries = []
    root_hash = None
    tip_hash = None
    
    with audit_file.open('r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                    if root_hash is None:
                        root_hash = entry.get('hash')
                    tip_hash = entry.get('hash')
                except json.JSONDecodeError:
                    continue
    
    # Create receipt
    receipt = {
        "run_id": run_id,
        "source_file": str(audit_file),
        "migrated_at": datetime.now().isoformat(),
        "entry_count": len(entries),
        "root_hash": root_hash,
        "tip_hash": tip_hash,
        "format_version": "v2.5.0",
        "description": "Migrated audit chain from legacy format"
    }
    
    return receipt

if __name__ == "__main__":
    migrate_audit_chains()
    print("Migration completed!")
