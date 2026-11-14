"""Legacy migration preserves history and installs a usable current runtime."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import migration  # noqa: E402
import spec  # noqa: E402


SOURCE = Path(__file__).resolve().parent.parent


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.target = self.tmp / "legacy"
        old = self.target / ".spec"
        for relative, content in {
            "INDEX.md": "# Old index\n",
            "15_architecture/decisions/ADR-001.md": "# Existing decision\n",
            "20_backlog/TASKS.md": "# Old tasks\n",
            "40_workspace/OLD-1/NOTES.md": "# Old evidence\n",
            "project.json": '{"old": true}\n',
        }.items():
            path = old / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        script = self.target / "scripts" / "orace.py"
        script.parent.mkdir()
        script.write_text("# old runtime\n", encoding="utf-8")
        (self.target / "AGENTS.md").write_text("# Project instructions\n", encoding="utf-8")
        adapter = self.target / ".claude" / "skills"
        for name, content in {"orace-workshop": "# stale workshop\n",
                              "custom-skill": "# project skill\n"}.items():
            path = adapter / name / "SKILL.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def test_preview_apply_archive_bridge_and_upgrade(self):
        report = migration.preview(SOURCE, self.target)
        self.assertEqual(report["status"], "ready")
        self.assertFalse((self.target / ".spec" / "installation.json").exists())
        self.assertIn("scripts/orace.py", report["runtime_files_to_replace"])
        self.assertTrue(report["claude_skills_directory_to_refresh"])
        report_path = self.target / migration.REPORT_NAME
        report_path.write_text(json.dumps(report), encoding="utf-8")
        applied = migration.apply(SOURCE, self.target, report_path)
        self.assertEqual(applied["status"], "applied")
        archive = self.target / applied["archive"]
        self.assertEqual((archive / "spec" / "INDEX.md").read_text(), "# Old index\n")
        self.assertEqual((archive / "spec" / "20_backlog" / "TASKS.md").read_text(), "# Old tasks\n")
        self.assertEqual((archive / "replaced" / "scripts" / "orace.py").read_text(), "# old runtime\n")
        self.assertEqual((archive / "replaced" / ".claude" / "skills" / "orace-workshop" / "SKILL.md").read_text(), "# stale workshop\n")
        self.assertEqual((self.target / ".claude" / "skills" / "custom-skill" / "SKILL.md").read_text(), "# project skill\n")
        self.assertNotIn("stale workshop", (self.target / ".claude" / "skills" / "orace-workshop" / "SKILL.md").read_text())
        self.assertIn("# Project instructions", (self.target / "AGENTS.md").read_text())
        self.assertTrue((self.target / ".spec" / "legacy" / "BRIDGE.md").is_file())
        index = (self.target / ".spec" / "INDEX.md").read_text()
        self.assertIn("| legacy-bridge |", index)
        refs = json.loads((self.target / ".spec" / "legacy" / "REFERENCES.json").read_text())
        self.assertEqual(len(refs["entries"]), 4)
        catalog = spec.load_playbook_catalog(self.target)
        registry = spec.load_registry(self.target, catalog)
        self.assertIn("legacy-bridge", registry)
        project = spec.load_project(self.target, registry, catalog)
        self.assertEqual(project["playbooks"], [])
        self.assertEqual(project["module_roots"], {})
        validation = subprocess.run([sys.executable, "scripts/spec.py", "validate"],
                                    cwd=self.target, capture_output=True, text=True)
        self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
        upgrade = migration.distribution.upgrade(SOURCE, self.target, dry_run=False)
        self.assertIn(".spec/INDEX.md", upgrade["conflicts"])
        self.assertIn("| legacy-bridge |", (self.target / ".spec" / "INDEX.md").read_text())

    def test_changed_legacy_file_blocks_apply(self):
        report_path = self.target / migration.REPORT_NAME
        report_path.write_text(json.dumps(migration.preview(SOURCE, self.target)), encoding="utf-8")
        (self.target / ".spec" / "INDEX.md").write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed"):
            migration.apply(SOURCE, self.target, report_path)
        self.assertFalse((self.target / ".spec" / "installation.json").exists())

    def test_migrated_project_uses_upgrade(self):
        report_path = self.target / migration.REPORT_NAME
        report_path.write_text(json.dumps(migration.preview(SOURCE, self.target)), encoding="utf-8")
        migration.apply(SOURCE, self.target, report_path)
        with self.assertRaisesRegex(ValueError, "upgrade"):
            migration.preview(SOURCE, self.target)

    def test_cli_preview_writes_report_and_symlink_blocks_apply(self):
        command = [sys.executable, str(SOURCE / "scripts" / "orace.py"),
                   "migrate", "--target", str(self.target), "--json"]
        preview = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        report_path = self.target / migration.REPORT_NAME
        self.assertTrue(report_path.is_file())
        self.assertEqual(json.loads(preview.stdout), json.loads(report_path.read_text()))
        old = self.target / ".spec" / "15_architecture" / "link.md"
        old.symlink_to("ADR-001.md")
        blocked = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(blocked.returncode, 1)
        self.assertIn(".spec/15_architecture/link.md", blocked.stdout)
        applied = subprocess.run(command[:-1] + ["--apply"], capture_output=True, text=True)
        self.assertNotEqual(applied.returncode, 0)
        self.assertFalse((self.target / ".spec" / "installation.json").exists())


if __name__ == "__main__":
    unittest.main()
