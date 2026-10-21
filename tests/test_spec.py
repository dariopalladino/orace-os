"""Tests for the SDDF routing engine.

Each test builds a throwaway repository so the assertions are about the engine,
not about whichever documents the framework happens to ship today.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import spec  # noqa: E402

REPO = Path(__file__).resolve().parent.parent

HEADER = (
    "# Index\n\n"
    "| ID | Path | Surfaces | Requires | Playbooks |\n"
    "| --- | --- | --- | --- | --- |\n"
)


def build(root: Path, rows: list[str], *, playbooks: dict[str, str] | None = None,
          globals_: dict[str, str] | None = None, config: dict | None = None) -> None:
    (root / ".spec" / "00_global").mkdir(parents=True)
    (root / ".spec" / "10_playbooks").mkdir(parents=True)
    for name, body in (globals_ or {}).items():
        (root / ".spec" / "00_global" / name).write_text(body, encoding="utf-8")
    for name, body in (playbooks or {}).items():
        folder = root / ".spec" / "10_playbooks" / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "PACK.md").write_text(body, encoding="utf-8")
    (root / ".spec" / "INDEX.md").write_text(HEADER + "\n".join(rows) + "\n", encoding="utf-8")
    base = {
        "version": 2,
        "playbooks": list(playbooks or {}),
        "orchestration": "supervisor",
        "module_roots": {},
        "checks": {},
    }
    base.update(config or {})
    (root / ".spec" / "project.json").write_text(json.dumps(base), encoding="utf-8")


class TempRepo(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)

    def load(self):
        catalog = spec.load_playbook_catalog(self.dir)
        specs = spec.load_registry(self.dir, catalog)
        config = spec.load_project(self.dir, specs, catalog)
        return specs, config, catalog

    def select(self, surfaces=(), paths=(), explicit=(), playbooks=None):
        specs, config, _ = self.load()
        active = frozenset(playbooks if playbooks is not None else config["playbooks"])
        return spec.select(specs, config, set(surfaces), list(paths), list(explicit), active)


class SelectionTests(TempRepo):
    def setUp(self) -> None:
        super().setUp()
        build(
            self.dir,
            [
                "| protocol | .spec/00_global/P.md | * | - | * |",
                "| security | .spec/00_global/S.md | security,auth | protocol | * |",
                "| ui | .spec/00_global/U.md | frontend | - | * |",
                "| play-react | .spec/10_playbooks/react/PACK.md | frontend | ui | react |",
                "| play-kotlin | .spec/10_playbooks/kotlin/PACK.md | native | - | kotlin |",
            ],
            globals_={"P.md": "protocol", "S.md": "security", "U.md": "ui"},
            playbooks={"react": "react pack", "kotlin": "kotlin pack"},
            config={"module_roots": {"frontend": ["web/"], "auth": ["web/src/auth/"]}},
        )

    def test_baseline_always_selected(self):
        self.assertIn("protocol", self.select(surfaces=["frontend"]))

    def test_surface_match(self):
        chosen = self.select(surfaces=["frontend"])
        self.assertIn("ui", chosen)
        self.assertNotIn("security", chosen)

    def test_dependency_closure_is_transitive(self):
        chosen = self.select(surfaces=["frontend"])
        self.assertIn("play-react", chosen)
        self.assertIn("ui", chosen)
        self.assertIn("required by:play-react", chosen["ui"])

    def test_inactive_playbook_is_not_selected(self):
        chosen = self.select(surfaces=["native"], playbooks=["react"])
        self.assertNotIn("play-kotlin", chosen)

    def test_path_adds_every_matching_surface(self):
        """A file under two module roots routes to both — this is how a UI path picks up auth."""
        chosen = self.select(paths=["web/src/auth/token.ts"])
        self.assertIn("ui", chosen)
        self.assertIn("security", chosen)
        self.assertTrue(any("-> auth" in reason for reason in chosen["security"]))

    def test_unknown_path_is_an_error_not_a_silent_empty_selection(self):
        with self.assertRaises(spec.SpecError):
            self.select(paths=["unmapped/file.ts"])

    def test_unmapped_path_requires_explicit_semantic_classification(self):
        chosen = self.select(surfaces=["security"], paths=["unmapped/token.ts"])
        self.assertIn("security", chosen)

    def test_segment_glob_does_not_cross_directories(self):
        _, config, _ = self.load()
        config["module_roots"]["data"] = ["services/*/migrations/"]
        self.assertIn("data", spec.surfaces_for_path(config, "services/payments/migrations/001.py"))
        self.assertNotIn("data", spec.surfaces_for_path(config, "services/payments/src/migrations/001.py"))

    def test_double_star_matches_nested_directories(self):
        _, config, _ = self.load()
        config["module_roots"]["data"] = ["services/**/migrations/"]
        self.assertIn("data", spec.surfaces_for_path(config, "services/payments/src/migrations/001.py"))
        self.assertIn("data", spec.surfaces_for_path(config, "services/migrations/001.py"))

    def test_nested_roots_and_windows_separators(self):
        _, config, _ = self.load()
        self.assertEqual(spec.surfaces_for_path(config, r"web\src\auth\token.ts"), {"frontend", "auth"})
        self.assertEqual(spec.surfaces_for_path(config, "webish/src/auth/token.ts"), set())

    def test_unsafe_candidate_path_rejected(self):
        _, config, _ = self.load()
        for value in ("../web/src/a.ts", "/web/src/a.ts", r"C:\web\src\a.ts"):
            with self.subTest(value=value), self.assertRaises(spec.SpecError):
                spec.surfaces_for_path(config, value)

    def test_explicit_reference_to_inactive_playbook_raises(self):
        """An incompatible explicit reference is a decision, never a silent omission."""
        with self.assertRaises(spec.SpecError) as ctx:
            self.select(surfaces=["frontend"], explicit=["play-kotlin"], playbooks=["react"])
        self.assertIn("not active", str(ctx.exception))

    def test_unknown_surface_raises(self):
        with self.assertRaises(spec.SpecError):
            self.select(surfaces=["nonsense"])


class RegistryTests(TempRepo):
    def test_invalid_module_root_glob_rejected(self):
        build(self.dir, ["| a | .spec/00_global/A.md | docs | - | * |"],
              globals_={"A.md": "a"}, config={"module_roots": {"data": ["services/pay*/migrations/"]}})
        with self.assertRaises(spec.SpecError):
            self.load()
    def test_missing_dependency_raises(self):
        build(self.dir, ["| a | .spec/00_global/A.md | docs | ghost | * |"], globals_={"A.md": "a"})
        with self.assertRaises(spec.SpecError):
            self.load()

    def test_dependency_cycle_raises(self):
        build(
            self.dir,
            [
                "| a | .spec/00_global/A.md | docs | b | * |",
                "| b | .spec/00_global/B.md | docs | a | * |",
            ],
            globals_={"A.md": "a", "B.md": "b"},
        )
        with self.assertRaises(spec.SpecError) as ctx:
            self.load()
        self.assertIn("cycle", str(ctx.exception))

    def test_duplicate_id_raises(self):
        build(
            self.dir,
            [
                "| a | .spec/00_global/A.md | docs | - | * |",
                "| a | .spec/00_global/B.md | docs | - | * |",
            ],
            globals_={"A.md": "a", "B.md": "b"},
        )
        with self.assertRaises(spec.SpecError):
            self.load()

    def test_missing_document_raises(self):
        build(self.dir, ["| a | .spec/00_global/A.md | docs | - | * |"])
        with self.assertRaises(spec.SpecError):
            self.load()

    def test_path_traversal_rejected(self):
        build(self.dir, ["| a | ../outside.md | docs | - | * |"], globals_={"A.md": "a"})
        with self.assertRaises(spec.SpecError):
            self.load()

    def test_unknown_playbook_in_row_raises(self):
        build(self.dir, ["| a | .spec/00_global/A.md | docs | - | ghost |"], globals_={"A.md": "a"})
        with self.assertRaises(spec.SpecError):
            self.load()

    def test_unregistered_global_policy_is_reported(self):
        build(
            self.dir,
            ["| a | .spec/00_global/A.md | docs | - | * |"],
            globals_={"A.md": "a", "ORPHAN.md": "nobody routes to me"},
        )
        specs, config, catalog = self.load()
        problems = spec.check_coverage(self.dir, specs, config, catalog)
        self.assertTrue(any("ORPHAN.md" in problem for problem in problems))

    def test_unregistered_architecture_artifact_is_reported(self):
        """The rule that keeps an ADR from being written and never read."""
        build(self.dir, ["| a | .spec/00_global/A.md | docs | - | * |"],
              globals_={"A.md": "a"},
              config={"architecture_root": ".spec/15_architecture"})
        decisions = self.dir / ".spec" / "15_architecture" / "decisions"
        decisions.mkdir(parents=True)
        (decisions / "001-event-sourcing.md").write_text("adr", encoding="utf-8")
        (self.dir / ".spec" / "15_architecture" / "README.md").write_text("placeholder", encoding="utf-8")
        specs, config, catalog = self.load()
        problems = spec.check_coverage(self.dir, specs, config, catalog)
        self.assertTrue(any("001-event-sourcing.md" in problem for problem in problems))
        self.assertFalse(any("README.md" in problem for problem in problems))

    def test_active_playbook_without_a_row_raises(self):
        build(self.dir, ["| a | .spec/00_global/A.md | docs | - | * |"],
              globals_={"A.md": "a"}, playbooks={"react": "pack"})
        with self.assertRaises(spec.SpecError) as ctx:
            self.load()
        self.assertIn("no registered routing row", str(ctx.exception))


class TaskTests(TempRepo):
    def test_task_routing_metadata_is_read(self):
        build(
            self.dir,
            [
                "| protocol | .spec/00_global/P.md | * | - | * |",
                "| security | .spec/00_global/S.md | security | - | * |",
            ],
            globals_={"P.md": "p", "S.md": "s"},
        )
        backlog = self.dir / ".spec" / "20_backlog"
        backlog.mkdir(parents=True)
        (backlog / "TASKS.md").write_text(
            "# Backlog\n\n## PAY-014 — Screening outage degradation\n\n"
            "- Surfaces: security, backend\n"
            "- Specifications: security\n"
            "- Paths: services/payments/\n",
            encoding="utf-8",
        )
        task = spec.read_task(self.dir, "PAY-014")
        self.assertEqual(task["surfaces"], ["security", "backend"])
        self.assertEqual(task["specifications"], ["security"])
        self.assertEqual(task["paths"], ["services/payments/"])

    def test_missing_task_raises(self):
        build(self.dir, ["| a | .spec/00_global/A.md | docs | - | * |"], globals_={"A.md": "a"})
        (self.dir / ".spec" / "20_backlog").mkdir(parents=True)
        (self.dir / ".spec" / "20_backlog" / "TASKS.md").write_text("# Backlog\n", encoding="utf-8")
        with self.assertRaises(spec.SpecError):
            spec.read_task(self.dir, "NOPE-001")


class ShippedFrameworkTests(unittest.TestCase):
    """The framework's own registry must be valid and its routing cases must hold."""

    def test_validate_passes(self):
        self.assertEqual(spec.main(["--root", str(REPO), "validate"]), 0)

    def test_every_playbook_pack_states_that_architecture_governs(self):
        for pack in sorted((REPO / ".spec" / "10_playbooks").glob("*/PACK.md")):
            with self.subTest(pack=pack.name):
                self.assertIn("**Precedence.**", pack.read_text(encoding="utf-8"))

    def test_documentation_only_work_stays_cheap(self):
        catalog = spec.load_playbook_catalog(REPO)
        specs = spec.load_registry(REPO, catalog)
        config = spec.load_project(REPO, specs, catalog)
        chosen = spec.select(specs, config, {"docs"}, [], [], frozenset(config["playbooks"]))
        _, tokens = spec.measure(REPO, specs, sorted(chosen))
        self.assertLess(tokens, 3000, "the baseline is paid on every task; keep it small")


if __name__ == "__main__":
    unittest.main()
