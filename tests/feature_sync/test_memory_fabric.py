# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Feature sync proof: Memory Fabric functionality."""

from pathlib import Path


def test_memory_fabric_module_exists():
    """Verify Memory Fabric module exists."""
    mem_dir = Path(__file__).parent.parent.parent / "src" / "ioa_core" / "memory_fabric"
    assert mem_dir.exists(), "Memory fabric directory not found"
    assert (mem_dir / "__init__.py").exists(), "__init__.py not found"
    print("✅ Memory fabric module exists")


def test_memory_stores_exist():
    """Verify memory storage backends exist."""
    stores_dir = Path(__file__).parent.parent.parent / "src" / "ioa_core" / "memory_fabric" / "stores"
    
    assert stores_dir.exists(), "Stores directory not found"
    assert (stores_dir / "base.py").exists(), "base.py not found"
    assert (stores_dir / "sqlite.py").exists(), "sqlite.py not found"
    assert (stores_dir / "local_jsonl.py").exists(), "local_jsonl.py not found"
    assert (stores_dir / "s3.py").exists(), "s3.py not found"
    print("✅ Memory storage backends exist: sqlite, local_jsonl, s3")


def test_memory_core_modules_exist():
    """Verify core memory modules exist."""
    mem_dir = Path(__file__).parent.parent.parent / "src" / "ioa_core" / "memory_fabric"
    
    assert (mem_dir / "fabric.py").exists(), "fabric.py not found"
    assert (mem_dir / "schema.py").exists(), "schema.py not found"
    assert (mem_dir / "crypto.py").exists(), "crypto.py not found"
    assert (mem_dir / "tiering_4d.py").exists(), "tiering_4d.py not found"
    print("✅ Core memory modules exist: fabric, schema, crypto, tiering_4d")


if __name__ == "__main__":
    test_memory_fabric_module_exists()
    test_memory_stores_exist()
    test_memory_core_modules_exist()
    print("\n✅ All memory fabric proof tests passed")
