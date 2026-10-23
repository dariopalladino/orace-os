"""Managed runtime upgrades preserve project edits and avoid copying internal tests."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import distribution  # noqa: E402


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.source = self.temp / "source"
        self.target = self.temp / "target"
        (self.source / "scripts").mkdir(parents=True)
        (self.source / ".agents" / "skills" / "sample").mkdir(parents=True)
        (self.source / ".agents" / "roles").mkdir(parents=True)
        (self.source / ".codex" / "agents").mkdir(parents=True)
        (self.target / ".spec").mkdir(parents=True)
        (self.source / "VERSION").write_text("0.1.0\n", encoding="utf-8")
        (self.source / "scripts" / "runtime.py").write_text("v1\n", encoding="utf-8")
        (self.source / ".agents" / "skills" / "sample" / "SKILL.md").write_text("skill\n", encoding="utf-8")
        (self.source / ".agents" / "roles" / "SAMPLE.md").write_text(
            "---\nname: Sample\ndescription: Sample role.\n---\n\nFollow AGENTS.md.\n", encoding="utf-8")
        (self.source / ".codex" / "agents" / "orace_sample.toml").write_text('name = "orace_sample"\n', encoding="utf-8")

    def test_upgrade_preserves_modified_files_and_previews_changes(self):
        distribution.install(self.source, self.target, fresh_spec=False, dry_run=False)
        runtime = self.target / "scripts" / "runtime.py"
        self.assertEqual(runtime.read_text(encoding="utf-8"), "v1\n")
        self.assertTrue((self.target / ".claude" / "skills").exists())
        self.assertTrue((self.target / ".agents" / "roles" / "SAMPLE.md").is_file())
        self.assertTrue((self.target / ".codex" / "agents" / "orace_sample.toml").is_file())
        runtime.write_text("project edit\n", encoding="utf-8")
        (self.source / "scripts" / "runtime.py").write_text("v2\n", encoding="utf-8")
        (self.source / "scripts" / "new.py").write_text("new\n", encoding="utf-8")
        (self.source / "VERSION").write_text("0.2.0\n", encoding="utf-8")
        preview = distribution.upgrade(self.source, self.target, dry_run=True)
        self.assertIn("scripts/runtime.py", preview["conflicts"])
        self.assertIn("add scripts/new.py", preview["actions"])
        self.assertFalse((self.target / "scripts" / "new.py").exists())
        applied = distribution.upgrade(self.source, self.target, dry_run=False)
        self.assertIn("scripts/runtime.py", applied["conflicts"])
        self.assertEqual(runtime.read_text(encoding="utf-8"), "project edit\n")
        self.assertEqual((self.target / "scripts" / "new.py").read_text(encoding="utf-8"), "new\n")
        manifest = json.loads((self.target / distribution.MANIFEST).read_text(encoding="utf-8"))
        self.assertEqual(manifest["framework_version"], "0.2.0")


if __name__ == "__main__":
    unittest.main()
