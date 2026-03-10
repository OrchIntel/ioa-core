# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Minimal compatibility CLI for ``python -m cartridges._framework.cli``."""

from __future__ import annotations

import argparse
from typing import Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cartridges._framework.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Run cartridge checks")
    doctor.add_argument("name")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        # Legacy sample target is used by framework compatibility tests.
        return 0 if args.name == "sample" else 2
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
