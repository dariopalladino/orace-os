"""Host adapters must match the canonical skill and role trees."""

from __future__ import annotations

import sys
import unittest
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sync_skills  # noqa: E402
import model_config  # noqa: E402

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

    def test_explicit_models_apply_only_to_selected_host_and_role(self):
        models = model_config.defaults()
        models["codex"] = {"workshop": "gpt-workshop", "supervisor": "gpt-supervisor",
                           "subagents": "gpt-subagent"}
        models["claude"]["subagents"] = "claude-worker"
        models["copilot"]["supervisor"] = "copilot-supervisor"
        roles = sync_skills.role_adapters(REPO, models)
        self.assertIn('model = "gpt-supervisor"', roles[Path(".codex/agents/orace_supervisor.toml")].decode())
        self.assertIn('model = "gpt-subagent"', roles[Path(".codex/agents/orace_planner.toml")].decode())
        self.assertIn('model: "claude-worker"', roles[Path(".claude/agents/PLANNER.md")].decode())
        self.assertNotIn("model:", roles[Path(".github/agents/orace_planner.agent.md")].decode())
        self.assertIn('model: "copilot-supervisor"',
                      roles[Path(".github/agents/orace_supervisor.agent.md")].decode())
        self.assertEqual(len([path for path in roles if path.parts[:2] == (".github", "agents")]), 10)

    def test_parallel_supervisor_contract_reaches_all_hosts(self):
        self.assertEqual(json.loads((REPO / ".spec/project.json").read_text())["orchestration"],
                         "supervisor")
        self.assertIn("run independent work packages in parallel", (REPO / "AGENTS.md").read_text())
        roles = sync_skills.role_adapters(REPO)
        for path in (Path(".claude/agents/SUPERVISOR.md"),
                     Path(".codex/agents/orace_supervisor.toml"),
                     Path(".github/agents/orace_supervisor.agent.md")):
            with self.subTest(host=path.parts[0]):
                self.assertIn("Launch independent packages concurrently", roles[path].decode())


if __name__ == "__main__":
    unittest.main()
