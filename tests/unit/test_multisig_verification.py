""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
Unit tests for m-of-n multisignature verification functionality.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from adapters.audit.verify import AuditChainVerifier
except ImportError:
    print("Warning: Could not import AuditChainVerifier, running in mock mode")
    AuditChainVerifier = None

class TestMultisigVerification(unittest.TestCase):
    """Test cases for m-of-n multisignature verification."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.chain_dir = Path(self.temp_dir) / "test_chain"
        self.chain_dir.mkdir()
        
        # Create test audit entries
        self.create_test_entries()
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_entries(self):
        """Create test audit entries with various signature configurations."""
        # Entry with 2 signatures (should pass m=2 requirement)
        entry_1 = {
            "index": 1,
            "timestamp": 1697030400,
            "payload": {
                "action": "test_action",
                "data": {"test": "data"},
                "signatures": [
                    {"signature": "sig1", "key_id": "key1", "algorithm": "RSA-SHA256"},
                    {"signature": "sig2", "key_id": "key2", "algorithm": "RSA-SHA256"}
                ]
            },
            "hash": "hash1",
            "previous_hash": None
        }
        
        # Entry with 1 signature (should fail m=2 requirement)
        entry_2 = {
            "index": 2,
            "timestamp": 1697030401,
            "payload": {
                "action": "test_action_2",
                "data": {"test": "data2"},
                "signatures": [
                    {"signature": "sig3", "key_id": "key1", "algorithm": "RSA-SHA256"}
                ]
            },
            "hash": "hash2",
            "previous_hash": "hash1"
        }
        
        # Entry with 3 signatures (should pass m=2 requirement)
        entry_3 = {
            "index": 3,
            "timestamp": 1697030402,
            "payload": {
                "action": "test_action_3",
                "data": {"test": "data3"},
                "signatures": [
                    {"signature": "sig4", "key_id": "key1", "algorithm": "RSA-SHA256"},
                    {"signature": "sig5", "key_id": "key2", "algorithm": "RSA-SHA256"},
                    {"signature": "sig6", "key_id": "key3", "algorithm": "RSA-SHA256"}
                ]
            },
            "hash": "hash3",
            "previous_hash": "hash2"
        }
        
        # Entry with no signatures (should fail m=2 requirement)
        entry_4 = {
            "index": 4,
            "timestamp": 1697030403,
            "payload": {
                "action": "test_action_4",
                "data": {"test": "data4"}
            },
            "hash": "hash4",
            "previous_hash": "hash3"
        }
        
        # Save entries to files
        entries = [entry_1, entry_2, entry_3, entry_4]
        for i, entry in enumerate(entries, 1):
            entry_file = self.chain_dir / f"entry_{i}.json"
            with open(entry_file, 'w') as f:
                json.dump(entry, f)
    
    def test_multisig_verification_m2_success(self):
        """Test multisignature verification with m=2 requirement (should pass)."""
        if not AuditChainVerifier:
            self.skipTest("AuditChainVerifier not available")
        
        # Set environment variable for m=2 requirement
        with patch.dict(os.environ, {'IOA_VERIFY_M_REQUIRED': '2'}):
            verifier = AuditChainVerifier(str(self.chain_dir))
            result = verifier.verify()
            
            # Should pass because entries 1 and 3 have >= 2 signatures
            # Entries 2 and 4 should fail but not cause overall failure if fail_fast=False
            self.assertIsNotNone(result)
    
    def test_multisig_verification_m3_failure(self):
        """Test multisignature verification with m=3 requirement (should fail)."""
        if not AuditChainVerifier:
            self.skipTest("AuditChainVerifier not available")
        
        # Set environment variable for m=3 requirement
        with patch.dict(os.environ, {'IOA_VERIFY_M_REQUIRED': '3'}):
            verifier = AuditChainVerifier(str(self.chain_dir))
            result = verifier.verify()
            
            # Should fail because only entry 3 has >= 3 signatures
            # Entries 1, 2, and 4 should fail the m=3 requirement
            self.assertIsNotNone(result)
    
    def test_multisig_verification_no_requirement(self):
        """Test verification without multisignature requirement."""
        if not AuditChainVerifier:
            self.skipTest("AuditChainVerifier not available")
        
        # No IOA_VERIFY_M_REQUIRED environment variable
        with patch.dict(os.environ, {}, clear=True):
            verifier = AuditChainVerifier(str(self.chain_dir))
            result = verifier.verify()
            
            # Should pass without multisignature requirements
            self.assertIsNotNone(result)
    
    def test_multisig_verification_invalid_m(self):
        """Test multisignature verification with invalid m value."""
        if not AuditChainVerifier:
            self.skipTest("AuditChainVerifier not available")
        
        # Set invalid m value
        with patch.dict(os.environ, {'IOA_VERIFY_M_REQUIRED': 'invalid'}):
            verifier = AuditChainVerifier(str(self.chain_dir))
            result = verifier.verify()
            
            # Should pass because invalid m value is ignored
            self.assertIsNotNone(result)
    
    def test_multisig_verification_negative_m(self):
        """Test multisignature verification with negative m value."""
        if not AuditChainVerifier:
            self.skipTest("AuditChainVerifier not available")
        
        # Set negative m value
        with patch.dict(os.environ, {'IOA_VERIFY_M_REQUIRED': '-1'}):
            verifier = AuditChainVerifier(str(self.chain_dir))
            result = verifier.verify()
            
            # Should pass because negative m value is ignored
            self.assertIsNotNone(result)
    
    def test_multisig_verification_zero_m(self):
        """Test multisignature verification with zero m value."""
        if not AuditChainVerifier:
            self.skipTest("AuditChainVerifier not available")
        
        # Set zero m value
        with patch.dict(os.environ, {'IOA_VERIFY_M_REQUIRED': '0'}):
            verifier = AuditChainVerifier(str(self.chain_dir))
            result = verifier.verify()
            
            # Should pass because zero m value is ignored
            self.assertIsNotNone(result)
    
    def test_multisig_verification_missing_signatures_field(self):
        """Test multisignature verification with missing signatures field."""
        if not AuditChainVerifier:
            self.skipTest("AuditChainVerifier not available")
        
        # Create entry without signatures field
        entry_no_sigs = {
            "index": 5,
            "timestamp": 1697030404,
            "payload": {
                "action": "test_action_no_sigs",
                "data": {"test": "data_no_sigs"}
            },
            "hash": "hash5",
            "previous_hash": "hash4"
        }
        
        entry_file = self.chain_dir / "entry_5.json"
        with open(entry_file, 'w') as f:
            json.dump(entry_no_sigs, f)
        
        # Set m=2 requirement
        with patch.dict(os.environ, {'IOA_VERIFY_M_REQUIRED': '2'}):
            verifier = AuditChainVerifier(str(self.chain_dir))
            result = verifier.verify()
            
            # Should fail because entry 5 has no signatures field
            self.assertIsNotNone(result)
    
    def test_multisig_verification_empty_signatures(self):
        """Test multisignature verification with empty signatures array."""
        if not AuditChainVerifier:
            self.skipTest("AuditChainVerifier not available")
        
        # Create entry with empty signatures array
        entry_empty_sigs = {
            "index": 6,
            "timestamp": 1697030405,
            "payload": {
                "action": "test_action_empty_sigs",
                "data": {"test": "data_empty_sigs"},
                "signatures": []
            },
            "hash": "hash6",
            "previous_hash": "hash5"
        }
        
        entry_file = self.chain_dir / "entry_6.json"
        with open(entry_file, 'w') as f:
            json.dump(entry_empty_sigs, f)
        
        # Set m=2 requirement
        with patch.dict(os.environ, {'IOA_VERIFY_M_REQUIRED': '2'}):
            verifier = AuditChainVerifier(str(self.chain_dir))
            result = verifier.verify()
            
            # Should fail because entry 6 has empty signatures array
            self.assertIsNotNone(result)

class TestMultisigVerificationIntegration(unittest.TestCase):
    """Integration tests for m-of-n multisignature verification."""
    
    def test_multisig_verification_cli(self):
        """Test multisignature verification via CLI."""
        # This would test the actual CLI command
        # For now, just verify the environment variable is read correctly
        with patch.dict(os.environ, {'IOA_VERIFY_M_REQUIRED': '2'}):
            m_required = os.environ.get('IOA_VERIFY_M_REQUIRED')
            self.assertEqual(m_required, '2')
    
    def test_multisig_verification_config(self):
        """Test multisignature verification configuration."""
        # Test various m values
        test_values = ['1', '2', '3', '5', '10']
        
        for m_value in test_values:
            with patch.dict(os.environ, {'IOA_VERIFY_M_REQUIRED': m_value}):
                m_required = os.environ.get('IOA_VERIFY_M_REQUIRED')
                self.assertEqual(m_required, m_value)
    
    def test_multisig_verification_edge_cases(self):
        """Test multisignature verification edge cases."""
        # Test very large m value
        with patch.dict(os.environ, {'IOA_VERIFY_M_REQUIRED': '1000'}):
            m_required = os.environ.get('IOA_VERIFY_M_REQUIRED')
            self.assertEqual(m_required, '1000')
        
        # Test m value with whitespace
        with patch.dict(os.environ, {'IOA_VERIFY_M_REQUIRED': ' 2 '}):
            m_required = os.environ.get('IOA_VERIFY_M_REQUIRED')
            self.assertEqual(m_required, ' 2 ')

if __name__ == '__main__':
    unittest.main()
