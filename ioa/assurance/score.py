""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class AssuranceScore:
    """Assurance score data structure."""
    assurance_score: float
    assurance_score: float  # Mirror for compatibility
    laws_coverage: float
    security_score: float
    docs_score: float
    hygiene_score: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


def compute_laws_coverage() -> float:
    """Compute laws coverage score (1-7 scale)."""
    laws_dir = Path("src/ioa_core/laws")
    if not laws_dir.exists():
        return 0.0
    
    # Count implemented laws
    law_files = list(laws_dir.glob("law*.py"))
    implemented_laws = len(law_files)
    
    # Normalize to 0-1 scale (7 laws max)
    return min(implemented_laws / 7.0, 1.0)


def compute_security_score() -> float:
    """Compute security score based on security checks."""
    security_checks = [
        "src/ioa_core/security/",
        ".github/workflows/security-scan.yml",
        "config/security.yaml",
        "SECURITY.md"
    ]
    
    score = 0.0
    for check in security_checks:
        if Path(check).exists():
            score += 0.25
    
    return min(score, 1.0)


def compute_docs_score() -> float:
    """Compute documentation score."""
    docs_checks = [
        "README.md",
        "docs/",
        "docs/api/",
        "docs/governance/",
        "docs/user-guide/",
        "mkdocs.yml"
    ]
    
    score = 0.0
    for check in docs_checks:
        if Path(check).exists():
            score += 0.16  # ~1/6
    
    return min(score, 1.0)


def compute_hygiene_score() -> float:
    """Compute hygiene score based on CI checks."""
    hygiene_checks = [
        ".github/workflows/hygiene.yml",
        ".github/workflows/python-tests.yml",
        ".github/workflows/ci-gates.yml",
        "pytest.ini",
        "requirements.txt",
        "requirements-dev.txt"
    ]
    
    score = 0.0
    for check in hygiene_checks:
        if Path(check).exists():
            score += 0.16  # ~1/6
    
    return min(score, 1.0)


def compute_assurance_score(
    laws_weight: float = 0.4,
    security_weight: float = 0.3,
    docs_weight: float = 0.2,
    hygiene_weight: float = 0.1
) -> AssuranceScore:
    """
    Compute weighted assurance score.
    
    Args:
        laws_weight: Weight for laws coverage (default: 0.4)
        security_weight: Weight for security score (default: 0.3)
        docs_weight: Weight for docs score (default: 0.2)
        hygiene_weight: Weight for hygiene score (default: 0.1)
    
    Returns:
        AssuranceScore object with computed scores
    """
    # Compute individual scores
    laws_score = compute_laws_coverage()
    security_score = compute_security_score()
    docs_score = compute_docs_score()
    hygiene_score = compute_hygiene_score()
    
    # Compute weighted assurance score
    assurance_score = (
        laws_score * laws_weight +
        security_score * security_weight +
        docs_score * docs_weight +
        hygiene_score * hygiene_weight
    )
    
    # Create timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Create assurance score object
    score = AssuranceScore(
        assurance_score=assurance_score,
        laws_coverage=laws_score,
        security_score=security_score,
        docs_score=docs_score,
        hygiene_score=hygiene_score,
        timestamp=timestamp
    )
    
    return score


def write_assurance_score(score: AssuranceScore, output_dir: str = "artifacts/lens/assurance") -> None:
    """Write assurance score to files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write JSON
    json_file = output_path / "assurance_score.json"
    with open(json_file, 'w') as f:
        f.write(score.to_json())
    
    # Write markdown report
    md_file = output_path / "assurance_report.md"
    with open(md_file, 'w') as f:
        f.write(f"""# Assurance Score Report

**Generated:** {score.timestamp}  

## Scores

- **Assurance Score:** {score.assurance_score:.3f}
- **assurance Score:** {score.assurance_score:.3f} (mirror)

## Components

- **Laws Coverage:** {score.laws_coverage:.3f}
- **Security Score:** {score.security_score:.3f}
- **Documentation Score:** {score.docs_score:.3f}
- **Hygiene Score:** {score.hygiene_score:.3f}

## Interpretation

- **0.8-1.0:** Excellent assurance
- **0.6-0.8:** Good assurance
- **0.4-0.6:** Moderate assurance
- **0.2-0.4:** Poor assurance
- **0.0-0.2:** Critical assurance issues

## Files

- **JSON:** `{json_file}`
- **Report:** `{md_file}`
""")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute IOA Assurance Score v1")
    parser.add_argument("--write", action="store_true", help="Write score to files")
    parser.add_argument("--output-dir", default="artifacts/lens/assurance", help="Output directory")
    parser.add_argument("--format", choices=["json", "md", "both"], default="both", help="Output format")
    
    args = parser.parse_args()
    
    # Compute score
    score = compute_assurance_score()
    
    if args.write:
        write_assurance_score(score, args.output_dir)
        print(f"✅ Assurance score written to {args.output_dir}")
    else:
        if args.format in ["json", "both"]:
            print(score.to_json())
        if args.format in ["md", "both"]:
            print(f"# Assurance Score: {score.assurance_score:.3f}")
            print(f"**Components:** Laws: {score.laws_coverage:.3f}, Security: {score.security_score:.3f}, Docs: {score.docs_score:.3f}, Hygiene: {score.hygiene_score:.3f}")


if __name__ == "__main__":
    main()
