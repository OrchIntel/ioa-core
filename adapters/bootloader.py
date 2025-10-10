""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""


# bootloader.py
# Bootloader for IOA: Initializes new project instances with wizard for multi-domains.
# Creates .ioa folder, schema.json, boot_prompt.json, memory.json, etc.
# MVP: Basic scaffolding; Phase 2: Domain wizard, schema load/gen via LLM, models.

import os
import json
import sys
import logging
from llm_adapter import OpenAIService  # For custom schema gen
from typing import Dict, List
from cli.errors import NonInteractiveError

class Bootloader:
    def __init__(self, base_path: str = "./projects"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
    
    def _check_non_interactive(self) -> None:
        """Check if running in non-interactive environment and raise error if so."""
        # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-014 <add non-interactive safety>
        if os.getenv('IOA_NON_INTERACTIVE') == '1' or not sys.stdin.isatty():
            # Emit structured JSON for CL-006 compliance
            try:
                from datetime import datetime, timezone
                import json as _json
                log_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "INFO",
                    "message": "Interactive wizard skipped in non-interactive environment",
                    "non_interactive_skip": True,
                    "environment": "CI/non-interactive",
                    "module": "bootloader",
                    "dispatch_code": "DISPATCH-GPT-20250819-016"
                }
                print(_json.dumps(log_entry), file=sys.stderr)
            except Exception as exc:
                logging.getLogger(__name__).debug(
                    "Failed to emit non-interactive JSON log: %s", exc
                )
            raise NonInteractiveError("Interactive wizard disallowed in non-interactive environment")

    def run_wizard(self):
        """Runs interactive wizard for project setup."""
        # Check non-interactive environment first
        self._check_non_interactive()
        
        print("Welcome to IOA Bootloader.")
        project_type = self._get_project_type()
        project_name = input("Project name: ")
        project_path = os.path.join(self.base_path, f"{project_name}.ioa")
        os.makedirs(project_path, exist_ok=True)

        # Create basic files
        with open(os.path.join(project_path, "instructions.txt"), 'w') as f:
            f.write("Default instructions.")  # From MVP
        with open(os.path.join(project_path, "agents.json"), 'w') as f:
            json.dump([], f)
        with open(os.path.join(project_path, "governance.config.yaml"), 'w') as f:
            f.write("roundtable_mode_enabled: true\n")
        with open(os.path.join(project_path, "memory.json"), 'w') as f:
            json.dump([], f)  # Initial empty for JSONStorage

        # Phase 2: Schema + Boot Prompt
        schema = self._load_or_generate_schema(project_type)
        with open(os.path.join(project_path, "schema.json"), 'w') as f:
            json.dump(schema, f)

        # Generate boot_prompt.json
        boot_prompt = {
            "type": project_type,
            "name": f"{project_name}.IOA",
            "schema": schema,
            "agents": self._get_default_agents(project_type)
        }
        with open(os.path.join(project_path, "boot_prompt.json"), 'w') as f:
            json.dump(boot_prompt, f)

        # Entry script (MVP)
        entry_script = f"from cli_interface import IOACLI\nimport os\nif __name__ == '__main__':\n    project_path = os.path.dirname(os.path.abspath(__file__))\n    IOACLI(project_path=project_path).cmdloop()"
        with open(os.path.join(project_path, f"{project_name}.py"), 'w') as f:
            f.write(entry_script)

        print(f"Project {project_name}.IOA initialized at {project_path} with {project_type} schema.")

    def _get_project_type(self):
        """Get project type from user input."""
        # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-015 <add non-interactive safety>
        # Check non-interactive environment first
        self._check_non_interactive()
        
        options = ["screenwriting", "legal", "education", "custom"]
        print("Project type options: " + ", ".join(options))
        choice = input("Enter type: ").lower()
        return choice if choice in options else "custom"

    def _load_or_generate_schema(self, project_type: str) -> Dict:
        """Load or generate schema for project type."""
        # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-015 <add non-interactive safety>
        # Check non-interactive environment first
        self._check_non_interactive()
        
        presets = {
            "screenwriting": {"characters": ["name", "bio", "traits"], "scenes": ["id", "title", "content"]},
            "legal": {"case": ["id", "client", "facts", "precedents"]},
            "education": {"lesson": ["topic", "objectives", "materials"]}
        }
        if project_type in presets:
            return presets[project_type]
        else:
            desc = input("Describe schema (e.g., 'case: id, client, facts'): ")
            # Use LLM for JSON gen
            llm = OpenAIService()
            prompt = f"Generate JSON schema from: {desc}. Format as dict: {{'entity': ['field1', 'field2']}}"
            response = llm.execute(prompt)
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"custom": ["field1", "field2"]}  # Fallback on invalid JSON
            except Exception as exc:
                logging.getLogger(__name__).debug("Schema generation failed: %s", exc)
                return {"custom": ["field1", "field2"]}

    def _get_default_agents(self, project_type: str) -> List[str]:
        # Preset agents per type (expand as needed)
        defaults = {
            "screenwriting": ["Analyzer", "Editor"],  # PATCH: Cursor-2024-12-19 ET-001 Step 3 - Remove Lorekeeper
            "legal": ["LegalClerk", "Analyzer"],
            "education": ["TeacherBot", "QuizMaster"]
        }
        return defaults.get(project_type, ["Analyzer", "Editor"])  # Default fallback
# Bootloader entry point
if __name__ == "__main__":
    Bootloader().run_wizard()
