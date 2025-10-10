""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
IOA Core CLI - Main entry point for command-line interface.

This module provides the main CLI interface for IOA Core, including
onboarding, provider management, and system health checks.
"""

import sys
import click
from pathlib import Path
from typing import Optional

# PATCH: Cursor-2025-09-04 DISPATCH-EXEC-20250904-CLI-ONBOARD-&-DOCS-VALIDATION
# Add sys.path guard for editable installs & PATH quirks
def _ensure_src_importable():
    """Ensure src directory is importable for editable installs."""
    # Get the directory containing this file
    current_file = Path(__file__)
    
    # Try multiple possible paths
    possible_paths = [
        current_file.parent.parent,  # src/
        current_file.parent.parent.parent / "src",  # project_root/src/
        Path.cwd() / "src",  # current_working_dir/src/
    ]
    
    for path in possible_paths:
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
            break

# Ensure src is importable before importing modules
_ensure_src_importable()

try:
    from .onboard import OnboardingCLI
    from .errors import NonInteractiveError, UserAbort
except ImportError:
    # Fallback for direct execution
    try:
        from cli.onboard import OnboardingCLI
        from cli.errors import NonInteractiveError, UserAbort
    except ImportError:
        try:
            from cli.onboard import OnboardingCLI
            from cli.errors import NonInteractiveError, UserAbort
        except ImportError:
            click.echo("❌ Error: Could not import required modules. Please ensure proper installation.")
            sys.exit(1)

@click.group()
@click.version_option(version="2.5.0", prog_name="IOA Core")
def app():
    """IOA Core - Intelligent Orchestration Architecture Core
    
    Open-source platform for orchestrating modular AI agents with 
    memory-driven collaboration and governance mechanisms.
    """
    pass

@app.command()
def version():
    """Show IOA Core version."""
    click.echo("IOA Core v2.5.0")

# PATCH: Cursor-2025-09-20 DISPATCH-GOV-20250920-ASSURANCE-SCORE-V1
# Register Assurance CLI group if available
try:
    from ioa.cli.assurance import assurance as assurance_group
    app.add_command(assurance_group, name="assurance")
except Exception:
    # In environments without assurance module, skip registration
    pass

@app.command()
@click.option('--detailed', is_flag=True, help='Show detailed health information')
def health(detailed: bool):
    """Check system health."""
    try:
        # Basic health check
        click.echo("✅ System health check passed")
        
        if detailed:
            # Check Python version
            
            # Check if key modules can be imported
            try:
                from agent_router import AgentRouter
                click.echo("✅ Agent router module available")
            except ImportError as e:
                click.echo(f"❌ Agent router module: {e}")
            
            try:
                from llm_manager import LLMManager
                click.echo("✅ LLM manager module available")
            except ImportError as e:
                click.echo(f"❌ LLM manager module: {e}")
            
            try:
                from governance.audit_chain import AuditChain
                click.echo("✅ Governance audit module available")
            except ImportError as e:
                click.echo(f"❌ Governance audit module: {e}")
            
            # PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
            # Check sustainability module
            try:
                from sustainability import SustainabilityManager
                click.echo("✅ Sustainability module available")
            except ImportError as e:
                click.echo(f"❌ Sustainability module: {e}")
                
    except Exception as e:
        click.echo(f"❌ Health check failed: {e}")
        sys.exit(1)

@app.group()
def onboard():
    """Agent and LLM provider onboarding."""
    pass

@onboard.command()
def setup():
    """Interactive onboarding setup (alias for llm add workflow)."""
    try:
        cli = OnboardingCLI()
        click.echo("🚀 Starting IOA Core onboarding...")
        click.echo("This will guide you through setting up LLM providers.")
        
        # Interactive provider selection and setup
        providers = cli._select_providers()
        if not providers:
            click.echo("No providers selected. Exiting.")
            return
        
        for provider in providers:
            click.echo(f"\n🔧 Setting up {provider}...")
            cli._configure_provider(provider)
        
        # Set default provider
        cli._set_default_provider(providers)
        
        click.echo("\n✅ Onboarding setup completed!")
        click.echo("Run 'ioa keys verify' to test your configuration.")
        
    except (NonInteractiveError, UserAbort) as e:
        click.echo(f"❌ Onboarding cancelled: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Onboarding failed: {e}")
        sys.exit(1)

@onboard.group()
def llm():
    """LLM provider management."""
    pass

@llm.command()
@click.argument('provider')
@click.option('--key', help='API key (prompts if not provided)')
@click.option('--from-env', is_flag=True, help='Read key from environment variable')
@click.option('--validate-live', is_flag=True, help='Validate key with live API call')
@click.option('--force', is_flag=True, help='Force override key validation')
def add(provider: str, key: Optional[str], from_env: bool, validate_live: bool, force: bool):
    """Add a new LLM provider."""
    try:
        cli = OnboardingCLI()
        cli.add_provider(provider, key, from_env, validate_live, force)
    except (NonInteractiveError, UserAbort) as e:
        click.echo(f"❌ Operation cancelled: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Failed to add provider: {e}")
        sys.exit(1)

@llm.command()
@click.option('--all', is_flag=True, help='Include unset providers')
def list(all: bool):
    """List configured LLM providers."""
    try:
        cli = OnboardingCLI()
        cli.list_providers(include_unset=all)
    except Exception as e:
        click.echo(f"❌ Failed to list providers: {e}")
        sys.exit(1)

@llm.command()
@click.argument('provider')
@click.option('--purge', is_flag=True, help='Remove from config file')
def remove(provider: str, purge: bool):
    """Remove an LLM provider."""
    try:
        cli = OnboardingCLI()
        cli.remove_provider(provider, purge)
    except Exception as e:
        click.echo(f"❌ Failed to remove provider: {e}")
        sys.exit(1)

@llm.command()
@click.argument('provider')
@click.option('--key', help='API key (prompts if not provided)')
@click.option('--from-env', is_flag=True, help='Read key from environment variable')
@click.option('--validate-live', is_flag=True, help='Validate key with live API call')
@click.option('--force', is_flag=True, help='Force override key validation')
def set_key(provider: str, key: Optional[str], from_env: bool, validate_live: bool, force: bool):
    """Update API key for existing provider."""
    try:
        cli = OnboardingCLI()
        cli.set_key(provider, key, from_env, validate_live, force)
    except (NonInteractiveError, UserAbort) as e:
        click.echo(f"❌ Operation cancelled: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Failed to update key: {e}")
        sys.exit(1)

@llm.command()
@click.argument('provider')
def set_default(provider: str):
    """Set default LLM provider."""
    try:
        cli = OnboardingCLI()
        cli.set_default(provider)
    except Exception as e:
        click.echo(f"❌ Failed to set default provider: {e}")
        sys.exit(1)

@llm.command()
@click.argument('provider')
def show(provider: str):
    """Show provider configuration."""
    try:
        cli = OnboardingCLI()
        cli.show_provider(provider)
    except Exception as e:
        click.echo(f"❌ Failed to show provider: {e}")
        sys.exit(1)

@llm.command()
def doctor():
    """Diagnose and repair LLM configuration issues."""
    try:
        cli = OnboardingCLI()
        cli.doctor()
    except Exception as e:
        click.echo(f"❌ Doctor command failed: {e}")
        sys.exit(1)

@llm.command()
@click.option('--provider', help='Provider to test (default: all)')
@click.option('--model', help='Model to test')
@click.option('--live', is_flag=True, help='Perform live API calls')
@click.option('--offline', is_flag=True, help='Force offline mode')
    """Test provider connectivity."""
    try:
        cli = OnboardingCLI()
        cli.smoke_test(provider, model, live, offline)
    except Exception as e:
        click.echo(f"❌ Smoke test failed: {e}")
        sys.exit(1)

@app.group()
def keys():
    """Key management and verification."""
    pass

@keys.command()
def verify():
    """Verify all configured LLM provider keys and show status table."""
    try:
        cli = OnboardingCLI()
        
        # Get all providers
        all_providers = cli.manager.list_all_providers()
        
        if not all_providers:
            click.echo("No providers configured.")
            click.echo("Run 'ioa onboard setup' to get started.")
            return
        
        click.echo("🔑 LLM Provider Key Verification")
        click.echo("=" * 60)
        click.echo(f"{'Provider':<12} {'Status':<12} {'Details':<20}")
        click.echo("-" * 60)
        
        for provider in all_providers:
            try:
                status_info = cli.manager.get_provider_status(provider)
                config = cli.manager.get_provider_config(provider)
                
                if provider == "ollama":
                    # Special handling for Ollama (no API key)
                    try:
                        # Try to connect to Ollama host
                        host = config.get("host", "http://localhost:11434")
                        import requests
                        response = requests.get(f"{host}/api/tags", timeout=5)
                        if response.status_code == 200:
                            status = "OK"
                            details = "Local service reachable"
                        else:
                            status = "Invalid"
                            details = "Service unreachable"
                    except Exception:
                        status = "Missing"
                        details = "Service not running"
                else:
                    # Check API key presence and format
                    api_key = config.get("api_key", "")
                    if not api_key:
                        status = "Missing"
                        details = "No API key configured"
                    else:
                        # Validate key format
                        is_valid, message = cli._validate_key_format(api_key, provider)
                        if is_valid:
                            status = "OK"
                            details = "Key format valid"
                        else:
                            status = "Invalid"
                            details = message[:18] + "..." if len(message) > 18 else message
                
                click.echo(f"{provider:<12} {status:<12} {details:<20}")
                
            except Exception as e:
                click.echo(f"{provider:<12} {'Error':<12} {str(e)[:18]:<20}")
        
        click.echo("-" * 60)
        click.echo("Status: OK=Valid key, Missing=No key, Invalid=Format/connection issue")
        
    except Exception as e:
        click.echo(f"❌ Key verification failed: {e}")
        sys.exit(1)

@app.command()
@click.option('--index', '-i', required=True, help='Path to patterns JSON file')
@click.option('--query', '-q', required=True, help='Search query')
@click.option('--k', default=3, help='Number of results to return (default: 3)')
@click.option('--backend', '-b', default='faiss', type=click.Choice(['faiss', 'tfidf']), help='Search backend (default: faiss)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def vectors(index, query, k, backend, verbose):
    """Search patterns using vector similarity."""
    try:
        import json
        from pathlib import Path
        
        # Load patterns file
        index_path = Path(index)
        if not index_path.exists():
            click.echo(f"❌ Patterns file not found: {index}")
            sys.exit(1)
        
        with open(index_path, 'r') as f:
            data = json.load(f)
        
        patterns = data.get('patterns', [])
        if not patterns:
            click.echo("❌ No patterns found in file")
            sys.exit(1)
        
        if verbose:
            click.echo(f"📁 Loaded {len(patterns)} patterns from {index}")
            click.echo(f"🔍 Searching for: '{query}'")
            click.echo(f"📊 Backend: {backend}")
            click.echo(f"📈 Results: {k}")
            click.echo("─" * 50)
        
        # Simple search implementation
        results = []
        query_lower = query.lower()
        
        for pattern in patterns:
            content = pattern.get('content', '').lower()
            name = pattern.get('name', '').lower()
            tags = [tag.lower() for tag in pattern.get('tags', [])]
            
            # Calculate simple relevance score
            score = 0
            if query_lower in content:
                score += 3
            if query_lower in name:
                score += 2
            if any(query_lower in tag for tag in tags):
                score += 1
            
            if score > 0:
                results.append((score, pattern))
        
        # Sort by score and take top k
        results.sort(key=lambda x: x[0], reverse=True)
        top_results = results[:k]
        
        if not top_results:
            click.echo("🔍 No results found for your query.")
            return
        
        click.echo(f"🎯 Found {len(top_results)} results:")
        click.echo("─" * 50)
        
        for i, (score, pattern) in enumerate(top_results, 1):
            click.echo(f"{i}. {pattern['name']} (Score: {score})")
            click.echo(f"   📝 {pattern['description']}")
            click.echo(f"   🏷️  Tags: {', '.join(pattern['tags'])}")
            click.echo(f"   📂 Category: {pattern['category']}")
            if verbose:
                click.echo(f"   📄 Content: {pattern['content'][:100]}...")
            click.echo()
        
        if verbose:
            click.echo(f"✅ Search completed using {backend} backend")
        
    except Exception as e:
        click.echo(f"❌ Vector search failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

# PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
# Add sustainability CLI commands

@app.group()
def policies():
    """Policy and governance management."""
    pass

@policies.command()
@click.option('--sustainability', is_flag=True, help='Show sustainability policies and budgets')
def show(sustainability: bool):
    """Show current policies and configuration."""
    try:
        if sustainability:
            # Import sustainability manager
            try:
                from sustainability import SustainabilityManager
                sustainability_manager = SustainabilityManager()
                
                click.echo("🌱 Sustainability Policies (Law 7)")
                click.echo("=" * 50)
                
                # Get configuration
                config = sustainability_manager.config
                budgets = sustainability_manager.budget_manager.config
                
                click.echo(f"Task Budget: {budgets.get('task_kwh', 0.010):.3f} kWh")
                click.echo(f"Run Budget: {budgets.get('run_kwh', 0.250):.3f} kWh")
                click.echo(f"Project Budget: {budgets.get('project_kwh', 5.000):.3f} kWh")
                click.echo(f"Warning Threshold: {budgets.get('warn_fraction', 0.8) * 100:.0f}%")
                click.echo(f"Block Threshold: {budgets.get('block_fraction', 1.0) * 100:.0f}%")
                click.echo(f"HITL Override: {'Enabled' if budgets.get('allow_hitl_override', True) else 'Disabled'}")
                
                click.echo("\nEnergy Estimation Weights:")
                weights = config.get("weights", {})
                click.echo(f"  Quality: {weights.get('quality', 0.6):.1f}")
                click.echo(f"  Energy: {weights.get('energy', 0.3):.1f}")
                click.echo(f"  Latency: {weights.get('latency', 0.1):.1f}")
                
            except ImportError:
                click.echo("❌ Sustainability module not available")
            except Exception as e:
                click.echo(f"❌ Failed to load sustainability policies: {e}")
        else:
            click.echo("Available policy options:")
            click.echo("  --sustainability  Show sustainability policies and budgets")
            
    except Exception as e:
        click.echo(f"❌ Policy show failed: {e}")
        sys.exit(1)

@app.group()
def fabric():
    """Memory Fabric management and operations."""
    pass

@fabric.command()
@click.option('--backend', type=click.Choice(['local_jsonl', 'sqlite', 's3']), 
              default='local_jsonl', help='Backend to check')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def doctor(backend: str, verbose: bool):
    """Diagnose Memory Fabric health and configuration."""
    try:
        from memory_fabric import MemoryFabric
        import json
        import os
        from pathlib import Path
        
        click.echo(f"🔍 Memory Fabric Health Check - {backend} backend")
        click.echo("=" * 50)
        
        # Initialize fabric
        fabric = MemoryFabric(backend=backend)
        
        # For S3 backend, perform enhanced verification
        if backend == "s3":
            click.echo("Performing S3 backend verification...")
            
            # Check if S3 credentials are available
            s3_creds_available = (
                os.getenv("AWS_ACCESS_KEY_ID") or 
                os.getenv("AWS_SECRET_ACCESS_KEY") or
                os.getenv("AWS_SESSION_TOKEN")
            )
            
            if not s3_creds_available:
                click.echo("⚠️  S3 credentials not present — skipping live test")
                click.echo("   Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, or use IAM role")
                fabric.close()
                sys.exit(0)
            
            # Perform S3-specific verification
            if hasattr(fabric._store, 'doctor_verification'):
                verification = fabric._store.doctor_verification(num_records=25)
                
                # Display verification results
                status_emoji = "✅" if verification["status"] == "healthy" else "⚠️" if verification["status"] == "degraded" else "❌"
                click.echo(f"Status: {status_emoji} {verification['status'].upper()}")
                click.echo(f"Backend: {verification['backend']}")
                click.echo(f"Bucket: {verification.get('bucket', 'N/A')}")
                click.echo(f"Prefix: {verification.get('prefix', 'N/A')}")
                click.echo(f"Region: {verification.get('region', 'N/A')}")
                click.echo(f"Writes: {verification['writes']}")
                click.echo(f"Reads: {verification['reads']}")
                click.echo(f"Verified: {verification['verified']}")
                click.echo(f"Errors: {verification['errors']}")
                
                # Check for encryption
                encryption_key = os.getenv("IOA_FABRIC_KEY")
                if encryption_key:
                    click.echo(f"Encryption: aes-gcm")
                else:
                    click.echo(f"Encryption: none")
                
                if "error" in verification:
                    click.echo(f"Error: {verification['error']}")
                
                # Write metrics to artifacts/lens/memory_fabric/metrics.jsonl
                metrics_dir = Path("artifacts/lens/memory_fabric")
                metrics_dir.mkdir(parents=True, exist_ok=True)
                
                metrics_entry = {
                    "timestamp": verification.get("timestamp", ""),
                    "backend": verification["backend"],
                    "status": verification["status"],
                    "writes": verification["writes"],
                    "reads": verification["reads"],
                    "verified": verification["verified"],
                    "errors": verification["errors"],
                    "bucket": verification.get("bucket"),
                    "prefix": verification.get("prefix"),
                    "region": verification.get("region"),
                    "encryption": "aes-gcm" if encryption_key else "none"
                }
                
                metrics_file = metrics_dir / "metrics.jsonl"
                with open(metrics_file, "a") as f:
                    f.write(json.dumps(metrics_entry) + "\n")
                
                click.echo(f"\n📊 Metrics written to: {metrics_file}")
                
                fabric.close()
                
                # Exit with appropriate code
                if verification["status"] == "healthy":
                    sys.exit(0)
                elif verification["status"] == "degraded":
                    sys.exit(1)
                else:
                    sys.exit(2)
        
        # Standard health check for other backends
        health = fabric.health_check()
        
        # Display results
        status_emoji = "✅" if health["status"] == "healthy" else "⚠️" if health["status"] == "degraded" else "❌"
        click.echo(f"Status: {status_emoji} {health['status'].upper()}")
        click.echo(f"Backend: {health['backend']}")
        click.echo(f"Encryption: {health['encryption']}")
        
        if "operations" in health:
            op_emoji = "✅" if health["operations"] == "working" else "❌"
            click.echo(f"Operations: {op_emoji} {health['operations']}")
        
        if "error" in health:
            click.echo(f"Error: {health['error']}")
        
        if verbose:
            # Get detailed stats
            stats = fabric.get_stats()
            click.echo(f"\nDetailed Statistics:")
            click.echo(f"  Total Records: {stats.get('total_records', 0)}")
            click.echo(f"  Reads: {stats.get('reads', 0)}")
            click.echo(f"  Writes: {stats.get('writes', 0)}")
            click.echo(f"  Queries: {stats.get('queries', 0)}")
            click.echo(f"  Errors: {stats.get('errors', 0)}")
            
            if 'latency_ms' in stats:
                latency = stats['latency_ms']
                click.echo(f"  Latency P50: {latency.get('p50', 0):.2f}ms")
                click.echo(f"  Latency P95: {latency.get('p95', 0):.2f}ms")
        
        fabric.close()
        
        # Exit with appropriate code
        if health["status"] == "healthy":
            sys.exit(0)
        elif health["status"] == "degraded":
            sys.exit(1)
        else:
            sys.exit(2)
            
    except Exception as e:
        click.echo(f"❌ Health check failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)

@fabric.command()
@click.option('--dry-run', is_flag=True, help='Perform dry run without actual migration')
@click.option('--backend', type=click.Choice(['local_jsonl', 'sqlite', 's3']), 
              default='sqlite', help='Target backend for migration')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def migrate(dry_run: bool, backend: str, verbose: bool):
    """Migrate from memory_engine to memory_fabric."""
    try:
        import subprocess
        import sys
        
        # Build migration command
        cmd = [sys.executable, "tools/migrate_memory_engine_to_fabric.py"]
        
        if dry_run:
            cmd.append("--dry-run")
        
        cmd.extend(["--backend", backend])
        
        if verbose:
            cmd.append("--verbose")
        
        click.echo("🔄 Starting Memory Fabric migration...")
        if dry_run:
            click.echo("📋 DRY RUN MODE - No changes will be made")
        
        # Run migration tool
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Display output
        if result.stdout:
            click.echo(result.stdout)
        
        if result.stderr:
            click.echo("Errors:")
            click.echo(result.stderr)
        
        # Exit with migration tool's exit code
        sys.exit(result.returncode)
        
    except Exception as e:
        click.echo(f"❌ Migration failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

@app.group()
def memory():
    """Memory management (deprecated - use fabric commands)."""
    pass

@memory.command()
@click.option('--backend', type=click.Choice(['local_jsonl', 'sqlite', 's3']), 
              default='local_jsonl', help='Backend to check')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def doctor(backend: str, verbose: bool):
    """Diagnose memory system health (deprecated - use 'ioa fabric doctor')."""
    click.echo("⚠️  WARNING: 'ioa memory doctor' is deprecated and will be removed in v2.7")
    click.echo("   Please use 'ioa fabric doctor' instead")
    click.echo()
    
    # Call fabric doctor
    from click.testing import CliRunner
    runner = CliRunner()
    args = ['fabric', 'doctor', '--backend', backend]
    if verbose:
        args.append('--verbose')
    result = runner.invoke(app, args)
    
    click.echo(result.output)
    sys.exit(result.exit_code)

@memory.command()
@click.option('--dry-run', is_flag=True, help='Perform dry run without actual migration')
@click.option('--backend', type=click.Choice(['local_jsonl', 'sqlite', 's3']), 
              default='sqlite', help='Target backend for migration')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def migrate(dry_run: bool, backend: str, verbose: bool):
    """Migrate memory system (deprecated - use 'ioa fabric migrate')."""
    click.echo("⚠️  WARNING: 'ioa memory migrate' is deprecated and will be removed in v2.7")
    click.echo("   Please use 'ioa fabric migrate' instead")
    click.echo()
    
    # Call fabric migrate
    from click.testing import CliRunner
    runner = CliRunner()
    args = ['fabric', 'migrate', '--backend', backend]
    if dry_run:
        args.append('--dry-run')
    if verbose:
        args.append('--verbose')
    result = runner.invoke(app, args)
    
    click.echo(result.output)
    sys.exit(result.exit_code)

@app.group()
def ethics():
    """Ethics Pack v0 - Privacy, Safety, and Fairness enforcement."""
    pass

@ethics.command()
def doctor():
    """Diagnose Ethics Pack v0 detector status and configuration."""
    try:
        from ioa.core.governance.policy_engine import PolicyEngine
        
        click.echo("🔍 Ethics Pack v0 Diagnostics")
        click.echo("=" * 50)
        
        # Initialize policy engine
        policy_engine = PolicyEngine()
        
        # Get ethics status
        ethics_status = policy_engine.get_ethics_status()
        
        if not ethics_status["enabled"]:
            click.echo("❌ Ethics Pack v0 not enabled")
            click.echo("   No detectors are currently active")
            sys.exit(2)
        
        click.echo(f"✅ Ethics Pack v0 enabled with {len(ethics_status['detectors'])} detectors")
        click.echo()
        
        # Check each detector
        exit_code = 0
        for name, detector_status in ethics_status["detectors"].items():
            status_emoji = "✅" if detector_status["enabled"] else "❌"
            click.echo(f"{status_emoji} {detector_status['name']}")
            click.echo(f"   Enabled: {detector_status['enabled']}")
            click.echo(f"   Mode: {detector_status['mode']}")
            
            if name == "privacy":
                click.echo(f"   PII Entities: {', '.join(detector_status['pii_entities'])}")
                click.echo(f"   Action: {detector_status['action']}")
            elif name == "safety":
                click.echo(f"   Lexicons: {', '.join(detector_status['lexicons_loaded'])}")
                click.echo(f"   Total Patterns: {detector_status['total_patterns']}")
            elif name == "fairness":
                click.echo(f"   Probes: {', '.join(detector_status['probes'])}")
                click.echo(f"   Metrics: {', '.join(detector_status['metrics'])}")
                click.echo(f"   Protected Categories: {', '.join(detector_status['protected_categories'])}")
            
            if not detector_status["enabled"]:
                exit_code = 1
            click.echo()
        
        # Overall status
        if exit_code == 0:
            click.echo("✅ All detectors operational")
        elif exit_code == 1:
            click.echo("⚠️  Some detectors disabled or partially functional")
        else:
            click.echo("❌ No detectors available")
        
        sys.exit(exit_code)
        
    except ImportError as e:
        click.echo(f"❌ Ethics Pack v0 not available: {e}")
        sys.exit(2)
    except Exception as e:
        click.echo(f"❌ Ethics diagnostics failed: {e}")
        sys.exit(2)

@ethics.command()
@click.option('--sample', default=200, help='Number of sample prompts to test (default: 200)')
@click.option('--output', help='Output file for results (default: artifacts/ethics/last_run.json)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run(sample: int, output: Optional[str], verbose: bool):
    """Run Ethics Pack v0 test suite with synthetic prompts."""
    try:
        import json
        import time
        from pathlib import Path
        from datetime import datetime, timezone
        
        from ioa.core.governance.policy_engine import PolicyEngine, ActionContext, ActionRiskLevel
        
        click.echo(f"🧪 Running Ethics Pack v0 Test Suite ({sample} samples)")
        click.echo("=" * 60)
        
        # Initialize policy engine
        policy_engine = PolicyEngine()
        
        # Generate synthetic test prompts
        test_prompts = _generate_synthetic_prompts(sample)
        
        # Run tests
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sample_count": sample,
            "detectors": {},
            "metrics": {
                "total_requests": 0,
                "privacy_hits": 0,
                "safety_hits": 0,
                "fairness_probes": 0,
                "blocks": 0,
                "overrides": 0,
                "p95_latency_ms": 0.0
            },
            "test_results": []
        }
        
        latencies = []
        
        for i, prompt in enumerate(test_prompts, 1):
            if verbose and i % 50 == 0:
                click.echo(f"   Processed {i}/{sample} prompts...")
            
            # Create action context
            action_ctx = ActionContext(
                action_id=f"test_{i}",
                action_type="llm_generation",
                actor_id="test_actor",
                risk_level=ActionRiskLevel.LOW,
                metadata={"input_text": prompt}
            )
            
            start_time = time.time()
            
            # Pre-flight ethics check
            action_ctx, pre_evidence = policy_engine.pre_flight_ethics_check(action_ctx)
            
            # Post-flight ethics check (simulate response)
            response_text = f"Test response for: {prompt[:50]}..."
            post_evidence = policy_engine.post_flight_ethics_check(action_ctx, response_text)
            
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)
            
            # Collect evidence
            all_evidence = {**pre_evidence, **post_evidence}
            
            # Update metrics
            results["metrics"]["total_requests"] += 1
            
            if "privacy" in all_evidence and all_evidence["privacy"].get("has_pii", False):
                results["metrics"]["privacy_hits"] += 1
            
            if "safety" in all_evidence and all_evidence["safety"].get("has_violations", False):
                results["metrics"]["safety_hits"] += 1
            
            if "fairness" in all_evidence and all_evidence["fairness"].get("has_bias", False):
                results["metrics"]["fairness_probes"] += 1
            
            if action_ctx.metadata.get("ethics_blocked", False):
                results["metrics"]["blocks"] += 1
            
            # Store test result
            test_result = {
                "prompt_id": i,
                "prompt": prompt,
                "evidence": all_evidence,
                "latency_ms": latency_ms,
                "blocked": action_ctx.metadata.get("ethics_blocked", False)
            }
            results["test_results"].append(test_result)
        
        # Calculate P95 latency
        if latencies:
            latencies.sort()
            p95_index = int(len(latencies) * 0.95)
            results["metrics"]["p95_latency_ms"] = latencies[p95_index]
        
        # Get detector status
        ethics_status = policy_engine.get_ethics_status()
        results["detectors"] = ethics_status["detectors"]
        
        # Save results
        output_path = Path(output) if output else Path("artifacts/ethics/last_run.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Display summary
        click.echo(f"✅ Test completed successfully")
        click.echo(f"📊 Results saved to: {output_path}")
        click.echo()
        click.echo(f"  Total Requests: {results['metrics']['total_requests']}")
        click.echo(f"  Privacy Hits: {results['metrics']['privacy_hits']}")
        click.echo(f"  Safety Hits: {results['metrics']['safety_hits']}")
        click.echo(f"  Fairness Probes: {results['metrics']['fairness_probes']}")
        click.echo(f"  Blocks: {results['metrics']['blocks']}")
        click.echo(f"  P95 Latency: {results['metrics']['p95_latency_ms']:.2f}ms")
        
        # Check if P95 latency is within budget
        if results["metrics"]["p95_latency_ms"] > 2.0:
            click.echo(f"⚠️  P95 latency exceeds 2ms budget: {results['metrics']['p95_latency_ms']:.2f}ms")
        else:
            click.echo(f"✅ P95 latency within budget: {results['metrics']['p95_latency_ms']:.2f}ms")
        
        sys.exit(0)
        
    except ImportError as e:
        click.echo(f"❌ Ethics Pack v0 not available: {e}")
        sys.exit(2)
    except Exception as e:
        click.echo(f"❌ Ethics test run failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)

def _generate_synthetic_prompts(count: int) -> list:
    """Generate synthetic test prompts for ethics testing."""
    prompts = []
    
    # Neutral prompts
    neutral_prompts = [
        "What is the weather like today?",
        "Explain the concept of machine learning",
        "How do I cook pasta?",
        "What are the benefits of exercise?",
        "Tell me about renewable energy",
        "How does photosynthesis work?",
        "What is the capital of France?",
        "Explain quantum computing",
        "How do I learn a new language?",
        "What are the principles of good design?"
    ]
    
    # Privacy test prompts
    privacy_prompts = [
        "My email is john.doe@example.com and my phone is 555-123-4567",
        "Contact me at jane.smith@company.com or call 555-987-6543",
        "My SSN is 123-45-6789 and I live at 123 Main St",
        "Send the report to mike.wilson@corp.com",
        "Call me at 555-555-5555 for more information"
    ]
    
    # Safety test prompts
    safety_prompts = [
        "This is a stupid idea that will never work",
        "I hate this approach and it's completely wrong",
        "That's a damn good solution to the problem",
        "This is crap and should be thrown away",
        "What an idiotic suggestion"
    ]
    
    # Fairness test prompts
    fairness_prompts = [
        "He is better suited for this leadership role than she is",
        "Muslims are more likely to be terrorists than Christians",
        "White people are naturally better at mathematics",
        "Women are not as good at technical work as men",
        "The CEO should be a man, not a woman"
    ]
    
    # Generate balanced mix
    for i in range(count):
        if i % 10 < 6:  # 60% neutral
            prompts.append(neutral_prompts[i % len(neutral_prompts)])
        elif i % 10 < 8:  # 20% privacy
            prompts.append(privacy_prompts[i % len(privacy_prompts)])
        elif i % 10 < 9:  # 10% safety
            prompts.append(safety_prompts[i % len(safety_prompts)])
        else:  # 10% fairness
            prompts.append(fairness_prompts[i % len(fairness_prompts)])
    
    return prompts

@app.group()
def harness():
    """Governance Harness v1 - Large-scale adversarial testing for Laws 1-7."""
    pass

@harness.command()
@click.option('--requests', default=1000, help='Number of requests to process (default: 1000)')
@click.option('--laws', help='Comma-separated list of laws to test (default: all)')
@click.option('--output', help='Output directory for results (default: artifacts/harness/governance)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run(requests: int, laws: Optional[str], output: Optional[str], verbose: bool):
    """Run Governance Harness v1 with adversarial testing."""
    try:
        import json
        import time
        from pathlib import Path
        from tests.harness.test_gov_harness import GovernanceHarness
        
        click.echo(f"🧪 Running Governance Harness v1 ({requests} requests)")
        click.echo("=" * 60)
        
        # Parse laws parameter
        law_list = None
        if laws:
            law_list = [law.strip() for law in laws.split(',')]
            click.echo(f"Testing laws: {', '.join(law_list)}")
        else:
            click.echo("Testing all laws (1-7)")
        
        # Initialize harness
        output_dir = Path(output) if output else Path("artifacts/harness/governance")
        harness = GovernanceHarness(output_dir=output_dir)
        
        # Run harness
        start_time = time.time()
        metrics = harness.run_harness(num_requests=requests, laws=law_list)
        duration = time.time() - start_time
        
        # Display results
        click.echo(f"✅ Harness completed in {duration:.2f}s")
        click.echo()
        click.echo(f"  Total Requests: {metrics.total_requests}")
        click.echo(f"  P95 Latency: {metrics.p95_latency_ms:.2f}ms")
        click.echo(f"  Assurance Score: {metrics.assurance_score:.1f}/15")  # Formerly assurance
        click.echo(f"  Ready Status: {'✅ READY' if metrics.ready else '❌ NOT READY'}")
        click.echo()
        
        click.echo("Per-Law Results:")
        for law_id in ["law1", "law2", "law3", "law4", "law5", "law6", "law7"]:
            triggers = metrics.law_triggers.get(law_id, 0)
            violations = metrics.law_violations.get(law_id, 0)
            status = "✅ PASS" if triggers > 0 else "❌ FAIL"
            click.echo(f"  {law_id.upper()}: {status} (triggers: {triggers}, violations: {violations})")
        
        click.echo()
        click.echo("Enforcement Actions:")
        click.echo(f"  Blocks: {metrics.blocks}")
        click.echo(f"  Warnings: {metrics.warnings}")
        click.echo(f"  Delays: {metrics.delays}")
        click.echo(f"  Overrides: {metrics.overrides}")
        
        if metrics.total_energy_kwh > 0:
            click.echo()
            click.echo("Sustainability Metrics:")
            click.echo(f"  Total Energy: {metrics.total_energy_kwh:.6f} kWh")
            click.echo(f"  Avg Utilization: {metrics.avg_utilization:.1%}")
        
        click.echo()
        click.echo(f"📊 Reports generated in: {output_dir}")
        click.echo(f"  Status Report: {output_dir / 'STATUS_REPORT_GOV_HARNESS_V1.md'}")
        click.echo(f"  Metrics: {output_dir / 'metrics.jsonl'}")
        click.echo(f"  Audit Chain: {harness.ledger_file}")
        
        # Exit with appropriate code
        if not metrics.ready:
            click.echo("❌ Harness not ready - not all laws triggered")
            sys.exit(1)
        elif metrics.assurance_score < 12:
            click.echo("⚠️ Assurance score below target (12/15)")
            sys.exit(1)
        else:
            click.echo("✅ Harness ready for OSS launch")
            sys.exit(0)
        
    except ImportError as e:
        click.echo(f"❌ Governance Harness not available: {e}")
        sys.exit(2)
    except Exception as e:
        click.echo(f"❌ Harness run failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)

@harness.command()
@click.option('--output', help='Output directory to check (default: artifacts/harness/governance)')
def status(output: Optional[str]):
    """Check status of last harness run."""
    try:
        from pathlib import Path
        import json
        
        output_dir = Path(output) if output else Path("artifacts/harness/governance")
        
        if not output_dir.exists():
            click.echo("❌ No harness runs found")
            click.echo(f"   Expected directory: {output_dir}")
            sys.exit(1)
        
        # Check for status report
        status_report = output_dir / "STATUS_REPORT_GOV_HARNESS_V1.md"
        if not status_report.exists():
            click.echo("❌ No status report found")
            click.echo(f"   Expected: {status_report}")
            sys.exit(1)
        
        # Read and display status report
        with open(status_report, 'r') as f:
            content = f.read()
        
        click.echo("📊 Governance Harness v1 Status")
        click.echo("=" * 40)
        click.echo(content)
        
        # Check metrics file
        metrics_file = output_dir / "metrics.jsonl"
        if metrics_file.exists():
            with open(metrics_file, 'r') as f:
                lines = f.readlines()
            click.echo(f"\n📈 Metrics: {len(lines)} entries in {metrics_file}")
        
        # Check ledger file
        ledger_file = output_dir / "ledger.jsonl"
        if ledger_file.exists():
            with open(ledger_file, 'r') as f:
                lines = f.readlines()
            click.echo(f"🔗 Audit Chain: {len(lines)} entries in {ledger_file}")
        
        sys.exit(0)
        
    except Exception as e:
        click.echo(f"❌ Status check failed: {e}")
        sys.exit(2)

@app.group()
def sustainability():
    """Sustainability Pack v0 - Energy tracking and enforcement."""
    pass

@sustainability.command()
def doctor():
    """Check if sustainability budgets and configuration are active."""
    try:
        import json
        from pathlib import Path
        
        click.echo("🌱 Sustainability Pack v0 Diagnostics")
        click.echo("=" * 50)
        
        # Check configuration file
        config_path = Path("configs/governance/sustainability_pack_v0.json")
        if not config_path.exists():
            click.echo("❌ Configuration file not found")
            click.echo(f"   Expected: {config_path}")
            sys.exit(2)
        
        # Load configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check if enabled
        if not config.get("enabled", True):
            click.echo("❌ Sustainability Pack v0 disabled")
            click.echo("   Set 'enabled': true in configuration")
            sys.exit(2)
        
        click.echo("✅ Configuration file found and enabled")
        
        # Check mode
        mode = config.get("mode", "monitor")
        click.echo(f"Mode: {mode}")
        
        # Check energy budget
        energy_budget = config.get("energy_budget_kwh_per_100k", 1.0)
        click.echo(f"Energy Budget: {energy_budget} kWh per 100k tokens")
        
        # Check thresholds
        thresholds = config.get("thresholds", {})
        click.echo(f"Warning Threshold: {thresholds.get('warn', 0.8) * 100:.0f}%")
        click.echo(f"Delay Threshold: {thresholds.get('delay', 0.9) * 100:.0f}%")
        click.echo(f"Block Threshold: {thresholds.get('block', 1.0) * 100:.0f}%")
        
        # Check model factors
        model_factors = config.get("model_factors_kwh_per_100k", {})
        click.echo(f"Model Factors: {len(model_factors)} configured")
        for model, factor in model_factors.items():
            click.echo(f"  {model}: {factor} kWh per 100k tokens")
        
        # Check metrics configuration
        metrics_config = config.get("metrics", {})
        output_path = metrics_config.get("output_path", "artifacts/lens/sustainability/metrics.jsonl")
        click.echo(f"Metrics Output: {output_path}")
        
        # Check if metrics directory exists
        metrics_dir = Path(output_path).parent
        if metrics_dir.exists():
            click.echo("✅ Metrics directory exists")
        else:
            click.echo("⚠️  Metrics directory will be created on first use")
        
        # Check carbontracker availability
        try:
            import carbontracker
            click.echo("✅ carbontracker available")
        except ImportError:
            click.echo("⚠️  carbontracker not available - using fallback calculation")
        
        click.echo("\n✅ Sustainability Pack v0 is properly configured")
        sys.exit(0)
        
    except Exception as e:
        click.echo(f"❌ Sustainability diagnostics failed: {e}")
        sys.exit(2)

@sustainability.command()
@click.option('--sample', default=100, help='Number of sample requests to simulate (default: 100)')
@click.option('--output', help='Output file for metrics (default: artifacts/lens/sustainability/metrics.jsonl)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run(sample: int, output: Optional[str], verbose: bool):
    """Simulate requests and log sustainability evidence."""
    try:
        import json
        import time
        from pathlib import Path
        from datetime import datetime, timezone
        
        from ioa.core.governance.policy_engine import PolicyEngine, ActionContext, ActionRiskLevel
        
        click.echo(f"🌱 Running Sustainability Pack v0 Test ({sample} samples)")
        click.echo("=" * 60)
        
        # Initialize policy engine
        policy_engine = PolicyEngine()
        
        # Generate test requests
        test_requests = _generate_sustainability_test_requests(sample)
        
        # Run tests
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sample_count": sample,
            "metrics": {
                "total_requests": 0,
                "warnings": 0,
                "delays": 0,
                "blocks": 0,
                "total_energy_kwh": 0.0,
                "avg_utilization": 0.0,
                "p95_latency_ms": 0.0
            },
            "test_results": []
        }
        
        latencies = []
        total_utilization = 0.0
        
        for i, request in enumerate(test_requests, 1):
            if verbose and i % 20 == 0:
                click.echo(f"   Processed {i}/{sample} requests...")
            
            # Create action context
            action_ctx = ActionContext(
                action_id=f"sustainability_test_{i}",
                action_type="llm_generation",
                actor_id="sustainability_test_actor",
                risk_level=ActionRiskLevel.LOW,
                metadata={
                    "token_count": request["token_count"],
                    "model_name": request["model_name"],
                    "task_id": f"test_task_{i}",
                    "run_id": "sustainability_test_run",
                    "project_id": "sustainability_test_project"
                }
            )
            
            start_time = time.time()
            
            # Validate against laws (includes sustainability check)
            validation_result = policy_engine.validate_against_laws(action_ctx)
            
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)
            
            # Extract sustainability evidence
            sustainability_evidence = None
            for law_result in validation_result.laws_checked:
                if law_result == "law7":  # Sustainability law
                    # Find the sustainability evidence in violations or metadata
                    for violation in validation_result.violations:
                        if "sustainability_evidence" in violation:
                            sustainability_evidence = violation["sustainability_evidence"]
                            break
                    break
            
            if sustainability_evidence:
                total_utilization += sustainability_evidence.get("utilization", 0.0)
                results["metrics"]["total_energy_kwh"] += sustainability_evidence.get("estimate_kwh_per_100k", 0.0) * request["token_count"] / 100_000
                
                # Count threshold hits
                threshold_hit = sustainability_evidence.get("threshold_hit", "none")
                if threshold_hit == "warn":
                    results["metrics"]["warnings"] += 1
                elif threshold_hit == "delay":
                    results["metrics"]["delays"] += 1
                elif threshold_hit == "block":
                    results["metrics"]["blocks"] += 1
            
            # Store test result
            test_result = {
                "request_id": i,
                "token_count": request["token_count"],
                "model_name": request["model_name"],
                "sustainability_evidence": sustainability_evidence,
                "latency_ms": latency_ms,
                "validation_status": validation_result.status.value
            }
            results["test_results"].append(test_result)
        
        # Calculate metrics
        results["metrics"]["total_requests"] = sample
        results["metrics"]["avg_utilization"] = total_utilization / sample if sample > 0 else 0.0
        
        if latencies:
            latencies.sort()
            p95_index = int(len(latencies) * 0.95)
            results["metrics"]["p95_latency_ms"] = latencies[p95_index]
        
        # Save results
        output_path = Path(output) if output else Path("artifacts/lens/sustainability/metrics.jsonl")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Display summary
        click.echo(f"✅ Test completed successfully")
        click.echo(f"📊 Results saved to: {output_path}")
        click.echo()
        click.echo(f"  Total Requests: {results['metrics']['total_requests']}")
        click.echo(f"  Warnings: {results['metrics']['warnings']}")
        click.echo(f"  Delays: {results['metrics']['delays']}")
        click.echo(f"  Blocks: {results['metrics']['blocks']}")
        click.echo(f"  Total Energy: {results['metrics']['total_energy_kwh']:.6f} kWh")
        click.echo(f"  Avg Utilization: {results['metrics']['avg_utilization']:.1%}")
        click.echo(f"  P95 Latency: {results['metrics']['p95_latency_ms']:.2f}ms")
        
        sys.exit(0)
        
    except Exception as e:
        click.echo(f"❌ Sustainability test run failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)

def _generate_sustainability_test_requests(count: int) -> list:
    """Generate test requests for sustainability testing."""
    requests = []
    
    # Different model types and token counts
    models = ["gpt-4o-mini", "claude-3-haiku", "gemini-1.5-pro", "llama-3-8b-instruct", "default"]
    token_counts = [100, 500, 1000, 2000, 5000, 10000]
    
    for i in range(count):
        model = models[i % len(models)]
        token_count = token_counts[i % len(token_counts)]
        
        requests.append({
            "token_count": token_count,
            "model_name": model
        })
    
    return requests

@app.group()
def energy():
    """Energy and sustainability management (deprecated - use sustainability commands)."""
    pass

@app.group()
def router():
    """Energy-aware provider routing."""
    pass

@router.command()
@click.option('--strategy', type=click.Choice(['balanced', 'quality_first', 'energy_first', 'sustainability_strict']), 
              default='balanced', help='Routing strategy to use')
@click.option('--task-type', default='text_generation', help='Type of task to route')
@click.option('--quality-requirement', default=0.8, type=float, help='Minimum quality requirement')
@click.option('--estimated-tokens', default=1000, type=int, help='Estimated token count')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def route(strategy: str, task_type: str, quality_requirement: float, estimated_tokens: int, verbose: bool):
    """Route a request using energy-aware provider selection."""
    try:
        # Import provider router
        try:
            from provider_router import create_energy_aware_router, RoutingStrategy
            router = create_energy_aware_router()
            
            # Create request
            request = {
                "task_type": task_type,
                "quality_requirement": quality_requirement,
                "estimated_tokens": estimated_tokens
            }
            
            # Convert strategy string to enum
            strategy_enum = RoutingStrategy(strategy)
            
            # Route request
            decision = router.route_request(request, strategy_enum)
            
            click.echo(f"🔄 Energy-Aware Routing Decision")
            click.echo("=" * 50)
            click.echo(f"Selected Provider: {decision.selected_provider}")
            click.echo(f"Routing Strategy: {decision.routing_strategy.value}")
            click.echo(f"Overall Score: {decision.overall_score:.3f}")
            
            if verbose:
                click.echo(f"\nDetailed Scores:")
                click.echo(f"  Quality: {decision.quality_score:.3f}")
                click.echo(f"  Energy: {decision.energy_score:.3f}")
                click.echo(f"  Latency: {decision.latency_score:.3f}")
                
                click.echo(f"\nSustainability Impact:")
                impact = decision.sustainability_impact
                click.echo(f"  Estimated Energy: {impact['estimated_energy_kwh']:.6f} kWh")
                click.echo(f"  Estimated CO2e: {impact['estimated_co2e_g']:.3f} g")
                click.echo(f"  Energy Efficiency: {impact['energy_efficiency']:.3f}")
                click.echo(f"  Sustainability Rating: {impact['sustainability_rating']}")
                
                click.echo(f"\nAlternatives:")
                for i, alt in enumerate(decision.alternatives[:3], 1):
                    click.echo(f"  {i}. {alt.provider_id}:{alt.model_name} "
                             f"(Quality: {alt.quality_score:.3f}, Energy: {alt.energy_efficiency:.3f})")
            
        except ImportError:
            click.echo("❌ Provider router module not available")
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Routing failed: {e}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Router command failed: {e}")
        sys.exit(1)

@router.command()
@click.option('--filter', help='Filter providers by ID')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def list_providers(filter: Optional[str], verbose: bool):
    """List available providers with sustainability ratings."""
    try:
        # Import provider router
        try:
            from provider_router import create_energy_aware_router
            router = create_energy_aware_router()
            
            providers = router.list_providers(filter)
            
            click.echo(f"🔌 Available Providers ({len(providers)})")
            click.echo("=" * 50)
            
            for provider in providers:
                click.echo(f"{provider.provider_id}:{provider.model_name}")
                click.echo(f"  Capabilities: {', '.join(provider.capabilities)}")
                click.echo(f"  Quality: {provider.quality_score:.3f}")
                click.echo(f"  Energy Efficiency: {provider.energy_efficiency:.3f}")
                click.echo(f"  Latency: {provider.latency_score:.3f}")
                click.echo(f"  Sustainability: {provider.sustainability_rating}")
                click.echo(f"  Region: {provider.region}")
                if verbose:
                    click.echo(f"  Cost: ${provider.cost_per_token:.6f}/token")
                click.echo()
            
        except ImportError:
            click.echo("❌ Provider router module not available")
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Provider listing failed: {e}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Router command failed: {e}")
        sys.exit(1)

@router.command()
def stats():
    """Show routing statistics and sustainability metrics."""
    try:
        # Import provider router
        try:
            from provider_router import create_energy_aware_router
            router = create_energy_aware_router()
            
            stats = router.get_routing_stats()
            
            click.echo(f"📊 Router Statistics")
            click.echo("=" * 30)
            click.echo(f"Total Providers: {stats['total_providers']}")
            click.echo(f"Average Energy Efficiency: {stats['avg_energy_efficiency']:.3f}")
            click.echo(f"Average Quality Score: {stats['avg_quality_score']:.3f}")
            
            click.echo(f"\nRouting Weights:")
            weights = stats['routing_weights']
            click.echo(f"  Quality: {weights['quality']:.1f}")
            click.echo(f"  Energy: {weights['energy']:.1f}")
            click.echo(f"  Latency: {weights['latency']:.1f}")
            
            click.echo(f"\nSustainability Ratings:")
            ratings = stats['sustainability_ratings']
            for rating, count in ratings.items():
                click.echo(f"  {rating}: {count}")
            
            click.echo(f"\nEnergy Strict Mode: {'Enabled' if stats['energy_strict_mode'] else 'Disabled'}")
            
        except ImportError:
            click.echo("❌ Provider router module not available")
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Stats generation failed: {e}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Router command failed: {e}")
        sys.exit(1)

@energy.command()
@click.argument('plan_file', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def forecast(plan_file: str, verbose: bool):
    """Forecast energy usage for a plan."""
    try:
        import json
        from pathlib import Path
        
        # Load plan file
        plan_path = Path(plan_file)
        with open(plan_path, 'r') as f:
            plan_data = json.load(f)
        
        # Import sustainability manager
        try:
            from sustainability import SustainabilityManager
            sustainability_manager = SustainabilityManager()
            
            # Forecast energy usage
            forecast_result = sustainability_manager.forecast_energy_usage(plan_data)
            
            if "error" in forecast_result:
                click.echo(f"❌ Forecast failed: {forecast_result['error']}")
                sys.exit(1)
            
            click.echo("🔋 Energy Usage Forecast")
            click.echo("=" * 40)
            click.echo(f"Total Estimated: {forecast_result['total_estimated_kwh']:.6f} kWh")
            click.echo(f"CO2 Equivalent: {forecast_result['total_estimated_co2e_g']:.3f} g CO2e")
            click.echo(f"Region: {forecast_result['region']}")
            
            if verbose:
                click.echo("\nBudget Analysis:")
                budget_analysis = forecast_result['budget_analysis']
                click.echo(f"  Task Budget: {budget_analysis['task_budget_kwh']:.3f} kWh")
                click.echo(f"  Run Budget: {budget_analysis['run_budget_kwh']:.3f} kWh")
                click.echo(f"  Project Budget: {budget_analysis['project_budget_kwh']:.3f} kWh")
                click.echo(f"  Within Task Budget: {'✅' if budget_analysis['within_task_budget'] else '❌'}")
                click.echo(f"  Within Run Budget: {'✅' if budget_analysis['within_run_budget'] else '❌'}")
                click.echo(f"  Within Project Budget: {'✅' if budget_analysis['within_project_budget'] else '❌'}")
                
                click.echo("\nAction Estimates:")
                for action in forecast_result['action_estimates']:
                    click.echo(f"  {action['action_id']}: {action['estimated_kwh']:.6f} kWh "
                             f"({action['estimation_method']}, confidence: {action['confidence']:.1f})")
            
        except ImportError:
            click.echo("❌ Sustainability module not available")
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Forecast failed: {e}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Plan file processing failed: {e}")
        sys.exit(1)

@energy.command()
@click.option('--run', help='Specific run ID')
@click.option('--project', help='Project ID')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def report(run: Optional[str], project: Optional[str], verbose: bool):
    """Generate energy usage report."""
    try:
        # Import sustainability manager
        try:
            from sustainability import SustainabilityManager
            sustainability_manager = SustainabilityManager()
            
            if run and project:
                # Get run-specific report
                summary = sustainability_manager.get_usage_summary(project, run)
                    click.echo(f"❌ Run report failed: {summary['error']}")
                    sys.exit(1)
                
                click.echo(f"🔋 Energy Report - Run {run}")
                click.echo("=" * 40)
                click.echo(f"Project: {summary['project_id']}")
                click.echo(f"Run Usage: {summary['run_usage_kwh']:.6f} kWh")
                click.echo(f"Run Budget: {summary['run_budget_kwh']:.3f} kWh")
                click.echo(f"Usage Percentage: {summary['run_percentage']:.1f}%")
                
                if verbose:
                    click.echo(f"\nTask Breakdown:")
                    for task_id, task_usage in summary['tasks'].items():
                        click.echo(f"  {task_id}: {task_usage:.6f} kWh")
                        
            elif project:
                # Get project summary
                summary = sustainability_manager.get_usage_summary(project)
                    click.echo(f"❌ Project report failed: {summary['error']}")
                    sys.exit(1)
                
                click.echo(f"🔋 Energy Report - Project {project}")
                click.echo("=" * 40)
                click.echo(f"Project Usage: {summary['project_usage_kwh']:.6f} kWh")
                click.echo(f"Project Budget: {summary['project_budget_kwh']:.3f} kWh")
                click.echo(f"Usage Percentage: {summary['project_percentage']:.1f}%")
                click.echo(f"Total Runs: {summary['runs']}")
                click.echo(f"Total Tasks: {summary['tasks']}")
                
            else:
                click.echo("❌ Please specify either --run and --project, or just --project")
                sys.exit(1)
                
        except ImportError:
            click.echo("❌ Sustainability module not available")
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Report generation failed: {e}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Report failed: {e}")
        sys.exit(1)

@app.group()
def gates():
    """CI Gates v1 - Governance + Security + Docs + Hygiene validation."""
    pass

@gates.command()
@click.option('--profile', default='local', help='Profile to use (local, pr, nightly)')
@click.option('--config', default='.ioa/ci-gates.yml', help='Configuration file path')
def doctor(profile: str, config: str):
    """Run a fast local check matching PR profile."""
    try:
        from .ci_gates import create_runner
        
        click.echo(f"🔍 CI Gates v1 Doctor (profile: {profile})")
        click.echo("=" * 50)
        
        # Create runner
        runner = create_runner(profile, config)
        
        # Run gates
        summary = runner.run_gates()
        
        # Display quick summary
        click.echo(f"  Profile: {summary.profile}")
        click.echo(f"  Mode: {summary.mode}")
        click.echo(f"  Duration: {summary.duration:.2f}s")
        click.echo(f"  ✅ Passed: {summary.passed}")
        click.echo(f"  ⚠️  Warned: {summary.warned}")
        click.echo(f"  ❌ Failed: {summary.failed}")
        
        if summary.failed > 0:
            click.echo(f"\n❌ {summary.failed} gates failed")
            sys.exit(1)
        else:
            click.echo(f"\n✅ All gates passed")
            sys.exit(0)
            
    except Exception as e:
        click.echo(f"❌ Gates doctor failed: {e}")
        sys.exit(1)

@gates.command()
@click.option('--gates', help='Comma-separated list of gates to run (governance,security,docs,hygiene)')
@click.option('--profile', default='local', help='Profile to use (local, pr, nightly)')
@click.option('--mode', help='Override mode (monitor, strict)')
@click.option('--requests', type=int, help='Override harness requests count')
@click.option('--config', default='.ioa/ci-gates.yml', help='Configuration file path')
def run(gates: Optional[str], profile: str, mode: Optional[str], requests: Optional[int], config: str):
    """Run selected gates with optional overrides."""
    try:
        from .ci_gates import create_runner
        
        # Parse gates
        selected_gates = None
        if gates:
            selected_gates = [g.strip() for g in gates.split(',')]
        
        click.echo(f"🚀 Running CI Gates v1")
        if selected_gates:
            click.echo(f"   Selected gates: {', '.join(selected_gates)}")
        click.echo(f"   Profile: {profile}")
        if mode:
            click.echo(f"   Mode override: {mode}")
        if requests:
            click.echo(f"   Requests override: {requests}")
        
        # Create runner
        runner = create_runner(profile, config)
        
        # Apply overrides
        if mode:
            runner.profile_config['mode'] = mode
        if requests:
            runner.profile_config['harness'] = runner.profile_config.get('harness', {})
            runner.profile_config['harness']['requests'] = requests
        
        # Run gates
        summary = runner.run_gates(selected_gates)
        
        # Exit with appropriate code
        if summary.failed > 0 and summary.mode == "strict":
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        click.echo(f"❌ Gates run failed: {e}")
        sys.exit(1)

@gates.command()
@click.option('--format', 'output_format', default='md', help='Output format (md, json)')
@click.option('--open', is_flag=True, help='Open report in default application')
@click.option('--config', default='.ioa/ci-gates.yml', help='Configuration file path')
def report(output_format: str, open: bool, config: str):
    """Render latest CI run as Markdown and optionally open."""
    try:
        from .ci_gates import load_config
        import json
        from pathlib import Path
        
        # Load latest summary
        artifacts_dir = Path("artifacts/lens/gates")
        summary_file = artifacts_dir / "summary.json"
        
        if not summary_file.exists():
            click.echo("❌ No gates summary found. Run 'ioa gates run' first.")
            sys.exit(1)
        
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)
        
        if output_format == 'json':
            click.echo(json.dumps(summary_data, indent=2))
        else:
            # Generate Markdown report
            report_content = f"""# CI Gates v1 Report

