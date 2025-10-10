""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import json


@dataclass
class EvidenceRecord:
    """Evidence payload captured during cartridge execution."""

    cartridge: str
    kind: str
    payload: Dict[str, Any]
    created_at: str

    @staticmethod
    def create(cartridge: str, kind: str, payload: Dict[str, Any]) -> "EvidenceRecord":
        return EvidenceRecord(
            cartridge=cartridge,
            kind=kind,
            payload=payload,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class EvidenceWriter:
    """Writes evidence records to JSONL file per cartridge."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def append(self, record: EvidenceRecord) -> Path:
        target = self.directory / f"{record.cartridge}_evidence.jsonl"
        with target.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        return target


