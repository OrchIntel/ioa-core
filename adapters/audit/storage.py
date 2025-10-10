""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Multi-backend storage system for audit chains.

Supports both local filesystem and S3 storage with consistent interfaces
for reading and writing audit entries, manifests, and anchors.
"""

import os
import json
from abc import ABC, abstractmethod
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import threading
import time

from .models import AuditEntry, AuditManifest, AuditAnchor
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, get_circuit_breaker


class AuditStorage(ABC):
    """Abstract base class for audit storage backends."""
    
    @abstractmethod
    def list_chains(self) -> List[str]:
        """List available chain IDs."""
        pass
    
    @abstractmethod
    def list_entries(self, chain_id: str) -> List[str]:
        """List entry filenames for a chain."""
        pass
    
    @abstractmethod
    def read_entry(self, chain_id: str, entry_filename: str) -> AuditEntry:
        """Read a specific audit entry."""
        pass
    
    @abstractmethod
    def read_manifest(self, chain_id: str) -> AuditManifest:
        """Read chain manifest."""
        pass
    
    @abstractmethod
    def write_manifest(self, chain_id: str, manifest: AuditManifest) -> None:
        """Write chain manifest."""
        pass
    
    @abstractmethod
    def list_anchors(self, chain_id: Optional[str] = None) -> List[str]:
        """List available anchor files."""
        pass
    
    @abstractmethod
    def read_anchor(self, anchor_filename: str) -> AuditAnchor:
        """Read a specific anchor file."""
        pass


class FileSystemStorage(AuditStorage):
    """Local filesystem storage backend for audit chains."""
    
    def __init__(self, base_path: Union[str, Path] = "audit_chain"):
        """Initialize filesystem storage.
        
        Args:
            base_path: Base directory for audit chains
        """
        self.base_path = Path(base_path)
        self.chains_dir = self.base_path / "chains"
        self.anchors_dir = self.base_path / "anchors"
        # Optional at-rest encryption for manifests
        self._enc_enabled = os.getenv("IOA_AUDIT_ENCRYPT_MANIFEST", "0") in ("1", "true", "TRUE")
        self._enc_key_b64 = os.getenv("IOA_AUDIT_ENC_KEY_B64")
        
        # Ensure directories exist
        self.chains_dir.mkdir(parents=True, exist_ok=True)
        self.anchors_dir.mkdir(parents=True, exist_ok=True)
    
    def list_chains(self) -> List[str]:
        """List available chain IDs."""
        if not self.chains_dir.exists():
            return []
        
        chains = []
        for chain_dir in self.chains_dir.iterdir():
            if chain_dir.is_dir() and (chain_dir / "MANIFEST.json").exists():
                chains.append(chain_dir.name)
        
        return sorted(chains)
    
    def list_entries(self, chain_id: str) -> List[str]:
        """List entry filenames for a chain."""
        chain_dir = self.chains_dir / chain_id
        if not chain_dir.exists():
            return []
        
        entries = []
        for entry_file in chain_dir.iterdir():
            if entry_file.is_file() and entry_file.name != "MANIFEST.json":
                # Sort by filename (which should be zero-padded)
                entries.append(entry_file.name)
        
        return sorted(entries)
    
    def read_entry(self, chain_id: str, entry_filename: str) -> AuditEntry:
        """Read a specific audit entry."""
        entry_path = self.chains_dir / chain_id / entry_filename
        
        if not entry_path.exists():
            raise FileNotFoundError(f"Entry not found: {entry_path}")
        
        with entry_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        return AuditEntry(**data)
    
    def read_manifest(self, chain_id: str) -> AuditManifest:
        """Read chain manifest."""
        manifest_path = self.chains_dir / chain_id / "MANIFEST.json"
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
        with manifest_path.open('rb') as f:
            raw = f.read()
        if self._enc_enabled and self._enc_key_b64 and raw.startswith(b"ENC1:"):
            # Format: ENC1:<nonce_b64>:<ciphertext_b64>
            try:
                _, nonce_b64, ct_b64 = raw.split(b":", 2)
                key = base64.b64decode(self._enc_key_b64)
                aesgcm = AESGCM(key)
                nonce = base64.b64decode(nonce_b64)
                ct = base64.b64decode(ct_b64)
                plaintext = aesgcm.decrypt(nonce, ct, None)
                data = json.loads(plaintext.decode('utf-8'))
            except Exception as e:
                raise RuntimeError(f"Failed to decrypt manifest: {e}")
        else:
            data = json.loads(raw.decode('utf-8'))
        
        return AuditManifest(**data)
    
    def write_manifest(self, chain_id: str, manifest: AuditManifest) -> None:
        """Write chain manifest."""
        chain_dir = self.chains_dir / chain_id
        chain_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_path = chain_dir / "MANIFEST.json"
        payload = json.dumps(manifest.model_dump(), indent=2, default=str).encode('utf-8')
        if self._enc_enabled and self._enc_key_b64:
            try:
                key = base64.b64decode(self._enc_key_b64)
                aesgcm = AESGCM(key)
                import os as _os
                nonce = _os.urandom(12)
                ct = aesgcm.encrypt(nonce, payload, None)
                blob = b"ENC1:" + base64.b64encode(nonce) + b":" + base64.b64encode(ct)
            except Exception as e:
                raise RuntimeError(f"Failed to encrypt manifest: {e}")
        else:
            blob = payload
        with manifest_path.open('wb') as f:
            f.write(blob)
    
    def list_anchors(self, chain_id: Optional[str] = None) -> List[str]:
        """List available anchor files."""
        if not self.anchors_dir.exists():
            return []
        
        anchors = []
        for anchor_file in self.anchors_dir.rglob("*.json"):
            if chain_id is None or anchor_file.stem.startswith(f"{chain_id}_"):
                # Return relative path from anchors_dir
                rel_path = anchor_file.relative_to(self.anchors_dir)
                anchors.append(str(rel_path))
        
        return sorted(anchors)
    
    def read_anchor(self, anchor_filename: str) -> AuditAnchor:
        """Read a specific anchor file."""
        anchor_path = self.anchors_dir / anchor_filename
        
        if not anchor_path.exists():
            raise FileNotFoundError(f"Anchor not found: {anchor_path}")
        
        with anchor_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        return AuditAnchor(**data)


class S3Storage(AuditStorage):
    """S3 storage backend for audit chains with circuit breaker and connection management."""

    def __init__(self, bucket: str, prefix: str = "", region: str = "us-east-1"):
        """Initialize S3 storage with connection management and circuit breaker.

        Args:
            bucket: S3 bucket name
            prefix: S3 key prefix for audit chains
            region: AWS region
        """
        self.bucket = bucket
        self.prefix = prefix.rstrip('/')
        self.region = region

        # Circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=int(os.getenv('IOA_S3_FAILURE_THRESHOLD', '3')),
            recovery_timeout=int(os.getenv('IOA_S3_RECOVERY_TIMEOUT', '30')),
            success_threshold=int(os.getenv('IOA_S3_SUCCESS_THRESHOLD', '2')),
            timeout=float(os.getenv('IOA_S3_TIMEOUT', '10.0'))
        )
        self.circuit_breaker = get_circuit_breaker(f"s3-{bucket}", cb_config)

        # Connection management
        self._connection_pool_size = int(os.getenv('IOA_S3_CONNECTION_POOL_SIZE', '10'))
        self._max_retries = int(os.getenv('IOA_S3_MAX_RETRIES', '3'))
        self._retry_delay = float(os.getenv('IOA_S3_RETRY_DELAY', '0.5'))

        # Thread-safe connection management
        self._connection_lock = threading.Lock()
        self._s3_client = None
        self._last_health_check = 0
        self._health_check_interval = int(os.getenv('IOA_S3_HEALTH_CHECK_INTERVAL', '300'))  # 5 minutes

        # Connection leak prevention
        self._active_connections = 0
        self._max_connections = self._connection_pool_size

        logger.info(f"S3Storage initialized for bucket '{bucket}' with circuit breaker protection")

    def _get_s3_client(self):
        """Get or create S3 client with connection management."""
        with self._connection_lock:
            current_time = time.time()

            # Health check if needed
            if current_time - self._last_health_check > self._health_check_interval:
                self._perform_health_check()
                self._last_health_check = current_time

            # Create client if needed
            if self._s3_client is None:
                if self._active_connections >= self._max_connections:
                    raise RuntimeError(f"S3 connection pool exhausted (max: {self._max_connections})")

                try:
                    import boto3
                    from botocore.config import Config

                    # Configure connection pooling and timeouts
                    config = Config(
                        region_name=self.region,
                        max_pool_connections=self._connection_pool_size,
                        retries={'max_attempts': self._max_retries},
                        connect_timeout=5.0,
                        read_timeout=10.0
                    )

                    self._s3_client = boto3.client('s3', config=config)
                    self._active_connections += 1

                    logger.debug(f"S3 client created (active connections: {self._active_connections})")

                except ImportError:
                    raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")

            return self._s3_client

    def _perform_health_check(self):
        """Perform health check on S3 connection."""
        try:
            if self._s3_client:
                # Simple head operation to test connectivity
                self._s3_client.head_bucket(Bucket=self.bucket)
                logger.debug("S3 health check passed")
        except Exception as e:
            logger.warning(f"S3 health check failed: {e}")
            # Reset client on health check failure
            self._reset_connection()

    def _reset_connection(self):
        """Reset S3 connection on failure."""
        with self._connection_lock:
            if self._s3_client:
                try:
                    # Close any underlying connections
                    if hasattr(self._s3_client, '_client_config'):
                        # boto3 client cleanup
                        pass
                except Exception:
                    pass  # Ignore cleanup errors

                self._s3_client = None
                self._active_connections = max(0, self._active_connections - 1)
                logger.debug(f"S3 connection reset (active connections: {self._active_connections})")

    def _execute_with_circuit_breaker(self, operation_name: str, operation_func, *args, **kwargs):
        """Execute S3 operation with circuit breaker protection."""
        def wrapped_operation():
            return operation_func(*args, **kwargs)

        try:
            return self.circuit_breaker.call(wrapped_operation)
        except Exception as e:
            logger.error(f"S3 operation '{operation_name}' failed: {e}")
            # Reset connection on failure
            self._reset_connection()
            raise e
    
    def _get_key(self, *path_parts: str) -> str:
        """Construct S3 key from path parts."""
        if self.prefix:
            return f"{self.prefix}/{'/'.join(path_parts)}"
        return '/'.join(path_parts)
    
    def list_chains(self) -> List[str]:
        """List available chain IDs with circuit breaker protection."""
        def _list_chains():
            s3_client = self._get_s3_client()
            prefix = self._get_key("chains")

            response = s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                Delimiter='/'
            )

            chains = []
            for prefix_info in response.get('CommonPrefixes', []):
                # Extract chain ID from prefix like "chains/myapp/"
                chain_path = prefix_info['Prefix'].rstrip('/')
                chain_id = chain_path.split('/')[-1]
                chains.append(chain_id)

            return sorted(chains)

        return self._execute_with_circuit_breaker("list_chains", _list_chains)
    
    def list_entries(self, chain_id: str) -> List[str]:
        """List entry filenames for a chain with circuit breaker protection."""
        def _list_entries():
            s3_client = self._get_s3_client()
            prefix = self._get_key("chains", chain_id)

            response = s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )

            entries = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                filename = key.split('/')[-1]
                if filename != "MANIFEST.json":
                    entries.append(filename)

            return sorted(entries)

        return self._execute_with_circuit_breaker("list_entries", _list_entries)

    def read_entry(self, chain_id: str, entry_filename: str) -> AuditEntry:
        """Read a specific audit entry with circuit breaker protection."""
        def _read_entry():
            s3_client = self._get_s3_client()
            key = self._get_key("chains", chain_id, entry_filename)

            response = s3_client.get_object(Bucket=self.bucket, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            return AuditEntry(**data)

        return self._execute_with_circuit_breaker("read_entry", _read_entry)

    def read_manifest(self, chain_id: str) -> AuditManifest:
        """Read chain manifest with circuit breaker protection."""
        def _read_manifest():
            s3_client = self._get_s3_client()
            key = self._get_key("chains", chain_id, "MANIFEST.json")

            response = s3_client.get_object(Bucket=self.bucket, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            return AuditManifest(**data)

        return self._execute_with_circuit_breaker("read_manifest", _read_manifest)

    def write_manifest(self, chain_id: str, manifest: AuditManifest) -> None:
        """Write chain manifest with circuit breaker protection."""
        def _write_manifest():
            s3_client = self._get_s3_client()
            key = self._get_key("chains", chain_id, "MANIFEST.json")

            manifest_json = json.dumps(manifest.model_dump(), indent=2, default=str)
            s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=manifest_json.encode('utf-8'),
                ContentType='application/json'
            )

        self._execute_with_circuit_breaker("write_manifest", _write_manifest)
    
    def list_anchors(self, chain_id: Optional[str] = None) -> List[str]:
        """List available anchor files with circuit breaker protection."""
        def _list_anchors():
            s3_client = self._get_s3_client()
            prefix = self._get_key("anchors")

            response = s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )

            anchors = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                if key.endswith('.json'):
                    # Extract relative path from anchors prefix
                    rel_path = key[len(prefix):].lstrip('/')
                    if chain_id is None or chain_id in rel_path:
                        anchors.append(rel_path)

            return sorted(anchors)

        return self._execute_with_circuit_breaker("list_anchors", _list_anchors)

    def read_anchor(self, anchor_filename: str) -> AuditAnchor:
        """Read a specific anchor file with circuit breaker protection."""
        def _read_anchor():
            s3_client = self._get_s3_client()
            key = self._get_key("anchors", anchor_filename)

            response = s3_client.get_object(Bucket=self.bucket, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            return AuditAnchor(**data)

        return self._execute_with_circuit_breaker("read_anchor", _read_anchor)

    def close(self):
        """Clean up connections and resources."""
        with self._connection_lock:
            self._reset_connection()
            logger.info(f"S3Storage for bucket '{self.bucket}' closed")

    def __del__(self):
        """Ensure cleanup on destruction."""
        try:
            self.close()
        except Exception:
            pass  # Ignore cleanup errors during destruction


def create_storage(backend: str = "auto", **kwargs) -> AuditStorage:
    """Create appropriate storage backend based on configuration.
    
    Args:
        backend: Storage backend type ("fs", "s3", or "auto")
        **kwargs: Backend-specific configuration
        
    Returns:
        Configured storage backend
        
    Raises:
        ValueError: If backend type is not supported
    """
    if backend == "auto":
        # Check environment variables for S3 configuration
        if os.getenv("IOA_AUDIT_BACKEND") == "s3":
            backend = "s3"
        else:
            backend = "fs"
    
    if backend == "fs":
        base_path = kwargs.get("base_path", "audit_chain")
        return FileSystemStorage(base_path)
    elif backend == "s3":
        bucket = kwargs.get("bucket") or os.getenv("IOA_AUDIT_S3_BUCKET")
        prefix = kwargs.get("prefix") or os.getenv("IOA_AUDIT_S3_PREFIX", "")
        region = kwargs.get("region") or os.getenv("AWS_REGION", "us-east-1")
        
        if not bucket:
            raise ValueError("S3 bucket must be specified via 'bucket' parameter or IOA_AUDIT_S3_BUCKET env var")
        
        return S3Storage(bucket, prefix, region)
    else:
        raise ValueError(f"Unsupported storage backend: {backend}")
