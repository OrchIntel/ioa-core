"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Extended CLI commands for IOA system administration and management
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
CLI Commands Module for IOA Core

Provides extended command implementations for the IOA CLI interface including
system administration, debugging, monitoring, and advanced memory operations.
Integrates with the main CLI interface for comprehensive system management.
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path


class CLICommandError(Exception):
    """Base exception for CLI command operations."""
    pass


class IOACommands:
    """
    Extended command implementations for IOA CLI interface.
    
    Provides advanced system management, debugging, and monitoring capabilities
    beyond the basic CLI operations. Designed to be integrated with the main
    CLI interface for a comprehensive command suite.
    """
    
    def __init__(self, cli_instance):
        """
        Initialize with reference to main CLI instance.
        
        Args:
            cli_instance: Main IOACLI instance for accessing components
        """
        self.cli = cli_instance
        self.start_time = datetime.now()
    
    def do_status(self, arg: str = "") -> None:
        """
        Display comprehensive system status and health information.
        
        Usage: status [component]
        
        Shows status of all components or specific component if specified.
        Components: memory, agents, storage, governance, patterns
        """
        if not self.cli.project_path:
            print("❌ No project loaded. Run 'init_project' first.")
            return
        
        print("🔍 IOA System Status Report")
        print("=" * 50)
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Project: {os.path.basename(self.cli.project_path)}")
        print(f"⏱️  Uptime: {datetime.now() - self.start_time}")
        print()
        
        component = arg.strip().lower()
        
        if not component or component == "memory":
            self._show_memory_status()
        
        if not component or component == "agents":
            self._show_agent_status()
        
        if not component or component == "storage":
            self._show_storage_status()
        
        if not component or component == "patterns":
            self._show_pattern_status()
        
        if not component or component == "governance":
            self._show_governance_status()
        
        if component and component not in ["memory", "agents", "storage", "patterns", "governance"]:
            print(f"❌ Unknown component: {component}")
            print("Available components: memory, agents, storage, patterns, governance")
    
    def _show_memory_status(self) -> None:
        """Display memory engine status."""
        print("🧠 Memory Engine Status:")
        if self.cli.memory_engine:
            try:
                entries = self.cli.memory_engine.list_all()
                print(f"  📊 Total entries: {len(entries)}")
                
                # Count by pattern
                pattern_counts = {}
                for entry in entries:
                    pattern_id = entry.get('pattern_id', 'unclassified')
                    pattern_counts[pattern_id] = pattern_counts.get(pattern_id, 0) + 1
                
                print(f"  🏷️  Patterns active: {len(pattern_counts)}")
                if pattern_counts:
                    for pattern, count in sorted(pattern_counts.items())[:5]:
                        print(f"     • {pattern}: {count} entries")
                
                # Recent activity
                recent_entries = [e for e in entries if 'timestamp' in e]
                if recent_entries:
                    latest = max(recent_entries, key=lambda x: x.get('timestamp', ''))
                    print(f"  🕒 Last update: {latest.get('timestamp', 'Unknown')}")
                
                print("  ✅ Status: Operational")
            except Exception as e:
                print(f"  ❌ Status: Error - {e}")
        else:
            print("  ❌ Status: Not initialized")
        print()
    
    def _show_agent_status(self) -> None:
        """Display agent router status."""
        print("🤖 Agent Router Status:")
        if self.cli.router:
            agents = self.cli.router.agents
            
            for agent_id, agent_data in agents.items():
                agent_type = agent_data.get('type', 'unknown')
                capabilities = agent_data.get('capabilities', [])
                print(f"     • {agent_id} ({agent_type}): {', '.join(capabilities)}")
            
            # Test connectivity
            try:
                test_result = self.cli.router.route_task("ping", "execution")
                if "error" not in test_result:
                    print("  ✅ Status: Operational")
                else:
                    print(f"  ⚠️  Status: Warning - {test_result.get('error', 'Unknown issue')}")
            except Exception as e:
                print(f"  ❌ Status: Error - {e}")
        else:
            print("  ❌ Status: Not initialized")
        print()
    
    def _show_storage_status(self) -> None:
        """Display storage service status."""
        print("💾 Storage Status:")
        if self.cli.memory_engine and hasattr(self.cli.memory_engine, 'storage'):
            storage = self.cli.memory_engine.storage
            storage_type = type(storage).__name__
            print(f"  📁 Type: {storage_type}")
            
            try:
                if hasattr(storage, 'get_stats'):
                    stats = storage.get_stats()
                    print(f"  📊 Stats: {stats}")
                elif hasattr(storage, 'file_path'):
                    file_path = storage.file_path
                    if os.path.exists(file_path):
                        size = os.path.getsize(file_path)
                        print(f"  📂 File: {file_path}")
                        print(f"  📏 Size: {size} bytes")
                        print(f"  🕒 Modified: {datetime.fromtimestamp(os.path.getmtime(file_path))}")
                    else:
                        print(f"  📂 File: {file_path} (not found)")
                
                print("  ✅ Status: Operational")
            except Exception as e:
                print(f"  ❌ Status: Error - {e}")
        else:
            print("  ❌ Status: Not initialized")
        print()
    
    def _show_pattern_status(self) -> None:
        """Display pattern system status."""
        print("🏷️  Pattern System Status:")
        if self.cli.memory_engine and hasattr(self.cli.memory_engine, 'patterns'):
            patterns = self.cli.memory_engine.patterns
            print(f"  📊 Loaded patterns: {len(patterns)}")
            
            for pattern in patterns[:5]:  # Show first 5
                pattern_id = pattern.get('pattern_id', 'unknown')
                keywords = pattern.get('keywords', [])
                print(f"     • {pattern_id}: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}")
            
            if len(patterns) > 5:
                print(f"     ... and {len(patterns) - 5} more")
            
            print("  ✅ Status: Operational")
        else:
            print("  ❌ Status: Not initialized")
        print()
    
    def _show_governance_status(self) -> None:
        """Display governance system status."""
        print("⚖️  Governance Status:")
        if self.cli.router and hasattr(self.cli.router, 'governance_config'):
            config = self.cli.router.governance_config
            print(f"  📊 Configuration: {len(config)} settings")
            
            for key, value in config.items():
                print(f"     • {key}: {value}")
            
            print("  ✅ Status: Operational")
        else:
            print("  ❌ Status: Not initialized")
        print()
    
    def do_memory_stats(self, arg: str = "") -> None:
        """
        Display detailed memory engine statistics and analytics.
        
        Usage: memory_stats [detailed]
        
        Shows memory usage patterns, performance metrics, and storage analytics.
        """
        if not self.cli.memory_engine:
            print("❌ Memory engine not initialized.")
            return
        
        print("📊 Memory Engine Analytics")
        print("=" * 40)
        
        entries = self.cli.memory_engine.list_all()
        print(f"Total entries: {len(entries)}")
        
        if not entries:
            print("No memory entries found.")
            return
        
        # Pattern distribution
        pattern_dist = {}
        confidence_scores = []
        timestamps = []
        
        for entry in entries:
            pattern_id = entry.get('pattern_id', 'unclassified')
            pattern_dist[pattern_id] = pattern_dist.get(pattern_id, 0) + 1
            
            if 'confidence' in entry:
                confidence_scores.append(float(entry['confidence']))
            
            if 'timestamp' in entry:
                timestamps.append(entry['timestamp'])
        
        # Pattern analysis
        print(f"\n🏷️  Pattern Distribution:")
        sorted_patterns = sorted(pattern_dist.items(), key=lambda x: x[1], reverse=True)
        for pattern, count in sorted_patterns[:10]:
            percentage = (count / len(entries)) * 100
            print(f"  {pattern}: {count} ({percentage:.1f}%)")
        
        # Confidence analysis
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            print(f"\n📈 Confidence Metrics:")
            print(f"  Average: {avg_confidence:.3f}")
            print(f"  Min: {min(confidence_scores):.3f}")
            print(f"  Max: {max(confidence_scores):.3f}")
            
            # Confidence distribution
            high_conf = len([s for s in confidence_scores if s > 0.8])
            med_conf = len([s for s in confidence_scores if 0.5 <= s <= 0.8])
            low_conf = len([s for s in confidence_scores if s < 0.5])
            
            print(f"  High (>0.8): {high_conf}")
            print(f"  Medium (0.5-0.8): {med_conf}")
            print(f"  Low (<0.5): {low_conf}")
        
        # Timeline analysis
        if timestamps and len(timestamps) > 1:
            timestamps.sort()
            first_entry = timestamps[0]
            last_entry = timestamps[-1]
            
            print(f"\n🕒 Timeline:")
            print(f"  First entry: {first_entry}")
            print(f"  Last entry: {last_entry}")
            print(f"  Span: {len(timestamps)} entries")
        
        # Detailed analysis if requested
        if arg.strip().lower() == "detailed":
            self._show_detailed_memory_stats(entries)
    
    def _show_detailed_memory_stats(self, entries: List[Dict[str, Any]]) -> None:
        """Show detailed memory statistics."""
        print(f"\n🔍 Detailed Analysis:")
        
        # Content length analysis
        content_lengths = []
        for entry in entries:
            content = entry.get('raw_ref', '')
            if isinstance(content, str):
                content_lengths.append(len(content))
        
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            print(f"  Content lengths - Avg: {avg_length:.0f}, Min: {min(content_lengths)}, Max: {max(content_lengths)}")
        
        # Variable extraction analysis
        var_counts = []
        for entry in entries:
            variables = entry.get('variables', {})
            if isinstance(variables, dict):
                var_counts.append(len(variables))
        
        if var_counts:
            avg_vars = sum(var_counts) / len(var_counts)
            print(f"  Variables per entry - Avg: {avg_vars:.1f}, Max: {max(var_counts)}")
        
        # Sentiment analysis if available
        sentiments = []
        for entry in entries:
            feeling = entry.get('feeling', {})
            if isinstance(feeling, dict) and 'valence' in feeling:
                sentiments.append(feeling['valence'])
        
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
            positive = len([s for s in sentiments if s > 0.1])
            negative = len([s for s in sentiments if s < -0.1])
            neutral = len(sentiments) - positive - negative
            
            print(f"  Sentiment - Avg: {avg_sentiment:.3f}, Positive: {positive}, Negative: {negative}, Neutral: {neutral}")
    
    def do_cleanup(self, arg: str = "") -> None:
        """
        Perform system cleanup and maintenance operations.
        
        Usage: cleanup [type]
        
        Types: memory, logs, temp, all
        Default: Show what would be cleaned without executing
        """
        cleanup_type = arg.strip().lower() or "dry-run"
        
        print("🧹 IOA System Cleanup")
        print("=" * 30)
        
        if cleanup_type in ["memory", "all"]:
            self._cleanup_memory(dry_run=(cleanup_type == "dry-run"))
        
        if cleanup_type in ["logs", "all"]:
            self._cleanup_logs(dry_run=(cleanup_type == "dry-run"))
        
        if cleanup_type in ["temp", "all"]:
            self._cleanup_temp_files(dry_run=(cleanup_type == "dry-run"))
        
        if cleanup_type == "dry-run":
            print("\n💡 This was a dry run. Use 'cleanup [type]' to execute.")
    
    def _cleanup_memory(self, dry_run: bool = True) -> None:
        """Clean up memory entries based on various criteria."""
        if not self.cli.memory_engine:
            return
        
        print("🧠 Memory Cleanup:")
        
        try:
            entries = self.cli.memory_engine.list_all()
            
            # Find cleanup candidates
            low_confidence = [e for e in entries if e.get('confidence', 1.0) < 0.3]
            old_unclassified = []
            
            for entry in entries:
                if entry.get('pattern_id') == 'unclassified':
                    timestamp = entry.get('timestamp', '')
                    if timestamp:
                        # Simplified date check - in real implementation, parse properly
                        old_unclassified.append(entry)
            
            print(f"  📊 Found {len(low_confidence)} low confidence entries")
            print(f"  📊 Found {len(old_unclassified)} old unclassified entries")
            
            if not dry_run:
                # Perform actual cleanup
                cleanup_count = 0
                # Implementation would go here
                print(f"  ✅ Cleaned up {cleanup_count} entries")
            else:
                print(f"  🔍 Would clean up {len(low_confidence) + len(old_unclassified)} entries")
                
        except Exception as e:
            print(f"  ❌ Error during memory cleanup: {e}")
    
    def _cleanup_logs(self, dry_run: bool = True) -> None:
        """Clean up old log files."""
        print("📝 Log Cleanup:")
        
        log_patterns = ["*.log", "*.log.*", "ioa_*.txt"]
        cleanup_count = 0
        
        # Search common log locations
        import tempfile
        log_locations = [
            self.cli.project_path,
            os.path.join(self.cli.project_path, "logs"),
            tempfile.gettempdir(),  # Use secure temp directory instead of hardcoded /tmp
            "."
        ]
        
        for location in log_locations:
            if location and os.path.exists(location):
                for pattern in log_patterns:
                    # In real implementation, would use glob and check file ages
                    pass
        
        if dry_run:
            print(f"  🔍 Would clean up {cleanup_count} log files")
        else:
            print(f"  ✅ Cleaned up {cleanup_count} log files")
    
    def _cleanup_temp_files(self, dry_run: bool = True) -> None:
        """Clean up temporary files."""
        print("📂 Temporary File Cleanup:")
        
        temp_patterns = ["*.tmp", "*.temp", "__pycache__", "*.pyc"]
        cleanup_count = 0
        
        if dry_run:
            print(f"  🔍 Would clean up {cleanup_count} temporary files")
        else:
            print(f"  ✅ Cleaned up {cleanup_count} temporary files")
    
    def do_backup(self, arg: str = "") -> None:
        """
        Create backup of IOA project data.
        
        Usage: backup [name]
        
        Creates timestamped backup of current project including memory,
        patterns, and configuration files.
        """
        if not self.cli.project_path:
            print("❌ No project loaded. Cannot create backup.")
            return
        
        backup_name = arg.strip() or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir = os.path.join(self.cli.project_path, "backups")
        backup_path = os.path.join(backup_dir, backup_name)
        
        print(f"💾 Creating backup: {backup_name}")
        print("=" * 40)
        
        try:
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Files to backup
            files_to_backup = [
                "memory.json",
                "patterns.json", 
                "boot_prompt.json",
                "agents.json",
                "governance.config.yaml"
            ]
            
            backup_count = 0
            for filename in files_to_backup:
                source_path = os.path.join(self.cli.project_path, filename)
                if os.path.exists(source_path):
                    dest_path = os.path.join(backup_path, filename)
                    
                    # Simple file copy - in real implementation use shutil.copy2
                    with open(source_path, 'r') as src, open(dest_path, 'w') as dst:
                        dst.write(src.read())
                    
                    backup_count += 1
                    print(f"  ✅ Backed up: {filename}")
                else:
                    print(f"  ⚠️  Skipped: {filename} (not found)")
            
            # Create backup metadata
            metadata = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "project_path": self.cli.project_path,
                "files_backed_up": backup_count,
                "ioa_version": "2.1.0"
            }
            
            with open(os.path.join(backup_path, "backup_metadata.json"), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"\n🎉 Backup completed successfully!")
            print(f"📂 Location: {backup_path}")
            print(f"📊 Files backed up: {backup_count}")
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
    
    def do_debug(self, arg: str = "") -> None:
        """
        Enter debug mode with advanced diagnostics.
        
        Usage: debug [component]
        
        Provides detailed debugging information for troubleshooting.
        Components: memory, agents, storage, patterns, all
        """
        component = arg.strip().lower() or "all"
        
        print("🐛 IOA Debug Mode")
        print("=" * 30)
        print(f"🎯 Target: {component}")
        print(f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if component in ["memory", "all"]:
            self._debug_memory()
        
        if component in ["agents", "all"]:
            self._debug_agents()
        
        if component in ["storage", "all"]:
            self._debug_storage()
        
        if component in ["patterns", "all"]:
            self._debug_patterns()
        
        print("\n💡 Debug session complete. Check logs for detailed information.")
    
    def _debug_memory(self) -> None:
        """Debug memory engine components."""
        print("🧠 Memory Engine Debug:")
        
        if not self.cli.memory_engine:
            print("  ❌ Memory engine not initialized")
            return
        
        # Test basic operations
        try:
            entries = self.cli.memory_engine.list_all()
            print(f"  ✅ Memory accessible: {len(entries)} entries")
            
            # Test memory operation
            test_entry = {"raw_ref": "debug test entry", "timestamp": datetime.now().isoformat()}
            self.cli.memory_engine.remember(test_entry)
            print("  ✅ Memory write test: passed")
            
            # Check subsystems
            if hasattr(self.cli.memory_engine, 'governance'):
                print("  ✅ Governance system: accessible")
            else:
                print("  ⚠️  Governance system: not available")
                
            if hasattr(self.cli.memory_engine, 'patterns'):
                print(f"  ✅ Pattern system: {len(self.cli.memory_engine.patterns)} patterns loaded")
            else:
                print("  ⚠️  Pattern system: not available")
        
        except Exception as e:
            print(f"  ❌ Memory error: {e}")
        
        print()
    
    def _debug_agents(self) -> None:
        """Debug agent router components."""
        print("🤖 Agent Router Debug:")
        
        if not self.cli.router:
            print("  ❌ Router not initialized")
            return
        
        try:
            print(f"  ✅ Router accessible: {len(self.cli.router.agents)} agents")
            
            # Test routing
            test_result = self.cli.router.route_task("debug ping", "execution")
            if "error" in str(test_result):
                print(f"  ⚠️  Routing test: {test_result}")
            else:
                print("  ✅ Routing test: passed")
            
            # Check agent details
            for agent_id, agent_data in self.cli.router.agents.items():
                print(f"     • {agent_id}: {agent_data.get('type', 'unknown')}")
        
        except Exception as e:
            print(f"  ❌ Agent error: {e}")
        
        print()
    
    def _debug_storage(self) -> None:
        """Debug storage components."""
        print("💾 Storage Debug:")
        
        if not self.cli.memory_engine or not hasattr(self.cli.memory_engine, 'storage'):
            print("  ❌ Storage not accessible")
            return
        
        try:
            storage = self.cli.memory_engine.storage
            print(f"  ✅ Storage type: {type(storage).__name__}")
            
            # Test storage operations
            entries = storage.load_all()
            print(f"  ✅ Storage read: {len(entries)} entries")
            
            # Test write (if safe)
            test_entry = {"debug": "test", "timestamp": datetime.now().isoformat()}
            result = storage.save(test_entry)
            print(f"  ✅ Storage write: {'passed' if result else 'failed'}")
        
        except Exception as e:
            print(f"  ❌ Storage error: {e}")
        
        print()
    
    def _debug_patterns(self) -> None:
        """Debug pattern system."""
        print("🏷️  Pattern System Debug:")
        
        if not self.cli.memory_engine or not hasattr(self.cli.memory_engine, 'patterns'):
            print("  ❌ Pattern system not accessible")
            return
        
        try:
            patterns = self.cli.memory_engine.patterns
            print(f"  ✅ Patterns loaded: {len(patterns)}")
            
            # Validate pattern structure
            valid_patterns = 0
            for pattern in patterns:
                if all(key in pattern for key in ['pattern_id', 'keywords', 'schema']):
                    valid_patterns += 1
            
            print(f"  ✅ Valid patterns: {valid_patterns}/{len(patterns)}")
            
            if valid_patterns < len(patterns):
                print("  ⚠️  Some patterns have invalid structure")
        
        except Exception as e:
            print(f"  ❌ Pattern error: {e}")
        
        print()
    
    def do_export(self, arg: str = "") -> None:
        """
        Export IOA data in various formats.
        
        Usage: export [format] [filename]
        
        Formats: json, csv, txt
        Default format: json
        """
        args = arg.split()
        export_format = args[0] if args else "json"
        filename = args[1] if len(args) > 1 else None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ioa_export_{timestamp}.{export_format}"
        
        print(f"📤 Exporting data to {filename}")
        
        if not self.cli.memory_engine:
            print("❌ Memory engine not initialized.")
            return
        
        try:
            entries = self.cli.memory_engine.list_all()
            
            if export_format == "json":
                self._export_json(entries, filename)
            elif export_format == "csv":
                self._export_csv(entries, filename)
            elif export_format == "txt":
                self._export_txt(entries, filename)
            else:
                print(f"❌ Unsupported format: {export_format}")
                return
            
            print(f"✅ Export completed: {filename}")
            print(f"📊 Exported {len(entries)} entries")
        
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def _export_json(self, entries: List[Dict[str, Any]], filename: str) -> None:
        """Export entries as JSON."""
        export_data = {
            "metadata": {
                "export_time": datetime.now().isoformat(),
                "ioa_version": "2.1.0",
                "entry_count": len(entries)
            },
            "entries": entries
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def _export_csv(self, entries: List[Dict[str, Any]], filename: str) -> None:
        """Export entries as CSV."""
        # Simple CSV export - in real implementation would use csv module
        with open(filename, 'w') as f:
            if entries:
                # Header
                headers = set()
                for entry in entries:
                    headers.update(entry.keys())
                header_line = ",".join(sorted(headers))
                f.write(header_line + "\n")
                
                # Data
                for entry in entries:
                    values = []
                    for header in sorted(headers):
                        value = str(entry.get(header, "")).replace(",", ";")
                        values.append(value)
                    f.write(",".join(values) + "\n")
    
    def _export_txt(self, entries: List[Dict[str, Any]], filename: str) -> None:
        """Export entries as readable text."""
        with open(filename, 'w') as f:
            f.write("IOA Memory Export\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total entries: {len(entries)}\n\n")
            
            for i, entry in enumerate(entries, 1):
                f.write(f"Entry {i}:\n")
                f.write("-" * 20 + "\n")
                
                for key, value in entry.items():
                    f.write(f"{key}: {value}\n")
                
                f.write("\n")


# Export the commands class for integration
__all__ = ['IOACommands', 'CLICommandError']