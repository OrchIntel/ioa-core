""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

from typing import Dict, List

from .schema import (
    AssuranceConfig,
    AssuranceInput,
    AssuranceRollup,
    PerLawScore,
)


def compute_per_law_score(per_law: PerLawScore, weights: AssuranceConfig | None = None) -> float:
    """Compute weighted per-law score on 0–15 scale.

    Each dimension (code, tests, runtime, docs) is 0–4. Weighted sum scaled to 0–15.
    """
    cfg = weights or AssuranceConfig()
    w = cfg.weights
    raw = (
        per_law.code * w.code
        + per_law.tests * w.tests
        + per_law.runtime * w.runtime
        + per_law.docs * w.docs
    )
    # Max per dimension is 4; weighted max is 4. Scale to 15 by * (15/4)
    scaled = raw * (15.0 / 4.0)
    per_law.total = round(scaled, 2)
    return per_law.total


def compute_rollup(assurance_input: AssuranceInput, config: AssuranceConfig | None = None) -> AssuranceRollup:
    """Aggregate per-law scores into domain means and overall 0–15 score."""
    cfg = config or AssuranceConfig()

    # Compute totals for each law
    per_law_scores: List[PerLawScore] = []
    for pls in assurance_input.per_law:
        compute_per_law_score(pls, cfg)
        per_law_scores.append(pls)

    # Domain mapping (v1): Laws 1-5 Governance, 6 Security, 7 Docs? Keep simple: evenly assign
    domain_buckets: Dict[str, list[float]] = {"Governance": [], "Security": [], "Docs": []}
    for pls in per_law_scores:
        if pls.law_id in ("law1", "law2", "law3", "law4", "law5"):
            domain_buckets["Governance"].append(pls.total)
        elif pls.law_id == "law6":
            domain_buckets["Security"].append(pls.total)
        else:  # law7
            domain_buckets["Docs"].append(pls.total)

    domain_means: Dict[str, float] = {}
    for domain, vals in domain_buckets.items():
        domain_means[domain] = round(sum(vals) / len(vals), 2) if vals else 0.0

    # Overall = mean of per-law totals
    overall = round(sum(pl.total for pl in per_law_scores) / max(len(per_law_scores), 1), 2)

    # Status
    if overall >= cfg.thresholds.pass_overall:
        status = "pass"
    elif overall >= cfg.thresholds.warn_overall:
        status = "warn"
    else:
        status = "monitor"

    return AssuranceRollup(
        timestamp=assurance_input.timestamp,
        version=assurance_input.version,
        per_law=per_law_scores,
        domain_means=domain_means,
        overall=overall,
        weights=cfg.weights,
        thresholds=cfg.thresholds,
        status=status,
    )


