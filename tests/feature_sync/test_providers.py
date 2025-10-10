# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Feature sync proof: LLM Provider support."""

from pathlib import Path


def test_llm_module_exists():
    """Verify LLM module exists."""
    llm_dir = Path(__file__).parent.parent.parent / "src" / "ioa_core" / "llm_providers"
    assert llm_dir.exists(), "LLM providers directory not found"
    print("✅ LLM providers module exists")


def test_provider_modules_exist():
    """Verify provider support modules exist."""
    llm_dir = Path(__file__).parent.parent.parent / "src" / "ioa_core" / "llm_providers"
    
    # Check for provider utility modules
    utils_files = ["ollama_utils.py", "ollama_smoketest.py"]
    
    found_files = []
    for util_file in utils_files:
        if (llm_dir / util_file).exists():
            found_files.append(util_file)
    
    print(f"ℹ️  Found {len(found_files)} provider support files: {', '.join(found_files)}")
    assert len(found_files) >= 1, f"Expected provider support files, found {len(found_files)}"
    print("✅ Provider support modules exist")


def test_llm_manager_exists():
    """Verify LLM manager exists."""
    manager_file = Path(__file__).parent.parent.parent / "src" / "ioa_core" / "llm_manager.py"
    assert manager_file.exists(), "llm_manager.py not found"
    
    content = manager_file.read_text()
    assert "class LLMManager" in content or "LLMManager" in content, "LLMManager reference not found"
    print("✅ LLM Manager module exists")


if __name__ == "__main__":
    test_llm_module_exists()
    test_provider_modules_exist()
    test_llm_manager_exists()
    print("\n✅ All provider proof tests passed")
