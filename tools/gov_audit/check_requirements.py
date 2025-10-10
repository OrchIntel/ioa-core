""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Any
import sys

class RequirementsChecker:
    """Analyzes current requirements and compares with recommended governance dependencies."""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.current_deps = set()
        self.recommended_deps = {
            "fairness": {
                "fairlearn": {
                    "description": "Primary fairness metrics and bias detection",
                    "priority": "high",
                    "law_mapping": ["law_2"],
                    "usage": "Disparate impact analysis, demographic parity"
                },
                "aif360": {
                    "description": "Comprehensive fairness toolkit (optional/heavier)",
                    "priority": "medium", 
                    "law_mapping": ["law_2"],
                    "usage": "Advanced bias metrics, adversarial debiasing"
                }
            },
            "pii_detection": {
                "presidio-analyzer": {
                    "description": "PII detection and analysis",
                    "priority": "high",
                    "law_mapping": ["law_3"],
                    "usage": "GDPR compliance, data anonymization"
                },
                "presidio-anonymizer": {
                    "description": "PII anonymization and masking",
                    "priority": "high",
                    "law_mapping": ["law_3"],
                    "usage": "Data protection, privacy preservation"
                },
                "phonenumbers": {
                    "description": "Phone number validation and formatting",
                    "priority": "medium",
                    "law_mapping": ["law_3"],
                    "usage": "PII detection fallback"
                }
            },
            "toxicity_moderation": {
                "detoxify": {
                    "description": "Toxicity and harassment detection",
                    "priority": "medium",
                    "law_mapping": ["law_2", "law_4"],
                    "usage": "Content moderation, safety enforcement"
                }
            },
            "nlp_sentiment": {
                "vadersentiment": {
                    "description": "VADER sentiment analysis",
                    "priority": "medium",
                    "law_mapping": ["law_1", "law_4"],
                    "usage": "Tone analysis, emotional valence"
                },
                "textstat": {
                    "description": "Text readability and complexity metrics",
                    "priority": "low",
                    "law_mapping": ["law_1"],
                    "usage": "Transparency scoring, explainability"
                },
                "wordfreq": {
                    "description": "Word frequency analysis",
                    "priority": "low",
                    "law_mapping": ["law_1"],
                    "usage": "Language complexity assessment"
                }
            },
            "sustainability": {
                "carbon-tracker": {
                    "description": "ML model carbon footprint tracking",
                    "priority": "high",
                    "law_mapping": ["law_7"],
                    "usage": "Environmental impact monitoring"
                },
                "codecarbon": {
                    "description": "Code execution carbon tracking",
                    "priority": "medium",
                    "law_mapping": ["law_7"],
                    "usage": "Development sustainability metrics"
                }
            },
            "existing": {
                "scikit-learn": {
                    "description": "Already present - statistical analysis",
                    "priority": "present",
                    "law_mapping": ["law_2"],
                    "usage": "Gini coefficient, selection rate analysis"
                }
            }
        }

    def scan_current_requirements(self) -> None:
        """Scan current requirements files for installed packages."""
        req_files = [
            "requirements.txt",
            "requirements-dev.txt", 
            "pyproject.toml"
        ]
        
        for req_file in req_files:
            file_path = self.repo_root / req_file
            if file_path.exists():
                self._parse_requirements_file(file_path)

    def _parse_requirements_file(self, file_path: Path) -> None:
        """Parse a requirements file and extract package names."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.name == "pyproject.toml":
                self._parse_pyproject_toml(content)
            else:
                self._parse_requirements_txt(content)
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    def _parse_requirements_txt(self, content: str) -> None:
        """Parse requirements.txt format."""
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before ==, >=, etc.)
                package = re.split(r'[>=<!=]', line)[0].strip()
                if package:
                    self.current_deps.add(package.lower())

    def _parse_pyproject_toml(self, content: str) -> None:
        """Parse pyproject.toml for dependencies."""
        # Simple regex-based parsing for dependencies
        in_deps = False
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('[project]') or line.startswith('[tool.poetry]'):
                in_deps = True
                continue
            elif line.startswith('[') and not line.startswith('[project') and not line.startswith('[tool.poetry'):
                in_deps = False
                continue
            
            if in_deps and '=' in line and not line.startswith('#'):
                # Look for dependency lines
                if 'dependencies' in line or '=' in line:
                    # Extract package names from quoted strings
                    packages = re.findall(r'"([^"]+)"', line)
                    for package in packages:
                        if not package.startswith('['):  # Skip extras
                            self.current_deps.add(package.lower())

    def analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze current vs recommended dependencies."""
        analysis = {
            "current_dependencies": list(self.current_deps),
            "recommended_dependencies": {},
            "missing_dependencies": {},
            "present_dependencies": {},
            "law_coverage": {},
            "priority_analysis": {
                "high_priority_missing": [],
                "medium_priority_missing": [],
                "low_priority_missing": []
            }
        }
        
        # Flatten recommended deps for easier analysis
        all_recommended = {}
        for category, deps in self.recommended_deps.items():
            for dep_name, dep_info in deps.items():
                all_recommended[dep_name] = {**dep_info, "category": category}
        
        # Check what's missing and what's present
        for dep_name, dep_info in all_recommended.items():
            if dep_name in self.current_deps:
                analysis["present_dependencies"][dep_name] = dep_info
            else:
                analysis["missing_dependencies"][dep_name] = dep_info
                
                # Categorize by priority
                priority = dep_info.get("priority", "low")
                if priority == "high":
                    analysis["priority_analysis"]["high_priority_missing"].append(dep_name)
                elif priority == "medium":
                    analysis["priority_analysis"]["medium_priority_missing"].append(dep_name)
                else:
                    analysis["priority_analysis"]["low_priority_missing"].append(dep_name)
        
        # Analyze law coverage
        for law_id in ["law_1", "law_2", "law_3", "law_4", "law_5", "law_6", "law_7"]:
            analysis["law_coverage"][law_id] = {
                "present": [],
                "missing": [],
                "coverage_score": 0
            }
            
            for dep_name, dep_info in all_recommended.items():
                if law_id in dep_info.get("law_mapping", []):
                    if dep_name in self.current_deps:
                        analysis["law_coverage"][law_id]["present"].append(dep_name)
                    else:
                        analysis["law_coverage"][law_id]["missing"].append(dep_name)
            
            # Calculate coverage score
            total_deps = len(analysis["law_coverage"][law_id]["present"]) + len(analysis["law_coverage"][law_id]["missing"])
            if total_deps > 0:
                analysis["law_coverage"][law_id]["coverage_score"] = len(analysis["law_coverage"][law_id]["present"]) / total_deps
        
        return analysis

    def generate_delta_report(self) -> str:
        """Generate a markdown report of requirements delta."""
        analysis = self.analyze_dependencies()
        
        report = """# Requirements Delta Report - Governance Dependencies

## Executive Summary

This report analyzes the current state of governance-related dependencies in IOA Core v2.5.0 and identifies gaps for implementing IOA Laws 1-7.

## Current Dependencies Status

### Present Dependencies
"""
        
        if analysis["present_dependencies"]:
            for dep_name, dep_info in analysis["present_dependencies"].items():
                report += f"- **{dep_name}**: {dep_info['description']}\n"
                report += f"  - Priority: {dep_info['priority']}\n"
                report += f"  - Laws: {', '.join(dep_info['law_mapping'])}\n"
                report += f"  - Usage: {dep_info['usage']}\n\n"
        else:
            report += "No governance-specific dependencies currently installed.\n\n"
        
        report += "### Missing Dependencies by Priority\n\n"
        
        for priority in ["high", "medium", "low"]:
            missing_deps = analysis["priority_analysis"][f"{priority}_priority_missing"]
            if missing_deps:
                report += f"#### {priority.title()} Priority Missing\n\n"
                for dep_name in missing_deps:
                    dep_info = analysis["missing_dependencies"][dep_name]
                    report += f"- **{dep_name}**: {dep_info['description']}\n"
                    report += f"  - Laws: {', '.join(dep_info['law_mapping'])}\n"
                    report += f"  - Usage: {dep_info['usage']}\n\n"
        
        report += "## Law Coverage Analysis\n\n"
        
        for law_id, coverage in analysis["law_coverage"].items():
            law_name = law_id.replace("law_", "Law ").replace("_", " ").title()
            report += f"### {law_name} (Coverage: {coverage['coverage_score']:.1%})\n\n"
            
            if coverage["present"]:
                report += "**Present Dependencies:**\n"
                for dep in coverage["present"]:
                    report += f"- {dep}\n"
                report += "\n"
            
            if coverage["missing"]:
                report += "**Missing Dependencies:**\n"
                for dep in coverage["missing"]:
                    dep_info = analysis["missing_dependencies"][dep]
                    report += f"- {dep} ({dep_info['priority']} priority)\n"
                report += "\n"
        
        report += "## Recommendations\n\n"
        
        high_priority = analysis["priority_analysis"]["high_priority_missing"]
        if high_priority:
            report += "### Immediate Action Required\n"
            report += "Install these high-priority dependencies for core governance functionality:\n\n"
            for dep in high_priority:
                dep_info = analysis["missing_dependencies"][dep]
                report += f"- `{dep}`: {dep_info['description']}\n"
            report += "\n"
        
        report += "### Implementation Strategy\n\n"
        report += "1. **Phase 1**: Install high-priority dependencies with basic tests\n"
        report += "2. **Phase 2**: Add medium-priority dependencies with integration tests\n"
        report += "3. **Phase 3**: Evaluate low-priority dependencies based on usage patterns\n\n"
        
        report += "### Notes\n\n"
        report += "- All dependencies should be installed with version pinning\n"
        report += "- Consider using optional dependencies for heavier packages (aif360, detoxify)\n"
        report += "- Implement proper error handling for missing optional dependencies\n"
        report += "- Add governance-specific test datasets for validation\n"
        
        return report

def main():
    """Main entry point for the requirements checker."""
    repo_root = Path(__file__).parent.parent.parent
    checker = RequirementsChecker(str(repo_root))
    
    print("Scanning current requirements...")
    checker.scan_current_requirements()
    
    print("Analyzing dependency gaps...")
    analysis = checker.analyze_dependencies()
    
    # Save analysis
    output_dir = repo_root / "docs" / "ops" / "governance_audit"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON analysis
    with open(output_dir / "requirements_analysis.json", 'w') as f:
        json.dump(analysis, f, indent=2)
    
    # Generate markdown report
    report = checker.generate_delta_report()
    with open(output_dir / "requirements_delta.md", 'w') as f:
        f.write(report)
    
    print(f"Analysis saved to: {output_dir}")
    print(f"Found {len(checker.current_deps)} current dependencies")
    print(f"Missing {len(analysis['missing_dependencies'])} recommended dependencies")

if __name__ == "__main__":
    main()
