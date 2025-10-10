""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
LlamaIndex adapter for IOA Core.

This module integrates the IOA memory engine with the LlamaIndex
framework for vector search.  It provides a convenience class to
index documents from a directory and ingest them into the memory
engine, then build a ``VectorStoreIndex`` for semantic querying.

Note: This adapter requires the ``llama_index`` library to be
installed.  It is not imported at module import time to allow the
package to be installed without the dependency; the import occurs in
the method body instead.
"""

from typing import Any
from memory_fabric.fabric import MemoryFabric


class IOAIndexAdapter:
    """Adapter that bridges IOA memory with LlamaIndex."""

    def __init__(self, memory_fabric: MemoryFabric) -> None:
        self.memory = memory_fabric

    async def index_data(self, directory: str) -> Any:
        """
        Index data from a directory using LlamaIndex and ingest into IOA.

        Reads all documents from the specified directory using
        ``SimpleDirectoryReader``, stores the raw text in the IOA memory
        engine and returns a ``VectorStoreIndex`` built from those
        documents.  The method is asynchronous to allow integration
        within async workflows.

        Args:
            directory: Path to the directory containing documents to index.

        Returns:
            A ``VectorStoreIndex`` instance constructed from the documents.
        """
        # Perform imports inside the method to avoid mandatory dependency
        from llama_index import VectorStoreIndex, SimpleDirectoryReader
        # Load documents from directory
        documents = SimpleDirectoryReader(directory).load_data()
        # Ingest documents into IOA memory
        for doc in documents:
            # Each document has a ``text`` attribute
            self.memory.store(doc.text, {"raw_ref": True})
        # Build and return the vector store index
        return VectorStoreIndex.from_documents(documents)