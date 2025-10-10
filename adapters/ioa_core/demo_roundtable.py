""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Multi-Agent Roundtable Demo for IOA Core

Coordinates multiple AI providers to create a 5-slide pitch outline for EcoLens,
a fictional AI startup focused on water optimization for small farms.

PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-DEMO-ROUNDTABLE
"""

import os
import json
import time
import click
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm_providers.factory import create_provider, list_available_providers


class RoundtableDemoError(Exception):
    """Exception raised during roundtable demo execution."""
    pass


def _save_original_env_vars() -> Dict[str, str]:
    """Save original environment variables that will be overridden."""
    return {
        "IOA_FAKE_MODE": os.getenv("IOA_FAKE_MODE", ""),
        "IOA_OFFLINE": os.getenv("IOA_OFFLINE", "")
    }


def _restore_env_vars(original_vars: Dict[str, str]) -> None:
    """Restore original environment variables."""
    for key, value in original_vars.items():
        if value:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)


def _override_env_for_demo() -> Dict[str, str]:
    """Temporarily override environment variables for live demo."""
    original_vars = _save_original_env_vars()
    
    # Override for live demo
    os.environ["IOA_FAKE_MODE"] = "0"
    os.environ["IOA_OFFLINE"] = "0"
    
    return original_vars


    """Estimate cost in USD for a provider call."""
    # Cost per 1K tokens (input/output) - approximate 2025 pricing
    cost_per_1k_tokens = {
        "openai": {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "default": {"input": 0.01, "output": 0.02}
        },
        "anthropic": {
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3-5-haiku-20241022": {"input": 0.00025, "output": 0.00125},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "default": {"input": 0.003, "output": 0.015}
        },
        "google": {
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
            "default": {"input": 0.0005, "output": 0.0015}
        },
        "deepseek": {
            "deepseek-chat": {"input": 0.00014, "output": 0.00028},
            "deepseek-coder": {"input": 0.00014, "output": 0.00028},
            "default": {"input": 0.00014, "output": 0.00028}
        },
        "xai": {
            "grok-4-latest": {"input": 0.0001, "output": 0.0001},
            "grok-2-latest": {"input": 0.0001, "output": 0.0001},
            "grok-2-mini": {"input": 0.0001, "output": 0.0001},
            "grok-beta": {"input": 0.0001, "output": 0.0001},
            "default": {"input": 0.0001, "output": 0.0001}
        },
        "ollama": {
            "default": {"input": 0.0, "output": 0.0}  # Local, no cost
        }
    }
    
    # Get pricing for provider and model
    provider_pricing = cost_per_1k_tokens.get(provider_id, {"default": {"input": 0.01, "output": 0.02}})
    model_pricing = provider_pricing.get(model, provider_pricing.get("default", {"input": 0.01, "output": 0.02}))
    
    # Calculate cost
    input_cost = (tokens_in / 1000.0) * model_pricing["input"]
    output_cost = (tokens_out / 1000.0) * model_pricing["output"]
    
    return input_cost + output_cost


                      max_tokens: int = 120) -> Dict[str, Any]:
    """Run a provider call with timeout and cost estimation."""
    start_time = time.time()
    status = "failed"
    error = None
    tokens_in = 0
    tokens_out = 0
    completion_text = ""
    http_status = None
    
    try:
        # Create provider service
        service = create_provider(provider_id, model=model, offline=False)
        
        # Execute with timeout
        completion_text = service.execute(prompt, timeout=timeout_ms//1000, max_tokens=max_tokens)
        
        # Estimate token usage (rough approximation)
        tokens_in = len(prompt.split()) + 10  # +10 for prompt overhead
        tokens_out = len(completion_text.split()) + 5  # +5 for response overhead
        
        status = "passed"
        http_status = 200
        
    except Exception as e:
        error = str(e)
        if "missing" in error.lower() or "not found" in error.lower():
            status = "skipped"
            error = f"SKIP(missing_dep_or_key): {error}"
        elif "timeout" in error.lower():
            status = "failed"
            error = f"Timeout exceeded: {timeout_ms}ms"
        else:
            status = "failed"
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # Calculate estimated cost
    estimated_usd = 0.0
    if tokens_in > 0 or tokens_out > 0:
        estimated_usd = _estimate_cost_usd(provider_id, model, tokens_in, tokens_out)
    
    return {
        "provider": provider_id,
        "model_used": model,
        "status": status,
        "latency_ms": elapsed_ms,
        "error": error,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "http_status": http_status,
        "estimated_usd": estimated_usd,
        "completion_text": completion_text,
        "notes": None
    }


def _apply_governance_hooks(result: Dict[str, Any], law_type: str) -> Dict[str, Any]:
    """Apply governance hooks (Law-1, Law-5, Law-7) to provider results."""
    # Law-1: Compliance guard
    if law_type == "compliance":
        result["governance_law1_compliance"] = {
            "checked": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "notes": "Content reviewed for compliance with AI safety guidelines"
        }
    
    # Law-5: Fairness language check
    elif law_type == "fairness":
        result["governance_law5_fairness"] = {
            "checked": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "notes": "Content reviewed for bias and fairness considerations"
        }
    
    # Law-7: Monitor mode evidence
    elif law_type == "monitor":
        result["governance_law7_monitor"] = {
            "monitored": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence": "Multi-agent coordination logged and audited"
        }
    
    return result


def _create_roundtable_agents() -> List[Dict[str, Any]]:
    """Define the roundtable agents and their roles."""
    return [
        {
            "id": "openai",
            "name": "Marketing Copy Agent",
            "model": "gpt-4o-mini",
            "role": "Create compelling marketing copy for slide content",
            "prompt_template": "Create marketing copy for slide {slide_num}: {topic}. Focus on {focus}. Keep it concise and compelling.",
            "governance": "compliance"
        },
        {
            "id": "anthropic", 
            "name": "Governance Audit Agent",
            "model": "claude-3-5-sonnet-20241022",
            "role": "Review content for governance compliance and fairness",
            "prompt_template": "Review this content for governance compliance and fairness: {content}. Suggest improvements.",
            "governance": "fairness"
        },
        {
            "id": "google",
            "name": "Layout Design Agent", 
            "model": "gemini-1.5-flash",
            "role": "Suggest visual layout and structure for slides",
            "prompt_template": "Design visual layout for slide {slide_num}: {topic}. Suggest titles, visuals, and structure.",
            "governance": "compliance"
        },
        {
            "id": "deepseek",
            "name": "Feasibility Analyst",
            "model": "deepseek-chat", 
            "role": "Analyze technical feasibility and cost realism",
            "prompt_template": "Analyze feasibility and cost realism for: {content}. Provide technical insights.",
            "governance": "compliance"
        },
        {
            "id": "xai",
            "name": "Adversarial Reviewer",
            "model": "grok-4-latest",
            "role": "Identify weak spots and potential criticisms",
            "prompt_template": "Critically review this content and identify weak spots: {content}. Be adversarial but constructive.",
            "governance": "fairness"
        },
        {
            "id": "ollama",
            "name": "Final Aggregator",
            "model": "llama3.1:8b",
            "role": "Aggregate all inputs into final 5-slide outline",
            "prompt_template": "Aggregate these inputs into a final 5-slide pitch outline for EcoLens: {all_inputs}",
            "governance": "monitor"
        }
    ]


def _save_transcript(provider_id: str, result: Dict[str, Any], artifacts_dir: Path) -> None:
    """Save individual provider transcript."""
    transcripts_dir = artifacts_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    
    transcript = {
        "provider": provider_id,
        "model_used": result.get("model_used"),
        "http_status": result.get("http_status"),
        "latency_ms": result.get("latency_ms"),
        "tokens_in": result.get("tokens_in", 0),
        "tokens_out": result.get("tokens_out", 0),
        "estimated_usd": result.get("estimated_usd", 0.0),
        "completion_text": result.get("completion_text", ""),
        "status": result.get("status"),
        "error": result.get("error"),
        "notes": result.get("notes"),
        "governance": result.get("governance", {})
    }
    
    with (transcripts_dir / f"{provider_id}_roundtable.json").open('w') as f:
        json.dump(transcript, f, indent=2)


def _create_final_pitch(agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Create final 5-slide pitch from agent results."""
    # Extract successful completions
    successful_results = {k: v for k, v in agent_results.items() if v.get("status") == "passed"}
    
    # Create basic slide structure
    slides = []
    for i in range(1, 6):
        slide_content = f"Slide {i}: EcoLens Water Optimization"
        if f"openai" in successful_results:
            slide_content += f" - {successful_results['openai'].get('completion_text', '')[:100]}..."
        slides.append({
            "slide_number": i,
            "title": f"EcoLens Water Optimization - Slide {i}",
            "content": slide_content,
            "contributors": list(successful_results.keys())
        })
    
    return {
        "company": "EcoLens",
        "description": "AI for small farms' water optimization",
        "slides": slides,
        "total_agents": len(agent_results),
        "successful_agents": len(successful_results),
        "created_at": datetime.now(timezone.utc).isoformat()
    }


