# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



import os
import json
import hashlib
import math
from typing import List, Dict, Any, Optional, Tuple
"""Vector Search module."""

from pathlib import Path
from dataclasses import dataclass


@dataclass
class VectorResult:
    """Result from vector search."""
    content: str
    metadata: Dict[str, Any]
    score: float
    id: str


class VectorIndex:
    """Simple vector index for pattern matching."""

    def __init__(self, index_path: str):
        """
        Initialize vector index.

        Args:
            index_path: Path to index file
        """
        self.index_path = Path(index_path)
        self.index_data: Dict[str, Any] = {}
        self.load_index()

    def load_index(self):
        """Load index from file."""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r') as f:
                    self.index_data = json.load(f)
            except Exception:
                # Create empty index if loading fails
                self.index_data = {"vectors": {}, "metadata": {}}
        else:
            # Create new index
            self.index_data = {"vectors": {}, "metadata": {}}

    def save_index(self):
        """Save index to file."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, 'w') as f:
            json.dump(self.index_data, f, indent=2)

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add document to index.

        Args:
            doc_id: Unique document ID
            content: Document content
            metadata: Document metadata
        """
        # Simple text hashing as "vector" representation
        vector = self._text_to_vector(content)

        self.index_data["vectors"][doc_id] = {
            "vector": vector,
            "content": content[:500],  # Truncate for storage
            "metadata": metadata or {}
        }

        self.index_data["metadata"][doc_id] = {
            "length": len(content),
            "hash": hashlib.md5(content.encode()).hexdigest()
        }

    def search(self, query: str, k: int = 5) -> List[VectorResult]:
        """
        Search for similar documents.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of VectorResult objects
        """
        if not self.index_data.get("vectors"):
            return []

        query_vector = self._text_to_vector(query)
        results = []

        for doc_id, doc_data in self.index_data["vectors"].items():
            doc_vector = doc_data["vector"]
            score = self._cosine_similarity(query_vector, doc_vector)

            result = VectorResult(
                content=doc_data["content"],
                metadata=doc_data["metadata"],
                score=score,
                id=doc_id
            )
            results.append(result)

        # Sort by score (descending) and return top k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]

    def _text_to_vector(self, text: str) -> List[float]:
        """Convert text to simple vector representation."""
        # Simple character frequency vector (for demo purposes)
        vector = [0.0] * 256  # ASCII character space

        for char in text.lower():
            if ord(char) < 256:
                vector[ord(char)] += 1.0

        # Normalize
        total = sum(vector)
        if total > 0:
            vector = [x / total for x in vector]

        return vector

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            if len(vec1) != len(vec2):
                return 0.0

            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = math.sqrt(sum(a * a for a in vec1))
            norm2 = math.sqrt(sum(b * b for b in vec2))

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_documents": len(self.index_data.get("vectors", {})),
            "index_path": str(self.index_path),
            "total_size_bytes": self.index_path.stat().st_size if self.index_path.exists() else 0
        }


class VectorSearchEngine:
    """Vector search engine for IOA Core."""

    def __init__(self):
        """Initialize vector search engine."""
        self.indices: Dict[str, VectorIndex] = {}

    def create_index(self, index_path: str) -> VectorIndex:
        """
        Create or load an index.

        Args:
            index_path: Path to index file

        Returns:
            VectorIndex instance
        """
        index = VectorIndex(index_path)
        self.indices[index_path] = index
        return index

    def search_index(self, index_path: str, query: str, k: int = 5) -> List[VectorResult]:
        """
        Search an index.

        Args:
            index_path: Path to index file
            query: Search query
            k: Number of results

        Returns:
            List of search results
        """
        if index_path not in self.indices:
            self.indices[index_path] = VectorIndex(index_path)

        index = self.indices[index_path]
        return index.search(query, k)

    def add_to_index(self, index_path: str, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add document to index.

        Args:
            index_path: Path to index file
            doc_id: Document ID
            content: Document content
            metadata: Document metadata
        """
        if index_path not in self.indices:
            self.indices[index_path] = VectorIndex(index_path)

        index = self.indices[index_path]
        index.add_document(doc_id, content, metadata)
        index.save_index()
