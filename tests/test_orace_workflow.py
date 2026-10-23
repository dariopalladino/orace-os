"""Contract tests for the ORACE technology-profile workflow."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import init_project  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WORKSHOP_ROOT = REPO / ".agents" / "skills" / "orace-workshop"
WORKSHOP_ENTRY = (WORKSHOP_ROOT / "SKILL.md").read_text(encoding="utf-8")
WORKSHOP = WORKSHOP_ENTRY + "\n" + "\n".join(
    path.read_text(encoding="utf-8") for path in sorted((WORKSHOP_ROOT / "references").glob("*.md"))
)
BOOTSTRAP_ROOT = REPO / ".agents" / "skills" / "spec-bootstrap"
BOOTSTRAP_ENTRY = (BOOTSTRAP_ROOT / "SKILL.md").read_text(encoding="utf-8")
BOOTSTRAP = BOOTSTRAP_ENTRY + "\n" + "\n".join(
    path.read_text(encoding="utf-8") for path in sorted((BOOTSTRAP_ROOT / "references").glob("*.md"))
)
ADOPTION = (REPO / "docs" / "ADOPTION.md").read_text(encoding="utf-8")
README = (REPO / "README.md").read_text(encoding="utf-8")


class OraceWorkshopTechnologyTests(unittest.TestCase):
    def test_workshop_loads_one_phase_at_a_time(self):
        self.assertLess(len(WORKSHOP_ENTRY), 7000)
        self.assertIn("Read only the reference for the active phase", WORKSHOP_ENTRY)
        for phase in "orace":
            self.assertTrue((WORKSHOP_ROOT / "references" / f"phase-{phase}.md").is_file())

    def test_resume_requires_persisted_approaches_and_technology_profile(self):
        self.assertIn("approaches.md + technology-profile.md", WORKSHOP)
        self.assertIn("A is done when `approaches.md` and `technology-profile.md` exist", WORKSHOP)
        self.assertIn("zero ADRs is valid", WORKSHOP)

    def test_targeted_technology_rerun_is_non_destructive(self):
        self.assertIn("--rerun technology", WORKSHOP)
        self.assertIn("Preserve `approaches.md`, existing ADRs, views, and evidence", WORKSHOP)
        self.assertIn("do not silently edit a view", WORKSHOP)
        self.assertIn("Retain`, `Migrate`, `Retire`, or `TBD", WORKSHOP)
        self.assertIn("list the files that phase owns", WORKSHOP)
        self.assertIn("registered routing rows that point to them", WORKSHOP)
        self.assertIn("open or completed backlog tasks that cite those rows", WORKSHOP)
        self.assertIn("report which later artifacts may now be stale", WORKSHOP)

    def test_requirements_stay_technology_neutral(self):
        self.assertIn("Keep Phase R implementation-neutral", WORKSHOP)
        self.assertIn("record the technology later in Phase A", WORKSHOP)

    def test_technology_profile_has_agent_ready_traceability(self):
        for required in (
            "### technology-profile.md template",
            "## Component Technology Baseline",
            "Version policy",
            "Lifecycle status",
            "Rationale / Traceability",
            "Source of truth",
            "Playbook",
            "## Delivery Toolchain",
            "## Unresolved Technology Decisions",
        ):
            with self.subTest(required=required):
                self.assertIn(required, WORKSHOP)

    def test_existing_project_discovery_requires_evidence_and_confirmation(self):
        self.assertIn("inspect repository evidence using targeted file discovery (`rg --files`)", WORKSHOP)
        self.assertIn("Evidence is a candidate, not a decision", WORKSHOP)
        self.assertIn("A lockfile alone does not prove", WORKSHOP)
        self.assertIn("Never convert a detected dependency into `Retain` or `Accepted`", WORKSHOP)


class OraceWorkshopUsageTests(unittest.TestCase):
    def test_usage_boundary_precedes_workshop_work_and_is_invocation_scoped(self):
        self.assertIn("before the resume scan, repository discovery, or first interview question", WORKSHOP)
        self.assertIn("report usage for **this invocation only**", WORKSHOP)
        self.assertIn("sum root-agent turns and any subagent turns attributable to this workshop", WORKSHOP)

    def test_usage_accuracy_modes_and_sources_are_explicit(self):
        self.assertIn("**Measured (host-reported, best-effort):**", WORKSHOP)
        self.assertIn("**Estimated (trace-counted):**", WORKSHOP)
        self.assertIn("**Unavailable:**", WORKSHOP)
        self.assertIn("Accuracy: Measured (host-reported, best-effort)", WORKSHOP)
        self.assertIn("Accuracy: Estimated (trace-counted)", WORKSHOP)
        self.assertIn("Accuracy: Unavailable", WORKSHOP)
        self.assertIn("Never present `characters ÷ 4`", WORKSHOP)

    def test_usage_categories_are_not_double_counted(self):
        self.assertIn("`total_tokens = input_tokens + output_tokens`", WORKSHOP)
        self.assertIn("Cached input is already included in input tokens", WORKSHOP)
        self.assertIn("Reasoning tokens are already included in output tokens", WORKSHOP)
        self.assertIn("print `not reported` rather than treating it as zero", WORKSHOP)

    def test_usage_report_discloses_temporal_and_billing_limits(self):
        self.assertIn("last content", WORKSHOP)
        self.assertIn("final response while generating that response", WORKSHOP)
        self.assertIn("not a final bill", WORKSHOP)
        self.assertIn("do not write it to `outcomes.md`", WORKSHOP)


class SpecBootstrapTechnologyTests(unittest.TestCase):
    def test_bootstrap_loads_one_step_at_a_time(self):
        self.assertLess(len(BOOTSTRAP_ENTRY), 5000)
        self.assertIn("load only the next step reference", BOOTSTRAP_ENTRY)

    def test_bootstrap_uses_profile_for_playbooks_roots_and_checks(self):
        self.assertIn("Use `technology-profile.md` as the primary source", BOOTSTRAP)
        self.assertIn("module/deployment views plus accepted ADRs as cross-checks", BOOTSTRAP)
        self.assertIn("Report these mismatches before proposing configuration", BOOTSTRAP)
        self.assertIn("view or accepted ADR that contradicts the profile's lifecycle status", BOOTSTRAP)
        self.assertIn("propose `module_roots` from the module view", BOOTSTRAP)
        self.assertIn("Propose `.spec/project.json` `checks`", BOOTSTRAP)
        self.assertIn("Do not invent a conventional command", BOOTSTRAP)

    def test_bootstrap_registers_new_phase_a_artifacts_selectively(self):
        self.assertIn("| `approaches.md` |", BOOTSTRAP)
        self.assertIn("| `technology-profile.md` |", BOOTSTRAP)
        self.assertIn("not automatically universal", BOOTSTRAP)

    def test_older_architecture_gets_a_targeted_upgrade_path(self):
        self.assertIn("/orace-workshop <path> --rerun technology", BOOTSTRAP)
        self.assertIn("without resetting Outcomes, Requirements, existing ADRs, or Evidence", BOOTSTRAP)
        self.assertIn("--rerun technology", ADOPTION)


class InitializerGuidanceTests(unittest.TestCase):
    def test_initializer_offers_discovery_before_optional_workshop(self):
        with tempfile.TemporaryDirectory() as target, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(init_project.main(["--target", target, "--dry-run"]), 0)
        guidance = output.getvalue()
        self.assertLess(guidance.index("scripts/orace.py discover"), guidance.index("Review .spec/project.json"))
        self.assertIn("scripts/orace.py task", guidance)
        self.assertIn("as architecture needs grow", guidance)
        self.assertIn("--rerun technology", guidance)


class ReadmeLatestChangesTests(unittest.TestCase):
    def test_readme_explains_the_technology_lifecycle_and_sources_of_truth(self):
        for required in (
            "### Technology baseline: project truth, not generic guidance",
            "Phase R",
            "implementation-neutral",
            "Retain`, `Migrate`, `Retire`, or `TBD",
            "`technology-profile.md`",
            "`.spec/10_playbooks/`",
            "`.spec/project.json`",
            "/orace-workshop .spec/15_architecture --rerun technology",
            "`/spec-bootstrap` then treats the confirmed profile as the primary source",
        ):
            with self.subTest(required=required):
                self.assertIn(required, README)

    def test_readme_explains_token_accuracy_accounting_and_scope(self):
        for required in (
            "### Workshop token consumption",
            "Measured (host-reported, best-effort)",
            "Estimated (trace-counted)",
            "Unavailable",
            "`total_tokens = input_tokens + output_tokens`",
            "Cached input is already included in input",
            "reasoning tokens are already included in output",
            "post-response accounting",
            "not a final bill",
            "not persisted",
            "`characters ÷ 4`",
            "never reported as consumed workshop tokens",
        ):
            with self.subTest(required=required):
                self.assertIn(required, README)


if __name__ == "__main__":
    unittest.main()
