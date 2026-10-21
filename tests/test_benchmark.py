"""Benchmark reports distinguish measured routing from unobserved comparisons."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import benchmark  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


class BenchmarkTests(unittest.TestCase):
    def test_shipped_routing_suite_meets_its_declared_cases(self):
        suite = json.loads((REPO / "benchmarks" / "routing-suite.json").read_text(encoding="utf-8"))
        report = benchmark.routing_run(REPO, suite)
        self.assertEqual(report["summary"]["case_count"], 4)
        self.assertEqual(report["summary"]["mean_required_policy_recall"], 1)
        self.assertEqual(report["summary"]["mode_accuracy"], 1)
        self.assertEqual(report["summary"]["irrelevant_selection_count"], 0)

    def test_missing_comparative_measurements_remain_null(self):
        report = benchmark.comparative_report({"runs": [
            {"system": "ORACE-OS", "task": "one", "tokens": 100},
            {"system": "ORACE-OS", "task": "two", "tokens": 200},
        ]})
        summary = report["systems"][0]
        self.assertEqual(summary["median_tokens"], 150)
        self.assertIsNone(summary["median_supported_claim_rate"])
        self.assertEqual(summary["observed_supported_claim_rate"], 0)


if __name__ == "__main__":
    unittest.main()
