""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Optional

import click

from ioa.cartridges.eu_ai_act_v1 import (
    load_config,
    classify_use_case,
    preflight_check,
    postflight_record,
)


@click.group()
def euaia():
    """EU AI Act governance (v1)."""
    pass


@euaia.command()
@click.option('--config', 'config_path', default='configs/governance/eu_ai_act_v1.yml', help='Config path')
def doctor(config_path: str):
    """Validate config and show scope, risk classifier status, required packs."""
    cfg = load_config(config_path)
    click.echo("🔍 EU AIA v1 Doctor")
    click.echo(f"Enabled: {cfg.get('enabled')} | Mode: {cfg.get('scope',{}).get('default_mode')}")
    jurs = cfg.get('scope',{}).get('jurisdictions', [])
    click.echo(f"Jurisdictions: {', '.join(jurs) if jurs else 'n/a'}")
    strategy = cfg.get('risk',{}).get('classifier',{}).get('strategy')
    click.echo(f"Classifier: {strategy}")
    # Required packs (v1 relies on Ethics/PII masks but accepts absence in monitor)
    click.echo("Required packs: Ethics Pack (bias probes), PII Masking (EU)")


@euaia.command()
@click.option('--usecase', required=True, help='Use-case label to classify')
@click.option('--config', 'config_path', default='configs/governance/eu_ai_act_v1.yml', help='Config path')
def classify(usecase: str, config_path: str):
    """Classify a usecase into risk category."""
    cfg = load_config(config_path)
    risk, details = classify_use_case(usecase, cfg)
    actions, _ = preflight_check({"use_case": usecase}, cfg)
    click.echo(f"risk: {risk}, actions: oversight_required={actions['oversight_required']}, transparency_on={actions['transparency_on']}")


@euaia.command()
@click.option('--sample', type=int, default=250, help='Number of simulated requests')
@click.option('--mode', type=click.Choice(['monitor','graduated','strict','shadow']), default='monitor')
@click.option('--config', 'config_path', default='configs/governance/eu_ai_act_v1.yml', help='Config path')
def run(sample: int, mode: str, config_path: str):
    """Simulate batch run across categories and emit metrics."""
    cfg = load_config(config_path)
    cfg.setdefault('scope', {}).update({'default_mode': mode})
    categories = [
        'employment_hr', 'biometric_identification', 'social_scoring', 'ads', 'minimal'
    ]
    count = 0
    for cat in categories:
        for _ in range(max(1, sample // len(categories))):
            actions, ev = preflight_check({"use_case": cat}, cfg)
            trace_id = str(uuid.uuid4())
            postflight_record(trace_id, actions, cfg, {"ok": True})
            count += 1
    click.echo(f"✅ EU AIA v1 run completed: {count} records written to artifacts/lens/euaia/metrics.jsonl")


@euaia.group()
def techdoc():
    """Technical documentation utilities."""
    pass


@techdoc.command('emit')
@click.option('--out', 'out_path', required=True, help='Output YAML path')
def techdoc_emit(out_path: str):
    """Emit a Technical Documentation scaffold (v1 minimal)."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
sections:
  - id: system_overview
    title: System Overview
  - id: risk_management
    title: Risk Management
  - id: data_governance
    title: Data Governance
  - id: transparency
    title: Transparency & Disclosures
  - id: human_oversight
    title: Human Oversight
  - id: logging_traceability
    title: Logging & Traceability
  - id: robustness_accuracy
    title: Robustness & Accuracy
  - id: post_market
    title: Post-Market Monitoring
evidence_pointers:
  metrics_log: artifacts/lens/euaia/metrics.jsonl
"""
    p.write_text(content)
    click.echo(f"📝 TechDoc scaffold written: {p}")


@euaia.group()
def registry():
    """Local shadow registry tools."""
    pass


@registry.command('sync')
@click.option('--out', 'out_path', required=True, help='Output JSON path')
def registry_sync(out_path: str):
    """Write a local shadow EU registry JSON with basic metadata."""
    import json
    from datetime import datetime, timezone
    data = {
        "version": 1,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "systems": [
            {"id": "core-system", "risk": "mixed", "jurisdictions": ["EU","EEA"]}
        ],
    }
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))
    click.echo(f"📚 Registry written: {p}")


@euaia.group()
def incidents():
    """Incident summaries."""
    pass


@incidents.command('report')
@click.option('--from', 'from_path', required=True, help='Metrics JSONL path')
def incidents_report(from_path: str):
    """Summarize reportable events (monitoring only)."""
    import json
    total = 0
    high_risk = 0
    prohibited = 0
    p = Path(from_path)
    if not p.exists():
        click.echo("❌ Metrics file not found")
        sys.exit(1)
    with p.open() as f:
        for line in f:
            try:
                rec = json.loads(line)
                total += 1
                r = rec.get('risk')
                if r == 'high_risk':
                    high_risk += 1
                if r == 'prohibited':
                    prohibited += 1
            except Exception:
                continue


@euaia.command()
@click.option('--config', 'config_path', default='configs/governance/eu_ai_act_v1.yml', help='Config path')
def checklist(config_path: str):
    """Print what must be satisfied per category in current config (summary)."""
    cfg = load_config(config_path)
    click.echo("✅ EU AIA v1 Checklist (summary)")
    click.echo("- Transparency: model capability card, limitations, generated flag")
    click.echo("- Data governance: provenance manifest (high-risk required), PII masking")
    click.echo("- Oversight: HITL gate for high-risk")
    click.echo("- Logging: append evidence to Lens + audit chain")
    click.echo("- Robustness: min acceptance threshold, drift alerts")


