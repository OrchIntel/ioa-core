# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Test bootstrap example."""

import json
import subprocess
import tempfile
from pathlib import Path


def test_bootstrap_creates_project():
    """Test that bootstrap creates project files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["python", "examples/00_bootstrap/boot_project.py", "test-project"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check output
        assert "✅ Project scaffolded" in result.stdout
        
        # Check files were created
        project_dir = Path.cwd() / "test-project"
        assert project_dir.exists()
        assert (project_dir / "ioa.yaml").exists()
        assert (project_dir / "README.md").exists()
        
        # Cleanup
        import shutil
        shutil.rmtree(project_dir)


if __name__ == "__main__":
    test_bootstrap_creates_project()
    print("✅ Bootstrap test passed")

