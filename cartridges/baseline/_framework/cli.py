""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .evidence import EvidenceRecord, EvidenceWriter
from .lifecycle import CartridgeContext
from .registry import CartridgeInfo, get_registry


def _ensure_sample_registry() -> None:
    registry = get_registry()
    if "sample" not in registry.list():
        registry.register(
            CartridgeInfo(
                name="sample",
                version="1.0.0",
                description="Sample cartridge for framework doctor",
            ),
            doctor=lambda: True,
        )


def command_doctor(name: str) -> int:
    reg = get_registry()
    reg.get(name)  # validate exists
    ok = reg.doctor(name)
    return 0 if ok else 2


def command_run(name: str, profile: str, outdir: Optional[str]) -> int:
    reg = get_registry()
    info = reg.get(name)
    ctx = CartridgeContext(profile=profile)
    # For v1 scaffold, record a simple evidence line
    writer = EvidenceWriter(Path(outdir or "artifacts/evidence"))
    writer.append(EvidenceRecord.create(info.name, "run", {"profile": profile}))
    return 0


def command_report(name: str, outdir: Optional[str]) -> int:
    reg = get_registry()
    info = reg.get(name)
    writer = EvidenceWriter(Path(outdir or "artifacts/evidence"))
    writer.append(EvidenceRecord.create(info.name, "report", {"status": "ok"}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ioa cart")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_doctor = sub.add_parser("doctor")
    p_doctor.add_argument("name")

    p_run = sub.add_parser("run")
    p_run.add_argument("name")
    p_run.add_argument("--profile", default="monitor")
    p_run.add_argument("--outdir")

    p_report = sub.add_parser("report")
    p_report.add_argument("name")
    p_report.add_argument("--outdir")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    _ensure_sample_registry()
    args = build_parser().parse_args(argv)
    if args.cmd == "doctor":
        return command_doctor(args.name)
    if args.cmd == "run":
        return command_run(args.name, args.profile, args.outdir)
    if args.cmd == "report":
        return command_report(args.name, args.outdir)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