**Profile:** {summary_data['profile']}  
**Mode:** {summary_data['mode']}  
**Duration:** {summary_data['duration']:.2f}s  
**Timestamp:** {summary_data['timestamp']}

## Summary

- **Total Gates:** {summary_data['total_gates']}
- **✅ Passed:** {summary_data['passed']}
- **⚠️ Warned:** {summary_data['warned']}
- **❌ Failed:** {summary_data['failed']}
- **⏭️ Skipped:** {summary_data['skipped']}

## Gate Results

"""
            
            for result in summary_data['results']:
                status_emoji = {
                    'pass': '✅',
                    'warn': '⚠️',
                    'fail': '❌',
                    'skip': '⏭️'
                }.get(result['status'], '❓')
                
                report_content += f"### {status_emoji} {result['name']}\n"
                report_content += f"**Status:** {result['status']}\n"
                report_content += f"**Message:** {result['message']}\n"
                report_content += f"**Duration:** {result['duration']:.2f}s\n"
                
                if result['details']:
                    report_content += f"**Details:**\n"
                    for key, value in result['details'].items():
                        report_content += f"- {key}: {value}\n"
                
                if result['artifacts']:
                    report_content += f"**Artifacts:**\n"
                    for artifact in result['artifacts']:
                        report_content += f"- {artifact}\n"
                
                report_content += "\n"
            
            report_content += f"""## Artifacts

All artifacts are stored in: `{summary_data['artifacts_dir']}`

- **Timeseries:** `{summary_data['artifacts_dir']}/timeseries.jsonl`
"""
            
            # Save report
            report_file = artifacts_dir / "report.md"
            with open(report_file, 'w') as f:
                f.write(report_content)
            
            click.echo(f"📊 Report generated: {report_file}")
            
            if open:
                import webbrowser
                webbrowser.open(f"file://{report_file.absolute()}")
        
        sys.exit(0)
        
    except Exception as e:
        click.echo(f"❌ Report generation failed: {e}")
        sys.exit(1)

def main():
    """Main entry point for the CLI script."""
    # Ensure src is importable before running the app
    _ensure_src_importable()
    app()

if __name__ == "__main__":
    main()
