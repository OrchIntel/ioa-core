# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Ensure local `src/` packages are importable in subprocess `python -m` calls."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"

if _SRC.is_dir():
    src_path = str(_SRC)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Force legacy `cli.*` imports to resolve to local src/cli package.
    cli_init = _SRC / "cli" / "__init__.py"
    if cli_init.exists():
        spec = importlib.util.spec_from_file_location(
            "cli",
            cli_init,
            submodule_search_locations=[str(_SRC / "cli")],
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["cli"] = module
            spec.loader.exec_module(module)
