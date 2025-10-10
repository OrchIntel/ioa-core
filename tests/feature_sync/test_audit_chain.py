# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Feature sync proof: Audit Chain functionality."""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_audit_module_exists():
    """Verify audit chain module exists."""
    audit_chain_file = Path(__file__).parent.parent.parent / "src" / "ioa_core" / "governance" / "audit_chain.py"
    assert audit_chain_file.exists(), "Audit chain module not found"
    print("✅ Audit chain module exists")


def test_audit_has_auditchain_class():
    """Verify AuditChain class is defined."""
    audit_chain_file = Path(__file__).parent.parent.parent / "src" / "ioa_core" / "governance" / "audit_chain.py"
    content = audit_chain_file.read_text()
    
    assert "class AuditChain" in content, "AuditChain class not found"
    assert "def log" in content, "log method not found"
    print("✅ AuditChain class and log method found")


def test_audit_governance_structure():
    """Verify governance module structure."""
    gov_dir = Path(__file__).parent.parent.parent / "src" / "ioa_core" / "governance"
    
    assert gov_dir.exists(), "Governance directory not found"
    assert (gov_dir / "audit_chain.py").exists(), "audit_chain.py not found"
    assert (gov_dir / "__init__.py").exists(), "__init__.py not found"
    print("✅ Governance module structure verified")


if __name__ == "__main__":
    test_audit_module_exists()
    test_audit_has_auditchain_class()
    test_audit_governance_structure()
    print("\n✅ All audit chain proof tests passed")
