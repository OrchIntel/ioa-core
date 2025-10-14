"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

import click

from src.ioa.assurance.schema import AssuranceConfig
from src.ioa.assurance.collect import collect_inputs
from src.ioa.assurance.calc import compute_rollup
from src.ioa.assurance.emit import emit_summary, emit_timeseries, render_markdown


@click.group()
def assurance():
    """Assurance Score v1 - evidence-backed readiness scoring."""
    pass


@assurance.command()
def doctor():
    """Validate presence of inputs and schema versions."""
    try:
        cfg = _load_config()
        inputs = collect_inputs(cfg)
        click.echo("🔍 Assurance Doctor")
        click.echo("=" * 40)
        click.echo("Inputs:")
        for name, path in inputs.evidence_paths.items():
            p = Path(path)
            status = "✅" if p.exists() else "⚠️"
            click.echo(f"  {status} {name}: {path}")
        click.echo("\n✅ Doctor completed")
    except Exception as e:
        click.echo(f"❌ Doctor failed: {e}")
        raise


@assurance.command()
@click.option('--write', 'write_outputs', is_flag=True, help='Write rollup artifacts to artifacts/lens/assurance')
def compute(write_outputs: bool):
    """Run collect + calc; print table and optionally write rollups."""
    cfg = _load_config()
    inputs = collect_inputs(cfg)
    rollup = compute_rollup(inputs, cfg)

    # Print summary table
    click.echo("📊 Assurance Score v1")
    click.echo("=" * 30)
    click.echo(f"Overall: {rollup.overall:.2f}/15 [{rollup.status}]")
    click.echo("Per-Law:")
    for pls in rollup.per_law:
        click.echo(f"  {pls.law_id.upper()}: {pls.total:.2f} (code={pls.code}, tests={pls.tests}, runtime={pls.runtime}, docs={pls.docs})")

    if write_outputs:
        summary = emit_summary(rollup)
        series = emit_timeseries(rollup)
        click.echo(f"\n💾 Wrote: {summary}")
        click.echo(f"💾 Appended: {series}")


@assurance.command()
@click.option('--format', 'output_format', default='md', type=click.Choice(['md','json']))
def report(output_format: str):
    """Render report from latest rollup (stdout)."""
    cfg = _load_config()
    inputs = collect_inputs(cfg)
    rollup = compute_rollup(inputs, cfg)
    if output_format == 'json':
        data = rollup.model_dump() if hasattr(rollup, 'model_dump') else rollup.__dict__
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        click.echo(render_markdown(rollup))


def _load_config() -> AssuranceConfig:
    """Load config from .ioa/assurance.yml or return defaults."""
    import yaml
    cfg_path = Path('.ioa/assurance.yml')
    if not cfg_path.exists():
        return AssuranceConfig()
    with open(cfg_path, 'r') as f:
        data = yaml.safe_load(f) or {}
    return AssuranceConfig(**data)


