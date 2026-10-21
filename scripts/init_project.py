#!/usr/bin/env python3
"""Install SDDF into another repository without clobbering what is already there.

    python3 scripts/init_project.py --target /path/to/repo
    python3 scripts/init_project.py --target /path/to/repo --dry-run

The `.spec/` template is copied for a new project. Managed runtime files are
copied individually and recorded in `.spec/installation.json`; framework tests
are not installed into the target repository.
Instruction files (`AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`)
are *merged*: an existing file keeps its content and gains an appended SDDF
section, so a repository's own conventions are never overwritten. Repeat
installations use `python3 scripts/orace.py upgrade --target ...`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import distribution

MERGE_FILES = ["AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"]
EXTRAS = ["PROMPT.md", "docs/ADOPTION.md", "docs/CODEX.md", "docs/EXTENDING.md"]
MARKER = "<!-- sddf:begin -->"
END_MARKER = "<!-- sddf:end -->"
SKIP = {".git", "__pycache__", ".pytest_cache", ".DS_Store"}
SPEC_TEMPLATE_DIRS = ("00_global", "10_playbooks", "validation")
SPEC_TEMPLATE_FILES = ("README.md", "INDEX.md", "project.json",
                       "15_architecture/README.md", "40_workspace/README.md",
                       "50_archive/README.md")


def copy_spec_template(source: Path, target: Path, dry_run: bool, log: list[str]) -> None:
    if target.exists():
        log.append(f"preserved existing {target}")
        return
    if dry_run:
        log.append(f"would copy clean specification template -> {target}")
        return
    for name in SPEC_TEMPLATE_DIRS:
        shutil.copytree(source / name, target / name,
                        ignore=shutil.ignore_patterns(*SKIP))
    for name in SPEC_TEMPLATE_FILES:
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name, destination)
    backlog = (source / "20_backlog/TASKS.md").read_text(encoding="utf-8")
    if "<!-- tasks start -->" in backlog:
        backlog_header = backlog.split("<!-- tasks start -->", 1)[0]
    elif "\n---\n" in backlog:
        # A framework checkout may have an empty backlog without the legacy marker.
        backlog_header = backlog.split("\n---\n", 1)[0].rstrip() + "\n\n"
    else:
        raise ValueError("Backlog template is missing its task separator")
    destination = target / "20_backlog/TASKS.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(backlog_header + "<!-- tasks start -->\n", encoding="utf-8")
    promotion = (source / "30_delivery/PROMOTION_LOG.md").read_text(encoding="utf-8")
    destination = target / "30_delivery/PROMOTION_LOG.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if "\n---\n" not in promotion:
        raise ValueError("Promotion log template is missing its separator")
    destination.write_text(promotion.split("\n---\n", 1)[0].rstrip() + "\n\n---\n",
                           encoding="utf-8")
    log.append(f"copied clean specification template -> {target}")


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
    parser.add_argument("--force", action="store_true", help="Deprecated; existing installations use upgrade")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen and change nothing")
    args = parser.parse_args(argv)

    source_root = Path(__file__).resolve().parent.parent
    target_root = Path(args.target).expanduser().resolve()
    if not target_root.is_dir():
        raise SystemExit(f"error: target is not a directory: {target_root}")
    if target_root == source_root:
        raise SystemExit("error: target is the framework itself")
    if (target_root / distribution.MANIFEST).is_file():
        raise SystemExit("error: ORACE is already installed; use 'orace.py upgrade --target ...'")
    if args.force and (target_root / ".spec").exists():
        raise SystemExit("error: --force would replace project configuration; use upgrade or resolve .spec/ manually")

    log: list[str] = []
    fresh_spec = not (target_root / ".spec").exists()
    copy_spec_template(source_root / ".spec", target_root / ".spec", args.dry_run, log)
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

    if fresh_spec and not args.dry_run:
        project = target_root / ".spec" / "project.json"
        config = json.loads(project.read_text(encoding="utf-8"))
        config["playbooks"] = []
        config["module_roots"] = {}
        config["checks"]["framework"] = [
            "python3 scripts/spec.py validate",
            "python3 scripts/sync_skills.py --check",
        ]
        project.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        log.append("initialized .spec/project.json with no unconfirmed active playbooks or module roots")

    log.extend(distribution.install(source_root, target_root, fresh_spec=fresh_spec,
                                    dry_run=args.dry_run))

    for line in log:
        print(line)

    print("\nNext:")
    print("  1. Run python3 scripts/orace.py discover and review observed facts, unknowns, and suggested playbooks.")
    print("  2. Review .spec/project.json; configure only evidenced playbooks, roots, and checks.")
    print("  3. Run python3 scripts/spec.py validate, then python3 scripts/orace.py task '<request>' --path <path>.")
    print("  4. Invoke the orace-workshop and spec-bootstrap skills as architecture needs grow.")
    print("  Existing ORACE project? Invoke orace-workshop with .spec/15_architecture --rerun technology.")
    if args.dry_run:
        print("\n(dry run — nothing was written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
