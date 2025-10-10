""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

import subprocess
import sys


def test_doctor_sample_exits_zero():
    # Ensure CLI returns 0 for sample doctor
    proc = subprocess.run(
        [sys.executable, "-m", "cartridges._framework.cli", "doctor", "sample"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr


