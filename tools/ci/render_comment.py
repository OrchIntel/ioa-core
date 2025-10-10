""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, Template


def load_summary(summary_path: str) -> Dict[str, Any]:
    """Load gates summary from JSON file."""
    try:
        with open(summary_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {summary_path} not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing {summary_path}: {e}", file=sys.stderr)
        sys.exit(1)


def load_template(template_path: str) -> Template:
    """Load Jinja2 template."""
    try:
        template_dir = Path(template_path).parent
        template_name = Path(template_path).name
        
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        return env.get_template(template_name)
    except Exception as e:
        print(f"Error loading template {template_path}: {e}", file=sys.stderr)
        sys.exit(1)


    """Transform summary data for template rendering."""
    # Convert results array to dict for easier template access
    results = {}
    for result in summary.get('results', []):
        gate_name = result.get('name', 'unknown').lower().replace(' ', '_')
        results[gate_name] = {
            'ok': result.get('status') == 'pass',
            'status': result.get('status', 'unknown'),
            'message': result.get('message', ''),
            'details': result.get('details', {}),
            'duration': result.get('duration', 0),
            'links': []
        }
        
        # Add artifact links if available
            artifacts_dir = summary['artifacts_dir']
            if gate_name == 'governance':
                results[gate_name]['links'].append({
                    'name': 'Governance Report',
                    'href': f"{artifacts_dir}/governance_report.json"
                })
            elif gate_name == 'security':
                results[gate_name]['links'].append({
                    'name': 'Security Report',
                    'href': f"{artifacts_dir}/security_report.json"
                })
            elif gate_name == 'docs':
                results[gate_name]['links'].append({
                    'name': 'Docs Report',
                    'href': f"{artifacts_dir}/docs_report.json"
                })
            elif gate_name == 'hygiene':
                results[gate_name]['links'].append({
                    'name': 'Forbidden Patterns',
                    'href': f"{artifacts_dir}/forbidden.json"
                })
    
    data = {
        'profile': summary.get('profile', 'unknown'),
        'mode': summary.get('mode', 'monitor'),
        'duration': summary.get('duration', 0),
        'total_gates': summary.get('total_gates', 0),
        'passed': summary.get('passed', 0),
        'warned': summary.get('warned', 0),
        'failed': summary.get('failed', 0),
        'skipped': summary.get('skipped', 0),
        'results': results,
        'artifacts_dir': summary.get('artifacts_dir', 'artifacts/lens/gates')
    }

    # Try to include Assurance Score summary if available
    try:
        from pathlib import Path
        import json as _json
        assurance_summary = Path('artifacts/lens/assurance/summary.json')
        if assurance_summary.exists():
            with open(assurance_summary, 'r') as f:
                a = _json.load(f)
            data['assurance_overall'] = a.get('overall')
            data['assurance_status'] = a.get('status')
    except Exception:
        pass

    return data


def main():
    """Main entry point for comment renderer."""
    parser = argparse.ArgumentParser(description="Render CI Gates PR comment from summary")
    parser.add_argument("--summary", default="artifacts/lens/gates/summary.json", 
                       help="Path to gates summary JSON")
    parser.add_argument("--template", default="docs/ops/ci/CI_GATES_V1_COMMENT_TPL.md.j2",
                       help="Path to Jinja2 template")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()
    
    # Load and transform data
    summary = load_summary(args.summary)
    template = load_template(args.template)
    data = transform_summary(summary)
    
    # Render template
    try:
        rendered = template.render(**data)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(rendered)
        else:
            print(rendered)
    except Exception as e:
        print(f"Error rendering template: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
