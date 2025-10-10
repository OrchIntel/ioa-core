""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from datetime import datetime, timezone

from workflow_executor import WorkflowExecutor


def _default_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="IOA Workflows CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    run_p = sub.add_subparser if hasattr(sub, 'add_subparser') else sub.add_parser  # compat
    run = run_p("run", help="Run a workflow from YAML")
    run.add_argument("-f", "--file", required=True, help="Path to workflow YAML (DSL)")
    run.add_argument("--json", action="store_true", help="Print FinalReport JSON to stdout")
    run.add_argument(
        "--log-file",
        help="Path to JSONL log file (default: reports/workflows/<STAMP>/run.jsonl)",
    )

    args = parser.parse_args(argv)
    if args.command != "run":
        parser.print_help()
        return 2

    # Execute workflow
    executor = WorkflowExecutor(dispatch_code="DISPATCH-GPT-20250818-010")
    spec = executor.parse_yaml(args.file)
    compiled = executor.compile(spec)

    # Determine log file location
    stamp = _default_stamp()
    default_log = Path(compiled.artifacts_output_dir.replace("${STAMP}", stamp)) / "run.jsonl"
    log_path = args.log_file or str(default_log)

    report = executor.run(compiled, log_file=log_path)
    artifacts = executor.save_artifacts(report, log_path=log_path, out_dir=compiled.artifacts_output_dir)

    if args.json:
        import json
        print(json.dumps(report.model_dump(), indent=2))

    print(f"Artifacts saved:\n  FinalReport: {artifacts['final_report']}\n  Logs: {artifacts['logs']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


