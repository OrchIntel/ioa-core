""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from src.ioa.assurance.schema import AssuranceConfig, AssuranceInput, PerLawScore
from src.ioa.assurance.calc import compute_per_law_score, compute_rollup


def test_per_law_scaling_default_weights():
    cfg = AssuranceConfig()
    pls = PerLawScore(law_id="law1", code=4, tests=4, runtime=4, docs=4)
    score = compute_per_law_score(pls, cfg)
    assert score == 15.0


def test_rollup_overall_mean():
    cfg = AssuranceConfig()
    per_law = [
        PerLawScore(law_id="law1", code=4, tests=4, runtime=4, docs=4),  # 15
        PerLawScore(law_id="law2", code=2, tests=2, runtime=2, docs=2),  # 7.5
    ]
    inp = AssuranceInput(per_law=per_law)
    rollup = compute_rollup(inp, cfg)
    assert abs(rollup.overall - ((15.0 + 7.5) / 2)) < 1e-6
    assert rollup.status in ("pass", "warn", "monitor")


