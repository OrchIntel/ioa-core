""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Test IOA Security: Signature Engine

Verifies that the signature engine correctly signs and verifies data.
"""

from src.security.signature_engine import SignatureEngine

def test_signature_roundtrip():
    """Test that signature engine correctly signs and verifies data."""
    eng = SignatureEngine()
    msg = b"ioa-core-v2.5.0"
    sig = eng.sign(msg)
    assert eng.verify(msg, sig) is True
    assert eng.verify(b"tampered", sig) is False
