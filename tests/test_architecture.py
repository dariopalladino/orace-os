"""Architecture impact reports keep accepted decisions visible without changing them."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import architecture  # noqa: E402
import orace  # noqa: E402
import spec  # noqa: E402
from test_spec import build  # noqa: E402


class ArchitectureImpactTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        build(self.root, [
            "| protocol | .spec/00_global/P.md | * | - | * |",
            "| adr-payments | .spec/15_architecture/decisions/001-payments.md | data | protocol | * |",
        ], globals_={"P.md": "p"}, config={"module_roots": {"backend": ["services/"]}})
        architecture_root = self.root / ".spec" / "15_architecture"
        (architecture_root / "decisions").mkdir(parents=True)
        (architecture_root / "quality-scenarios.md").write_text("# QA-AVAIL-01\n", encoding="utf-8")
        self.adr = architecture_root / "decisions" / "001-payments.md"
        self.adr.write_text(
            "---\nstatus: Accepted\nowner: Payments team\naffected_paths:\n"
            "  - services/payments/\nscenarios_addressed:\n  - QA-AVAIL-01\n"
            "supersedes: none\n---\n# ADR-001: Process payments\n",
            encoding="utf-8",
        )

    def loaded(self):
        catalog = spec.load_playbook_catalog(self.root)
        specs = spec.load_registry(self.root, catalog)
        config = spec.load_project(self.root, specs, catalog)
        return specs, config

    def test_exact_path_impact_and_scenario_link(self):
        specs, config = self.loaded()
        report = architecture.impact(self.root, specs, config,
                                     ["services/payments/handler.py"], {"backend"})
        self.assertEqual(report["affected_decisions"][0]["match"], "path")
        self.assertEqual(report["findings"], [])

    def test_missing_scenario_and_superseded_link_are_reported(self):
        self.adr.write_text(self.adr.read_text(encoding="utf-8")
                            .replace("QA-AVAIL-01", "QA-AVAIL-99")
                            .replace("supersedes: none", "supersedes: ADR-999"), encoding="utf-8")
        specs, config = self.loaded()
        kinds = {item["kind"] for item in architecture.impact(
            self.root, specs, config, ["services/payments/handler.py"], {"backend"})["findings"]}
        self.assertIn("scenario_link_missing", kinds)
        self.assertIn("superseded_adr_missing", kinds)

    def test_routing_gap_is_visible_to_change_check(self):
        report = orace.change_report(self.root, [{"status": "M", "path": "services/payments/handler.py",
                                                  "role": "current"}], "Fix flow", set(), [])
        self.assertEqual(report["mode"], "governed")
        self.assertIn("architecture_routing_gap", {item["kind"] for item in report["findings"]})


if __name__ == "__main__":
    unittest.main()
