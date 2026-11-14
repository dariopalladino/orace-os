"""Preview and migrate a pre-manifest ORACE specification store."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import tempfile
from pathlib import Path

import distribution
import init_project

REPORT_NAME = "ORACE_MIGRATION_REPORT.json"
REFERENCE_PATHS = ("15_architecture", "20_backlog", "40_workspace", "INDEX.md")
BRIDGE_ROW = "| legacy-bridge | .spec/legacy/BRIDGE.md | architecture,planning,review | - | * |"


def _files(folder: Path) -> list[Path]:
    return sorted(path for path in folder.rglob("*") if path.is_file() or path.is_symlink())


def _symlink_component(target: Path, relative: Path) -> Path | None:
    current = target
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return current.relative_to(target)
    return None


def _source_fingerprint(source: Path) -> str:
    paths = set(distribution.source_files(source))
    for name in init_project.MERGE_FILES + init_project.EXTRAS:
        path = Path(name)
        if (source / path).is_file():
            paths.add(path)
    for name in init_project.SPEC_TEMPLATE_FILES:
        path = Path(".spec") / name
        if (source / path).is_file():
            paths.add(path)
    for name in init_project.SPEC_TEMPLATE_DIRS:
        paths.update(path.relative_to(source) for path in _files(source / ".spec" / name))
    digest = hashlib.sha256()
    for relative in sorted(paths):
        digest.update(relative.as_posix().encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(distribution.digest(source / relative)))
    return digest.hexdigest()


def _inventory(target: Path, source: Path) -> dict:
    old_spec = target / ".spec"
    if not old_spec.is_dir() or old_spec.is_symlink():
        raise ValueError("Migration requires an existing, ordinary .spec/ directory")
    if (old_spec / "installation.json").exists():
        raise ValueError("Installation manifest exists; use 'orace.py upgrade' instead")
    if not any((old_spec / name).exists() for name in REFERENCE_PATHS):
        raise ValueError("No legacy architecture, backlog, workspace, or INDEX.md to migrate")

    old_files = _files(old_spec)
    runtime_paths = [path for path in distribution.source_files(source)
                     if path.parts[0] != ".spec"]
    collisions = [path for path in runtime_paths if (target / path).exists()]
    instruction_paths = [Path(name) for name in init_project.MERGE_FILES
                         if (target / name).exists()]
    adapter = target / ".claude" / "skills"
    adapter_directory = adapter.is_dir() and not adapter.is_symlink()
    blockers = [str(path.relative_to(target)) for path in old_files
                if path.is_symlink()]
    blockers += [str(path) for path in collisions + instruction_paths
                 if (target / path).is_symlink() or ((target / path).exists() and
                     not (target / path).is_file())]
    if adapter.is_symlink() and adapter.resolve() != (target / ".agents" / "skills").resolve():
        blockers.append(".claude/skills")
    if adapter_directory:
        blockers += [str(path.relative_to(target)) for path in _files(adapter)
                     if path.is_symlink()]
    for relative in runtime_paths + [Path(name) for name in
                                     init_project.MERGE_FILES + init_project.EXTRAS]:
        symlink = _symlink_component(target, relative)
        if symlink is not None:
            blockers.append(str(symlink))
    blockers = sorted(set(blockers))
    fingerprint = hashlib.sha256()
    for path in old_files + [target / item for item in collisions + instruction_paths]:
        relative = path.relative_to(target).as_posix()
        fingerprint.update(relative.encode("utf-8") + b"\0")
        if path.is_symlink():
            fingerprint.update(b"SYMLINK\0")
        else:
            fingerprint.update(bytes.fromhex(distribution.digest(path)))
    if adapter_directory:
        for path in _files(adapter):
            fingerprint.update(path.relative_to(target).as_posix().encode("utf-8") + b"\0")
            if path.is_symlink():
                fingerprint.update(b"SYMLINK\0")
            else:
                fingerprint.update(bytes.fromhex(distribution.digest(path)))
    return {"fingerprint": fingerprint.hexdigest(), "old_files": old_files,
            "runtime_paths": runtime_paths, "collisions": collisions,
            "instruction_paths": instruction_paths, "adapter_directory": adapter_directory,
            "blockers": blockers}


def preview(source: Path, target: Path) -> dict:
    source, target = source.resolve(), target.resolve()
    if not target.is_dir() or target == source:
        raise ValueError("Target must be another existing repository directory")
    inventory = _inventory(target, source)
    digest = inventory["fingerprint"]
    archive = f".spec/50_archive/legacy-{digest[:12]}"
    return {
        "schema_version": 1,
        "status": "blocked" if inventory["blockers"] else "ready",
        "source_framework_version": distribution.version(source),
        "source_fingerprint": _source_fingerprint(source),
        "target": str(target),
        "fingerprint": digest,
        "archive": archive,
        "legacy_spec_files": len(inventory["old_files"]),
        "references": {name: (target / ".spec" / name).exists()
                       for name in REFERENCE_PATHS},
        "runtime_files_to_replace": [str(path) for path in inventory["collisions"]],
        "instruction_files_to_merge": [str(path) for path in inventory["instruction_paths"]],
        "claude_skills_directory_to_refresh": inventory["adapter_directory"],
        "blockers": inventory["blockers"],
        "review_after_apply": [
            "Review inherited instruction text for obsolete ORACE commands.",
            "Confirm project.json playbooks, module roots, and checks from the actual repository.",
            "Review archived decisions and tasks before promoting them into current routing.",
            "Review old runtime files absent from the new distribution; they are retained.",
        ],
    }


def _bridge(spec_root: Path, archive: str, old_files: list[Path], target: Path) -> None:
    entries = []
    for path in old_files:
        old = path.relative_to(target / ".spec").as_posix()
        if old == "INDEX.md" or any(old == name or old.startswith(name + "/")
                                       for name in REFERENCE_PATHS[:-1]):
            entries.append({"old_path": ".spec/" + old,
                            "archived_path": archive + "/spec/" + old,
                            "sha256": distribution.digest(path)})
    bridge = spec_root / "legacy" / "BRIDGE.md"
    bridge.parent.mkdir(parents=True, exist_ok=True)
    bridge.write_text(
        "# Legacy ORACE reference bridge\n\n"
        "This migration preserved the former specification store as historical evidence. "
        "The archived files are not automatically current requirements or accepted decisions. "
        "Review each document against current policy before registering or promoting it.\n\n"
        "- Old routing index: `" + archive + "/spec/INDEX.md` (if present)\n"
        "- Old architecture: `" + archive + "/spec/15_architecture/`\n"
        "- Old backlog: `" + archive + "/spec/20_backlog/`\n"
        "- Old workspace: `" + archive + "/spec/40_workspace/`\n"
        "- File-level paths and checksums: `.spec/legacy/REFERENCES.json`\n\n"
        "Use the current `.spec/INDEX.md` for routing. Copy or adapt only reviewed "
        "artifacts into the current structure and add one routing row per active document.\n",
        encoding="utf-8",
    )
    (bridge.parent / "REFERENCES.json").write_text(
        json.dumps({"schema_version": 1, "archive": archive,
                    "entries": entries}, indent=2) + "\n", encoding="utf-8")
    index = spec_root / "INDEX.md"
    body = index.read_text(encoding="utf-8")
    header = "| ID | Path | Surfaces | Requires | Playbooks |"
    if header not in body:
        raise ValueError("New INDEX.md lacks routing table")
    end = body.find("\n\n", body.index(header))
    if end < 0:
        raise ValueError("New INDEX.md has no routing table end")
    index.write_text(body[:end] + "\n" + BRIDGE_ROW + body[end:], encoding="utf-8")
    # Keep the installed base hash in the manifest. The bridge row is a project
    # edit and future upgrades must report it as a conflict, never erase it.


def apply(source: Path, target: Path, report_path: Path) -> dict:
    source, target = source.resolve(), target.resolve()
    if not report_path.is_file():
        raise ValueError(f"Migration preview missing: {report_path}")
    recorded = json.loads(report_path.read_text(encoding="utf-8"))
    current = preview(source, target)
    if recorded != current:
        raise ValueError("Legacy files or migration plan changed; rerun migration preview")
    if current["blockers"]:
        raise ValueError("Migration has blockers: " + ", ".join(current["blockers"]))
    inventory = _inventory(target, source)
    archive = current["archive"]
    with tempfile.TemporaryDirectory(prefix="orace-migration-", dir=target.parent) as tmp:
        staging = Path(tmp) / "prepared"
        staging.mkdir()
        with contextlib.redirect_stdout(io.StringIO()):
            init_project.main(["--target", str(staging)])
        prepared_spec = staging / ".spec"
        archived = prepared_spec / archive.removeprefix(".spec/")
        shutil.copytree(target / ".spec", archived / "spec")
        for relative in inventory["collisions"] + inventory["instruction_paths"]:
            backup = archived / "replaced" / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target / relative, backup)
        if inventory["adapter_directory"]:
            shutil.copytree(target / ".claude" / "skills",
                            archived / "replaced" / ".claude" / "skills")
        _bridge(prepared_spec, archive, inventory["old_files"], target)

        backup_spec = Path(tmp) / "old-spec"
        (target / ".spec").rename(backup_spec)
        changed: list[Path] = []
        adapter = target / ".claude" / "skills"
        adapter_existed = adapter.exists() or adapter.is_symlink()
        try:
            prepared_spec.rename(target / ".spec")
            installed_archive = target / archive
            for relative in inventory["runtime_paths"]:
                src = staging / relative
                if not src.is_file():
                    continue
                dst = target / relative
                dst.parent.mkdir(parents=True, exist_ok=True)
                changed.append(relative)
                shutil.copy2(src, dst)
            for name in init_project.MERGE_FILES:
                relative = Path(name)
                if (source / relative).is_file():
                    changed.append(relative)
                    init_project.merge_file(source / relative, target / relative,
                                            False, [])
            for name in init_project.EXTRAS:
                relative = Path(name)
                if (source / relative).is_file() and not (target / relative).exists():
                    dst = target / relative
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    changed.append(relative)
                    shutil.copy2(source / relative, dst)
            if inventory["adapter_directory"]:
                canonical = target / ".agents" / "skills"
                for skill in canonical.iterdir():
                    if not skill.is_dir():
                        continue
                    destination = adapter / skill.name
                    if destination.is_dir():
                        shutil.rmtree(destination)
                    elif destination.exists():
                        destination.unlink()
                    shutil.copytree(skill, destination)
            else:
                distribution.ensure_claude_adapter(target, False, [])
        except Exception:
            if not adapter_existed and (adapter.exists() or adapter.is_symlink()):
                if adapter.is_symlink():
                    adapter.unlink()
                elif adapter.is_dir():
                    shutil.rmtree(adapter)
            elif inventory["adapter_directory"]:
                shutil.rmtree(adapter)
                previous = ((target / archive / "replaced" / ".claude" / "skills")
                            if (target / ".spec").exists()
                            else (archived / "replaced" / ".claude" / "skills"))
                shutil.copytree(previous, adapter)
            for relative in reversed(changed):
                destination = target / relative
                original = ((target / archive / "replaced" / relative)
                            if (target / ".spec").exists()
                            else (archived / "replaced" / relative))
                if original.is_file():
                    shutil.copy2(original, destination)
                else:
                    destination.unlink(missing_ok=True)
            shutil.rmtree(target / ".spec", ignore_errors=True)
            backup_spec.rename(target / ".spec")
            raise
    return {**current, "status": "applied"}
