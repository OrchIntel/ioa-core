"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
This module provides secure cold storage capabilities with AES-256 encryption
for data at rest. Enterprise versions can extend this with key rotation and
advanced key management features.
"""

import os
import json
import base64
from typing import Any, Dict, Optional, Union
from pathlib import Path
import logging

# PATCH: Cursor-2025-08-24 Added AES-256 encryption support for cold storage
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logging.warning("cryptography library not available. Cold storage will use plain text.")

logger = logging.getLogger(__name__)

class ColdStorage:
    """Secure cold storage with AES-256 encryption at rest."""
    
    def __init__(self, storage_path: Union[str, Path], 
                 encryption_key: Optional[str] = None,
                 enable_encryption: bool = True):
        """
        Initialize cold storage with optional encryption.
        
        Args:
            storage_path: Directory path for storage
            encryption_key: Encryption key (if None, generates from environment)
            enable_encryption: Whether to enable encryption (feature flag)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.enable_encryption = enable_encryption and CRYPTOGRAPHY_AVAILABLE
        
        if self.enable_encryption:
            self._setup_encryption(encryption_key)
            logger.info("Cold storage encryption enabled with AES-256")
        else:
            logger.warning("Cold storage encryption disabled - data stored in plain text")
    
    def _setup_encryption(self, encryption_key: Optional[str]) -> None:
        """Setup encryption with key derivation."""
        if encryption_key:
            key = encryption_key.encode()
        else:
            # Generate key from environment or use default
            env_key = os.getenv('IOA_COLD_STORAGE_KEY')
            if env_key:
                key = env_key.encode()
            else:
                # Generate a default key (not recommended for production)
                key = os.urandom(32)
                logger.warning("Using generated encryption key. Set IOA_COLD_STORAGE_KEY for production.")
        
        # Derive encryption key using PBKDF2
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key))
        
        self.fernet = Fernet(derived_key)
        self.salt = salt
    
    def store(self, key: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store data with optional encryption.
        
        Args:
            key: Unique identifier for the data
            data: Data to store
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare data for storage
            storage_data = {
                'data': data,
                'metadata': metadata or {},
                'timestamp': self._get_timestamp(),
                'encrypted': self.enable_encryption
            }
            
            # Serialize data
            json_data = json.dumps(storage_data, default=str)
            
            if self.enable_encryption:
                # Encrypt data
                encrypted_data = self.fernet.encrypt(json_data.encode())
                file_path = self.storage_path / f"{key}.enc"
                
                # Store encrypted data with salt
                with open(file_path, 'wb') as f:
                    f.write(self.salt)
                    f.write(encrypted_data)
            else:
                # Store plain text
                file_path = self.storage_path / f"{key}.json"
                with open(file_path, 'w') as f:
                    f.write(json_data)
            
            logger.info(f"Stored data with key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store data with key {key}: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from storage.
        
        Args:
            key: Unique identifier for the data
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            # Try encrypted file first
            encrypted_path = self.storage_path / f"{key}.enc"
            plain_path = self.storage_path / f"{key}.json"
            
            if encrypted_path.exists():
                if not self.enable_encryption:
                    logger.error("Cannot decrypt data - encryption not available")
                    return None
                
                # Read and decrypt data
                with open(encrypted_path, 'rb') as f:
                    salt = f.read(16)
                    encrypted_data = f.read()
                
                # Recreate Fernet instance with stored salt
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                env_key = os.getenv('IOA_COLD_STORAGE_KEY', 'default_key')
                derived_key = base64.urlsafe_b64encode(kdf.derive(env_key.encode()))
                fernet = Fernet(derived_key)
                
                decrypted_data = fernet.decrypt(encrypted_data)
                storage_data = json.loads(decrypted_data.decode())
                
            elif plain_path.exists():
                # Read plain text data
                with open(plain_path, 'r') as f:
                    storage_data = json.load(f)
            else:
                logger.warning(f"No data found for key: {key}")
                return None
            
            logger.info(f"Retrieved data with key: {key}")
            return storage_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve data with key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete data from storage.
        
        Args:
            key: Unique identifier for the data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            encrypted_path = self.storage_path / f"{key}.enc"
            plain_path = self.storage_path / f"{key}.json"
            
            if encrypted_path.exists():
                encrypted_path.unlink()
            elif plain_path.exists():
                plain_path.unlink()
            else:
                logger.warning(f"No data found for key: {key}")
                return False
            
            logger.info(f"Deleted data with key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete data with key {key}: {e}")
            return False
    
    def list_keys(self) -> list:
        """List all stored keys."""
        keys = []
        
        # Collect encrypted keys
        for enc_file in self.storage_path.glob("*.enc"):
            keys.append(enc_file.stem)
        
        # Collect plain text keys
        for json_file in self.storage_path.glob("*.json"):
            keys.append(json_file.stem)
        
        return sorted(keys)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information and statistics."""
        keys = self.list_keys()
        total_files = len(keys)
        encrypted_files = len([k for k in keys if (self.storage_path / f"{k}.enc").exists()])
        plain_files = total_files - encrypted_files
        
        return {
            'total_files': total_files,
            'encrypted_files': encrypted_files,
            'plain_files': plain_files,
            'encryption_enabled': self.enable_encryption,
            'cryptography_available': CRYPTOGRAPHY_AVAILABLE,
            'storage_path': str(self.storage_path)
        }
    
    def _get_timestamp(self) -> str:
        """Get current UTC timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

# Feature flag for encryption
ENCRYPTION_ENABLED = os.getenv('IOA_ENABLE_COLD_STORAGE_ENCRYPTION', 'true').lower() == 'true'

# Convenience function
def create_cold_storage(storage_path: Union[str, Path], 
                       encryption_key: Optional[str] = None) -> ColdStorage:
    """Create a cold storage instance with default settings."""
    return ColdStorage(
        storage_path=storage_path,
        encryption_key=encryption_key,
        enable_encryption=ENCRYPTION_ENABLED
    )
