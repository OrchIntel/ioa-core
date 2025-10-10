""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Literal

try:
    from pydantic import BaseModel, Field
except ImportError:  # Fallback minimal shim if pydantic not present
        pass

    def Field(default=None, **kwargs):  # type: ignore
        return default


class AssuranceWeights(BaseModel):
    code: float = Field(0.25, ge=0.0, le=1.0)
    tests: float = Field(0.25, ge=0.0, le=1.0)
    runtime: float = Field(0.25, ge=0.0, le=1.0)
    docs: float = Field(0.25, ge=0.0, le=1.0)


class AssuranceThresholds(BaseModel):
    pass_overall: float = Field(10.0, ge=0.0, le=15.0)
    warn_overall: float = Field(8.0, ge=0.0, le=15.0)


class AssuranceConfig(BaseModel):
    weights: AssuranceWeights = Field(default_factory=AssuranceWeights)
    thresholds: AssuranceThresholds = Field(default_factory=AssuranceThresholds)


class PerLawScore(BaseModel):
    law_id: Literal["law1","law2","law3","law4","law5","law6","law7"]
    code: int = Field(0, ge=0, le=4)
    tests: int = Field(0, ge=0, le=4)
    runtime: int = Field(0, ge=0, le=4)
    docs: int = Field(0, ge=0, le=4)
    total: float = 0.0


class AssuranceInput(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    per_law: List[PerLawScore] = Field(default_factory=list)
    evidence_paths: Dict[str, str] = Field(default_factory=dict)


class AssuranceRollup(BaseModel):
    timestamp: datetime
    per_law: List[PerLawScore]
    domain_means: Dict[str, float]
    overall: float
    weights: AssuranceWeights
    thresholds: AssuranceThresholds
    status: Literal["pass","warn","monitor"]
    notes: Optional[str] = None


