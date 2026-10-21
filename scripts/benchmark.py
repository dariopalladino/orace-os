#!/usr/bin/env python3
"""Measure routing behavior and summarize externally observed engineering runs."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import orace
import spec


def routing_run(root: Path, suite: dict) -> dict:
    results = []
    for case in suite.get("cases", []):
        args = argparse.Namespace(description=case["description"], path=case.get("paths", []),
                                  surface=case.get("surfaces", []), spec=[], mode=None,
                                  executor="native", external_name=None)
        start = time.perf_counter()
        plan = orace.task_plan(root, args)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
        selected = {item["id"] for item in plan["selected"]}
        required = set(case.get("required_specs", []))
        irrelevant = set(case.get("irrelevant_specs", []))
        results.append({
            "id": case["id"], "mode": plan["mode"], "expected_mode": case.get("expected_mode"),
            "mode_correct": plan["mode"] == case.get("expected_mode"),
            "required_policy_recall": len(selected & required) / len(required) if required else None,
            "irrelevant_selected": sorted(selected & irrelevant),
            "selected_count": len(selected), "estimated_context_tokens": plan["estimated_tokens"],
            "routing_duration_ms": elapsed_ms,
        })
    recalls = [item["required_policy_recall"] for item in results if item["required_policy_recall"] is not None]
    return {"schema_version": 1, "kind": "routing_benchmark",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "cases": results,
            "summary": {"case_count": len(results),
                        "mean_required_policy_recall": statistics.mean(recalls) if recalls else None,
                        "mode_accuracy": statistics.mean(item["mode_correct"] for item in results) if results else None,
                        "irrelevant_selection_count": sum(len(item["irrelevant_selected"]) for item in results),
                        "median_routing_ms": statistics.median(item["routing_duration_ms"] for item in results) if results else None},
            "limits": "Synthetic routing cases measure selector behavior, not developer productivity or production governance."}


def comparative_report(data: dict) -> dict:
    runs = data.get("runs", [])
    if not isinstance(runs, list):
        raise ValueError("runs must be a list")
    systems = sorted({item["system"] for item in runs})
    summaries = []
    numeric = ("onboarding_seconds", "routine_overhead_seconds", "tokens",
               "required_policy_recall", "irrelevant_selection_count",
               "violations_found", "supported_claim_rate")
    for system in systems:
        subset = [item for item in runs if item["system"] == system]
        summary = {"system": system, "run_count": len(subset)}
        for field in numeric:
            values = [item[field] for item in subset if isinstance(item.get(field), (int, float))]
            summary[f"median_{field}"] = statistics.median(values) if values else None
            summary[f"observed_{field}"] = len(values)
        summaries.append(summary)
    return {"schema_version": 1, "kind": "comparative_report", "systems": summaries,
            "limits": "Only supplied observed runs are summarized; missing measurements remain null."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run deterministic routing cases")
    run.add_argument("--suite", default="benchmarks/routing-suite.json")
    run.add_argument("--root", default=".")
    run.add_argument("--output", help="Write JSON report to this file")
    report = sub.add_parser("report", help="Summarize observed cross-system runs")
    report.add_argument("--input", required=True)
    report.add_argument("--output", help="Write JSON report to this file")
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            root = spec.repo_root(Path(args.root))
            suite = json.loads(Path(args.suite).read_text(encoding="utf-8"))
            result = routing_run(root, suite)
        else:
            data = json.loads(Path(args.input).read_text(encoding="utf-8"))
            result = comparative_report(data)
        output = json.dumps(result, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        return 0
    except (OSError, ValueError, KeyError, spec.SpecError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
