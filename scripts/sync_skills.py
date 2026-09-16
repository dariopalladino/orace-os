#!/usr/bin/env python3
"""Keep host skill directories in sync with the canonical tree in .agents/skills.

`.agents/skills/` is the single source of truth. Claude Code discovers skills in
`.claude/skills/`; this script links or copies the canonical tree there.

    python3 scripts/sync_skills.py          # create or refresh the adapter
    python3 scripts/sync_skills.py --check  # fail if the adapter has drifted
"""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import sys
from pathlib import Path

CANONICAL = Path(".agents/skills")
ADAPTERS = [Path(".claude/skills")]


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
    for path in sorted(target.rglob("*")):
        if path.is_dir() or ".DS_Store" in path.name:
            continue
        if not (source / path.relative_to(target)).is_file():
            problems.append(f"not in canonical tree: {path}")
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
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"ok: {len(ADAPTERS)} skill adapter(s) match {CANONICAL}")
    return 0


def sync(root: Path) -> int:
    source = root / CANONICAL
    for adapter in ADAPTERS:
        target = root / adapter
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)
        try:
            target.symlink_to(link_target(root, adapter), target_is_directory=True)
            print(f"linked {adapter} -> {link_target(root, adapter)}")
        except OSError:
            shutil.copytree(source, target, ignore=shutil.ignore_patterns(".DS_Store"))
            print(f"copied {CANONICAL} -> {adapter} (symlinks unavailable on this platform)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify without writing")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    root = repo_root(Path(args.root))
    return check(root) if args.check else sync(root)


if __name__ == "__main__":
    raise SystemExit(main())
