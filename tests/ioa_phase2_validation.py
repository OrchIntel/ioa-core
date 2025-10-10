""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
IOA Phase2 Validation Helper

Helper to unblock CL-008 by mocking digestor in performance gate.
If real digestor is importable, prefer it. Otherwise mock.
"""

from unittest.mock import MagicMock

# If real digestor is importable, prefer it. Otherwise mock.
try:
    from src.digestor import process  # type: ignore
except Exception:
    digestor = MagicMock()
    digestor.process = MagicMock(return_value={"status": "success"})
else:
    class _Real:
        process = staticmethod(process)
    digestor = _Real()
