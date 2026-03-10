# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# IOA Module: src/audit/storage.py
# Version: v2.5.0
# Last-Updated: 2025-09-10
# Agents: Cursor assist
# Summary: Multi-backend storage for audit chains (FS and S3)

"""
Multi-backend storage system for audit chains.

Supports both local filesystem and S3 storage with consistent interfaces
for reading and writing audit entries, manifests, and anchors.
"""

import os
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from .models import AuditEntry, AuditManifest, AuditAnchor


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
        
        with manifest_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        return AuditManifest(**data)
    
    def write_manifest(self, chain_id: str, manifest: AuditManifest) -> None:
        """Write chain manifest."""
        chain_dir = self.chains_dir / chain_id
        chain_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_path = chain_dir / "MANIFEST.json"
        with manifest_path.open('w', encoding='utf-8') as f:
            json.dump(manifest.model_dump(), f, indent=2, default=str)
    
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
    """S3 storage backend for audit chains."""
    
    def __init__(self, bucket: str, prefix: str = "", region: str = "us-east-1"):
        """Initialize S3 storage.
        
        Args:
            bucket: S3 bucket name
            prefix: S3 key prefix for audit chains
            region: AWS region
        """
        self.bucket = bucket
        self.prefix = prefix.rstrip('/')
        self.region = region
        
        # Import boto3 only when needed
        try:
            import boto3
            self.s3_client = boto3.client('s3', region_name=region)
        except ImportError:
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
    
    def _get_key(self, *path_parts: str) -> str:
        """Construct S3 key from path parts."""
        if self.prefix:
            return f"{self.prefix}/{'/'.join(path_parts)}"
        return '/'.join(path_parts)
    
    def list_chains(self) -> List[str]:
        """List available chain IDs."""
        prefix = self._get_key("chains")
        
        try:
            response = self.s3_client.list_objects_v2(
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
        except Exception as e:
            raise RuntimeError(f"Failed to list chains: {e}")
    
    def list_entries(self, chain_id: str) -> List[str]:
        """List entry filenames for a chain."""
        prefix = self._get_key("chains", chain_id)
        
        try:
            response = self.s3_client.list_objects_v2(
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
        except Exception as e:
            raise RuntimeError(f"Failed to list entries for chain {chain_id}: {e}")
    
    def read_entry(self, chain_id: str, entry_filename: str) -> AuditEntry:
        """Read a specific audit entry."""
        key = self._get_key("chains", chain_id, entry_filename)
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            return AuditEntry(**data)
        except Exception as e:
            raise RuntimeError(f"Failed to read entry {entry_filename}: {e}")
    
    def read_manifest(self, chain_id: str) -> AuditManifest:
        """Read chain manifest."""
        key = self._get_key("chains", chain_id, "MANIFEST.json")
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            return AuditManifest(**data)
        except Exception as e:
            raise RuntimeError(f"Failed to read manifest for chain {chain_id}: {e}")
    
    def write_manifest(self, chain_id: str, manifest: AuditManifest) -> None:
        """Write chain manifest."""
        key = self._get_key("chains", chain_id, "MANIFEST.json")
        
        try:
            manifest_json = json.dumps(manifest.model_dump(), indent=2, default=str)
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=manifest_json.encode('utf-8'),
                ContentType='application/json'
            )
        except Exception as e:
            raise RuntimeError(f"Failed to write manifest for chain {chain_id}: {e}")
    
    def list_anchors(self, chain_id: Optional[str] = None) -> List[str]:
        """List available anchor files."""
        prefix = self._get_key("anchors")
        
        try:
            response = self.s3_client.list_objects_v2(
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
        except Exception as e:
            raise RuntimeError(f"Failed to list anchors: {e}")
    
    def read_anchor(self, anchor_filename: str) -> AuditAnchor:
        """Read a specific anchor file."""
        key = self._get_key("anchors", anchor_filename)
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            return AuditAnchor(**data)
        except Exception as e:
            raise RuntimeError(f"Failed to read anchor {anchor_filename}: {e}")


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