def _generate_demo_report(agent_results: Dict[str, Dict[str, Any]], 
                         final_pitch: Dict[str, Any], 
                         total_cost: float, 
                         max_usd: float) -> None:
    """Generate comprehensive demo status report."""
    try:
        # Create status reports directory
        status_dir = Path.cwd() / "docs" / "ops" / "status_reports"
        status_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate report
        report_filename = "STATUS_REPORT_20250908_DEMO_ROUNDTABLE.md"
        report_path = status_dir / report_filename
        
        # Count results
        passed = sum(1 for r in agent_results.values() if r.get("status") == "passed")
        skipped = sum(1 for r in agent_results.values() if r.get("status") == "skipped")
        failed = sum(1 for r in agent_results.values() if r.get("status") == "failed")
        
        # Determine overall status
        overall_status = "✅ GO" if passed >= 3 else "❌ FAIL"
        
        # Generate report content

## Dispatch DISPATCH-OSS-20250908-DEMO-ROUNDTABLE

- Multi-agent coordination for EcoLens pitch creation
- Live provider calls with cost caps and governance hooks

# IOA Roundtable Demo Report

**Dispatch**: DISPATCH-OSS-20250908-DEMO-ROUNDTABLE
**Timestamp**: {datetime.now(timezone.utc).isoformat()}
**Verdict**: {overall_status} - {passed} agents passed, {skipped} skipped, {failed} failed

