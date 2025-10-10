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
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import ast

class DocLinkChecker:
    """Validates CLI commands and options referenced in governance documentation."""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.docs_root = self.repo_root / "docs"
        self.cli_commands = set()
        self.cli_options = set()
        self.validation_results = {
            "valid_commands": [],
            "invalid_commands": [],
            "valid_options": [],
            "invalid_options": [],
            "fenced_blocks": [],
            "governance_docs": []
        }

    def discover_cli_interface(self) -> None:
        """Discover available CLI commands and options."""
        print("Discovering CLI interface...")
        
        # Look for CLI entry points
        cli_files = [
            "ioa_cli.py",
            "src/cli/main.py",
            "src/cli/commands.py"
        ]
        
        for cli_file in cli_files:
            file_path = self.repo_root / cli_file
            if file_path.exists():
                self._parse_cli_file(file_path)
        
        # Try to run help command to get actual CLI interface
        try:
            result = subprocess.run(
                ["python", str(self.repo_root / "ioa_cli.py"), "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                self._parse_help_output(result.stdout)
        except Exception as e:
            print(f"Could not run CLI help: {e}")

    def _parse_cli_file(self, file_path: Path) -> None:
        """Parse CLI file for command definitions."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for command definitions
            command_patterns = [
                r'@click\.command\(\)\s*def\s+(\w+)',
                r'@click\.group\(\)\s*def\s+(\w+)',
                r'def\s+(\w+)_command',
                r'def\s+(\w+)_cmd'
            ]
            
            for pattern in command_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    self.cli_commands.add(match)
            
            # Look for option definitions
            option_patterns = [
                r'@click\.option\([^)]*--(\w+)',
                r'@click\.argument\([^)]*(\w+)',
                r'--(\w+)',
                r'-(\w+)'
            ]
            
            for pattern in option_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    self.cli_options.add(match)
                    
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    def _parse_help_output(self, help_text: str) -> None:
        """Parse CLI help output to extract commands and options."""
        lines = help_text.split('\n')
        in_commands = False
        
        for line in lines:
            line = line.strip()
            if 'Commands:' in line or 'Available commands:' in line:
                in_commands = True
                continue
            elif line.startswith('Options:') or line.startswith('--'):
                in_commands = False
                continue
            
            if in_commands and line:
                # Extract command name (first word)
                command = line.split()[0]
                if command and not command.startswith('-'):
                    self.cli_commands.add(command)
            
            # Extract options
            if line.startswith('--'):
                option = line.split()[0].lstrip('--')
                if option:
                    self.cli_options.add(option)

    def scan_governance_docs(self) -> None:
        """Scan governance documentation for CLI references."""
        print("Scanning governance documentation...")
        
        # Find governance-related docs
        governance_doc_patterns = [
            "**/governance/**/*.md",
            "**/audit/**/*.md", 
            "**/ops/**/*.md",
            "**/README.md"
        ]
        
        for pattern in governance_doc_patterns:
            for doc_file in self.docs_root.glob(pattern):
                if doc_file.is_file():
                    self._scan_doc_file(doc_file)

    def _scan_doc_file(self, doc_file: Path) -> None:
        """Scan a single documentation file for CLI references."""
        try:
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            doc_info = {
                "file": str(doc_file.relative_to(self.repo_root)),
                "fenced_blocks": [],
                "cli_references": []
            }
            
            # Find fenced code blocks
            fenced_pattern = r'```(?:bash|sh|shell)?\s*\n(.*?)\n```'
            fenced_matches = re.finditer(fenced_pattern, content, re.DOTALL | re.MULTILINE)
            
            for match in fenced_matches:
                code_block = match.group(1)
                fenced_info = {
                    "line_start": content[:match.start()].count('\n') + 1,
                    "line_end": content[:match.end()].count('\n') + 1,
                    "content": code_block,
                    "commands": [],
                    "options": []
                }
                
                # Extract commands and options from code block
                lines = code_block.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('ioa ') or line.startswith('python ioa_cli.py'):
                        # Extract command
                        parts = line.split()
                        if len(parts) > 1:
                            command = parts[1]
                            fenced_info["commands"].append(command)
                            
                            # Extract options
                            for part in parts[2:]:
                                if part.startswith('--'):
                                    option = part.lstrip('--').split('=')[0]
                                    fenced_info["options"].append(option)
                                elif part.startswith('-') and len(part) > 1:
                                    option = part[1:]
                                    fenced_info["options"].append(option)
                
                doc_info["fenced_blocks"].append(fenced_info)
            
            # Find inline CLI references
            inline_patterns = [
                r'`ioa\s+(\w+)`',
                r'`--(\w+)`',
                r'`-(\w+)`'
            ]
            
            for pattern in inline_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    ref = match.group(1)
                    doc_info["cli_references"].append({
                        "line": content[:match.start()].count('\n') + 1,
                        "reference": ref,
                        "type": "command" if "ioa" in match.group(0) else "option"
                    })
            
            self.validation_results["governance_docs"].append(doc_info)
            
        except Exception as e:
            print(f"Error scanning {doc_file}: {e}")

    def validate_references(self) -> None:
        """Validate all discovered CLI references."""
        print("Validating CLI references...")
        
        for doc_info in self.validation_results["governance_docs"]:
            # Validate fenced blocks
            for fenced in doc_info["fenced_blocks"]:
                for command in fenced["commands"]:
                    if command in self.cli_commands:
                        self.validation_results["valid_commands"].append({
                            "file": doc_info["file"],
                            "line": fenced["line_start"],
                            "command": command,
                            "context": fenced["content"][:100] + "..."
                        })
                    else:
                        self.validation_results["invalid_commands"].append({
                            "file": doc_info["file"],
                            "line": fenced["line_start"],
                            "command": command,
                            "context": fenced["content"][:100] + "..."
                        })
                
                for option in fenced["options"]:
                    if option in self.cli_options:
                        self.validation_results["valid_options"].append({
                            "file": doc_info["file"],
                            "line": fenced["line_start"],
                            "option": option,
                            "context": fenced["content"][:100] + "..."
                        })
                    else:
                        self.validation_results["invalid_options"].append({
                            "file": doc_info["file"],
                            "line": fenced["line_start"],
                            "option": option,
                            "context": fenced["content"][:100] + "..."
                        })
            
            # Validate inline references
            for ref in doc_info["cli_references"]:
                if ref["type"] == "command":
                    if ref["reference"] in self.cli_commands:
                        self.validation_results["valid_commands"].append({
                            "file": doc_info["file"],
                            "line": ref["line"],
                            "command": ref["reference"],
                            "context": "inline reference"
                        })
                    else:
                        self.validation_results["invalid_commands"].append({
                            "file": doc_info["file"],
                            "line": ref["line"],
                            "command": ref["reference"],
                            "context": "inline reference"
                        })
                else:  # option
                    if ref["reference"] in self.cli_options:
                        self.validation_results["valid_options"].append({
                            "file": doc_info["file"],
                            "line": ref["line"],
                            "option": ref["reference"],
                            "context": "inline reference"
                        })
                    else:
                        self.validation_results["invalid_options"].append({
                            "file": doc_info["file"],
                            "line": ref["line"],
                            "option": ref["reference"],
                            "context": "inline reference"
                        })

    def generate_report(self) -> str:
        """Generate validation report."""
        report = """# CLI Documentation Validation Report

## Executive Summary

This report validates CLI commands and options referenced in governance documentation against the actual CLI interface.

## Discovered CLI Interface

### Available Commands
"""
        
        if self.cli_commands:
            for cmd in sorted(self.cli_commands):
                report += f"- `{cmd}`\n"
        else:
            report += "No commands discovered.\n"
        
        report += "\n### Available Options\n"
        
        if self.cli_options:
            for opt in sorted(self.cli_options):
                report += f"- `--{opt}`\n"
        else:
            report += "No options discovered.\n"
        
        report += "\n## Validation Results\n\n"
        
        # Valid commands
        report += "### Valid Command References\n"
        if self.validation_results["valid_commands"]:
            for ref in self.validation_results["valid_commands"]:
                report += f"- ✅ `{ref['command']}` in {ref['file']}:{ref['line']}\n"
        else:
            report += "No valid command references found.\n"
        
        # Invalid commands
        report += "\n### Invalid Command References\n"
        if self.validation_results["invalid_commands"]:
            for ref in self.validation_results["invalid_commands"]:
                report += f"- ❌ `{ref['command']}` in {ref['file']}:{ref['line']} (not found in CLI)\n"
        else:
            report += "No invalid command references found.\n"
        
        # Valid options
        report += "\n### Valid Option References\n"
        if self.validation_results["valid_options"]:
            for ref in self.validation_results["valid_options"]:
                report += f"- ✅ `--{ref['option']}` in {ref['file']}:{ref['line']}\n"
        else:
            report += "No valid option references found.\n"
        
        # Invalid options
        report += "\n### Invalid Option References\n"
        if self.validation_results["invalid_options"]:
            for ref in self.validation_results["invalid_options"]:
                report += f"- ❌ `--{ref['option']}` in {ref['file']}:{ref['line']} (not found in CLI)\n"
        else:
            report += "No invalid option references found.\n"
        
        # Summary statistics
        total_refs = (len(self.validation_results["valid_commands"]) + 
                     len(self.validation_results["invalid_commands"]) +
                     len(self.validation_results["valid_options"]) + 
                     len(self.validation_results["invalid_options"]))
        
        valid_refs = (len(self.validation_results["valid_commands"]) + 
                     len(self.validation_results["valid_options"]))
        
        report += f"\n## Summary Statistics\n\n"
        report += f"- Total references: {total_refs}\n"
        report += f"- Valid references: {valid_refs}\n"
        report += f"- Invalid references: {total_refs - valid_refs}\n"
        report += f"- Validation accuracy: {(valid_refs/total_refs*100):.1f}%" if total_refs > 0 else "N/A"
        
        report += "\n\n## Recommendations\n\n"
        
        if self.validation_results["invalid_commands"] or self.validation_results["invalid_options"]:
            report += "### Immediate Actions Required\n"
            report += "1. Update documentation to use correct CLI commands/options\n"
            report += "2. Verify CLI interface is up to date\n"
            report += "3. Consider adding CLI validation to CI/CD pipeline\n\n"
        
        report += "### Best Practices\n"
        report += "1. Use automated testing to validate CLI examples in docs\n"
        report += "2. Keep CLI help output synchronized with documentation\n"
        report += "3. Add linting rules to catch invalid CLI references\n"
        
        return report

def main():
    """Main entry point for the doclink checker."""
    repo_root = Path(__file__).parent.parent.parent
    checker = DocLinkChecker(str(repo_root))
    
    print("Discovering CLI interface...")
    checker.discover_cli_interface()
    
    print("Scanning governance documentation...")
    checker.scan_governance_docs()
    
    print("Validating references...")
    checker.validate_references()
    
    print("Generating report...")
    report = checker.generate_report()
    
    # Save results
    output_dir = repo_root / "docs" / "ops" / "status_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "CLI_DOC_VALIDATION_GOV_20250913.md", 'w') as f:
        f.write(report)
    
    # Save JSON results
    with open(output_dir / "cli_validation_results.json", 'w') as f:
        json.dump(checker.validation_results, f, indent=2)
    
    print(f"Report saved to: {output_dir}")
    print(f"Discovered {len(checker.cli_commands)} commands and {len(checker.cli_options)} options")

if __name__ == "__main__":
    main()
