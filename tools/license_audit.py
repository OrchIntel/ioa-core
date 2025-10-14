"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
IOA Core License Audit Tool
"""

import os
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Dependency:
    """Represents a dependency with its metadata."""
    name: str
    license: Optional[str] = None
    source: str = ""  # requirements.txt, pyproject.toml, etc.
    risk_level: str = "unknown"  # low, medium, high
    usage: str = ""
    action_required: str = "none"


class LicenseAuditor:
    """Comprehensive license auditor for Python projects."""

    # Permissive licenses only (Apache-2.0, MIT, BSD, etc.)
    PERMISSIVE_LICENSES = {
        "Apache-2.0", "Apache 2.0", "Apache License 2.0",
        "MIT", "MIT License",
        "BSD", "BSD-2-Clause", "BSD-3-Clause", "BSD License",
        "ISC", "ISC License",
        "CC0-1.0", "CC0 1.0",
        "Unlicense",
        "PostgreSQL",  # Permissive for database drivers
    }

    # High-risk licenses to flag
    HIGH_RISK_LICENSES = {
        "GPL", "GPL-2.0", "GPL-3.0", "GPLv2", "GPLv3",
        "AGPL", "AGPL-3.0", "AGPLv3",
        "LGPL", "LGPL-2.1", "LGPLv3",
        "CC-BY-NC", "CC-BY-NC-SA", "CC-BY-NC-ND",
        "Proprietary", "Commercial",
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dependencies: Dict[str, Dependency] = {}
        self.audit_log: List[str] = []

    def audit_project(self) -> Dict[str, Dependency]:
        """Perform complete license audit of the project."""
        self.audit_log.append(f"Starting license audit at {datetime.now(timezone.utc).isoformat()}")

        # Scan different sources
        self._scan_requirements_files()
        self._scan_pyproject_toml()
        self._scan_source_imports()

        # Get license information
        self._query_pip_licenses()

        # Analyze risks
        self._analyze_risks()

        self.audit_log.append(f"Audit complete. Found {len(self.dependencies)} dependencies.")
        return self.dependencies

    def _scan_requirements_files(self):
        """Scan requirements*.txt files."""
        for req_file in self.project_root.glob("requirements*.txt"):
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Parse package==version or package>=version
                            match = re.match(r'^([a-zA-Z0-9\-_.]+)([>=<~!]+.+)?', line)
                            if match:
                                name = match.group(1).lower()
                                if name not in self.dependencies:
                                    self.dependencies[name] = Dependency(
                                        name=name,
                                        source=f"{req_file.name}"
                                    )
            except Exception as e:
                self.audit_log.append(f"Error scanning {req_file}: {e}")

    def _scan_pyproject_toml(self):
        """Scan pyproject.toml for dependencies."""
        pyproject_path = self.project_root / "pyproject.toml"
        if not pyproject_path.exists():
            return

        try:
            import tomllib
        except ImportError:
            # Python < 3.11
            try:
                import tomli as tomllib
            except ImportError:
                self.audit_log.append("tomllib/tomli not available, skipping pyproject.toml scan")
                return

        try:
            with open(pyproject_path, 'rb') as f:
                data = tomllib.load(f)

            # Scan dependencies
            for section in ['dependencies', 'optional-dependencies']:
                if section in data.get('project', {}):
                    deps = data['project'][section]
                    if isinstance(deps, list):
                        for dep in deps:
                            name = self._extract_package_name(dep)
                            if name and name not in self.dependencies:
                                self.dependencies[name] = Dependency(
                                    name=name,
                                    source="pyproject.toml"
                                )

            # Scan build-system requires
            if 'build-system' in data and 'requires' in data['build-system']:
                for dep in data['build-system']['requires']:
                    name = self._extract_package_name(dep)
                    if name and name not in self.dependencies:
                        self.dependencies[name] = Dependency(
                            name=name,
                            source="pyproject.toml (build-system)"
                        )

        except Exception as e:
            self.audit_log.append(f"Error scanning pyproject.toml: {e}")

    def _scan_source_imports(self):
        """Scan Python source files for imports."""
        # Common third-party packages to look for
        common_packages = {
            'numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn',
            'requests', 'urllib3', 'aiohttp', 'httpx',
            'click', 'typer', 'rich', 'tqdm',
            'pydantic', 'fastapi', 'uvicorn',
            'sqlalchemy', 'alembic',
            'pytest', 'black', 'flake8', 'mypy',
            'cryptography', 'bcrypt', 'passlib',
            'redis', 'pymongo', 'psycopg2',
            'celery', 'flower',
            'jinja2', 'markupsafe',
            'python-dotenv', 'pyyaml', 'toml',
            'structlog', 'loguru'
        }

        for py_file in self.project_root.glob("**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Find import statements
                import_pattern = re.compile(r'^(?:from|import)\s+([a-zA-Z0-9_][a-zA-Z0-9_\.]*)')
                for match in import_pattern.finditer(content):
                    module = match.group(1).split('.')[0].lower()

                    if module in common_packages and module not in self.dependencies:
                        self.dependencies[module] = Dependency(
                            name=module,
                            source=f"source: {py_file.relative_to(self.project_root)}"
                        )

            except Exception as e:
                self.audit_log.append(f"Error scanning {py_file}: {e}")

    def _extract_package_name(self, dep_spec: str) -> Optional[str]:
        """Extract package name from dependency specification."""
        # Handle various formats: package==1.0, package>=1.0, "package>=1.0"
        dep_spec = dep_spec.strip('"\'')
        match = re.match(r'^([a-zA-Z0-9\-_.]+)', dep_spec)
        return match.group(1).lower() if match else None

    def _query_pip_licenses(self):
        """Query pip-licenses for license information."""
        try:
            # Try to use pip-licenses if available
            result = subprocess.run([
                sys.executable, '-m', 'pip_licenses', '--format', 'json'
            ], capture_output=True, text=True, cwd=self.project_root)

            if result.returncode == 0:
                licenses_data = json.loads(result.stdout)
                for pkg_data in licenses_data:
                    name = pkg_data.get('Name', '').lower()
                    if name in self.dependencies:
                        self.dependencies[name].license = pkg_data.get('License')
                        self.dependencies[name].version = pkg_data.get('Version')

            else:
                self.audit_log.append("pip-licenses not available, using fallback license detection")
                self._fallback_license_detection()

        except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
            self.audit_log.append("pip-licenses failed, using fallback license detection")
            self._fallback_license_detection()

    def _fallback_license_detection(self):
        """Fallback license detection when pip-licenses is not available."""
        # This is a simplified fallback - in practice you'd want more comprehensive license data
        fallback_licenses = {
            'click': 'BSD-3-Clause',
            'pydantic': 'MIT',
            'requests': 'Apache-2.0',
            'pyyaml': 'MIT',
            'cryptography': 'Apache-2.0',
            'pytest': 'MIT',
            'black': 'MIT',
            'rich': 'MIT',
            'structlog': 'MIT',
            'tqdm': 'MIT',
            'python-dotenv': 'BSD-3-Clause',
            'jinja2': 'BSD-3-Clause',
            'markupsafe': 'BSD-3-Clause',
        }

        for name, license_name in fallback_licenses.items():
            if name in self.dependencies and not self.dependencies[name].license:
                self.dependencies[name].license = license_name

    def _analyze_risks(self):
        """Analyze license risks and recommend actions."""
        for name, dep in self.dependencies.items():
            license_name = dep.license or "unknown"

            # Determine risk level
            if license_name in self.PERMISSIVE_LICENSES:
                dep.risk_level = "low"
                dep.action_required = "none"
            elif license_name in self.HIGH_RISK_LICENSES:
                dep.risk_level = "high"
                dep.action_required = "replace"
            elif license_name == "unknown":
                dep.risk_level = "medium"
                dep.action_required = "verify"
            else:
                dep.risk_level = "medium"
                dep.action_required = "review"

            # Set usage context
            if "test" in dep.source.lower():
                dep.usage = "testing"
            elif "dev" in dep.source.lower():
                dep.usage = "development"
            else:
                dep.usage = "production"

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """Generate comprehensive license report."""
        report_lines = [
            "# IOA Core Legal Dependencies Matrix",
            "",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            f"**Total Dependencies:** {len(self.dependencies)}",
            "",
            "## License Risk Summary",
        ]

        # Risk summary
        risk_counts = {"low": 0, "medium": 0, "high": 0}
        for dep in self.dependencies.values():
            risk_counts[dep.risk_level] += 1

        report_lines.extend([
            f"- **Low Risk:** {risk_counts['low']} (Apache-2.0/MIT/BSD)",
            f"- **Medium Risk:** {risk_counts['medium']} (requires review)",
            f"- **High Risk:** {risk_counts['high']} (GPL/AGPL/proprietary)",
            "",
            "## Dependencies Matrix",
            "",
            "| Package | Version | License | Risk | Usage | Action | Source |",
            "|---------|---------|---------|------|-------|--------|--------|"
        ])

        # Sort dependencies by name
        sorted_deps = sorted(self.dependencies.values(), key=lambda x: x.name)

        for dep in sorted_deps:
            report_lines.append(
                f"| {dep.name} | {dep.version or 'unknown'} | {dep.license or 'unknown'} | "
                f"{dep.risk_level} | {dep.usage} | {dep.action_required} | {dep.source} |"
            )

        # Add audit log
        report_lines.extend([
            "",
            "## Audit Log",
            "",
            "```",
            *self.audit_log,
            "```"
        ])

        report = "\n".join(report_lines)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report)

        return report

    def generate_third_party_notice(self, output_path: Optional[Path] = None) -> str:
        """Generate THIRD_PARTY_NOTICE file for distribution."""
        notice_lines = [
            "IOA Core Third Party Notices",
            "===============================",
            "",
            "This product includes third-party software components.",
            "Below is a list of the components and their licenses.",
            "",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            "",
            "Components:",
            ""
        ]

        # Sort by license type for better organization
        sorted_deps = sorted(self.dependencies.values(), key=lambda x: (x.license or "unknown", x.name))

        current_license = None
        for dep in sorted_deps:
            license_name = dep.license or "unknown"

            # Group by license
            if license_name != current_license:
                if current_license is not None:
                    notice_lines.append("")
                notice_lines.append(f"License: {license_name}")
                notice_lines.append("-" * (len(license_name) + 9))
                current_license = license_name

            notice_lines.append(f"  - {dep.name}")
            notice_lines.append(f"    Usage: {dep.usage}")
            if dep.risk_level != "low":
                notice_lines.append(f"    Risk Level: {dep.risk_level}")
            notice_lines.append("")

        # Add attribution requirements
        notice_lines.extend([
            "",
            "License Texts:",
            "==============",
            "",
            "The following license texts are included for components that require attribution.",
            "",
            "Apache License 2.0:",
            "-------------------",
            "Licensed under the Apache License, Version 2.0 (the \"License\");",
            "you may not use this file except in compliance with the License.",
            "You may obtain a copy of the License at",
            "",
            "    http://www.apache.org/licenses/LICENSE-2.0",
            "",
            "Unless required by applicable law or agreed to in writing, software",
            "distributed under the License is distributed on an \"AS IS\" BASIS,",
            "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.",
            "See the License for the specific language governing permissions and",
            "limitations under the License.",
            "",
            "MIT License:",
            "------------",
            "Permission is hereby granted, free of charge, to any person obtaining a copy",
            "of this software and associated documentation files (the \"Software\"), to deal",
            "in the Software without restriction, including without limitation the rights",
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell",
            "copies of the Software, and to permit persons to whom the Software is",
            "furnished to do so, subject to the following conditions:",
            "",
            "The above copyright notice and this permission notice shall be included in all",
            "copies or substantial portions of the Software.",
            "",
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR",
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,",
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE",
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER",
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,",
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE",
            "SOFTWARE.",
            "",
            "BSD License:",
            "-----------",
            "Redistribution and use in source and binary forms, with or without modification,",
            "are permitted provided that the following conditions are met:",
            "",
            "1. Redistributions of source code must retain the above copyright notice, this",
            "   list of conditions and the following disclaimer.",
            "",
            "2. Redistributions in binary form must reproduce the above copyright notice,",
            "   this list of conditions and the following disclaimer in the documentation",
            "   and/or other materials provided with the distribution.",
            "",
            "THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND",
            "ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING MERCHANTABILITY AND FITNESS FOR A",
            "PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR",
            "CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,",
            "OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF",
            "SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS",
            "INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,",
            "STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY",
            "OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.",
            "",
            "For components with other licenses, please refer to the component's official",
            "license text or contact the component maintainer.",
            "",
            "Contact:",
            "--------",
            "For questions about third-party components, please contact:",
            "OrchIntel Systems Ltd. - maintainers@orchintel.com"
        ])

        notice = "\n".join(notice_lines)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(notice)

        return notice

    def create_licenses_directory(self, output_dir: Path):
        """Create LICENSES directory with individual license files."""
        licenses_dir = output_dir / "LICENSES"
        licenses_dir.mkdir(parents=True, exist_ok=True)

        # Group dependencies by license
        license_groups = {}
        for dep in self.dependencies.values():
            license_name = dep.license or "unknown"
            if license_name not in license_groups:
                license_groups[license_name] = []
            license_groups[license_name].append(dep)

        # Create license files
        for license_name, deps in license_groups.items():
            filename = f"{license_name.replace('/', '-').replace(' ', '_').lower()}.txt"
            license_file = licenses_dir / filename

            content_lines = [
                f"License: {license_name}",
                "=" * (len(license_name) + 9),
                "",
                f"Components using {license_name}:",
                ""
            ]

            for dep in sorted(deps, key=lambda x: x.name):
                content_lines.extend([
                    f"- {dep.name}",
                    f"  Usage: {dep.usage}",
                    ""
                ])

            # Add standard license texts
            if license_name == "Apache-2.0":
                content_lines.extend([
                    "",
                    "Apache License 2.0 Text:",
                    "-----------------------",
                    "Licensed under the Apache License, Version 2.0 (the \"License\");",
                    "you may not use this file except in compliance with the License.",
                    "You may obtain a copy of the License at",
                    "",
                    "    http://www.apache.org/licenses/LICENSE-2.0",
                    "",
                    "Unless required by applicable law or agreed to in writing, software",
                    "distributed under the License is distributed on an \"AS IS\" BASIS,",
                    "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.",
                    "See the License for the specific language governing permissions and",
                    "limitations under the License."
                ])
            elif license_name == "MIT":
                content_lines.extend([
                    "",
                    "MIT License Text:",
                    "-----------------",
                    "Permission is hereby granted, free of charge, to any person obtaining a copy",
                    "of this software and associated documentation files (the \"Software\"), to deal",
                    "in the Software without restriction, including without limitation the rights",
                    "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell",
                    "copies of the Software, and to permit persons to whom the Software is",
                    "furnished to do so, subject to the following conditions:",
                    "",
                    "The above copyright notice and this permission notice shall be included in all",
                    "copies or substantial portions of the Software.",
                    "",
                    "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR",
                    "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,",
                    "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE",
                    "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,",
                    "SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,",
                    "PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR",
                    "BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER",
                    "IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)",
                    "ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE",
                    "POSSIBILITY OF SUCH DAMAGE."
                ])

            with open(license_file, 'w') as f:
                f.write("\n".join(content_lines))

    def check_ci_gate(self) -> Dict[str, Any]:
        """Check if license audit passes CI gate requirements."""
        gate_results = {
            "passed": True,
            "blockers": [],
            "warnings": [],
            "summary": {}
        }

        # Count license types
        license_counts = {}
        for dep in self.dependencies.values():
            license_name = dep.license or "unknown"
            license_counts[license_name] = license_counts.get(license_name, 0) + 1

        # Check for high-risk licenses (blockers)
        high_risk_deps = [dep for dep in self.dependencies.values() if dep.risk_level == "high"]
        if high_risk_deps:
            gate_results["passed"] = False
            gate_results["blockers"].extend([
                f"High-risk license '{dep.license}' used by {dep.name}"
                for dep in high_risk_deps
            ])

        # Check for unknown licenses (warnings)
        unknown_deps = [dep for dep in self.dependencies.values() if not dep.license]
        if unknown_deps:
            gate_results["warnings"].extend([
                f"Unknown license for {dep.name}"
                for dep in unknown_deps
            ])

        # Summary
        gate_results["summary"] = {
            "total_dependencies": len(self.dependencies),
            "license_types": license_counts,
            "high_risk_count": len(high_risk_deps),
            "unknown_license_count": len(unknown_deps),
            "permissive_licenses": sum(count for license_name, count in license_counts.items()
                                     if license_name in self.PERMISSIVE_LICENSES)
        }

        return gate_results

    def check_copyleft_violations(self) -> List[str]:
        """Check for copyleft license violations in dependency tree."""
        violations = []

        # Define copyleft licenses that could contaminate distribution
        copyleft_licenses = {"GPL", "AGPL", "LGPL", "CDDL", "EPL", "MPL"}

        for dep in self.dependencies.values():
            license_name = dep.license or ""
            # Check if license contains copyleft terms
            if any(copyleft in license_name.upper() for copyleft in copyleft_licenses):
                violations.append(
                    f"Copyleft license '{dep.license}' detected in {dep.name} "
                    f"(usage: {dep.usage}). May require distribution under same license."
                )

        return violations


def main():
    """Main entry point for license audit tool."""
    import argparse

    parser = argparse.ArgumentParser(description="IOA Core License Audit Tool")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--output", "-o", type=Path,
                       help="Output file path")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--ci-gate", action="store_true", help="Run CI gate check and exit with code")
    parser.add_argument("--third-party-notice", type=Path, help="Generate THIRD_PARTY_NOTICE file")
    parser.add_argument("--licenses-dir", type=Path, help="Generate LICENSES directory with individual files")
    parser.add_argument("--check-copyleft", action="store_true", help="Check for copyleft license violations")

    args = parser.parse_args()

    auditor = LicenseAuditor(args.project_root)

    if args.verbose:
        print("🔍 Scanning project dependencies...")

    dependencies = auditor.audit_project()

    # CI gate mode
    if args.ci_gate:
        gate_result = auditor.check_ci_gate()
        if gate_result["passed"]:
            print("✅ CI Gate PASSED")
            print(f"   Total dependencies: {gate_result['summary']['total_dependencies']}")
            print(f"   Permissive licenses: {gate_result['summary']['permissive_licenses']}")
            return 0
        else:
            print("❌ CI Gate FAILED")
            for blocker in gate_result["blockers"]:
                print(f"  🚫 {blocker}")
            for warning in gate_result["warnings"]:
                print(f"  ⚠️  {warning}")
            return 1

    # Copyleft check mode
    if args.check_copyleft:
        copyleft_issues = auditor.check_copyleft_violations()
        if copyleft_issues:
            print("❌ Copyleft violations found:")
            for issue in copyleft_issues:
                print(f"  🚫 {issue}")
            return 1
        else:
            print("✅ No copyleft violations found")
            return 0

    # Generate THIRD_PARTY_NOTICE if requested
    if args.third_party_notice:
        print("📄 Generating THIRD_PARTY_NOTICE...")
        auditor.generate_third_party_notice(args.third_party_notice)
        print(f"   ✅ Generated: {args.third_party_notice}")

    # Generate LICENSES directory if requested
    if args.licenses_dir:
        print("📁 Generating LICENSES directory...")
        auditor.create_licenses_directory(args.licenses_dir)
        print(f"   ✅ Generated: {args.licenses_dir}/LICENSES/")

    # Generate report (if not just generating notice/licenses)
    if not (args.third_party_notice or args.licenses_dir or args.ci_gate or args.check_copyleft):
        report = auditor.generate_report(args.output)

        if args.output:
            print(f"✅ License audit report saved to {args.output}")
        else:
            print(report)

    # Check for high-risk licenses (legacy behavior)
    high_risk = [dep for dep in dependencies.values() if dep.risk_level == "high"]
    if high_risk:
        print(f"\n⚠️  WARNING: Found {len(high_risk)} high-risk dependencies:")
        for dep in high_risk:
            print(f"  - {dep.name}: {dep.license}")
        return 1

    print("\n✅ All dependencies appear to have acceptable licenses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
