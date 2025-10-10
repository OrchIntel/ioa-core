# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



import base64
import hashlib
import secrets
from typing import Optional, Dict, Any, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
"""Crypto module."""

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# PATCH: Cursor-2025-09-10 DISPATCH-OSS-20250910-MEMORY-FABRIC-REFACTOR <crypto module>

class MemoryCrypto:
    """AES-GCM encryption and redaction utilities for Memory Fabric."""
    
    def __init__(self, key: Optional[str] = None):
        """Initialize crypto with optional key."""
        self.key = key
        self._encryption_key = None
        self._is_encryption_enabled = False
        
        if self.key:
            self._encryption_key = self._derive_key(self.key)
            self._is_encryption_enabled = True
    
    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        if salt is None:
            salt = b'ioa_memory_fabric_salt'  # Fixed salt for consistency
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode('utf-8'))
    
    def encrypt_content(self, content: str) -> Tuple[str, str]:
        """Encrypt content using AES-GCM."""
        if not self._is_encryption_enabled:
            return content, "none"
        
        try:
            # Generate random nonce
            nonce = secrets.token_bytes(12)  # 96 bits for GCM
            
            # Encrypt content
            aesgcm = AESGCM(self._encryption_key)
            ciphertext = aesgcm.encrypt(nonce, content.encode('utf-8'), None)
            
            # Combine nonce + ciphertext and encode
            encrypted_data = nonce + ciphertext
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            return encrypted_b64, "aes-gcm"
            
        except Exception as e:
            # Return original content if encryption fails
            return content, "none"
    
    def decrypt_content(self, encrypted_content: str, encryption_mode: str) -> str:
        """Decrypt content using AES-GCM."""
        if encryption_mode != "aes-gcm" or not self._is_encryption_enabled:
            return encrypted_content
        
        try:
            # Decode base64
            encrypted_data = base64.b64decode(encrypted_content.encode('utf-8'))
            
            # Split nonce and ciphertext
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            
            # Decrypt content
            aesgcm = AESGCM(self._encryption_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            # Return original content if decryption fails
            return encrypted_content
    
    def redact_pii(self, content: str, redaction_rules: Optional[Dict[str, str]] = None) -> str:
        """Redact PII from content using configurable rules."""
        import re
        
        if redaction_rules is None:
            redaction_rules = {
                'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\b\d{3}-\d{4}\b',
                'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
                'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            }
        
        redacted_content = content
        
        for pii_type, pattern in redaction_rules.items():
            replacement = f'[{pii_type.upper()}]'
            redacted_content = re.sub(pattern, replacement, redacted_content, flags=re.IGNORECASE)
        
        return redacted_content
    
    def hash_content(self, content: str) -> str:
        """Generate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def is_encryption_enabled(self) -> bool:
        """Check if encryption is enabled."""
        return self._is_encryption_enabled
    
    def get_encryption_mode(self) -> str:
        """Get current encryption mode."""
        return "aes-gcm" if self._is_encryption_enabled else "none"
    
    def generate_key(self) -> str:
        """Generate a new encryption key."""
        return secrets.token_urlsafe(32)
