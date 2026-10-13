#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""Evaluate QiXMind gate detection on the synthetic case set.

Compares three detectors against engineering's expected labels (pending
clinician adjudication):

* live: the 2.14.0 content gates as deployed, which read the model output only;
* live + input: the same lexicons also run on the input, with no context rules;
* findings: the evaluation-only source-aware detector (ioa_core.health.findings).

Usage: python scripts/eval_gates.py [--cases PATH] [--out REPORT.md]
Synthetic data only. No case text is written to the report.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set

from ioa_core.health import (
    ContentGateEvaluator,
    detect_findings,
    get_subcategory_profile,
)
from ioa_core.health.findings import CONTEXT_RULES_VERSION, DETECTOR_VERSION

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests" / "health" / "fixtures" / "gate_eval" / "cases.json"
CONCERN = ("affirmed", "uncertain")


def _live_fired(profile_id: str, text: Optional[str]) -> Set[str]:
    if not text:
        return set()
    report = ContentGateEvaluator.for_profile(profile_id).evaluate(output_text=text)
    return {result.gate for result in report.results if result.fired}


def evaluate(cases: List[dict]) -> dict:
    rows = []
    per_gate: Dict[str, Counter] = defaultdict(Counter)
    totals = Counter()
    for case in cases:
        profile_id = case["profile_id"]
        declared = set(get_subcategory_profile(profile_id).content_gates)
        expected = {
            item["gate"]: item for item in case["expected"] if item["gate"] in declared
        }
        live = _live_fired(profile_id, case.get("output"))
        live_input = live | _live_fired(profile_id, case.get("input"))
        report = detect_findings(
            profile_id=profile_id,
            input_text=case.get("input"),
            output_text=case.get("output"),
        )
        found = {item.gate: item for item in report.findings}
        outcome = []
        for gate in sorted(declared):
            exp = expected.get(gate)
            got = found.get(gate)
            counts = per_gate[gate]
            exp_concern = bool(exp and exp["context"] in CONCERN)
            if exp and got:
                counts["tp"] += 1
                context_ok = got.context == exp["context"]
                source_ok = sorted(got.sources) == sorted(exp["sources"])
                counts["context_ok"] += int(context_ok)
                counts["source_ok"] += int(source_ok)
                missed = exp_concern and got.context not in CONCERN
                counts["missed_concern"] += int(missed)
                outcome.append(
                    f"{gate}: {got.context}"
                    + ("" if context_ok else f" (expected {exp['context']})")
                    + ("" if source_ok else f" [sources {'+'.join(got.sources)}]")
                )
            elif exp and not got:
                counts["fn"] += 1
                counts["missed_concern"] += int(exp_concern)
                outcome.append(f"{gate}: MISSED (expected {exp['context']})")
            elif got and not exp:
                counts["fp"] += 1
                outcome.append(f"{gate}: EXTRA {got.context}")
            # Baselines, judged on concern: did the detector raise the gate
            # when a clinician would expect concern, and stay quiet otherwise?
            for name, fired in (
                ("live", gate in live),
                ("live_input", gate in live_input),
            ):
                if exp_concern:
                    counts[f"{name}_concern_total"] += 1
                    counts[f"{name}_concern_caught"] += int(fired)
                elif fired:
                    counts[f"{name}_fired_without_concern"] += 1
            if exp_concern:
                counts["concern_total"] += 1
                counts["concern_caught"] += int(bool(got and got.context in CONCERN))
            if got and got.context == "uncertain":
                counts["unresolved"] += 1
            if got:
                counts["findings"] += 1
            if got and got.omitted_in_output:
                totals["omitted_flagged"] += 1
        if case["category"] in ("omitted", "refused"):
            totals["omitted_cases"] += 1
        rows.append(
            {
                "id": case["id"],
                "category": case["category"],
                "profile": profile_id,
                "expected": ", ".join(
                    f"{g}: {e['context']}" for g, e in sorted(expected.items())
                )
                or "none",
                "findings": "; ".join(outcome) or "none",
                "live": ", ".join(sorted(live)) or "none",
                "live_input": ", ".join(sorted(live_input)) or "none",
                "review_output": (report.review_output or {}).get("status", "n/a"),
            }
        )
    return {"rows": rows, "per_gate": per_gate, "totals": totals}


def _pct(numerator: int, denominator: int) -> str:
    return (
        f"{numerator}/{denominator} ({100 * numerator / denominator:.0f}%)"
        if denominator
        else "n/a"
    )


def render(result: dict, cases_doc: dict) -> str:
    per_gate = result["per_gate"]
    lines = [
        "# QiXMind gate evaluation (synthetic, evaluation only)",
        "",
        f"Cases: {len(result['rows'])}, version {cases_doc.get('version')}. Detector {DETECTOR_VERSION}, context rules {CONTEXT_RULES_VERSION}. "
        "Expected labels are engineering's and are pending clinician adjudication. All case text is synthetic and is not reproduced here.",
        "",
        "Concern means a finding a clinician would expect to act on (affirmed or uncertain).",
        "",
        "## Concern caught, by detector",
        "",
        "| Gate | Live (output only) | Live lexicon on input too | Findings detector | Findings: missed or downgraded concern |",
        "|---|---|---|---|---|",
    ]
    totals = Counter()
    for gate, c in sorted(per_gate.items()):
        for key, value in c.items():
            totals[key] += value
        lines.append(
            f"| {gate} | {_pct(c['live_concern_caught'], c['live_concern_total'])} | "
            f"{_pct(c['live_input_concern_caught'], c['live_input_concern_total'])} | "
            f"{_pct(c['concern_caught'], c['concern_total'])} | {c['missed_concern']} |"
        )
    lines += [
        f"| **All gates** | {_pct(totals['live_concern_caught'], totals['live_concern_total'])} | "
        f"{_pct(totals['live_input_concern_caught'], totals['live_input_concern_total'])} | "
        f"{_pct(totals['concern_caught'], totals['concern_total'])} | {totals['missed_concern']} |",
        "",
        "## Raised without expected concern",
        "",
        "Live baselines count a fired gate where a clinician would expect no concern (for example a denial). "
        "The findings detector reports those as findings with a non-concern context instead, which still need a disposition.",
        "",
        "| Gate | Live | Live lexicon on input too | Findings: extra findings | Findings: context agreement | Findings: source agreement | Findings: unresolved |",
        "|---|---|---|---|---|---|---|",
    ]
    for gate, c in sorted(per_gate.items()):
        lines.append(
            f"| {gate} | {c['live_fired_without_concern']} | {c['live_input_fired_without_concern']} | {c['fp']} | "
            f"{_pct(c['context_ok'], c['tp'])} | {_pct(c['source_ok'], c['tp'])} | {_pct(c['unresolved'], c['findings'])} |"
        )
    lines += [
        "",
        f"Omitted signals: {result['totals']['omitted_flagged']} input findings flagged as omitted from the output "
        f"across {result['totals']['omitted_cases']} omitted or refused cases.",
        "",
        "## Cases",
        "",
        "| Case | Category | Profile | Expected | Findings detector | Live | Live + input | Review output |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['id']} | {row['category']} | {row['profile']} | {row['expected']} | {row['findings']} | "
            f"{row['live']} | {row['live_input']} | {row['review_output']} |"
        )
    lines += [
        "",
        "## Not covered",
        "",
        *[f"- {item}" for item in cases_doc.get("not_covered", [])],
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    doc = json.loads(args.cases.read_text(encoding="utf-8"))
    text = render(evaluate(doc["cases"]), doc)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
