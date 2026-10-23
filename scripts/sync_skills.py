#!/usr/bin/env python3
"""Keep host skills and role adapters in sync with the canonical .agents tree.

`.agents/skills/` is the single source of truth. Claude Code discovers skills in
`.claude/skills/`; Codex discovers them in place. Role definitions live in
`.agents/roles/` and are rendered for Claude Code, Codex, and Copilot.

    python3 scripts/sync_skills.py          # create or refresh the adapter
    python3 scripts/sync_skills.py --check  # fail if the adapter has drifted
"""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
import sys
from pathlib import Path
import model_config

CANONICAL = Path(".agents/skills")
ADAPTERS = [Path(".claude/skills")]
ROLES = Path(".agents/roles")
CLAUDE_ROLES = Path(".claude/agents")
CODEX_ROLES = Path(".codex/agents")
COPILOT_ROLES = Path(".github/agents")


def role_adapters(root: Path, models: dict | None = None) -> dict[Path, bytes]:
    """Render role definitions with optional host-specific model choices."""
    rendered = {}
    models = model_config.validate(models) if models is not None else model_config.load(root)
    sources = sorted((root / ROLES).glob("*.md"))
    if not sources:
        raise ValueError(f"no role definitions found in {ROLES}")
    for source in sources:
        content = source.read_text(encoding="utf-8")
        if not content.startswith("---\n"):
            raise ValueError(f"missing role frontmatter: {source}")
        _, header, body = content.split("---", 2)
        fields = dict(line.split(":", 1) for line in header.strip().splitlines() if ":" in line)
        if not fields.get("name") or not fields.get("description") or not body.strip():
            raise ValueError(f"incomplete role: {source}")
        claude_model = model_config.for_role(models, "claude", source.stem)
        claude_header = header.rstrip() + (f"\nmodel: {json.dumps(claude_model)}\n" if claude_model != "auto" else "\n")
        rendered[CLAUDE_ROLES / source.name] = ("---" + claude_header + "---" + body).encode("utf-8")
        name = "orace_" + source.stem.lower()
        codex_model = model_config.for_role(models, "codex", source.stem)
        toml = (f"name = {json.dumps(name)}\n"
                f"description = {json.dumps(fields['description'].strip())}\n"
                f"developer_instructions = {json.dumps(body.strip())}\n"
                + (f"model = {json.dumps(codex_model)}\n" if codex_model != "auto" else ""))
        rendered[CODEX_ROLES / f"{name}.toml"] = toml.encode("utf-8")
        copilot_model = model_config.for_role(models, "copilot", source.stem)
        copilot_header = (f"---\nname: {name}\n"
                          f"description: {json.dumps(fields['description'].strip())}\n"
                          + (f"model: {json.dumps(copilot_model)}\n" if copilot_model != "auto" else "")
                          + "---")
        rendered[COPILOT_ROLES / f"{name}.agent.md"] = (copilot_header + body).encode("utf-8")
    return rendered


def repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / CANONICAL).is_dir():
            return candidate
    raise SystemExit(f"error: no {CANONICAL} directory found above {start}")


def differences(source: Path, target: Path) -> list[str]:
    """Report canonical files missing or different in a copied adapter."""
    problems = []
    for path in sorted(source.rglob("*")):
        if path.is_dir() or ".DS_Store" in path.name:
            continue
        mirrored = target / path.relative_to(source)
        if not mirrored.is_file():
            problems.append(f"missing in adapter: {mirrored}")
        elif not filecmp.cmp(path, mirrored, shallow=False):
            problems.append(f"differs from canonical: {mirrored}")
    return problems


def link_target(root: Path, adapter: Path) -> str:
    return os.path.relpath(root / CANONICAL, (root / adapter).parent)


def check(root: Path) -> int:
    problems = []
    source = root / CANONICAL
    for adapter in ADAPTERS:
        target = root / adapter
        if target.is_symlink():
            if os.readlink(target) != link_target(root, adapter):
                problems.append(f"{adapter} points at {os.readlink(target)}, expected {link_target(root, adapter)}")
            elif not target.resolve().is_dir():
                problems.append(f"{adapter} is a broken symlink")
            continue
        if not target.exists():
            problems.append(f"{adapter} does not exist; run scripts/sync_skills.py")
            continue
        problems.extend(differences(source, target))
    for relative, expected in role_adapters(root).items():
        target = root / relative
        if not target.is_file():
            problems.append(f"missing role adapter: {relative}")
        elif target.read_bytes() != expected:
            problems.append(f"role adapter differs from canonical: {relative}")
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"ok: skill and role adapters match .agents/")
    return 0


def sync(root: Path) -> int:
    source = root / CANONICAL
    conflicts = []
    for adapter in ADAPTERS:
        target = root / adapter
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            if os.readlink(target) != link_target(root, adapter):
                conflicts.append(f"{adapter} is an existing symlink to another location")
            continue
        if target.is_file():
            conflicts.append(f"{adapter} is an existing file")
            continue
        if target.is_dir():
            for path in source.rglob("*"):
                if not path.is_file() or path.name == ".DS_Store":
                    continue
                mirrored = target / path.relative_to(source)
                if mirrored.is_file():
                    if not filecmp.cmp(path, mirrored, shallow=False):
                        conflicts.append(f"{mirrored} differs from canonical")
                    continue
                mirrored.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, mirrored)
                print(f"copied {path.relative_to(root)} -> {mirrored.relative_to(root)}")
            continue
        try:
            target.symlink_to(link_target(root, adapter), target_is_directory=True)
            print(f"linked {adapter} -> {link_target(root, adapter)}")
        except OSError:
            shutil.copytree(source, target, ignore=shutil.ignore_patterns(".DS_Store"))
            print(f"copied {CANONICAL} -> {adapter} (symlinks unavailable on this platform)")
    for relative, expected in role_adapters(root).items():
        target = root / relative
        if target.is_file():
            if target.read_bytes() != expected:
                target.write_bytes(expected)
                print(f"updated {relative}")
            continue
        if target.exists():
            conflicts.append(f"{relative} is not a file")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(expected)
        print(f"created {relative}")
    for conflict in conflicts:
        print(f"error: {conflict}", file=sys.stderr)
    return 1 if conflicts else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify without writing")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    root = repo_root(Path(args.root))
    try:
        return check(root) if args.check else sync(root)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
