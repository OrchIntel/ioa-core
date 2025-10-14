"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
Module docstring:
Responsibilities and key public objects.

- Load and validate workflow YAML against an internal Pydantic model that mirrors `dsl/workflow_schema.yaml`.
- Compile orchestration parameters (quorum, voting_mode, timeout) into an execution plan.
- Execute via `AgentRouter` and `RoundtableExecutor` honoring DSL configuration.
- Emit JSONL logs conforming to the universal LogEntry schema, tagged with the originating dispatch code.
- Save `FinalReport` and logs into `reports/workflows/<STAMP>/` or the DSL-specified `artifacts.output_dir`.

Key Public Objects
- class WorkflowExecutor
  - parse_yaml(path) -> WorkflowSpec
  - compile(plan: WorkflowSpec) -> Dict[str, Any]
  - run(compiled: Dict[str, Any]) -> FinalReport
  - save_artifacts(report: FinalReport, log_path: str, out_dir: str) -> Dict[str, str]
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover - import error surfaced in tests if missing
    raise ImportError("PyYAML is required. Please install with: pip install pyyaml") from e

from pydantic import BaseModel, Field, ValidationError

# Absolute imports per IOA rules
from agent_router import AgentRouter
from roundtable_executor import RoundtableExecutor, FinalReport
from storage_adapter import JSONStorageService


class LogEntry(BaseModel):
    """Universal JSON log entry schema for JSONL emission.

    Matches `schemas/log_entry.schema.json`.
    """

    timestamp: str = Field(..., description="ISO 8601 timestamp with timezone")
    module: str = Field(..., description="Module name emitting the log")
    level: Literal["INFO", "WARNING", "ERROR", "DEBUG"]
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    dispatch_code: str


class AgentSpec(BaseModel):
    id: str
    provider: Optional[str] = None
    weight: float = 1.0


class OrchestrationSpec(BaseModel):
    router: str
    strategy: Literal["roundtable"] = "roundtable"
    quorum: float = Field(default=0.6, gt=0.0, le=1.0)
    voting_mode: Literal["majority", "weighted", "borda"] = "majority"
    timeout_s: int = Field(default=30, gt=0)
    retries: int = Field(default=0, ge=0)
    concurrency: int = Field(default=1, ge=1)


class TaskSpec(BaseModel):
    id: str
    type: str
    prompt: str
    inputs: Dict[str, Any] = Field(default_factory=dict)


class EvaluationSpec(BaseModel):
    enabled: bool = True
    policy: Optional[str] = None
    success_threshold: Optional[float] = None
    capture_feedback: bool = True


class ArtifactsSpec(BaseModel):
    save: List[Literal["final_report", "logs"]] = Field(default_factory=lambda: ["final_report", "logs"])
    output_dir: str = "reports/workflows/${STAMP}/"


class MetadataSpec(BaseModel):
    name: str
    description: Optional[str] = None
    created_at_utc: Optional[str] = None


class WorkflowSpec(BaseModel):
    kind: Literal["workflow"]
    metadata: MetadataSpec
    identity: Optional[Dict[str, Any]] = None
    task: TaskSpec
    orchestration: OrchestrationSpec
    evaluation: Optional[EvaluationSpec] = None
    artifacts: ArtifactsSpec


def _stamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


@dataclass
class CompiledPlan:
    task_prompt: str
    task_id: str
    quorum: float
    voting_mode: Literal["majority", "weighted", "borda"]
    timeout_s: int
    retries: int
    concurrency: int
    artifacts_output_dir: str


