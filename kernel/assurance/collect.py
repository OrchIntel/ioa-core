""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .schema import AssuranceConfig, AssuranceInput, PerLawScore


def _read_jsonl_last(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            last = None
            for line in f:
                line = line.strip()
                if line:
                    last = line
            if last:
                return json.loads(last)
    except Exception:
        return {}
    return {}


def collect_inputs(config: AssuranceConfig | None = None) -> AssuranceInput:
    cfg = config or AssuranceConfig()

    evidence_paths: Dict[str, str] = {
        "ethics": "artifacts/lens/ethics/metrics.jsonl",
        "sustainability": "artifacts/lens/sustainability/metrics.jsonl",
        "harness": "artifacts/harness/governance/metrics.jsonl",
        "bandit": "artifacts/security/bandit.json",
        "trufflehog": "artifacts/security/trufflehog.json",
        "cli_drift": "artifacts/lens/docs/cli_drift.json",
    }

    # Simple heuristic mapping to 0-4 for each law and domain based on evidence presence
    per_law: List[PerLawScore] = []
    for law_id in ["law1", "law2", "law3", "law4", "law5", "law6", "law7"]:
        pls = PerLawScore(law_id=law_id)

        # Governance laws 1-5: use ethics/sustainability/harness as signals
        if law_id in ("law1", "law2", "law3", "law4", "law5"):
            ethics_last = _read_jsonl_last(Path(evidence_paths["ethics"]))
            harness_last = _read_jsonl_last(Path(evidence_paths["harness"]))

            pls.code = 2 if ethics_last else 1
            pls.tests = 3 if harness_last else 1
            pls.runtime = 2 if ethics_last or harness_last else 0
            pls.docs = 2

        # Security law 6: bandit/trufflehog
        elif law_id == "law6":
            bandit = Path(evidence_paths["bandit"]).exists()
            truffle = Path(evidence_paths["trufflehog"]).exists()
            pls.code = 2 if bandit else 1
            pls.tests = 2 if truffle else 1
            pls.runtime = 2 if (bandit or truffle) else 0
            pls.docs = 2

        # Docs law 7: CLI drift validator
        else:
            cli_drift = Path(evidence_paths["cli_drift"]).exists()
            pls.code = 1
            pls.tests = 2 if cli_drift else 1
            pls.runtime = 2 if cli_drift else 0
            pls.docs = 3 if cli_drift else 1

        per_law.append(pls)

    return AssuranceInput(per_law=per_law, evidence_paths=evidence_paths)