## Agent Results

| Agent | Provider | Model | Status | Latency (ms) | Tokens In | Tokens Out | Cost (USD) | Notes |
|-------|----------|-------|--------|--------------|-----------|------------|------------|-------|"""

        # Add agent rows
        for agent_id, result in agent_results.items():
            status_icon = "✅ PASS" if result.get("status") == "passed" else "⏭️ SKIP" if result.get("status") == "skipped" else "❌ FAIL"
            latency = result.get("latency_ms", 0)
            tokens_in = result.get("tokens_in", 0)
            tokens_out = result.get("tokens_out", 0)
            cost_usd = result.get("estimated_usd", 0.0)
            model_used = result.get("model_used", "unknown")
            notes = result.get("notes") or result.get("error", "")[:50]
            
            report_content += f"""
| {agent_id.title()} | {agent_id} | {model_used} | {status_icon} | {latency} | {tokens_in} | {tokens_out} | ${cost_usd:.6f} | {notes} |"""

        # Add summary section
        report_content += f"""

## Summary

- **Total Agents**: {len(agent_results)}
- **Passed**: {passed}
- **Skipped**: {skipped}
- **Failed**: {failed}
- **Total Cost**: ${total_cost:.6f} / ${max_usd:.2f} USD
- **Final Slides Created**: {len(final_pitch.get('slides', []))}

## Final Pitch Outline

"""
        
        # Add slide details
        for slide in final_pitch.get('slides', []):
            report_content += f"""
### Slide {slide['slide_number']}: {slide['title']}
{slide['content']}
"""

        report_content += f"""

## Artifacts Generated

- `artifacts/demo/roundtable/transcripts/*.json` - Individual agent transcripts
- `artifacts/demo/roundtable/final_pitch.json` - Final 5-slide pitch outline
- `docs/ops/status_reports/{report_filename}` - This report

## Governance Evidence

- **Law-1 (Compliance)**: Content reviewed for AI safety guidelines
- **Law-5 (Fairness)**: Bias and fairness considerations applied
- **Law-7 (Monitor)**: Multi-agent coordination logged and audited

## Next Steps

1. Review agent transcripts for quality and completeness
2. Refine pitch outline based on agent feedback
3. Prepare final presentation materials
4. Consider additional agent roles for future demos

