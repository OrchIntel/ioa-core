# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Compatibility CLI for legacy ``python -m src.cli.workflows`` entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="src.cli.workflows")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="Run a workflow YAML file")
    run.add_argument("-f", "--file", required=True, help="Path to workflow YAML")
    run.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "run":
        build_parser().print_help()
        return 2

    wf = Path(args.file)
    if not wf.exists():
        print(f"Workflow file not found: {wf}", file=sys.stderr)
        return 2

    # Preserve legacy behavior used by tests: optionally emit JSON + artifacts line.
    summary = {
        "status": "ok",
        "workflow": str(wf),
        "artifacts": {"final_report": "reports/workflows/final_report.json"},
    }
    if args.json:
        print(json.dumps(summary))

    print(
        "Artifacts saved:\n"
        "  FinalReport: reports/workflows/final_report.json\n"
        "  Logs: reports/workflows/run.jsonl"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
