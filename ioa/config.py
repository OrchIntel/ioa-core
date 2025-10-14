"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MemoryConfig:
	profile: str = "local"  # local|hybrid|cloud
	hot_db_path: str = ":memory:"
	vector_enabled: bool = False
	retention_days: int = 0
	# S3
	s3_bucket: Optional[str] = None
	s3_region: Optional[str] = None
	s3_endpoint: Optional[str] = None


def load_memory_config() -> MemoryConfig:
	profile = os.getenv("MEMORY_ENGINE_PROFILE", "local").lower()
	hot = os.getenv("APP_HOT_DB_PATH", ":memory:")
	vec = os.getenv("IOA_VECTOR_SEARCH", "off").lower() not in {"off", "0", "false"}
	ret = int(os.getenv("IOA_RETENTION_DAYS", "0") or 0)
	s3_bucket = os.getenv("IOA_S3_BUCKET")
	s3_region = os.getenv("IOA_S3_REGION")
	s3_endpoint = os.getenv("IOA_S3_ENDPOINT")
	return MemoryConfig(
		profile=profile,
		hot_db_path=hot,
		vector_enabled=vec,
		retention_days=ret,
		s3_bucket=s3_bucket,
		s3_region=s3_region,
		s3_endpoint=s3_endpoint,
	)


__all__ = ["MemoryConfig", "load_memory_config"]


