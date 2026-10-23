#!/usr/bin/env python3
"""Task-first entry point for an SDDF repository (Python 3.10+, standard library)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import spec
import init_project
import architecture
import distribution
import model_config

LEVELS = ("lite", "standard", "governed")
SENSITIVE = {"auth", "security", "data", "architecture", "governance", "infra", "hitl"}
STANDARD = {"backend", "api", "domain", "ai", "release", "observability"}
CODE = {"backend", "frontend", "native", "api", "data", "auth", "security", "infra", "ai", "implementation"}
HINTS = (
    (r"\b(password|login|sign.?in|token|oauth|session|credential|permission|authorization|authentication)\b", {"auth", "security"}, "identity or access wording"),
    (r"\b(secret|encrypt|sensitive|personal data|pii|privacy|vulnerabilit|security)\b", {"security"}, "sensitive data or security wording"),
    (r"\b(migrat|database|schema|table|transaction|payment|financial)\b", {"data"}, "data or transaction wording"),
    (r"\b(api|endpoint|public contract|webhook)\b", {"api", "backend"}, "API wording"),
    (r"\b(css|layout|button|screen|mobile view|frontend|react|ui)\b", {"frontend"}, "UI wording"),
    (r"\b(deploy|infrastructure|terraform|kubernetes|cluster|ci pipeline)\b", {"infra"}, "deployment wording"),
    (r"\b(adr|architecture|architectural decision)\b", {"architecture"}, "architecture wording"),
    (r"\b(documentation|readme|typo|docs)\b", {"docs"}, "documentation wording"),
)
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(password|secret|token|api[_-]?key|authorization)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+"),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
)


def infer_surfaces(description: str) -> tuple[set[str], list[str]]:
    found: set[str] = set()
    reasons: list[str] = []
    for pattern, surfaces, reason in HINTS:
        if re.search(pattern, description, re.IGNORECASE):
            found.update(surfaces)
            reasons.append(reason)
    return found, reasons


def classify_mode(description: str, surfaces: set[str], selected: list[dict],
                  requested: str | None) -> tuple[str, list[str]]:
    reasons: list[str] = []
    lower = description.lower()
    if surfaces & SENSITIVE:
        reasons.append("sensitive or architecture-impacting surface: " + ", ".join(sorted(surfaces & SENSITIVE)))
    if re.search(r"\b(public contract|irreversible|production data|payment|financial transaction)\b", lower):
        reasons.append("high-impact change wording")
    if any("/decisions/" in item["path"] for item in selected):
        reasons.append("selected architecture decision")
    if reasons:
        minimum = "governed"
    elif surfaces & STANDARD:
        minimum = "standard"
        reasons.append("feature or service change")
    elif surfaces & CODE and not re.search(r"\b(fix|correct|align|typo|format|spacing|margin)\b", lower):
        minimum = "standard"
        reasons.append("implementation change without a narrow repair signal")
    else:
        minimum = "lite"
        reasons.append("narrow routine change")
    chosen = LEVELS[max(LEVELS.index(minimum), LEVELS.index(requested or minimum))]
    if requested and chosen != requested:
        reasons.append(f"requested {requested} escalated to {chosen}")
    return chosen, reasons


def suggested_checks(config: dict, surfaces: set[str], paths: list[str]) -> list[str]:
    checks = []
    if any(path.startswith((".spec/", ".agents/", ".claude/", ".codex/", "scripts/")) for path in paths):
        if "framework" in config["checks"]:
            checks.append("framework")
    for surface, key in (("backend", "backend_when_present"), ("api", "backend_when_present"),
                         ("frontend", "frontend_when_present"), ("native", "native_when_present")):
        if surface in surfaces and key in config["checks"] and key not in checks:
            checks.append(key)
    return checks


def task_plan(root: Path, args: argparse.Namespace) -> dict:
    catalog = spec.load_playbook_catalog(root)
    specs = spec.load_registry(root, catalog)
    config = spec.load_project(root, specs, catalog)
    guessed, clues = infer_surfaces(args.description)
    explicit = set(args.surface)
    paths = list(args.path)
    semantic_paths = [path for path in paths if not path.startswith(
        (".spec/", ".agents/", ".claude/", ".codex/", "docs/", "benchmarks/"))
        and not path.endswith((".md", ".json", ".yml", ".yaml"))]
    path_words = re.sub(r"([a-z])([A-Z])", r"\1 \2", " ".join(semantic_paths))
    path_words = re.sub(r"[/_.-]", " ", path_words)
    path_guesses, path_clues = infer_surfaces(path_words)
    guessed.update(path_guesses)
    clues.extend(f"path hint: {clue}" for clue in path_clues)
    path_surfaces: set[str] = set()
    unmapped: list[str] = []
    for path in paths:
        derived = spec.surfaces_for_path(config, path)
        path_surfaces.update(derived)
        if not derived:
            unmapped.append(path)
    surfaces = explicit | guessed | path_surfaces
    if not surfaces:
        raise spec.SpecError("Cannot classify this task from its description or paths; pass --surface")
    if unmapped and not (explicit or guessed):
        raise spec.SpecError("Unmapped paths require explicit --surface classification: " + ", ".join(unmapped))
    if surfaces & CODE:
        surfaces.add("implementation")
    active = frozenset(config["playbooks"])
    reasons = spec.select(specs, config, surfaces, paths, list(args.spec), active)
    selected = [
        {"id": key, "path": specs[key].path, "reasons": reasons[key]}
        for key in sorted(reasons, key=lambda key: specs[key].path)
    ]
    _, tokens = spec.measure(root, specs, list(reasons))
    hard = config["context_budget"].get("hard_tokens")
    if hard and tokens > hard:
        raise spec.SpecError(f"Selection estimates {tokens} tokens, above hard budget {hard}")
    mode, mode_reasons = classify_mode(args.description, surfaces, selected, args.mode)
    checks = suggested_checks(config, surfaces, paths)
    executor = getattr(args, "executor", "native")
    external_name = getattr(args, "external_name", None)
    if executor == "external" and not external_name:
        raise spec.SpecError("--executor external requires --external-name")
    execution_contract = {
        "schema_version": 1,
        "adapter": executor,
        "external_name": external_name if executor == "external" else None,
        "selected_spec_ids": [item["id"] for item in selected],
        "authorized_paths": paths,
        "scope_confirmed": bool(paths) and not unmapped,
        "approval_gate": "explicit_before_execution" if mode == "governed" else "request_authorization",
        "review_gate": "independent" if mode == "governed" else ("structured" if mode == "standard" else "compact"),
        "decision_authority": "accepted architecture and authorized human decision maker",
        "required_check_groups": checks,
        "handoff_fields": ["changed_files", "commands", "exit_codes", "criterion_evidence", "unproven_claims"],
    }
    return {
        "task": args.description,
        "requested_mode": args.mode,
        "explicit_spec_ids": list(args.spec),
        "mode": mode,
        "mode_reasons": mode_reasons,
        "active_playbooks": sorted(active),
        "surfaces": sorted(surfaces),
        "inferred_surfaces": sorted(guessed),
        "inference_clues": clues,
        "explicit_surfaces": sorted(explicit),
        "paths": paths,
        "unmapped_paths": unmapped,
        "path_scope_confirmed": bool(paths) and not unmapped,
        "selected": selected,
        "estimated_tokens": tokens,
        "check_groups": checks,
        "execution_contract": execution_contract,
        "acceptance_draft": [
            f"The reported behavior is resolved: {args.description}",
            "A relevant regression check passes and its actual result is recorded.",
        ],
        "acceptance_criteria": [
            {"id": "AC-01", "kind": "behavior", "text": f"The reported behavior is resolved: {args.description}"},
            {"id": "AC-02", "kind": "check", "text": "A relevant regression check passes and its actual result is recorded."},
        ],
        "next_step": {
            "lite": "Implement the scoped change; record a compact verification result.",
            "standard": "Confirm acceptance criteria and scope, implement, run relevant checks, and review evidence.",
            "governed": "Confirm architecture impact, scope, and approval before implementation; obtain independent review.",
        }[mode],
    }


def print_plan(plan: dict, explain: bool = False) -> None:
    print(f"Mode: {plan['mode'].title()} — {'; '.join(plan['mode_reasons'])}")
    print("Surfaces: " + ", ".join(plan["surfaces"]))
    if not plan["active_playbooks"]:
        print("Active playbooks: none; confirm discovery and activate applicable packs")
    if plan["inferred_surfaces"]:
        print("Inferred from request or path names (confirm): " + ", ".join(plan["inferred_surfaces"]))
    if not plan["paths"]:
        print("Affected paths: unconfirmed; identify files before implementation")
    elif plan["unmapped_paths"]:
        print("Unmapped paths (classification requires confirmation): " + ", ".join(plan["unmapped_paths"]))
    print("Selected specifications:")
    for item in plan["selected"]:
        print(f"  {item['id']}: {item['path']} ({'; '.join(item['reasons'])})")
    print("Suggested check groups: " + (", ".join(plan["check_groups"]) or "select relevant checks"))
    print(f"Estimated context: ~{plan['estimated_tokens']} tokens (characters/4)")
    if not explain:
        print("Draft acceptance:")
        for criterion in plan["acceptance_draft"]:
            print("  - " + criterion)
        print("Next: " + plan["next_step"])


def redact(value: str) -> str:
    for pattern in SECRET_PATTERNS:
        if pattern.pattern.startswith("(?i)\\bBearer"):
            value = pattern.sub("Bearer [REDACTED]", value)
        elif "@" in pattern.pattern:
            value = pattern.sub("[EMAIL REDACTED]", value)
        else:
            value = pattern.sub(lambda match: match.group(1) + "=[REDACTED]", value)
    return value


def discover(target: Path) -> dict:
    """Record observed repository facts without treating them as approved choices."""
    observed: list[dict] = []
    suggestions: set[str] = set()
    skipped = {".git", ".spec", ".agents", ".claude", ".codex", "node_modules", ".venv", "venv", "build", "dist"}
    for directory, folders, files in os.walk(target):
        folders[:] = [name for name in folders if name not in skipped]
        parent = Path(directory)
        depth = len(parent.relative_to(target).parts)
        if depth >= 3:
            folders[:] = []
        for name in files:
            path = parent / name
            relative = path.relative_to(target).as_posix()
            if name == "package.json":
                try:
                    manifest = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    observed.append({"path": relative, "fact": "package manifest present but unreadable"})
                    continue
                if not isinstance(manifest, dict):
                    observed.append({"path": relative, "fact": "package manifest is not an object"})
                    continue
                runtime_deps = manifest.get("dependencies") or {}
                dev_deps = manifest.get("devDependencies") or {}
                if not isinstance(runtime_deps, dict) or not isinstance(dev_deps, dict):
                    observed.append({"path": relative, "fact": "dependency declarations are not objects"})
                    continue
                deps = {**runtime_deps, **dev_deps}
                for dependency, pack in (("react", "react-frontend"), ("@auth0/auth0-react", "auth0-identity")):
                    if dependency in deps:
                        observed.append({"path": relative, "fact": f"dependency {dependency} declared"})
                        suggestions.add(pack)
                for tool in ("typescript", "vitest", "jest"):
                    if tool in deps:
                        observed.append({"path": relative, "fact": f"dependency {tool} declared"})
                for script in ("test", "lint", "typecheck"):
                    if script in manifest.get("scripts", {}):
                        observed.append({"path": relative, "fact": f"script {script} declared"})
            elif name in {"pyproject.toml", "requirements.txt", "Pipfile"}:
                observed.append({"path": relative, "fact": "Python manifest present"})
                suggestions.add("python-backend")
            elif name in {"build.gradle", "build.gradle.kts"}:
                observed.append({"path": relative, "fact": "Gradle build present"})
                suggestions.add("kotlin-native")
            elif ((name.startswith("test_") and name.endswith(".py"))
                  or name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx"))):
                observed.append({"path": relative, "fact": "test file present"})
            elif name.endswith(".md") and ("/decisions/" in "/" + relative or name.startswith("ADR-")):
                observed.append({"path": relative, "fact": "possible architecture decision"})
            elif relative.startswith(".github/workflows/") and name.endswith((".yml", ".yaml")):
                observed.append({"path": relative, "fact": "CI workflow present"})
    return {
        "status": "proposal_only",
        "observed": observed,
        "proposed_playbooks": sorted(suggestions),
        "unknowns": ["authentication architecture", "deployment architecture", "acceptance measures", "whether observed dependencies are intended to remain"],
        "note": "Observed files and declared dependencies are evidence candidates, not approved architecture or active configuration.",
    }


def diff_paths(root: Path, revision: str) -> list[dict]:
    if not revision or revision.startswith("-") or any(ord(char) < 32 for char in revision):
        raise spec.SpecError(f"Unsafe git revision: {revision!r}")
    result = subprocess.run(["git", "diff", "--name-status", "-z", "--find-renames", revision],
                            cwd=root, capture_output=True, check=False)
    if result.returncode:
        raise spec.SpecError("Cannot inspect git diff: " + result.stderr.decode("utf-8", "replace").strip())
    fields = result.stdout.decode("utf-8", "replace").split("\x00")
    entries: list[dict] = []
    index = 0
    while index < len(fields) and fields[index]:
        status = fields[index]
        index += 1
        if status.startswith(("R", "C")):
            if index + 1 >= len(fields):
                raise spec.SpecError("Malformed rename/copy record in git diff")
            entries.append({"status": status, "path": fields[index], "role": "old"})
            entries.append({"status": status, "path": fields[index + 1], "role": "new"})
            index += 2
        else:
            if index >= len(fields):
                raise spec.SpecError("Malformed path record in git diff")
            entries.append({"status": status, "path": fields[index], "role": "current"})
            index += 1
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z"],
                               cwd=root, capture_output=True, check=False)
    if untracked.returncode:
        raise spec.SpecError("Cannot inspect untracked paths: " + untracked.stderr.decode("utf-8", "replace").strip())
    for path in untracked.stdout.decode("utf-8", "replace").split("\x00"):
        if path:
            entries.append({"status": "U", "path": path, "role": "new"})
    return entries


def workspace_state(root: Path, base: str, excluded_paths: list[str] | None = None) -> dict:
    """Fingerprint changed file contents so same-commit worktree edits stale evidence."""
    excluded = set(excluded_paths or [])
    try:
        entries = diff_paths(root, base)
    except spec.SpecError as exc:
        return {"status": "unavailable", "reason": str(exc)}
    files = {}
    try:
        for path in sorted({item["path"] for item in entries} - excluded):
            target = spec.safe_path(root, path)
            files[path] = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
    except (OSError, spec.SpecError) as exc:
        return {"status": "unavailable", "reason": str(exc)}
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"status": "captured", "base": base, "excluded_paths": sorted(excluded),
            "files": files, "sha256": hashlib.sha256(encoded).hexdigest()}


def evidence_is_current(root: Path, record: dict, head_sha: str | None) -> bool:
    state = record.get("workspace_state")
    if not head_sha or record.get("commit_sha") != head_sha or not isinstance(state, dict):
        return False
    if state.get("status") != "captured" or not isinstance(state.get("excluded_paths"), list):
        return False
    current = workspace_state(root, state.get("base", "HEAD"), state["excluded_paths"])
    return current.get("status") == "captured" and current.get("sha256") == state.get("sha256")


def coverage(root: Path, args: argparse.Namespace) -> int:
    catalog = spec.load_playbook_catalog(root)
    specs = spec.load_registry(root, catalog)
    config = spec.load_project(root, specs, catalog)
    entries = [{"status": "provided", "path": path, "role": "current"} for path in args.path]
    if args.diff is not None:
        entries += diff_paths(root, args.diff)
    if not entries:
        raise spec.SpecError("Provide --path or --diff REVISION for routing coverage")
    for entry in entries:
        entry["surfaces"] = sorted(spec.surfaces_for_path(config, entry["path"]))
        entry["mapped"] = bool(entry["surfaces"])
    report = {"paths": entries, "unmapped": [item["path"] for item in entries if not item["mapped"]]}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for item in entries:
            label = ", ".join(item["surfaces"]) if item["mapped"] else "UNMAPPED — classify explicitly"
            print(f"{item['status']} {item['path']} [{item['role']}]: {label}")
    return 1 if report["unmapped"] else 0


def change_report(root: Path, entries: list[dict], description: str,
                  explicit_surfaces: set[str], evidence_paths: list[str]) -> dict:
    catalog = spec.load_playbook_catalog(root)
    specs = spec.load_registry(root, catalog)
    config = spec.load_project(root, specs, catalog)
    paths = list(dict.fromkeys(item["path"] for item in entries))
    path_surfaces: set[str] = set()
    unmapped = []
    for path in paths:
        found = spec.surfaces_for_path(config, path)
        path_surfaces.update(found)
        if not found:
            unmapped.append(path)
    semantic_paths = [path for path in paths if not path.startswith(
        (".spec/", ".agents/", ".claude/", ".codex/", "docs/", "benchmarks/"))
        and not path.endswith((".md", ".json", ".yml", ".yaml"))]
    path_words = re.sub(r"([a-z])([A-Z])", r"\1 \2", " ".join(semantic_paths))
    path_words = re.sub(r"[/_.-]", " ", path_words)
    inferred, clues = infer_surfaces(description + " " + path_words)
    surfaces = explicit_surfaces | inferred | path_surfaces
    if surfaces & CODE:
        surfaces.add("implementation")
    reasons = spec.select(specs, config, surfaces, [path for path in paths if path not in unmapped],
                          [], frozenset(config["playbooks"]))
    selected = [{"id": key, "path": specs[key].path, "reasons": reasons[key]}
                for key in sorted(reasons, key=lambda key: specs[key].path)]
    arch = architecture.impact(root, specs, config, paths, surfaces)
    selected_ids = set(reasons)
    for item in arch["affected_decisions"]:
        if item["match"] == "path" and item["id"] not in selected_ids:
            arch["findings"].append({"kind": "architecture_routing_gap", "id": item["id"],
                                     "detail": "ADR governs a changed path but routing did not select it"})
    mode, mode_reasons = classify_mode(description, surfaces, selected, None)
    if arch["affected_decisions"] and mode != "governed":
        mode = "governed"
        mode_reasons.append("registered architecture decision may be affected")
    expected_groups = suggested_checks(config, path_surfaces, paths)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                          capture_output=True, check=False)
    head_sha = head.stdout.strip() if head.returncode == 0 else None
    evidence = []
    for path in evidence_paths:
        source = spec.safe_path(root, path)
        try:
            record = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise spec.SpecError(f"Cannot read evidence {path}: {exc}") from exc
        if not isinstance(record, dict) or not isinstance(record.get("checks"), list):
            raise spec.SpecError(f"Evidence {path} has no checks list")
        evidence.append({"path": path, "record": record})
    stale = [item["path"] for item in evidence
             if not evidence_is_current(root, item["record"], head_sha)]
    current_evidence = [item for item in evidence if item["path"] not in stale]
    checks = []
    for group in expected_groups:
        for command in config["checks"][group]:
            observations = [(item["path"], check)
                            for item in current_evidence for check in item["record"]["checks"]
                            if isinstance(check, dict) and check.get("command") == command]
            if any(check.get("passed") is False for _, check in observations):
                status = "contradicted"
            elif any(check.get("passed") is True and check.get("exit_code") == 0 for _, check in observations):
                status = "covered"
            else:
                status = "unproven"
            checks.append({"group": group, "command": command, "status": status,
                           "evidence": sorted({path for path, _ in observations}),
                           "note": "evidence commit and worktree fingerprint must match"})
    findings = []
    findings.extend({"kind": "stale_evidence", "path": path} for path in stale)
    if unmapped:
        findings.append({"kind": "unmapped_paths", "paths": unmapped,
                         "detail": "confirm semantic surfaces or add module roots"})
    if inferred:
        findings.append({"kind": "classification_to_confirm", "surfaces": sorted(inferred),
                         "clues": clues})
    if mode == "governed":
        findings.append({"kind": "approval_external", "detail":
                         "independent review and required approval must be enforced by the host/branch policy"})
    findings += arch["findings"]
    _, tokens = spec.measure(root, specs, list(reasons))
    return {"schema_version": 1, "base_changes": entries, "head_sha": head_sha,
            "mode": mode, "mode_reasons": mode_reasons, "surfaces": sorted(surfaces),
            "selected": selected, "estimated_tokens": tokens, "architecture": arch,
            "checks": checks, "findings": findings,
            "status": "attention" if findings or any(item["status"] != "covered" for item in checks) else "clear",
            "claim_scope": "path routing, architecture links, and supplied check records; semantic acceptance and human approval are external"}


def print_change_report(report: dict) -> None:
    print(f"Mode: {report['mode'].title()} — {'; '.join(report['mode_reasons'])}")
    print("Surfaces: " + (", ".join(report["surfaces"]) or "unclassified"))
    print("Selected: " + (", ".join(item["id"] for item in report["selected"]) or "none"))
    for item in report["architecture"]["affected_decisions"]:
        print(f"Architecture: {item['id']} ({item['status']}, {item['match']})")
    for item in report["checks"]:
        print(f"Check {item['status']}: {item['command']}")
    for item in report["findings"]:
        print(f"Finding {item['kind']}: {item.get('detail', item.get('paths', ''))}")
    print("Status: " + report["status"])


def run_report_checks(root: Path, report: dict, timeout: int, max_output: int) -> None:
    """Run required commands now, so the result does not rely on supplied JSON."""
    observed = {}
    for item in report["checks"]:
        key = (item["group"], item["command"])
        if key not in observed:
            observed[key] = execute_check(root, *key, timeout, max_output)
        result = observed[key]
        item["status"] = "covered" if result["passed"] else "contradicted"
        item["evidence"] = ["live_command"]
        item["note"] = "command executed in this check invocation"
    report["live_checks"] = list(observed.values())
    report["status"] = "attention" if report["findings"] or any(
        item["status"] != "covered" for item in report["checks"]) else "clear"


def review_handoff(root: Path, plan: dict, handoff: dict, evidence_files: list[str]) -> dict:
    if handoff.get("schema_version") != 1 or not isinstance(handoff.get("criteria"), list):
        raise spec.SpecError("Handoff must have schema_version: 1 and a criteria list")
    contract = plan.get("execution_contract", {})
    expected_specs = set(contract.get("selected_spec_ids", []))
    reported_specs = set(handoff.get("selected_spec_ids", []))
    findings = []
    if not expected_specs <= reported_specs:
        findings.append({"kind": "missing_spec_handoff", "ids": sorted(expected_specs - reported_specs)})
    changed = handoff.get("changed_files", [])
    if not isinstance(changed, list) or not all(isinstance(path, str) for path in changed):
        raise spec.SpecError("Handoff changed_files must be a list of paths")
    allowed = [spec.path_parts(path) for path in contract.get("authorized_paths", [])]
    if contract.get("scope_confirmed"):
        outside = [path for path in changed if not any(
            spec.path_parts(path)[:len(prefix)] == prefix for prefix in allowed)]
        if outside:
            findings.append({"kind": "out_of_scope", "paths": outside})
    else:
        findings.append({"kind": "scope_unproven", "detail": "plan did not confirm affected paths"})
    current_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                                 capture_output=True, check=False)
    head = current_sha.stdout.strip() if current_sha.returncode == 0 else None
    observations = []
    for path in evidence_files:
        source = spec.safe_path(root, path)
        try:
            record = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise spec.SpecError(f"Cannot read evidence {path}: {exc}") from exc
        if not isinstance(record, dict) or not isinstance(record.get("checks"), list):
            raise spec.SpecError(f"Evidence {path} has no checks list")
        if evidence_is_current(root, record, head):
            observations.extend(item for item in record["checks"] if isinstance(item, dict))
        else:
            findings.append({"kind": "stale_evidence", "path": path})
    claims = {item.get("id"): item for item in handoff["criteria"] if isinstance(item, dict)}
    criteria = []
    for required in plan.get("acceptance_criteria", []):
        claim = claims.get(required["id"], {})
        commands = claim.get("check_commands", [])
        if not isinstance(commands, list):
            raise spec.SpecError(f"Criterion {required['id']} check_commands must be a list")
        matched = [item for item in observations if item.get("command") in commands]
        if claim.get("claim") == "contradicted" or any(item.get("passed") is False for item in matched):
            status = "contradicted"
        elif required["kind"] == "check" and commands and any(
                item.get("passed") is True and item.get("exit_code") == 0 for item in matched):
            status = "covered"
        else:
            status = "unproven"
        criteria.append({"id": required["id"], "kind": required["kind"],
                         "status": status, "claimed": claim.get("claim", "unreported"),
                         "observed_checks": sorted({item.get("command", "") for item in matched})})
    ready = not findings and all(item["status"] != "contradicted" and
                                 (item["kind"] != "check" or item["status"] == "covered")
                                 for item in criteria)
    return {"schema_version": 1, "criteria": criteria, "findings": findings,
            "status": "ready_for_review" if ready else "needs_evidence",
            "independent_review_required": plan.get("mode") == "governed",
            "claim_scope": "machine preflight only; a reviewer judges behavior and architecture measures"}


def execute_check(root: Path, group: str, command: str, timeout: int, max_output: int) -> dict:
    argv = shlex.split(command)
    if not argv:
        raise spec.SpecError(f"checks.{group} contains an empty command")
    try:
        result = subprocess.run(argv, cwd=root, text=True, capture_output=True,
                                timeout=timeout, check=False)
        code = result.returncode
        output = redact((result.stdout + result.stderr)[-max_output:])
    except (OSError, subprocess.TimeoutExpired) as exc:
        code = None
        output = redact(str(exc))
    return {"group": group, "command": redact(command), "exit_code": code,
            "passed": code == 0, "output_tail": output,
            "timestamp_utc": datetime.now(timezone.utc).isoformat()}


def verify(root: Path, args: argparse.Namespace) -> int:
    catalog = spec.load_playbook_catalog(root)
    specs = spec.load_registry(root, catalog)
    config = spec.load_project(root, specs, catalog)
    groups = args.check or ["framework"]
    unknown = set(groups) - set(config["checks"])
    if unknown:
        raise spec.SpecError("Unknown check groups: " + ", ".join(sorted(unknown)))
    records = []
    for group in groups:
        commands = config["checks"][group]
        if not isinstance(commands, list) or not all(isinstance(cmd, str) for cmd in commands):
            raise spec.SpecError(f"checks.{group} must be a list of commands")
        if not commands:
            raise spec.SpecError(f"checks.{group} is empty; it cannot establish verification")
        for command in commands:
            record = execute_check(root, group, command, args.timeout, args.max_output)
            records.append(record)
            print(f"{'PASS' if record['passed'] else 'FAIL'} {redact(command)}", file=sys.stderr)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                         capture_output=True, check=False)
    scope = {"status": "unproven", "reason": "no authorized paths supplied"}
    if args.authorized_path:
        allowed = [spec.path_parts(path) for path in args.authorized_path]
        changed = diff_paths(root, args.base)
        outside = [item["path"] for item in changed if not any(
            spec.path_parts(item["path"])[:len(prefix)] == prefix for prefix in allowed)]
        scope = {"status": "passed" if not outside else "failed",
                 "base": args.base, "authorized_paths": args.authorized_path,
                 "changed_paths": changed, "outside_scope": outside}
    report = {"schema_version": 1, "commit_sha": sha.stdout.strip() if sha.returncode == 0 else None,
              "task": args.task, "checks": records,
              "authorized_scope": scope,
              "workspace_state": workspace_state(root, args.base,
                                                 ([args.output] if args.output else []) +
                                                 getattr(args, "exclude_output", [])),
              "status": "passed" if all(item["passed"] for item in records) and scope["status"] != "failed" else "failed",
              "claim_scope": "command execution, worktree fingerprint, and optional changed-file scope only; acceptance and production measures require separate evidence"}
    output = json.dumps(report, indent=2) + "\n"
    if args.output:
        target = spec.safe_path(root, args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output, encoding="utf-8")
        print(f"Evidence: {args.output}", file=sys.stderr)
    else:
        print(output, end="")
    return 0 if report["status"] == "passed" else 1


def run_task(root: Path, args: argparse.Namespace) -> dict:
    """Execute a reviewed plan through a supplied command, then verify its changed files."""
    plan_path = spec.safe_path(root, args.plan)
    try:
        plan_bytes = plan_path.read_bytes()
        plan = json.loads(plan_bytes)
    except (OSError, ValueError) as exc:
        raise spec.SpecError(f"Cannot read plan {args.plan}: {exc}") from exc
    if not isinstance(plan, dict) or not isinstance(plan.get("task"), str):
        raise spec.SpecError("Execution plan must be a task JSON object")
    contract = plan.get("execution_contract", {})
    if not isinstance(contract, dict):
        raise spec.SpecError("Execution plan has no execution contract")
    expected = task_plan(root, argparse.Namespace(
        description=plan["task"], path=plan.get("paths", []),
        surface=plan.get("explicit_surfaces", []), spec=plan.get("explicit_spec_ids", []),
        mode=plan.get("requested_mode"), executor=contract.get("adapter", "native"),
        external_name=contract.get("external_name")))
    for key in ("mode", "surfaces", "selected", "check_groups"):
        if plan.get(key) != expected[key]:
            raise spec.SpecError(f"Plan {key} differs from current routing; create a new plan")
    criteria = plan.get("acceptance_criteria")
    if (not isinstance(criteria, list) or any(not isinstance(item, dict) or
            not isinstance(item.get("id"), str) or not item["id"] or
            item.get("kind") not in {"behavior", "check"} or
            not isinstance(item.get("text"), str) or not item["text"] for item in criteria)):
        raise spec.SpecError("Plan acceptance_criteria must contain ids, kinds, and text")
    criteria_by_id = {item["id"]: item for item in criteria}
    if len(criteria_by_id) != len(criteria) or any(
            criteria_by_id.get(item["id"], {}).get("kind") != item["kind"]
            for item in expected["acceptance_criteria"]):
        raise spec.SpecError("Plan must retain its unique baseline behavior and check criteria")
    for key in ("selected_spec_ids", "authorized_paths", "required_check_groups", "approval_gate"):
        if contract.get(key) != expected["execution_contract"][key]:
            raise spec.SpecError(f"Plan contract {key} differs from current routing; create a new plan")
    catalog = spec.load_playbook_catalog(root)
    specs = spec.load_registry(root, catalog)
    config_before = spec.load_project(root, specs, catalog)
    groups = plan["check_groups"] or ["framework"]
    check_commands_before = {group: config_before["checks"].get(group) for group in groups}
    if any(not commands for commands in check_commands_before.values()):
        raise spec.SpecError("A required check group is empty; configure a real check before execution")
    planned_paths = plan["paths"]
    allowed_paths = args.authorize_path or (planned_paths if contract.get("scope_confirmed") else [])
    if not allowed_paths:
        raise spec.SpecError("Confirm changed-file scope with --authorize-path (repeat for each path or directory)")
    allowed = [spec.path_parts(path) for path in allowed_paths]
    if any(not any(spec.path_parts(path)[:len(prefix)] == prefix for prefix in allowed)
           for path in planned_paths):
        raise spec.SpecError("Authorized paths do not cover every planned path")
    evidence_path = spec.safe_path(root, args.evidence)
    output_path = spec.safe_path(root, args.output) if args.output else None
    if evidence_path == plan_path or (output_path and output_path in {plan_path, evidence_path}):
        raise spec.SpecError("Plan, evidence, and run report must use distinct paths")
    for path in (evidence_path, output_path):
        if path and path.exists():
            raise spec.SpecError(f"Output already exists; choose a new path: {path.relative_to(root)}")
    approval = None
    approval_path = None
    approval_bytes = None
    if plan["mode"] == "governed":
        if not args.approval_record:
            raise spec.SpecError("Governed execution requires --approval-record tied to this plan")
        approval_path = spec.safe_path(root, args.approval_record)
        try:
            approval_bytes = approval_path.read_bytes()
            approval = json.loads(approval_bytes)
        except (OSError, ValueError) as exc:
            raise spec.SpecError(f"Cannot read approval record: {exc}") from exc
        plan_hash = hashlib.sha256(plan_bytes).hexdigest()
        if (not isinstance(approval, dict) or approval.get("decision") != "approved"
                or not approval.get("approver") or approval.get("plan_sha256") != plan_hash):
            raise spec.SpecError("Approval record must name an approver and approve this exact plan hash")
    argv = shlex.split(args.executor_command)
    if not argv:
        raise spec.SpecError("--command must name an executable")
    excluded = [args.evidence] + ([args.output] if args.output else [])
    before = workspace_state(root, "HEAD", excluded)
    if before.get("status") != "captured":
        raise spec.SpecError("Cannot establish pre-execution worktree state: " + before.get("reason", "unknown"))
    head_before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                                 capture_output=True, check=False)
    if head_before.returncode:
        raise spec.SpecError("Execution requires a Git commit to anchor its evidence")
    started = datetime.now(timezone.utc).isoformat()
    environment = os.environ.copy()
    environment["ORACE_PLAN_PATH"] = str(plan_path)
    environment["ORACE_REPO_ROOT"] = str(root)
    try:
        executed = subprocess.run(argv, cwd=root, env=environment, text=True, capture_output=True,
                                  timeout=args.timeout, check=False)
        executor_exit = executed.returncode
        executor_output = redact((executed.stdout + executed.stderr)[-args.max_output:])
    except (OSError, subprocess.TimeoutExpired) as exc:
        executor_exit = None
        executor_output = redact(str(exc))
    finished = datetime.now(timezone.utc).isoformat()
    after = workspace_state(root, "HEAD", excluded)
    head_after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                                capture_output=True, check=False)
    if after.get("status") != "captured" or head_after.returncode:
        raise spec.SpecError("Cannot establish post-execution worktree state")
    before_files, after_files = before["files"], after["files"]
    changed = sorted(path for path in before_files.keys() | after_files.keys()
                     if before_files.get(path) != after_files.get(path))
    outside = [path for path in changed if not any(
        spec.path_parts(path)[:len(prefix)] == prefix for prefix in allowed)]
    head_changed = head_before.stdout.strip() != head_after.stdout.strip()
    try:
        plan_changed = plan_path.read_bytes() != plan_bytes
    except OSError:
        plan_changed = True
    try:
        approval_changed = bool(approval_path and approval_path.read_bytes() != approval_bytes)
    except OSError:
        approval_changed = True
    artifact_collision = any(path and path.exists() for path in (evidence_path, output_path))
    try:
        catalog_after = spec.load_playbook_catalog(root)
        specs_after = spec.load_registry(root, catalog_after)
        config_after = spec.load_project(root, specs_after, catalog_after)
        checks_changed = any(config_after["checks"].get(group) != commands
                             for group, commands in check_commands_before.items())
    except spec.SpecError:
        checks_changed = True
    scope_passed = not outside and not head_changed and not plan_changed and not approval_changed and not artifact_collision and not checks_changed
    scope_state_error = None
    check_report = None
    review = None
    if executor_exit == 0 and scope_passed:
        verify_args = argparse.Namespace(check=groups, task=plan["task"], output=args.evidence,
                                         authorized_path=[], base="HEAD", timeout=args.timeout,
                                         max_output=args.max_output,
                                         exclude_output=[args.output] if args.output else [])
        verify(root, verify_args)
        check_report = json.loads(evidence_path.read_text(encoding="utf-8"))
        final = workspace_state(root, "HEAD", excluded)
        final_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                                    capture_output=True, check=False)
        if final.get("status") != "captured" or final_head.returncode:
            scope_passed = False
            scope_state_error = final.get("reason", "cannot inspect final Git state")
        else:
            final_files = final["files"]
            changed = sorted(path for path in before_files.keys() | final_files.keys()
                             if before_files.get(path) != final_files.get(path))
            outside = [path for path in changed if not any(
                spec.path_parts(path)[:len(prefix)] == prefix for prefix in allowed)]
            head_changed = head_before.stdout.strip() != final_head.stdout.strip()
            try:
                plan_changed = plan_path.read_bytes() != plan_bytes
            except OSError:
                plan_changed = True
            try:
                approval_changed = bool(approval_path and approval_path.read_bytes() != approval_bytes)
            except OSError:
                approval_changed = True
            try:
                final_catalog = spec.load_playbook_catalog(root)
                final_specs = spec.load_registry(root, final_catalog)
                final_config = spec.load_project(root, final_specs, final_catalog)
                checks_changed = any(final_config["checks"].get(group) != commands
                                     for group, commands in check_commands_before.items())
            except spec.SpecError:
                checks_changed = True
            artifact_collision = bool(output_path and output_path.exists())
            scope_passed = (not outside and not head_changed and not plan_changed and
                            not approval_changed and not checks_changed and not artifact_collision)
        commands = [redact(command) for group in groups for command in check_commands_before[group]]
        claims = [{"id": item["id"], "claim": "unproven"} if item["kind"] == "behavior"
                  else {"id": item["id"],
                        "claim": "covered" if check_report["status"] == "passed" else "contradicted",
                        "check_commands": commands} for item in criteria]
        handoff = {"schema_version": 1,
                   "selected_spec_ids": contract["selected_spec_ids"],
                   "changed_files": changed, "criteria": claims}
        review_plan = dict(plan)
        review_plan["execution_contract"] = {**contract, "scope_confirmed": True,
                                             "authorized_paths": allowed_paths}
        review = review_handoff(root, review_plan, handoff, [args.evidence])
    status = "ready_for_review" if (executor_exit == 0 and scope_passed and check_report
                                    and check_report["status"] == "passed" and review
                                    and review["status"] == "ready_for_review") else "failed"
    report = {"schema_version": 1, "status": status, "task": plan["task"],
              "mode": plan["mode"], "plan": args.plan,
              "approval_record": args.approval_record if approval else None,
              "executor": {"command": redact(args.executor_command), "exit_code": executor_exit,
                           "started_utc": started, "finished_utc": finished,
                           "output_tail": executor_output},
              "scope": {"status": "passed" if scope_passed else "failed",
                        "authorized_paths": allowed_paths, "changed_files": changed,
                        "outside_scope": outside, "head_changed": head_changed,
                        "plan_changed": plan_changed, "approval_changed": approval_changed,
                        "checks_changed": checks_changed,
                        "artifact_collision": artifact_collision,
                        "state_error": scope_state_error},
              "evidence": args.evidence if check_report else None,
              "checks": check_report["checks"] if check_report else [], "review": review,
              "claim_scope": "executor invocation, changed-file scope, and configured command results; behavioral acceptance and approval authenticity require independent review"}
    if output_path and not output_path.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(report, indent=2) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root (default: search upward from cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
    initializer = sub.add_parser("init", help="Install into a repository and propose a discovery profile")
    initializer.add_argument("--target", required=True)
    initializer.add_argument("--dry-run", action="store_true")
    initializer.add_argument("--force", action="store_true")
    initializer.add_argument("--harness", choices=model_config.HOSTS)
    initializer.add_argument("--workshop-model", default="auto")
    initializer.add_argument("--supervisor-model", default="auto")
    initializer.add_argument("--subagent-model", default="auto")
    launcher = sub.add_parser("launch", help="Start a harness with the configured workshop or supervisor model")
    launcher.add_argument("--harness", required=True, choices=model_config.HOSTS)
    launcher.add_argument("--role", required=True, choices=("workshop", "supervisor"))
    discovery = sub.add_parser("discover", help="Inspect a repository without approving inferred architecture")
    discovery.add_argument("--target", default=".")
    discovery.add_argument("--json", action="store_true")
    upgrader = sub.add_parser("upgrade", help="Preview or apply non-destructive managed runtime updates")
    upgrader.add_argument("--target", required=True)
    upgrader.add_argument("--apply", action="store_true", help="Apply safe updates after preview")
    upgrader.add_argument("--json", action="store_true")
    doctor = sub.add_parser("doctor", help="Diagnose routing configuration and managed runtime drift")
    doctor.add_argument("--json", action="store_true")
    coverage_cmd = sub.add_parser("coverage", help="Show routing coverage for paths or a git diff")
    coverage_cmd.add_argument("--path", action="append", default=[])
    coverage_cmd.add_argument("--diff", metavar="REVISION", help="Compare working tree to this git revision")
    coverage_cmd.add_argument("--json", action="store_true")
    impact_cmd = sub.add_parser("impact", help="Report affected accepted ADRs and architecture-link drift")
    impact_cmd.add_argument("--path", action="append", default=[])
    impact_cmd.add_argument("--diff", metavar="REVISION")
    impact_cmd.add_argument("--surface", action="append", default=[])
    impact_cmd.add_argument("--json", action="store_true")
    checker = sub.add_parser("check", help="Explain a change against routing, architecture, and check evidence")
    checker.add_argument("--path", action="append", default=[])
    checker.add_argument("--diff", metavar="REVISION")
    checker.add_argument("--description", default="")
    checker.add_argument("--surface", action="append", default=[])
    checker.add_argument("--evidence", action="append", default=[])
    checker.add_argument("--run-checks", action="store_true",
                         help="Execute required configured checks now, without trusting a supplied evidence file")
    checker.add_argument("--timeout", type=int, default=600)
    checker.add_argument("--max-output", type=int, default=12000)
    checker.add_argument("--strict", action="store_true", help="Fail on deterministic routing or check gaps")
    checker.add_argument("--github", action="store_true", help="Append a concise report to GITHUB_STEP_SUMMARY")
    checker.add_argument("--json", action="store_true")
    reviewer = sub.add_parser("review", help="Preflight a task handoff against machine evidence")
    reviewer.add_argument("--plan", required=True)
    reviewer.add_argument("--handoff", required=True)
    reviewer.add_argument("--evidence", action="append", default=[])
    reviewer.add_argument("--json", action="store_true")
    executor = sub.add_parser("run", help="Execute a routed plan with an explicit command and verify its result")
    executor.add_argument("--plan", required=True, help="Repository-relative task plan JSON")
    executor.add_argument("--command", dest="executor_command", required=True,
                          help="Executable and arguments; no shell is used; ORACE_PLAN_PATH is exported")
    executor.add_argument("--authorize-path", action="append", default=[],
                          help="Confirm the allowed changed-file path or directory; repeat as needed")
    executor.add_argument("--approval-record", help="Required for Governed plans; JSON tied to the plan hash")
    executor.add_argument("--evidence", required=True, help="New repository-relative verification JSON path")
    executor.add_argument("--output", help="New repository-relative run report JSON path")
    executor.add_argument("--timeout", type=int, default=600)
    executor.add_argument("--max-output", type=int, default=12000)
    executor.add_argument("--json", action="store_true")
    for name in ("task", "explain"):
        cmd = sub.add_parser(name, help="Prepare and explain an ad hoc task without backlog registration")
        cmd.add_argument("description")
        cmd.add_argument("--path", action="append", default=[])
        cmd.add_argument("--surface", action="append", default=[])
        cmd.add_argument("--spec", action="append", default=[])
        cmd.add_argument("--mode", choices=LEVELS)
        cmd.add_argument("--executor", choices=("native", "external"), default="native")
        cmd.add_argument("--external-name", help="Name of the external execution method")
        cmd.add_argument("--output", help="Write the JSON plan to a repository-relative file")
        cmd.add_argument("--json", action="store_true")
    runner = sub.add_parser("verify", help="Run configured check groups and capture machine evidence")
    runner.add_argument("--check", action="append", default=[])
    runner.add_argument("--task", help="Task id or short task label")
    runner.add_argument("--output", help="Repository-relative JSON evidence path")
    runner.add_argument("--authorized-path", action="append", default=[],
                        help="Allowed file or directory prefix; repeat to verify changed-file scope")
    runner.add_argument("--base", default="HEAD", help="Git revision for changed-file scope (default: HEAD)")
    runner.add_argument("--timeout", type=int, default=600)
    runner.add_argument("--max-output", type=int, default=12000)
    args = parser.parse_args(argv)
    try:
        if args.command == "upgrade":
            target = Path(args.target).expanduser().resolve()
            if not target.is_dir():
                raise spec.SpecError(f"Target is not a directory: {target}")
            try:
                report = distribution.upgrade(Path(__file__).resolve().parent.parent, target,
                                              dry_run=not args.apply)
            except ValueError as exc:
                raise spec.SpecError(str(exc)) from exc
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                print(f"Upgrade {report['from_version']} -> {report['to_version']}")
                for action in report["actions"]:
                    print(action)
                for conflict in report["conflicts"]:
                    print(f"preserved modified file: {conflict}")
                if not args.apply:
                    print("Preview only; pass --apply to update unchanged managed files")
            return 1 if report["conflicts"] else 0
        if args.command in {"init", "discover"}:
            target = Path(args.target).expanduser().resolve()
            if not target.is_dir():
                raise spec.SpecError(f"Target is not a directory: {target}")
            if args.command == "init":
                install_args = ["--target", str(target)]
                if args.dry_run:
                    install_args.append("--dry-run")
                if args.force:
                    install_args.append("--force")
                if args.harness:
                    install_args.extend(["--harness", args.harness])
                for flag, value in (("--workshop-model", args.workshop_model),
                                    ("--supervisor-model", args.supervisor_model),
                                    ("--subagent-model", args.subagent_model)):
                    install_args.extend([flag, value])
                result = init_project.main(install_args)
                if result:
                    return result
            profile = discover(target)
            if args.command == "init" and not args.dry_run:
                destination = target / ".spec" / "40_workspace" / "PROJECT_DISCOVERY.json"
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
                print(f"Discovery proposal: {destination.relative_to(target)}")
            if args.command == "discover" and args.json:
                print(json.dumps(profile, indent=2))
            else:
                for item in profile["observed"]:
                    print(f"Observed: {item['fact']} ({item['path']})")
                print("Suggested playbooks for review: " + (", ".join(profile["proposed_playbooks"]) or "none"))
                print("Unknown: " + "; ".join(profile["unknowns"]))
                print(profile["note"])
            return 0
        root = spec.repo_root(Path(args.root))
        if args.command == "launch":
            try:
                model = model_config.load(root)[args.harness][args.role]
            except ValueError as error:
                raise spec.SpecError(str(error)) from error
            command = [args.harness]
            if model != "auto":
                command.extend(["--model", model])
            print("Starting " + " ".join(shlex.quote(part) for part in command), flush=True)
            try:
                return subprocess.call(command, cwd=root)
            except FileNotFoundError:
                raise spec.SpecError(f"{args.harness} CLI is not installed or not on PATH")
        if args.command == "run":
            if args.timeout <= 0 or args.max_output <= 0:
                raise spec.SpecError("--timeout and --max-output must be positive")
            report = run_task(root, args)
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                print(f"Status: {report['status']}; executor exit: {report['executor']['exit_code']}")
                print("Changed: " + (", ".join(report["scope"]["changed_files"]) or "none"))
                if report["scope"]["outside_scope"]:
                    print("Outside scope: " + ", ".join(report["scope"]["outside_scope"]))
                if report["evidence"]:
                    print("Evidence: " + report["evidence"])
                if args.output:
                    print("Run report: " + args.output)
            return 0 if report["status"] == "ready_for_review" else 1
        if args.command == "review":
            try:
                plan = json.loads(spec.safe_path(root, args.plan).read_text(encoding="utf-8"))
                handoff = json.loads(spec.safe_path(root, args.handoff).read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise spec.SpecError(f"Cannot read plan or handoff: {exc}") from exc
            report = review_handoff(root, plan, handoff, args.evidence)
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                for item in report["criteria"]:
                    print(f"{item['id']}: {item['status']} (claimed {item['claimed']})")
                for item in report["findings"]:
                    print(f"Finding {item['kind']}: {item.get('paths', item.get('detail', item.get('ids', '')))}")
                print("Status: " + report["status"])
            return 1 if report["status"] == "needs_evidence" else 0
        if args.command == "doctor":
            catalog = spec.load_playbook_catalog(root)
            specs = spec.load_registry(root, catalog)
            config = spec.load_project(root, specs, catalog)
            issues = spec.check_coverage(root, specs, config, catalog) + spec.check_routing_cases(root, specs, config)
            try:
                manifest = distribution.read_manifest(root)
            except ValueError as exc:
                issues.append(str(exc))
                manifest = None
            drift = []
            if manifest:
                import sync_skills
                generated_roles = sync_skills.role_adapters(root, config["models"])
                for path, expected in manifest["managed"].items():
                    target = spec.safe_path(root, path)
                    relative = Path(path)
                    if relative in generated_roles:
                        if not target.is_file() or target.read_bytes() != generated_roles[relative]:
                            drift.append(path)
                        continue
                    if not target.is_file() or distribution.digest(target) != expected:
                        drift.append(path)
            report = {"framework_version": manifest.get("framework_version") if manifest else None,
                      "registered_specifications": len(specs), "active_playbooks": config["playbooks"],
                      "issues": issues, "managed_file_drift": drift,
                      "status": "attention" if issues or drift else "ok"}
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                print(f"Status: {report['status']}; {len(specs)} specifications; "
                      f"{len(config['playbooks'])} active playbooks")
                for issue in issues:
                    print(f"issue: {issue}")
                for path in drift:
                    print(f"managed file changed: {path}")
            return 1 if issues or drift else 0
        if args.command == "coverage":
            return coverage(root, args)
        if args.command in {"impact", "check"}:
            entries = [{"status": "provided", "path": path, "role": "current"} for path in args.path]
            if args.diff is not None:
                entries += diff_paths(root, args.diff)
            if not entries:
                raise spec.SpecError("Provide --path or --diff REVISION")
            catalog = spec.load_playbook_catalog(root)
            specs = spec.load_registry(root, catalog)
            config = spec.load_project(root, specs, catalog)
            explicit_surfaces = set(args.surface)
            if explicit_surfaces - spec.SURFACES:
                raise spec.SpecError(f"Unknown surfaces {sorted(explicit_surfaces - spec.SURFACES)}")
            if args.command == "impact":
                paths = list(dict.fromkeys(item["path"] for item in entries))
                derived = set().union(*(spec.surfaces_for_path(config, path) for path in paths))
                report = architecture.impact(root, specs, config, paths, explicit_surfaces | derived)
                if args.json:
                    print(json.dumps(report, indent=2))
                else:
                    for item in report["affected_decisions"]:
                        print(f"{item['id']}: {item['status']} ({item['match']})")
                    for item in report["findings"]:
                        print(f"Finding {item['kind']}: {item['detail']}")
                    if not report["affected_decisions"]:
                        print("No registered ADR matched; inspect unresolved path or semantic coverage")
                return 0
            if args.run_checks and args.evidence:
                raise spec.SpecError("Use --run-checks or --evidence, not both")
            if args.timeout <= 0 or args.max_output <= 0:
                raise spec.SpecError("--timeout and --max-output must be positive")
            report = change_report(root, entries, args.description, explicit_surfaces, args.evidence)
            if args.run_checks:
                run_report_checks(root, report, args.timeout, args.max_output)
                report["evidence_origin"] = "live_command"
            elif args.evidence:
                report["evidence_origin"] = "supplied_json_untrusted_for_gate"
                if args.strict:
                    report["findings"].append({"kind": "supplied_evidence_untrusted_for_gate",
                                               "detail": "use --run-checks for a strict command gate"})
                    report["status"] = "attention"
            else:
                report["evidence_origin"] = "none"
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                print_change_report(report)
            if args.github:
                summary = os.environ.get("GITHUB_STEP_SUMMARY")
                if summary:
                    lines = ["## ORACE change check", "", f"Mode: **{report['mode']}**",
                             f"Status: **{report['status']}**", "",
                             "Selected: " + ", ".join(item["id"] for item in report["selected"]), ""]
                    lines += [f"- {item['kind']}: {item.get('detail', item.get('paths', ''))}"
                              for item in report["findings"]]
                    lines += [f"- {item['status']}: `{item['command']}`" for item in report["checks"]]
                    with Path(summary).open("a", encoding="utf-8") as stream:
                        stream.write("\n".join(lines) + "\n")
            strict_findings = {"unmapped_paths", "architecture_routing_gap", "scenario_link_missing",
                               "superseded_adr_missing", "stale_evidence",
                               "supplied_evidence_untrusted_for_gate"}
            if args.strict and (any(item["kind"] in strict_findings for item in report["findings"])
                                or any(item["status"] != "covered" for item in report["checks"])):
                return 1
            return 0
        if args.command == "verify":
            if args.timeout <= 0 or args.max_output <= 0:
                raise spec.SpecError("--timeout and --max-output must be positive")
            return verify(root, args)
        plan = task_plan(root, args)
        if args.output:
            destination = spec.safe_path(root, args.output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps(plan, indent=2))
        else:
            print_plan(plan, explain=args.command == "explain")
        return 0
    except spec.SpecError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
