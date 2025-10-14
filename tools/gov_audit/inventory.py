"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import ast
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Any
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

class GovernanceInventory:
    """Scans codebase for governance-related modules, functions, and enforcement hooks."""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.src_root = self.repo_root / "src"
        self.policy_map = {
            "modules": {},
            "functions": {},
            "configs": {},
            "enforcement_hooks": {},
            "law_mappings": {}
        }
        
        # Target symbols to search for
        self.target_symbols = {
            "policy_engine": ["policy", "governance", "law", "rule"],
            "audit_chain": ["audit", "chain", "ledger", "tamper"],
            "governance": ["governance", "compliance", "regulatory"],
            "ethics": ["ethics", "fairness", "bias", "discrimination"],
            "nlp": ["nlp", "sentiment", "vader", "textstat"],
            "vad": ["vad", "valence", "arousal", "dominance"],
            "fairness": ["fairness", "disparate", "gini", "selection_rate"],
            "pii": ["pii", "privacy", "anonymize", "presidio"],
            "moderation": ["moderation", "toxicity", "profanity", "hate"],
            "doctor": ["doctor", "smoketest", "health", "diagnostic"],
            "roundtable": ["roundtable", "quorum", "consensus", "voting"],
            "sustainability": ["sustainability", "carbon", "energy", "efficiency"]
        }
        
        # Law mappings (IOA Laws 1-7)
        self.law_mappings = {
            "law_1": {
                "name": "Transparency and Explainability",
                "keywords": ["transparency", "explain", "interpret", "reasoning", "decision"]
            },
            "law_2": {
                "name": "Fairness and Non-Discrimination", 
                "keywords": ["fairness", "bias", "discrimination", "disparate", "protected"]
            },
            "law_3": {
                "name": "Privacy and Data Protection",
                "keywords": ["privacy", "pii", "gdpr", "anonymize", "consent"]
            },
            "law_4": {
                "name": "Safety and Reliability",
                "keywords": ["safety", "reliability", "robust", "error", "failure"]
            },
            "law_5": {
                "name": "Human Agency and Oversight",
                "keywords": ["human", "oversight", "control", "intervention", "agency"]
            },
            "law_6": {
                "name": "Accountability and Auditability",
                "keywords": ["accountability", "audit", "trace", "ledger", "tamper"]
            },
            "law_7": {
                "name": "Environmental and Social Impact",
                "keywords": ["sustainability", "environment", "carbon", "social", "impact"]
            }
        }

    def scan_python_files(self) -> None:
        """Scan all Python files for governance-related symbols."""
        for py_file in self.src_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST
                tree = ast.parse(content, filename=str(py_file))
                
                # Extract module info
                module_name = str(py_file.relative_to(self.src_root)).replace('/', '.').replace('.py', '')
                self.policy_map["modules"][module_name] = {
                    "file_path": str(py_file),
                    "functions": [],
                    "classes": [],
                    "imports": [],
                    "governance_relevance": self._assess_governance_relevance(content)
                }
                
                # Extract functions, classes, and imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_info = {
                            "name": node.name,
                            "line": node.lineno,
                            "governance_relevance": self._assess_governance_relevance(ast.get_source_segment(content, node))
                        }
                        self.policy_map["modules"][module_name]["functions"].append(func_info)
                        
                        # Check if function is enforcement hook
                        if self._is_enforcement_hook(node.name, content):
                            self.policy_map["enforcement_hooks"][f"{module_name}.{node.name}"] = {
                                "file": str(py_file),
                                "line": node.lineno,
                                "type": self._classify_hook_type(node.name, content)
                            }
                    
                    elif isinstance(node, ast.ClassDef):
                        class_info = {
                            "name": node.name,
                            "line": node.lineno,
                            "governance_relevance": self._assess_governance_relevance(ast.get_source_segment(content, node))
                        }
                        self.policy_map["modules"][module_name]["classes"].append(class_info)
                    
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        import_info = self._extract_import_info(node)
                        self.policy_map["modules"][module_name]["imports"].append(import_info)
                
            except Exception as e:
                print(f"Error parsing {py_file}: {e}")

    def scan_config_files(self) -> None:
        """Scan configuration files for governance settings."""
        config_patterns = [
            "**/governance_config.*",
            "**/system_laws.*", 
            "**/config/regulatory/*.json",
            "**/requirements*.txt",
            "**/pyproject.toml"
        ]
        
        for pattern in config_patterns:
            for config_file in self.repo_root.glob(pattern):
                if config_file.is_file():
                    self.policy_map["configs"][str(config_file)] = {
                        "type": self._classify_config_type(config_file),
                        "governance_content": self._extract_governance_config(config_file)
                    }

    def _assess_governance_relevance(self, content: str) -> Dict[str, bool]:
        """Assess how relevant content is to each governance area."""
        relevance = {}
        content_lower = content.lower()
        
        for area, keywords in self.target_symbols.items():
            relevance[area] = any(keyword in content_lower for keyword in keywords)
        
        return relevance

    def _is_enforcement_hook(self, func_name: str, content: str) -> bool:
        """Check if function appears to be an enforcement hook."""
        hook_patterns = [
            r"pre.?flight", r"post.?flight", r"enforce", r"validate", 
            r"check", r"audit", r"gate", r"guard"
        ]
        return any(re.search(pattern, func_name, re.IGNORECASE) for pattern in hook_patterns)

    def _classify_hook_type(self, func_name: str, content: str) -> str:
        """Classify the type of enforcement hook."""
        if re.search(r"pre.?flight", func_name, re.IGNORECASE):
            return "pre_flight"
        elif re.search(r"post.?flight", func_name, re.IGNORECASE):
            return "post_flight"
        elif re.search(r"validate|check", func_name, re.IGNORECASE):
            return "validation"
        elif re.search(r"audit|gate", func_name, re.IGNORECASE):
            return "audit"
        else:
            return "other"

    def _extract_import_info(self, node: ast.Import | ast.ImportFrom) -> Dict[str, Any]:
        """Extract import information."""
        if isinstance(node, ast.Import):
            return {
                "type": "import",
                "names": [alias.name for alias in node.names]
            }
        else:
            return {
                "type": "from_import",
                "module": node.module,
                "names": [alias.name for alias in node.names]
            }

    def _classify_config_type(self, config_file: Path) -> str:
        """Classify the type of configuration file."""
        if "governance" in str(config_file).lower():
            return "governance"
        elif "requirements" in str(config_file):
            return "requirements"
        elif "pyproject" in str(config_file):
            return "pyproject"
        elif "regulatory" in str(config_file):
            return "regulatory"
        else:
            return "other"

    def _extract_governance_config(self, config_file: Path) -> Dict[str, Any]:
        """Extract governance-related content from config files."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if config_file.suffix == '.json':
                return json.loads(content)
            else:
                # Extract lines that might contain governance settings
                lines = content.split('\n')
                governance_lines = []
                for i, line in enumerate(lines):
                    if any(keyword in line.lower() for keyword in 
                          ['governance', 'policy', 'law', 'audit', 'compliance']):
                        governance_lines.append({"line": i+1, "content": line.strip()})
                return {"governance_lines": governance_lines}
        except Exception as e:
            return {"error": str(e)}

    def map_laws_to_code(self) -> None:
        """Map IOA Laws to discovered code elements."""
        for law_id, law_info in self.law_mappings.items():
            self.policy_map["law_mappings"][law_id] = {
                "name": law_info["name"],
                "evidence": {
                    "modules": [],
                    "functions": [],
                    "configs": []
                }
            }
            
            # Find evidence for each law
            for module_name, module_info in self.policy_map["modules"].items():
                if any(keyword in str(module_info).lower() for keyword in law_info["keywords"]):
                    self.policy_map["law_mappings"][law_id]["evidence"]["modules"].append(module_name)
                
                for func in module_info["functions"]:
                    if any(keyword in func["name"].lower() for keyword in law_info["keywords"]):
                        self.policy_map["law_mappings"][law_id]["evidence"]["functions"].append(f"{module_name}.{func['name']}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate the complete policy map report."""
        self.scan_python_files()
        self.scan_config_files()
        self.map_laws_to_code()
        
        return self.policy_map

def main():
    """Main entry point for the inventory script."""
    repo_root = Path(__file__).parent.parent.parent
    inventory = GovernanceInventory(str(repo_root))
    
    print("Scanning codebase for governance-related code...")
    policy_map = inventory.generate_report()
    
    # Save policy map
    output_file = repo_root / "docs" / "ops" / "governance_audit" / "policy_map.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(policy_map, f, indent=2)
    
    print(f"Policy map saved to: {output_file}")
    print(f"Found {len(policy_map['modules'])} modules")
    print(f"Found {len(policy_map['enforcement_hooks'])} enforcement hooks")
    print(f"Found {len(policy_map['configs'])} config files")

if __name__ == "__main__":
    main()
