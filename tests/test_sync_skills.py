"""The Claude adapter must never drift from the canonical skill tree."""

from __future__ import annotations

import sys
import unittest
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


if __name__ == "__main__":
    unittest.main()
