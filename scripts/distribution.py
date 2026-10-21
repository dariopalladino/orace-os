"""Versioned, non-destructive installation and upgrade of the ORACE runtime."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

MANIFEST = Path(".spec/installation.json")
MANAGED_DIRS = (
    Path("scripts"), Path(".agents/skills"), Path(".agents/roles"),
    Path(".claude/agents"), Path(".codex/agents"),
    Path(".claude/commands"), Path(".spec/00_global"), Path(".spec/10_playbooks"),
    Path("benchmarks"),
)
MANAGED_FILES = (Path("VERSION"), Path(".spec/INDEX.md"), Path(".github/workflows/orace-check.yml"))
SKIP_PARTS = {"__pycache__", ".DS_Store", ".pytest_cache"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(source: Path) -> list[Path]:
    paths = []
    for folder in MANAGED_DIRS:
        if (source / folder).is_dir():
            paths.extend(path.relative_to(source) for path in (source / folder).rglob("*")
                         if path.is_file() and not any(part in SKIP_PARTS for part in path.parts))
    paths.extend(path for path in MANAGED_FILES if (source / path).is_file())
    return sorted(set(paths))


def version(source: Path) -> str:
    path = source / "VERSION"
    return path.read_text(encoding="utf-8").strip() if path.is_file() else "unknown"


def read_manifest(target: Path) -> dict | None:
    path = target / MANIFEST
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("managed"), dict):
        raise ValueError(f"Invalid installation manifest: {path}")
    return data


def write_manifest(target: Path, data: dict) -> None:
    path = target / MANIFEST
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def ensure_claude_adapter(target: Path, dry_run: bool, actions: list[str]) -> None:
    adapter = target / ".claude" / "skills"
    canonical = target / ".agents" / "skills"
    if adapter.exists() or adapter.is_symlink():
        if adapter.is_dir() and not adapter.is_symlink():
            for skill in canonical.iterdir():
                if not skill.is_dir():
                    continue
                destination = adapter / skill.name
                if destination.exists():
                    continue
                actions.append(f"add skill adapter {destination.relative_to(target)}")
                if not dry_run:
                    shutil.copytree(skill, destination)
        return
    actions.append("link .claude/skills -> ../.agents/skills")
    if not dry_run:
        adapter.parent.mkdir(parents=True, exist_ok=True)
        try:
            adapter.symlink_to("../.agents/skills", target_is_directory=True)
        except OSError:
            shutil.copytree(canonical, adapter)


def install(source: Path, target: Path, *, fresh_spec: bool, dry_run: bool) -> list[str]:
    """Copy only missing managed files and record only files we own."""
    actions = []
    old = read_manifest(target) if not dry_run else None
    managed = dict(old["managed"]) if old else {}
    for relative in source_files(source):
        if relative.parts[0] == ".spec" and not fresh_spec:
            continue
        destination = target / relative
        origin = source / relative
        if destination.is_file():
            if fresh_spec and relative.parts[0] == ".spec":
                managed[relative.as_posix()] = digest(destination)
            elif relative.as_posix() not in managed:
                actions.append(f"preserve existing {relative}")
            continue
        actions.append(f"install {relative}")
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, destination)
            managed[relative.as_posix()] = digest(destination)
    if not dry_run:
        ensure_claude_adapter(target, False, actions)
        write_manifest(target, {"schema_version": 1, "framework_version": version(source),
                                "managed": managed})
    return actions


def upgrade(source: Path, target: Path, *, dry_run: bool) -> dict:
    """Replace a managed file only when its installed hash still matches."""
    prior = read_manifest(target)
    if prior is None:
        raise ValueError("No .spec/installation.json; initialize this repository before upgrading")
    managed = dict(prior["managed"])
    actions = []
    conflicts = []
    for relative in source_files(source):
        key = relative.as_posix()
        destination = target / relative
        origin = source / relative
        expected = managed.get(key)
        if destination.is_file():
            actual = digest(destination)
            if expected is None or actual != expected:
                conflicts.append(key)
                continue
            if actual == digest(origin):
                continue
            actions.append(f"update {key}")
        elif expected is not None:
            conflicts.append(key)
            continue
        else:
            actions.append(f"add {key}")
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, destination)
            managed[key] = digest(destination)
    if not dry_run:
        ensure_claude_adapter(target, False, actions)
        write_manifest(target, {"schema_version": 1, "framework_version": version(source),
                                "managed": managed, "conflicts": conflicts})
    return {"from_version": prior.get("framework_version"), "to_version": version(source),
            "actions": actions, "conflicts": conflicts, "dry_run": dry_run}
