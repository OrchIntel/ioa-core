"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

import io
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from ..core.interfaces import MemoryEntry, MemoryStats, ColdStore, StorageError

try:
	import boto3  # type: ignore
	from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
	_BOTO_AVAILABLE = True
except Exception:
	_BOTO_AVAILABLE = False


class S3ColdStore(ColdStore):
	"""Streaming S3-backed cold store.

	Configuration via env vars:
	- IOA_S3_BUCKET, IOA_S3_REGION, IOA_S3_ENDPOINT(optional for MinIO), IOA_S3_PREFIX(optional)
	- IOA_S3_ACCESS_KEY, IOA_S3_SECRET_KEY (if not using instance/profile auth)
	"""

	def __init__(self) -> None:
		self.logger = logging.getLogger(__name__)
		self._configured = _BOTO_AVAILABLE and bool(os.getenv("IOA_S3_BUCKET"))
		self._bucket = os.getenv("IOA_S3_BUCKET", "")
		self._prefix = os.getenv("IOA_S3_PREFIX", "memory/")
		if self._configured:
			self._client = self._create_client()
		else:
			self._client = None

	def _create_client(self):
		endpoint_url = os.getenv("IOA_S3_ENDPOINT")
		region_name = os.getenv("IOA_S3_REGION")
		access_key = os.getenv("IOA_S3_ACCESS_KEY")
		secret_key = os.getenv("IOA_S3_SECRET_KEY")
		kwargs = {"region_name": region_name} if region_name else {}
		if endpoint_url:
			kwargs["endpoint_url"] = endpoint_url
		if access_key and secret_key:
			kwargs["aws_access_key_id"] = access_key
			kwargs["aws_secret_access_key"] = secret_key
		return boto3.client("s3", **kwargs)

	def _key(self, entry_id: str) -> str:
		return f"{self._prefix}{entry_id}.json"

	# ColdStore ---------------------------------------------------------------
	def store(self, entry: MemoryEntry) -> bool:
		if not self.is_available():
			self.logger.info("S3 cold store not configured; skipping store")
			return False
		payload = json.dumps(entry.to_dict()).encode("utf-8")
		try:
			self._client.put_object(Bucket=self._bucket, Key=self._key(entry.id), Body=payload)
			return True
		except (BotoCoreError, ClientError) as exc:
			self.logger.error("S3 put_object failed: %s", exc)
			raise StorageError(str(exc))

	def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
		if not self.is_available():
			return None
		try:
			obj = self._client.get_object(Bucket=self._bucket, Key=self._key(entry_id))
			data = obj["Body"].read().decode("utf-8")
			return MemoryEntry.from_dict(json.loads(data))
		except self._client.exceptions.NoSuchKey:  # type: ignore[attr-defined]
			return None
		except (BotoCoreError, ClientError) as exc:
			self.logger.error("S3 get_object failed: %s", exc)
			return None

	def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
		# Avoid listing large buckets by default; cold search is a no-op
		return []

	def delete(self, entry_id: str) -> bool:
		if not self.is_available():
			return False
		try:
			self._client.delete_object(Bucket=self._bucket, Key=self._key(entry_id))
			return True
		except (BotoCoreError, ClientError) as exc:
			self.logger.error("S3 delete_object failed: %s", exc)
			return False

	def list_all(self) -> List[MemoryEntry]:
		# Streaming listing would be expensive; keep minimal
		return []

	def get_stats(self) -> MemoryStats:
		return MemoryStats()

	def is_available(self) -> bool:
		return self._configured and self._client is not None

	def get_storage_info(self) -> Dict[str, any]:  # type: ignore[override]
		if not self.is_available():
			return {"available": False, "reason": "NotConfigured"}
		return {"available": True, "type": "s3", "bucket": self._bucket, "prefix": self._prefix}


