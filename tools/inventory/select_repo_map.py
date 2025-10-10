""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
import os, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
mode = os.environ.get("IOA_REPO_MODE", "internal").lower()
src = ROOT / "tools" / "inventory" / f"repo_map.{mode}.json"
dst_dir = ROOT / "ops" / "reports"
dst_dir.mkdir(parents=True, exist_ok=True)
dst = dst_dir / "latest_repo_map.json"

if not src.exists():
    raise SystemExit(f"[select_repo_map] missing {src}; set IOA_REPO_MODE=internal|public and ensure maps exist.")
shutil.copyfile(src, dst)
print(f"[select_repo_map] mode={mode} -> {dst}")
