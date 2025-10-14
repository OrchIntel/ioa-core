"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
LangChain adapter for IOA Core.

This module exposes the IOA agent router as a LangChain tool.  It
conforms to the ``BaseTool`` interface so that IOA can be used within
LangChain workflows alongside other tools.  The tool wraps the
``AgentRouter.route_task`` method and provides both synchronous and
asynchronous invocation variants.
"""

import asyncio
try:
    # Attempt to import BaseTool from langchain; if unavailable fall back
    from langchain.tools import BaseTool  # type: ignore
except Exception:
    # Define a minimal BaseTool to satisfy type checkers when LangChain is absent
    class BaseTool:  # type: ignore
        """Fallback BaseTool implementation used when LangChain is not installed."""
        name: str = ""
        description: str = ""

        def __init__(self, *args, **kwargs) -> None:
            pass

        def _run(self, *args, **kwargs):  # pragma: no cover
            raise NotImplementedError("LangChain BaseTool is not available.")

        async def _arun(self, *args, **kwargs):  # pragma: no cover
            raise NotImplementedError("LangChain BaseTool is not available.")

from agent_router import AgentRouter


class IOAAgentTool(BaseTool):
    """LangChain tool wrapper for the IOA agent router."""

    name: str = "IOA_Agent"
    description: str = (
        "IOA agent for multi‑agent orchestration with governance. "
        "Routes arbitrary tasks through the IOA agent router."
    )

    def __init__(self) -> None:
        super().__init__()
        self.router = AgentRouter()

    def _run(self, task: str) -> str:
        """Synchronously route a task to the agent router."""
        # Use asyncio.run to bridge to the async router API
        return asyncio.run(self.router.route_task(task))

    async def _arun(self, task: str) -> str:
        """Asynchronously route a task to the agent router."""
        return await self.router.route_task(task)