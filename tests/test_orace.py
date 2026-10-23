"""Task entry and verification evidence behavior."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import orace  # noqa: E402
from test_spec import build  # noqa: E402


class TaskEntryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        build(self.root, [
            "| protocol | .spec/00_global/P.md | * | - | * |",
            "| security | .spec/00_global/S.md | auth,security | protocol | * |",
            "| ui | .spec/00_global/U.md | frontend | - | * |",
        ], globals_={"P.md": "p", "S.md": "s", "U.md": "u"},
            config={"module_roots": {"frontend": ["web/"], "implementation": ["web/"]},
                    "checks": {"framework": ["python3 -c 'print(1)'"]}})

    def plan(self, description, *, path=(), surface=(), mode=None):
        args = argparse.Namespace(description=description, path=list(path), surface=list(surface),
                                  spec=[], mode=mode)
        return orace.task_plan(self.root, args)

    def test_small_css_fix_is_lite(self):
        plan = self.plan("Fix CSS margin", path=["web/button.css"])
        self.assertEqual(plan["mode"], "lite")
        self.assertIn("ui", [item["id"] for item in plan["selected"]])

    def test_auth_request_escalates_lite_to_governed(self):
        plan = self.plan("Fix password reset validation", path=["web/reset.tsx"], mode="lite")
        self.assertEqual(plan["mode"], "governed")
        self.assertIn("security", [item["id"] for item in plan["selected"]])

    def test_sensitive_filename_escalates_even_with_routine_description(self):
        plan = self.plan("Fix formatting", path=["web/src/TokenStore.ts"], mode="lite")
        self.assertEqual(plan["mode"], "governed")
        self.assertIn("auth", plan["inferred_surfaces"])

    def test_unmapped_path_needs_classification(self):
        with self.assertRaises(orace.spec.SpecError):
            self.plan("Fix a thing", path=["unmapped/file.ts"])
        plan = self.plan("Fix a thing", path=["unmapped/file.ts"], surface=["frontend"])
        self.assertEqual(plan["unmapped_paths"], ["unmapped/file.ts"])

    def test_external_execution_contract_keeps_approval_authority_explicit(self):
        args = argparse.Namespace(description="Fix password reset validation", path=["web/reset.tsx"],
                                  surface=[], spec=[], mode="lite", executor="external",
                                  external_name="Superpowers")
        plan = orace.task_plan(self.root, args)
        contract = plan["execution_contract"]
        self.assertEqual(contract["adapter"], "external")
        self.assertEqual(contract["approval_gate"], "explicit_before_execution")
        self.assertEqual(contract["review_gate"], "independent")
        self.assertIn("accepted architecture", contract["decision_authority"])

    def test_verify_captures_exit_and_redacts_output(self):
        config_path = self.root / ".spec" / "project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["checks"] = {"sample": ["python3 -c 'print(\"token=abc123\")'"]}
        config_path.write_text(json.dumps(config), encoding="utf-8")
        args = argparse.Namespace(check=["sample"], task="demo", output="evidence.json",
                                  timeout=10, max_output=12000, authorized_path=[], base="HEAD")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(orace.verify(self.root, args), 0)
        evidence = json.loads((self.root / "evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["checks"][0]["exit_code"], 0)
        self.assertIn("token=[REDACTED]", evidence["checks"][0]["output_tail"])
        self.assertNotIn("abc123", evidence["checks"][0]["output_tail"])
        self.assertEqual(evidence["status"], "passed")
        self.assertEqual(evidence["authorized_scope"]["status"], "unproven")

    def test_verify_reports_out_of_scope_changes(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", ".spec"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                        "commit", "-qm", "base"], cwd=self.root, check=True)
        (self.root / "unexpected.txt").write_text("outside", encoding="utf-8")
        args = argparse.Namespace(check=["framework"], task="scope", output="evidence.json",
                                  timeout=10, max_output=12000, authorized_path=["web/"], base="HEAD")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(orace.verify(self.root, args), 1)
        evidence = json.loads((self.root / "evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["authorized_scope"]["status"], "failed")
        self.assertIn("unexpected.txt", evidence["authorized_scope"]["outside_scope"])

    def test_verify_refuses_empty_check_group(self):
        config_path = self.root / ".spec" / "project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["checks"]["empty"] = []
        config_path.write_text(json.dumps(config), encoding="utf-8")
        args = argparse.Namespace(check=["empty"], task="empty", output=None,
                                  timeout=10, max_output=12000, authorized_path=[], base="HEAD")
        with self.assertRaisesRegex(orace.spec.SpecError, "empty"):
            orace.verify(self.root, args)

    def test_discovery_keeps_observation_separate_from_approval(self):
        (self.root / "package.json").write_text(json.dumps({
            "dependencies": {"react": "^19.0.0"},
            "devDependencies": {"vitest": "^3.0.0"},
            "scripts": {"test": "vitest run"},
        }), encoding="utf-8")
        profile = orace.discover(self.root)
        self.assertEqual(profile["status"], "proposal_only")
        self.assertIn("react-frontend", profile["proposed_playbooks"])
        self.assertTrue(any("vitest" in item["fact"] for item in profile["observed"]))
        self.assertIn("authentication architecture", profile["unknowns"])

    def test_coverage_handles_deleted_and_renamed_paths(self):
        (self.root / "web").mkdir()
        old = self.root / "web" / "old.ts"
        old.write_text("export const value = 1;\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "web/old.ts"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                        "commit", "-qm", "base"], cwd=self.root, check=True)
        old.rename(self.root / "web" / "new.ts")
        subprocess.run(["git", "add", "-A", "web"], cwd=self.root, check=True)
        entries = orace.diff_paths(self.root, "HEAD")
        self.assertIn("web/old.ts", [item["path"] for item in entries])
        self.assertIn("web/new.ts", [item["path"] for item in entries])
        self.assertIn("frontend", orace.spec.surfaces_for_path(
            {"module_roots": {"frontend": ["web/"]}}, "web/old.ts"))

    def test_review_distinguishes_check_evidence_from_behavior_claim(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", ".spec"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                        "commit", "-qm", "base"], cwd=self.root, check=True)
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, text=True,
                             capture_output=True, check=True).stdout.strip()
        plan = self.plan("Fix CSS margin", path=["web/button.css"])
        command = "python3 -c 'print(1)'"
        handoff = {"schema_version": 1,
                   "selected_spec_ids": plan["execution_contract"]["selected_spec_ids"],
                   "changed_files": ["web/button.css"],
                   "criteria": [{"id": "AC-01", "claim": "covered"},
                                {"id": "AC-02", "claim": "covered", "check_commands": [command]}]}
        evidence = {"commit_sha": sha,
                    "workspace_state": orace.workspace_state(self.root, "HEAD", ["evidence.json"]),
                    "checks": [{"command": command, "exit_code": 0, "passed": True}]}
        (self.root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
        report = orace.review_handoff(self.root, plan, handoff, ["evidence.json"])
        self.assertEqual([item["status"] for item in report["criteria"]], ["unproven", "covered"])
        self.assertEqual(report["status"], "ready_for_review")
        evidence["checks"][0].update({"exit_code": 1, "passed": False})
        (self.root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
        report = orace.review_handoff(self.root, plan, handoff, ["evidence.json"])
        self.assertEqual(report["criteria"][1]["status"], "contradicted")

    def test_changed_worktree_stales_verification_evidence(self):
        config_path = self.root / ".spec" / "project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["checks"]["frontend_when_present"] = config["checks"]["framework"]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", ".spec"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                        "commit", "-qm", "base"], cwd=self.root, check=True)
        web = self.root / "web"
        web.mkdir()
        component = web / "button.css"
        component.write_text("button { margin: 1px; }\n", encoding="utf-8")
        args = argparse.Namespace(check=["frontend_when_present"], task="css", output="evidence.json",
                                  timeout=10, max_output=12000, authorized_path=[], base="HEAD")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(orace.verify(self.root, args), 0)
        evidence = json.loads((self.root / "evidence.json").read_text(encoding="utf-8"))
        self.assertTrue(orace.evidence_is_current(self.root, evidence, evidence["commit_sha"]))
        entries = [{"status": "M", "path": "web/button.css", "role": "current"}]
        initial = orace.change_report(self.root, entries, "Fix CSS margin", set(), ["evidence.json"])
        self.assertEqual(initial["checks"][0]["status"], "covered")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(orace.main(["--root", str(self.root), "check", "--path", "web/button.css",
                                         "--evidence", "evidence.json", "--strict", "--json"]), 1)
        component.write_text("button { margin: 2px; }\n", encoding="utf-8")
        self.assertFalse(orace.evidence_is_current(self.root, evidence, evidence["commit_sha"]))
        stale = orace.change_report(self.root, entries, "Fix CSS margin", set(), ["evidence.json"])
        self.assertEqual(stale["checks"][0]["status"], "unproven")
        self.assertIn("stale_evidence", [item["kind"] for item in stale["findings"]])

    def test_playbook_filename_does_not_require_application_checks(self):
        config_path = self.root / ".spec" / "project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["checks"]["frontend_when_present"] = ["npm test"]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        entries = [{"status": "M", "path": ".spec/10_playbooks/react-frontend/PACK.md",
                    "role": "current"}]
        report = orace.change_report(self.root, entries, "Update policy wording", set(), [])
        self.assertNotIn("frontend", report["surfaces"])
        self.assertNotIn("npm test", [item["command"] for item in report["checks"]])

    def test_live_change_check_executes_configured_commands(self):
        config_path = self.root / ".spec" / "project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["checks"]["frontend_when_present"] = ["python3 -c 'print(1)'"]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        entries = [{"status": "M", "path": "web/button.css", "role": "current"}]
        report = orace.change_report(self.root, entries, "Fix CSS margin", set(), [])
        self.assertEqual(report["checks"][0]["status"], "unproven")
        orace.run_report_checks(self.root, report, 10, 12000)
        self.assertEqual(report["checks"][0]["status"], "covered")
        self.assertTrue(report["live_checks"][0]["passed"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(orace.main(["--root", str(self.root), "check", "--path", "web/button.css",
                                         "--run-checks", "--strict", "--json"]), 0)

    def test_run_executes_plan_and_preserves_current_evidence(self):
        config_path = self.root / ".spec" / "project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["checks"]["frontend_when_present"] = ["python3 -c 'print(1)'"]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", ".spec"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                        "commit", "-qm", "base"], cwd=self.root, check=True)
        plan = self.plan("Fix CSS margin", path=["web/button.css"])
        plan["acceptance_criteria"].append(
            {"id": "AC-03", "kind": "behavior", "text": "Button is aligned at mobile width"})
        (self.root / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        (self.root / "executor.py").write_text(
            "from pathlib import Path\nPath('web').mkdir(exist_ok=True)\n"
            "Path('web/button.css').write_text('button { margin: 1px; }\\n')\n",
            encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            result = orace.main(["--root", str(self.root), "run", "--plan", "plan.json",
                                 "--command", f"{shlex.quote(sys.executable)} executor.py",
                                 "--authorize-path", "web/", "--evidence", "evidence.json",
                                 "--output", "run.json", "--timeout", "10"])
        self.assertEqual(result, 0)
        report = json.loads((self.root / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "ready_for_review")
        self.assertEqual(report["scope"]["changed_files"], ["web/button.css"])
        self.assertEqual(report["review"]["criteria"][0]["status"], "unproven")
        self.assertEqual(report["review"]["criteria"][1]["status"], "covered")
        self.assertEqual(report["review"]["criteria"][2]["status"], "unproven")
        evidence = json.loads((self.root / "evidence.json").read_text(encoding="utf-8"))
        self.assertTrue(orace.evidence_is_current(self.root, evidence, evidence["commit_sha"]))

    def test_run_rejects_out_of_scope_executor_changes(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", ".spec"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                        "commit", "-qm", "base"], cwd=self.root, check=True)
        plan = self.plan("Fix CSS margin", path=["web/button.css"])
        (self.root / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        (self.root / "executor.py").write_text(
            "from pathlib import Path\nPath('outside.txt').write_text('unexpected')\n",
            encoding="utf-8")
        args = argparse.Namespace(plan="plan.json", executor_command=f"{shlex.quote(sys.executable)} executor.py",
                                  authorize_path=["web/"], approval_record=None,
                                  evidence="evidence.json", output=None, timeout=10, max_output=12000)
        report = orace.run_task(self.root, args)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["scope"]["outside_scope"], ["outside.txt"])
        self.assertFalse((self.root / "evidence.json").exists())

    def test_governed_run_requires_plan_bound_approval_record(self):
        plan = self.plan("Fix password reset validation", path=["web/reset.tsx"])
        (self.root / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        args = argparse.Namespace(plan="plan.json", executor_command="python3 -c 'print(1)'",
                                  authorize_path=["web/"], approval_record=None,
                                  evidence="evidence.json", output=None, timeout=10, max_output=12000)
        with self.assertRaisesRegex(orace.spec.SpecError, "approval-record"):
            orace.run_task(self.root, args)

    def test_governed_run_accepts_matching_approval_record(self):
        config_path = self.root / ".spec" / "project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["checks"]["frontend_when_present"] = ["python3 -c 'print(1)'"]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", ".spec"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                        "commit", "-qm", "base"], cwd=self.root, check=True)
        plan = self.plan("Fix password reset validation", path=["web/reset.tsx"])
        plan_bytes = json.dumps(plan).encode("utf-8")
        (self.root / "plan.json").write_bytes(plan_bytes)
        approval = {"decision": "approved", "approver": "Test Reviewer",
                    "plan_sha256": hashlib.sha256(plan_bytes).hexdigest()}
        (self.root / "approval.json").write_text(json.dumps(approval), encoding="utf-8")
        (self.root / "executor.py").write_text(
            "from pathlib import Path\nPath('web').mkdir(exist_ok=True)\n"
            "Path('web/reset.tsx').write_text('export const ready = true;\\n')\n",
            encoding="utf-8")
        args = argparse.Namespace(plan="plan.json", executor_command=f"{shlex.quote(sys.executable)} executor.py",
                                  authorize_path=["web/"], approval_record="approval.json",
                                  evidence="evidence.json", output=None, timeout=10, max_output=12000)
        with contextlib.redirect_stderr(io.StringIO()):
            report = orace.run_task(self.root, args)
        self.assertEqual(report["status"], "ready_for_review")
        self.assertTrue(report["review"]["independent_review_required"])

    def test_run_detects_modified_check_configuration(self):
        config_path = self.root / ".spec" / "project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["checks"]["frontend_when_present"] = ["python3 -c 'print(1)'"]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", ".spec"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                        "commit", "-qm", "base"], cwd=self.root, check=True)
        plan = self.plan("Fix CSS margin", path=["web/button.css"])
        (self.root / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        (self.root / "executor.py").write_text(
            "import json\nfrom pathlib import Path\np = Path('.spec/project.json')\n"
            "c = json.loads(p.read_text())\nc['checks']['frontend_when_present'] = []\n"
            "p.write_text(json.dumps(c))\n",
            encoding="utf-8")
        args = argparse.Namespace(plan="plan.json", executor_command=f"{shlex.quote(sys.executable)} executor.py",
                                  authorize_path=["web/", ".spec/"], approval_record=None,
                                  evidence="evidence.json", output=None, timeout=10, max_output=12000)
        report = orace.run_task(self.root, args)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(report["scope"]["checks_changed"])


class OnboardingTests(unittest.TestCase):
    def test_init_preserves_existing_instructions_and_does_not_activate_guesses(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "AGENTS.md").write_text("# Existing conventions\n", encoding="utf-8")
            (target / "package.json").write_text(json.dumps({"dependencies": {"react": "^19"}}),
                                                 encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(orace.main(["init", "--target", str(target)]), 0)
            config = json.loads((target / ".spec" / "project.json").read_text(encoding="utf-8"))
            proposal = json.loads((target / ".spec" / "40_workspace" / "PROJECT_DISCOVERY.json")
                                  .read_text(encoding="utf-8"))
            self.assertEqual(config["playbooks"], [])
            self.assertEqual(config["module_roots"], {})
            self.assertEqual(config["models"]["codex"],
                             {"workshop": "auto", "supervisor": "auto", "subagents": "auto"})
            self.assertIn("react-frontend", proposal["proposed_playbooks"])
            self.assertIn("# Existing conventions", (target / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertTrue((target / "docs" / "CODEX.md").is_file())
            self.assertTrue((target / "docs" / "CONTEXT_MANAGEMENT.md").is_file())
            self.assertTrue((target / ".agents" / "roles" / "REVIEWER.md").is_file())
            self.assertTrue((target / ".codex" / "agents" / "orace_reviewer.toml").is_file())
            self.assertFalse((target / "tests").exists())
            self.assertTrue((target / ".spec" / "installation.json").is_file())
            self.assertFalse((target / ".spec" / "40_workspace" / "orace-technology-profile").exists())
            self.assertNotIn("ORACE-TECH-001", (target / ".spec" / "20_backlog" / "TASKS.md")
                              .read_text(encoding="utf-8"))
            self.assertNotIn("ORACE-TECH-001", (target / ".spec" / "30_delivery" / "PROMOTION_LOG.md")
                              .read_text(encoding="utf-8"))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(orace.spec.main(["--root", str(target), "validate"]), 0)
                self.assertEqual(orace.main(["--root", str(target), "doctor", "--json"]), 0)
            adapter_check = subprocess.run([sys.executable, str(target / "scripts" / "sync_skills.py"),
                                            "--root", str(target), "--check"],
                                           cwd=target, text=True, capture_output=True, check=False)
            self.assertEqual(adapter_check.returncode, 0, adapter_check.stderr)
            task = subprocess.run([sys.executable, str(target / "scripts" / "orace.py"),
                                   "--root", str(target), "task", "Fix button spacing",
                                   "--path", "web/Button.tsx", "--surface", "frontend", "--json"],
                                  cwd=target, text=True, capture_output=True, check=False)
            self.assertEqual(task.returncode, 0, task.stderr)
            self.assertEqual(json.loads(task.stdout)["mode"], "lite")
            (target / "scripts" / "orace.py").write_text("# locally edited\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(orace.main(["--root", str(target), "doctor", "--json"]), 1)

    def test_init_renders_host_models_and_launch_uses_main_role_choice(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(orace.main([
                    "init", "--target", str(target), "--harness", "codex",
                    "--workshop-model", "gpt-workshop", "--supervisor-model", "gpt-supervisor",
                    "--subagent-model", "gpt-worker"]), 0)
            config = json.loads((target / ".spec/project.json").read_text())
            self.assertEqual(config["models"]["codex"]["workshop"], "gpt-workshop")
            self.assertEqual(config["models"]["claude"]["workshop"], "auto")
            self.assertIn('model = "gpt-worker"',
                          (target / ".codex/agents/orace_planner.toml").read_text())
            self.assertIn('model = "gpt-supervisor"',
                          (target / ".codex/agents/orace_supervisor.toml").read_text())
            self.assertNotIn("model:",
                             (target / ".github/agents/orace_planner.agent.md").read_text())
            with mock.patch.object(orace.subprocess, "call", return_value=0) as run:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(orace.main(["--root", str(target), "launch",
                                                 "--harness", "codex", "--role", "workshop"]), 0)
                run.assert_called_once_with(["codex", "--model", "gpt-workshop"], cwd=target.resolve())
            config["models"]["codex"]["subagents"] = "gpt-worker-v2"
            (target / ".spec/project.json").write_text(json.dumps(config), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(orace.distribution.sync_skills.sync(target.resolve()), 0)
                self.assertEqual(orace.main(["--root", str(target), "doctor", "--json"]), 0)
            preview = orace.distribution.upgrade(Path(__file__).resolve().parent.parent,
                                                 target.resolve(), dry_run=True)
            self.assertNotIn(".codex/agents/orace_planner.toml", preview["conflicts"])


if __name__ == "__main__":
    unittest.main()
