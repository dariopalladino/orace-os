"""Host adapters must match the canonical skill and role trees."""

from __future__ import annotations

import sys
import unittest
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sync_skills  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


class SyncSkillsTests(unittest.TestCase):
    def test_adapter_is_in_sync(self):
        self.assertEqual(sync_skills.check(REPO), 0)

    def test_every_canonical_skill_has_frontmatter(self):
        skills = sorted((REPO / ".agents" / "skills").glob("*/SKILL.md"))
        self.assertGreater(len(skills), 0)
        for skill in skills:
            with self.subTest(skill=skill.parent.name):
                text = skill.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"), "SKILL.md needs YAML frontmatter")
                header = text.split("---", 2)[1]
                self.assertIn("name:", header)
                self.assertIn("description:", header)

    def test_codex_roles_have_complete_schema_and_no_pinned_permissions(self):
        roles = sync_skills.role_adapters(REPO)
        codex = {path: content for path, content in roles.items()
                 if path.parts[:2] == (".codex", "agents")}
        self.assertEqual(len(codex), 10)
        for path, content in codex.items():
            with self.subTest(role=path.name):
                lines = content.decode("utf-8").splitlines()
                self.assertEqual(len(lines), 3)
                fields = dict(line.split(" = ", 1) for line in lines)
                self.assertEqual(set(fields), {"name", "description", "developer_instructions"})
                self.assertTrue(json.loads(fields["name"]).startswith("orace_"))
                self.assertTrue(json.loads(fields["description"]))
                self.assertIn("AGENTS.md", json.loads(fields["developer_instructions"]))


if __name__ == "__main__":
    unittest.main()
