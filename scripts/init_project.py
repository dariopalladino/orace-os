#!/usr/bin/env python3
"""Install SDDF into another repository without clobbering what is already there.

    python3 scripts/init_project.py --target /path/to/repo
    python3 scripts/init_project.py --target /path/to/repo --dry-run

Directories (`.spec/`, `.agents/`, `.claude/`, `scripts/`, `tests/`) are copied.
Instruction files (`AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`)
are *merged*: an existing file keeps its content and gains an appended SDDF
section, so a repository's own conventions are never overwritten.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

TREES = [".spec", ".agents", ".claude", "scripts", "tests"]
MERGE_FILES = ["AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"]
EXTRAS = ["PROMPT.md", "docs/ADOPTION.md", "docs/EXTENDING.md"]
MARKER = "<!-- sddf:begin -->"
END_MARKER = "<!-- sddf:end -->"
SKIP = {".git", "__pycache__", ".pytest_cache", ".DS_Store"}


def copy_tree(source: Path, target: Path, force: bool, dry_run: bool, log: list[str]) -> None:
    if target.exists() and not force:
        if target.name == ".spec":
            raise SystemExit(
                f"error: {target} already exists. This repository may already be governed. "
                "Merge by hand, or re-run with --force if you mean to replace it."
            )
        log.append(f"merge into existing {target}")
    if dry_run:
        log.append(f"would copy {source.name}/ -> {target}")
        return
    shutil.copytree(
        source, target, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(*SKIP),
    )
    log.append(f"copied {source.name}/ -> {target}")


def merge_file(source: Path, target: Path, dry_run: bool, log: list[str]) -> None:
    incoming = source.read_text(encoding="utf-8").strip()
    block = f"\n\n{MARKER}\n\n{incoming}\n\n{END_MARKER}\n"

    if not target.exists():
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(incoming + "\n", encoding="utf-8")
        log.append(f"created {target}")
        return

    existing = target.read_text(encoding="utf-8")
    if MARKER in existing:
        head, _, rest = existing.partition(MARKER)
        _, _, tail = rest.partition(END_MARKER)
        merged = head.rstrip() + block + tail.lstrip()
        action = "refreshed SDDF section in"
    else:
        merged = existing.rstrip() + block
        action = "appended SDDF section to"
    if not dry_run:
        target.write_text(merged, encoding="utf-8")
    log.append(f"{action} {target} (existing content preserved)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", required=True, help="Repository to install into")
    parser.add_argument("--force", action="store_true", help="Replace an existing .spec/ instead of refusing")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen and change nothing")
    args = parser.parse_args(argv)

    source_root = Path(__file__).resolve().parent.parent
    target_root = Path(args.target).expanduser().resolve()
    if not target_root.is_dir():
        raise SystemExit(f"error: target is not a directory: {target_root}")
    if target_root == source_root:
        raise SystemExit("error: target is the framework itself")

    log: list[str] = []
    for name in TREES:
        source = source_root / name
        if source.is_dir():
            copy_tree(source, target_root / name, args.force, args.dry_run, log)
    for name in MERGE_FILES:
        source = source_root / name
        if source.is_file():
            merge_file(source, target_root / name, args.dry_run, log)
    for name in EXTRAS:
        source = source_root / name
        target = target_root / name
        if source.is_file() and not target.exists():
            if not args.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            log.append(f"copied {name}")

    for line in log:
        print(line)

    print("\nNext:")
    print("  1. Edit .spec/project.json — playbooks, module_roots, checks, orchestration.")
    print("  2. Run /orace-workshop .spec/15_architecture to capture the architecture.")
    print("  3. Run /spec-bootstrap to register it and derive the backlog.")
    print("  4. python3 scripts/spec.py validate")
    if args.dry_run:
        print("\n(dry run — nothing was written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
