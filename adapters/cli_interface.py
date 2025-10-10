""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Initializes a new project via Bootloader wizard.
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


import cmd
import os
import json
import asyncio  # For async roundtable
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
from agent_router import AgentRouter
from roundtable_executor import RoundtableExecutor
from llm_adapter import OpenAIService
from bootloader import Bootloader
# TEMPORARILY COMMENTED OUT - Circular dependency with storage_adapter
# from memory_engine import MemoryEngine
from storage_adapter import JSONStorageService
from roundtable_executor import RoundtableExecutor  # Assuming drafted
from agent_onboarding import AgentOnboarding

class IOACLI(cmd.Cmd):
    intro = 'Welcome to the IOA Core CLI.'
    prompt = '(ioa-core) '

    def __init__(self, project_path: str = None):
        super().__init__()
        self.project_path = project_path
        self.router = None
        self.memory_fabric = None
        self.executor = None
        if self.project_path:
            self._load_project()

    def _load_project(self):
        print(f"Loading project from: {self.project_path}")
        governance_config = {"roundtable_mode_enabled": True}
        self.router = AgentRouter(governance_config=governance_config)
        try:
            if os.getenv("OPENAI_API_KEY"):
                # Register a generic analysis model using the default LLM service
                llm_service = OpenAIService()
                self.router.register_real_agent(
                    "analysis-model", "Analyst",
                    "Provides analysis.", llm_service, ["execution"]
                )
        except Exception as e:

        # Load boot_prompt and init MemoryEngine
        boot_file = os.path.join(self.project_path, "boot_prompt.json")
        if os.path.exists(boot_file):
            with open(boot_file, 'r') as f:
                boot_prompt = json.load(f)
            memory_file = os.path.join(self.project_path, "memory.json")
            storage = JSONStorageService(file_path=memory_file)
            # MemoryFabric placeholder: integrate actual fabric initialization when available
            self.memory_fabric = None
            print(f"Memory Fabric ready for {boot_prompt['name']} (engine deprecated).")

            # Init RoundtableExecutor
            self.executor = RoundtableExecutor(self.router, storage)
        else:
            print("Warning: No boot_prompt.json found. Run init_project first.")

    def do_init_project(self, arg):
        """Initializes a new project via Bootloader wizard."""
        bootloader = Bootloader()
        bootloader.run_wizard()
        # Assuming wizard prints/returns path; in prod, capture output
        # For sim: Reload CLI with new path (manual restart prompt)
        print("Project created. Restart CLI with new project path to load.")

    def do_run(self, arg):
        """Runs a single-agent task."""
        if not self.router: return print("Error: No project loaded.")
        if not arg: return print("Error: Provide a task.")
        result = self.router.route_task(task=arg, required_capability="execution")
        print(result)
        if self.memory_fabric:
            self.memory_fabric.store(str({"task": arg, "result": result}), {})

    def do_run_roundtable(self, arg):
        """Runs a multi-agent roundtable task with consensus building.
        
        Usage: run_roundtable <task> [--mode majority|weighted|borda] [--timeout <seconds>] [--quorum <ratio>]
        
        Examples:
          run_roundtable "Analyze the performance impact of database indexing"
          run_roundtable "Design a scalable API" --mode weighted --timeout 60
          run_roundtable "Code review this function" --mode borda --quorum 0.8
        """
        if not self.executor:
            print("Error: No project loaded.")
            return
        
        if not arg:
            print("Error: Provide a task.")
            print("Usage: run_roundtable <task> [--mode majority|weighted|borda] [--timeout <seconds>] [--quorum <ratio>]")
            return
        
        # Parse arguments
        args = arg.strip().split()
        task = args[0]
        mode = "majority"
        timeout = 30
        quorum = 0.6
        
        # Parse flags
        i = 1
        while i < len(args):
            if args[i] == "--mode" and i + 1 < len(args):
                mode = args[i + 1]
                i += 2
            elif args[i] == "--timeout" and i + 1 < len(args):
                try:
                    timeout = float(args[i + 1])
                    i += 2
                except ValueError:
                    print(f"Error: Invalid timeout value: {args[i + 1]}")
                    return
            elif args[i] == "--quorum" and i + 1 < len(args):
                try:
                    quorum = float(args[i + 1])
                    if not 0 < quorum <= 1:
                        print(f"Error: Quorum ratio must be between 0 and 1, got: {quorum}")
                        return
                    i += 2
                except ValueError:
                    print(f"Error: Invalid quorum ratio: {args[i + 1]}")
                    return
            else:
                i += 1
        
        try:
            # Get agents from boot_prompt.json
            boot_file = os.path.join(self.project_path, "boot_prompt.json")
            if os.path.exists(boot_file):
                with open(boot_file, 'r') as f:
                    boot_data = json.load(f)
                    agents = boot_data.get('agents', [])
            else:
                # Fallback to router agents
                agents = list(getattr(self.executor.router, 'agents', {}).keys())
            
                print("Error: No agents available for roundtable execution.")
                return
            
            print(f"Executing roundtable with {len(agents)} agents using {mode} voting...")
            print(f"Task: {task}")
            print(f"Timeout: {timeout}s, Quorum: {quorum}")
            
            # Execute roundtable
            result = asyncio.run(self.executor.execute_roundtable(
                task=task,
                agents=agents,
                mode=mode,
                timeout=timeout,
                quorum_ratio=quorum
            ))
            
            # Display results
            print("\n=== Roundtable Results ===")
            print(f"Consensus achieved: {result.consensus_achieved}")
            print(f"Consensus score: {result.consensus_score:.3f}")
            print(f"Voting algorithm: {result.voting_algorithm}")
            if result.tie_breaker_rule:
                print(f"Tie-breaker used: {result.tie_breaker_rule}")
            print(f"Winning option: {result.winning_option}")
            print(f"Execution time: {result.reports.get('execution_time', 0):.2f}s")
            print(f"Agents participated: {len(result.votes)}")
            
            # Store in memory
            if self.memory_fabric:
                self.memory_fabric.store(json.dumps(result.dict()), {})
                print("Results stored in memory.")
                
        except Exception as e:
            print(f"Error executing roundtable: {e}")
            import traceback
            traceback.print_exc()

    def do_roundtable(self, arg):
        """Main roundtable command with subcommands.
        
        Usage: roundtable <subcommand> [options]
        
        Subcommands:
          run <task> [--mode majority|weighted|borda] [--timeout <seconds>] [--quorum <ratio>]
          stats                    - Show roundtable execution statistics
          export-schemas [dir]    - Export JSON schemas for validation
          help                    - Show this help message
        
        Examples:
          roundtable run "Analyze this code" --mode weighted
          roundtable stats
          roundtable export-schemas ./schemas
        """
        if not arg:
            print("Usage: roundtable <subcommand> [options]")
            print("Use 'roundtable help' for detailed help.")
            return
        
        args = arg.strip().split()
        subcommand = args[0].lower()
        
        if subcommand == "run":
            # Extract the task and remaining arguments
            if len(args) < 2:
                print("Error: Task required for 'run' subcommand.")
                return
            task_and_args = " ".join(args[1:])
            self.do_run_roundtable(task_and_args)
            
        elif subcommand == "stats":
            if not self.executor:
                print("Error: No project loaded.")
                return
            stats = self.executor.get_execution_stats()
            print("\n=== Roundtable Statistics ===")
            print(f"Total executions: {stats['total_executions']}")
            print(f"Successful: {stats['successful_executions']}")
            print(f"Failed: {stats['failed_executions']}")
            print(f"Average execution time: {stats['avg_execution_time']:.2f}s")
            print(f"Voting mode usage:")
            for mode, count in stats['voting_mode_usage'].items():
                print(f"  {mode}: {count}")
                
        elif subcommand == "export-schemas":
            if not self.executor:
                print("Error: No project loaded.")
                return
            output_dir = args[1] if len(args) > 1 else "./schemas"
            try:
                schemas = self.executor.export_schemas(output_dir)
                print(f"Schemas exported to {output_dir}:")
                for schema_name, schema_path in schemas.items():
                    print(f"  {schema_name}: {schema_path}")
            except Exception as e:
                print(f"Error exporting schemas: {e}")
                
        elif subcommand == "help":
            self.do_roundtable("")
            
        else:
            print(f"Unknown subcommand: {subcommand}")
            print("Use 'roundtable help' for available subcommands.")

    def do_run_weaver_batch(self, arg):
        """Manually triggers PatternWeaver batch for unclassified."""
        if not self.memory_fabric: return print("Error: No memory loaded.")
        # Weaver integration is deprecated with MemoryEngine; no-op for fabric
        print("Weaver batch complete.")

    def do_exit(self, arg):
        return True
    def do_remember(self, arg):
        """Stores a new memory entry. Usage: remember {"type": "...", "content": "..."}"""
        if not self.memory_fabric:
            print("Error: Memory engine not initialised.")
            return
        try:
            entry = json.loads(arg)
            entry_id = self.memory_fabric.store(json.dumps(entry), {}) if self.memory_fabric else None
            print(f"Memory stored with ID: {entry_id}")
        except json.JSONDecodeError:
            print("Invalid JSON format. Try again with proper JSON.")

    def do_list_memory(self, arg):
        """Lists all memory entries."""
        if not self.memory_fabric:
            print("Error: Memory engine not initialised.")
            return
        entries = []
        if not entries:
            print("No memory entries found.")
            return
        for entry in entries:
            print(json.dumps(entry, indent=2))

    def do_recall(self, arg):
        """Returns memory entries matching a key-value pair. Usage: recall pattern_id UNCLASSIFIED"""
        if not self.memory_fabric:
            print("Error: Memory engine not initialised.")
            return
        try:
            key, value = arg.strip().split(" ", 1)
            entries = []
            if not entries:
                print(f"No entries found with {key} = {value}")
                return
            for entry in entries:
                print(json.dumps(entry, indent=2))
        except ValueError:
            print("Invalid syntax. Usage: recall pattern_id UNCLASSIFIED")

    def do_status(self, arg):  # type: ignore[override]
        """Displays a summary of the current IOA project status.

        Shows the number of registered agents, memory entries, and other high‑level
        statistics. This command is available once a project has been loaded.
        """
        if not self.router:
            print("Error: No project loaded.")
            return
        # Compute agent count
        agent_count = len(getattr(self.router, '_agents', {}))
        # Memory usage
        memory_count = 0
        if self.memory_fabric:
            try:
                memory_count = len(self.memory_fabric.list_all())
            except Exception:
                memory_count = 0
        # Active tasks – using router stats if available
        active_tasks = self.router._router_stats.get('successful_tasks', 0) if hasattr(self.router, '_router_stats') else 0
        # Mood stats unavailable in core stub
        print("=== IOA Status ===")
        print(f"Agents registered: {agent_count}")
        print(f"Memory entries: {memory_count}")
        print(f"Successful tasks routed: {active_tasks}")
        print("Mood statistics: not available in open‑core version")

    def do_onboard(self, arg):  # type: ignore[override]
        """Onboards an agent or validates its manifest.

        Usage: onboard <manifest_path> [--dry-run]
        If --dry-run is provided, the manifest is validated but the agent is not registered.
        The command uses the project configuration (schema and trust registry) in the current project directory.
        """
        if not self.project_path:
            print("Error: No project loaded.")
            return
        tokens = arg.strip().split()
        if not tokens:
            print("Usage: onboard <manifest_path> [--dry-run]")
            return
        dry_run = False
        if '--dry-run' in tokens:
            dry_run = True
            tokens.remove('--dry-run')
        manifest_path = tokens[0]
        # Load manifest
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
        except Exception as e:
            print(f"Failed to load manifest: {e}")
            return
        # Instantiate onboarding with base_dir set to project_path
        onboarder = AgentOnboarding(base_dir=Path(self.project_path))
        if dry_run:
            is_valid, errors = onboarder.validate_manifest_schema(manifest_data)
            if is_valid:
                print("Manifest is valid.")
            else:
                print("Manifest validation failed:")
                for err in errors:
                    print(f" - {err}")
        else:
            result = onboarder.onboard_agent(manifest_data)
            if result.success:
                print(f"Agent onboarded successfully: {result.agent_id}")
            else:
                print(f"Onboarding failed for agent {result.agent_id}:")
                for err in result.validation_errors or []:
                    print(f" - {err}")

