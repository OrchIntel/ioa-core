""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

from ..core.interfaces import VectorIndex


class _StubIndex(VectorIndex):
	def __init__(self) -> None:
		self._enabled = os.getenv("IOA_VECTOR_SEARCH", "off").lower() not in {"off", "0", "false"}

	def upsert(self, entry_id: str, content: str, metadata: Dict | None = None) -> bool:
		return False

	def query(self, text: str, k: int = 5) -> List[Tuple[str, float]]:
		return []

	def delete(self, entry_id: str) -> bool:
		return True

	def is_available(self) -> bool:
		return False


try:
	import faiss  # type: ignore
	_FAISS_AVAILABLE = True
except Exception:
	_FAISS_AVAILABLE = False


class FaissIndex(VectorIndex):
	"""Simple FAISS flat L2 index over naive embeddings.

	Note: We intentionally avoid adding heavy deps; if FAISS is missing, we fall back to a stub.
	Embeddings here are trivial character bigram counts to avoid extra dependencies.
	"""

	def __new__(cls, *args, **kwargs):  # type: ignore[override]
		if not _FAISS_AVAILABLE or os.getenv("IOA_VECTOR_SEARCH", "off").lower() in {"off", "0", "false"}:
			return _StubIndex()
		return super().__new__(cls)

	def __init__(self) -> None:
		if isinstance(self, _StubIndex):  # type: ignore[unreachable]
			return
		self._dim = 256
		self._index = faiss.IndexFlatL2(self._dim)
		self._ids: List[str] = []

	def _embed(self, text: str) -> List[float]:
		vec = [0.0] * self._dim
		for i, ch in enumerate(text.encode("utf-8")[: self._dim]):
			vec[i] = float(ch) / 255.0
		return vec

	def upsert(self, entry_id: str, content: str, metadata: Dict | None = None) -> bool:
		if isinstance(self, _StubIndex):  # type: ignore[unreachable]
			return False
		import numpy as np  # local import to avoid hard dependency at import time
		vec = np.array([self._embed(content)], dtype="float32")
		self._index.add(vec)
		self._ids.append(entry_id)
		return True

	def query(self, text: str, k: int = 5) -> List[Tuple[str, float]]:
		if isinstance(self, _StubIndex):  # type: ignore[unreachable]
			return []
		import numpy as np
		q = np.array([self._embed(text)], dtype="float32")
		dists, idxs = self._index.search(q, k)
		results: List[Tuple[str, float]] = []
		for i, d in zip(idxs[0], dists[0]):
			if i == -1:
				continue
			results.append((self._ids[i], float(d)))
		return results

	def delete(self, entry_id: str) -> bool:
		# Stateless simple index: no delete support; noop
		return True

	def is_available(self) -> bool:
		return True

__all__ = ["FaissIndex"]