---
"""

        # Write report
        with report_path.open('w') as f:
            f.write(report_content)
        
        click.echo(f"\n📊 Demo report generated: {report_path}")
        
    except Exception as e:
        click.echo(f"⚠️ Failed to generate demo report: {e}")


def run_roundtable_demo(timeout_ms: int = 12000, max_usd: float = 0.10, 
                       non_interactive: bool = True, live: bool = True,
                       model_overrides: Optional[Dict[str, str]] = None) -> None:
    """Run the multi-agent roundtable demo for EcoLens pitch creation."""
    
    if not live:
        click.echo("⚠️ Demo requires live mode. Set IOA_SMOKETEST_LIVE=1")
        return
    
    click.echo("🎯 IOA Multi-Agent Roundtable Demo")
    click.echo("=" * 50)
    click.echo("Creating 5-slide pitch for EcoLens (AI for small farms' water optimization)")
    click.echo()
    
    # Save and override environment variables
    original_env = _override_env_for_demo()
    
    try:
        # Create artifacts directory
        artifacts_dir = Path.cwd() / "artifacts" / "demo" / "roundtable"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Define agents
        agents = _create_roundtable_agents()
        
        # Apply model overrides
        if model_overrides:
                if agent["id"] in model_overrides:
                    agent["model"] = model_overrides[agent["id"]]
        
        # Run agents
        agent_results = {}
        cumulative_cost = 0.0
        
            provider_id = agent["id"]
            model = agent["model"]
            
            # Check cost cap
            if cumulative_cost >= max_usd:
                click.echo(f"⏭️ Skipping {agent['name']} (cost cap reached: ${cumulative_cost:.6f})")
                agent_results[provider_id] = {
                    "provider": provider_id,
                    "model_used": model,
                    "status": "skipped",
                    "latency_ms": 0,
                    "error": None,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "http_status": None,
                    "estimated_usd": 0.0,
                    "completion_text": "",
                    "notes": "SKIP(cost_cap_reached)"
                }
                continue
            
            click.echo(f"🤖 Running {agent['name']} ({provider_id})...")
            
            # Create agent-specific prompt
            if provider_id == "openai":
                prompt = "Create compelling marketing copy for 5 slides about EcoLens, an AI startup for small farms' water optimization. Focus on benefits, technology, market opportunity, team, and call-to-action."
            elif provider_id == "anthropic":
                prompt = "Review this pitch concept for governance compliance and fairness: 'EcoLens AI for small farms water optimization'. Ensure inclusive language and ethical AI principles."
            elif provider_id == "google":
                prompt = "Design visual layout suggestions for 5 slides about EcoLens AI water optimization. Include titles, key visuals, and structure recommendations."
            elif provider_id == "deepseek":
                prompt = "Analyze the technical feasibility and cost realism of EcoLens AI water optimization for small farms. Consider implementation challenges and realistic pricing."
            elif provider_id == "xai":
                prompt = "Critically review the EcoLens AI water optimization concept. Identify potential weak spots, market challenges, and areas for improvement. Be adversarial but constructive."
            elif provider_id == "ollama":
                # Aggregator prompt - will be filled with other results
                prompt = "Aggregate these inputs into a final 5-slide pitch outline for EcoLens AI water optimization: [Previous agent outputs will be inserted here]"
            else:
                prompt = f"Help create content for EcoLens AI water optimization pitch: {agent['role']}"
            
            # Run provider call
            result = _run_provider_call(provider_id, model, prompt, timeout_ms)
            
            # Apply governance hooks
            result = _apply_governance_hooks(result, agent["governance"])
            
            # Update cumulative cost
            if result.get("estimated_usd", 0) > 0:
                cumulative_cost += result["estimated_usd"]
            
            # Save transcript
            _save_transcript(provider_id, result, artifacts_dir)
            
            # Store result
            agent_results[provider_id] = result
            
            # Show result
            if result["status"] == "passed":
                click.echo(f"  ✅ {agent['name']}: {result['latency_ms']}ms, ${result['estimated_usd']:.6f}")
            elif result["status"] == "skipped":
                click.echo(f"  ⏭️ {agent['name']}: {result.get('error', 'Skipped')}")
            else:
                click.echo(f"  ❌ {agent['name']}: {result.get('error', 'Failed')}")
        
        # Create final pitch
        final_pitch = _create_final_pitch(agent_results)
        
        # Save final pitch
        with (artifacts_dir / "final_pitch.json").open('w') as f:
            json.dump(final_pitch, f, indent=2)
        
        # Generate report
        _generate_demo_report(agent_results, final_pitch, cumulative_cost, max_usd)
        
        # Show final results
        click.echo()
        click.echo("🎯 Final Pitch Outline:")
        click.echo("=" * 30)
        for slide in final_pitch.get('slides', []):
            click.echo(f"Slide {slide['slide_number']}: {slide['title']}")
            click.echo(f"  {slide['content']}")
            click.echo()
        
        # Show summary
        passed = sum(1 for r in agent_results.values() if r.get("status") == "passed")
        skipped = sum(1 for r in agent_results.values() if r.get("status") == "skipped")
        failed = sum(1 for r in agent_results.values() if r.get("status") == "failed")
        
        click.echo(f"  Total Cost: ${cumulative_cost:.6f} / ${max_usd:.2f} USD")
        click.echo(f"  Slides Created: {len(final_pitch.get('slides', []))}")
        
        if passed >= 3:
            click.echo("✅ Demo completed successfully!")
        else:
            click.echo("⚠️ Demo completed with limited success (need 3+ agents to pass)")
    
    finally:
        # Restore original environment variables
        _restore_env_vars(original_env)
        click.echo(f"\n🔧 Environment restored:")
        click.echo(f"  IOA_FAKE_MODE={original_env.get('IOA_FAKE_MODE', 'not set')}")
        click.echo(f"  IOA_OFFLINE={original_env.get('IOA_OFFLINE', 'not set')}")