class WorkflowExecutor:
    """Compile and execute IOA workflows from YAML DSL.

    The executor writes JSONL logs that validate against `LogEntry` and includes
    `dispatch_code` for traceability as required by dispatch acceptance criteria.
    """

    def __init__(self, dispatch_code: str = "DISPATCH-GPT-20250818-010") -> None:
        self.dispatch_code = dispatch_code

    def _log_jsonl(self, message: str, level: Literal["INFO", "WARNING", "ERROR", "DEBUG"], log_file: Path, data: Optional[Dict[str, Any]] = None) -> None:
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            module="workflow_executor",
            level=level,
            message=message,
            data=data or {},
            dispatch_code=self.dispatch_code,
        )
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")

    def parse_yaml(self, path: str) -> WorkflowSpec:
        """Load and validate a YAML workflow file into a `WorkflowSpec` model.

        Raises ValidationError on schema mismatch.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Best-effort variable expansion for NOW_UTC and STAMP-like placeholders
        def _expand(value: Any) -> Any:
            if isinstance(value, str):
                return (
                    value.replace("${NOW_UTC}", datetime.now(timezone.utc).isoformat())
                    .replace("${STAMP}", _stamp_now())
                )
            if isinstance(value, dict):
                return {k: _expand(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_expand(v) for v in value]
            return value

        data = _expand(data)
        try:
            return WorkflowSpec(**data)
        except ValidationError as e:
            raise e

    def compile(self, spec: WorkflowSpec) -> CompiledPlan:
        """Compile `WorkflowSpec` into an execution plan understood by runtime."""
        agents = [a.id for a in spec.agents]
        out_dir = spec.artifacts.output_dir.replace("${STAMP}", _stamp_now())
        return CompiledPlan(
            task_prompt=spec.task.prompt,
            task_id=spec.task.id,
            agents=agents,
            quorum=spec.orchestration.quorum,
            voting_mode=spec.orchestration.voting_mode,
            timeout_s=spec.orchestration.timeout_s,
            retries=spec.orchestration.retries,
            concurrency=spec.orchestration.concurrency,
            artifacts_output_dir=out_dir,
        )

    def run(self, plan: CompiledPlan, log_file: Optional[str] = None) -> FinalReport:
        """Execute the compiled plan using AgentRouter + RoundtableExecutor.

        Returns FinalReport. All internal log lines written to `log_file` (if given)
        validate against LogEntry and include the current `dispatch_code`.
        """
        out_dir = Path(plan.artifacts_output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        log_path = Path(log_file) if log_file else out_dir / "run.jsonl"

        self._log_jsonl("Initializing router and executor", "INFO", log_path, {
            "agents": plan.agents,
            "voting_mode": plan.voting_mode,
            "quorum": plan.quorum,
            "timeout_s": plan.timeout_s,
        })

        router = AgentRouter()
        # Provide a helper to register plan-specific agents (non-breaking API).
        if hasattr(router, "apply_compiled_plan"):
            try:
                router.apply_compiled_plan({"agents": plan.agents})  # type: ignore[arg-type]
            except Exception as exc:
                # Best effort; proceed even if registration fails (mock providers allowed)
                self._log_jsonl(
                    "Agent registration failed; continuing without registration",
                    "WARNING",
                    log_path,
                    {"error": str(exc)}
                )

        storage = JSONStorageService(str(out_dir / "memory.json"))
        max_workers = max(1, int(plan.concurrency))
        executor = RoundtableExecutor(router=router, storage=storage, default_quorum_ratio=plan.quorum, default_timeout=float(plan.timeout_s), max_workers=max_workers)

        self._log_jsonl("Starting roundtable execution", "INFO", log_path, {"task_id": plan.task_id})
        # Execute with timeout and quorum from plan; pass agents list; mode from plan
        # Note: RoundtableExecutor internally handles quorum/voting/timeout.
        attempt = 0
        last_error: Optional[str] = None
        while True:
            try:
                report = _run_roundtable_sync(executor, plan)
                break
            except Exception as e:
                attempt += 1
                last_error = str(e)
                self._log_jsonl("Roundtable attempt failed", "WARNING", log_path, {"attempt": attempt, "error": last_error})
                if attempt > plan.retries:
                    raise
        self._log_jsonl("Execution completed", "INFO", log_path, {
            "consensus": report.consensus_achieved,
            "score": report.consensus_score,
            "mode": report.voting_algorithm,
        })
        return report

    def save_artifacts(self, report: FinalReport, log_path: str, out_dir: str) -> Dict[str, str]:
        """Persist FinalReport JSON and logs to output directory.

        Returns paths of saved artifacts.
        """
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        report_path = out / "final_report.json"
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2, default=str)
        # If logs already at `log_path` but not under out_dir, copy them
        log_src = Path(log_path)
        if log_src.exists() and log_src.parent != out:
            dest = out / log_src.name
            dest.write_text(log_src.read_text(encoding="utf-8"), encoding="utf-8")
            log_dst = str(dest)
        else:
            log_dst = str(log_src)
        return {"final_report": str(report_path), "logs": log_dst}


def _run_roundtable_sync(executor: RoundtableExecutor, plan: CompiledPlan) -> FinalReport:
    """Helper to run the async execute_roundtable in a synchronous context."""
    import asyncio

    async def _run() -> FinalReport:
        return await executor.execute_roundtable(
            task=plan.task_prompt,
            agents=plan.agents,
            mode=plan.voting_mode,
            timeout=float(plan.timeout_s),
            quorum_ratio=float(plan.quorum),
            task_id=plan.task_id,
        )

    try:
        return asyncio.run(_run())
    except RuntimeError:
        # In case there's already an event loop (e.g., in certain test runners), use nest
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_run())


__all__ = [
    "WorkflowExecutor",
    "WorkflowSpec",
    "CompiledPlan",
]


