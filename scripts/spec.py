#!/usr/bin/env python3
"""SDDF routing engine: validate the specification registry and select what a task needs.

No third-party packages. Python 3.10+.

    python3 scripts/spec.py validate
    python3 scripts/spec.py select --surface backend --surface auth --path api/app/login.py
    python3 scripts/spec.py select --task PAY-014
    python3 scripts/spec.py playbooks

`select` prints the documents a compliant agent should load, why each was
included, and a character-based size estimate. It does not load anything into a
model context and it does not run project checks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

SURFACES = frozenset({
    "docs", "planning", "architecture", "domain", "backend", "frontend",
    "native", "api", "data", "auth", "security", "infra", "release",
    "governance", "ai", "hitl", "implementation", "review", "testing",
    "observability", "example",
})

ID_PATTERN = re.compile(r"[a-z][a-z0-9-]*")
TASK_PATTERN = re.compile(r"^##\s+([A-Z][A-Z0-9-]*)\s+—\s+(.*)$")
CHARS_PER_TOKEN = 4


class SpecError(ValueError):
    """A configuration or selection fault that must never silently omit policy."""


@dataclass(frozen=True)
class Spec:
    id: str
    path: str
    surfaces: tuple[str, ...]
    requires: tuple[str, ...]
    playbooks: tuple[str, ...]

    def baseline(self) -> bool:
        return "*" in self.surfaces

    def eligible(self, active: frozenset[str]) -> bool:
        return "*" in self.playbooks or bool(set(self.playbooks) & active)


# --------------------------------------------------------------------------- io


def repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".spec" / "INDEX.md").is_file():
            return candidate
    raise SpecError("No .spec/INDEX.md found; run inside an SDDF-governed repository")


def safe_path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise SpecError(f"Expected a portable repository-relative path: {value!r}")
    parts = PurePosixPath(value)
    if parts.is_absolute() or ".." in parts.parts or not parts.parts or ":" in value:
        raise SpecError(f"Unsafe repository-relative path: {value!r}")
    resolved = (root / value).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise SpecError(f"Path escapes the repository: {value!r}")
    return resolved


def path_parts(value: str) -> tuple[str, ...]:
    """Normalise a proposed source path without requiring the file to exist."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise SpecError(f"Expected a repository-relative source path: {value!r}")
    normalised = value.strip().replace("\\", "/")
    if normalised.startswith("/") or re.match(r"^[A-Za-z]:", normalised):
        raise SpecError(f"Expected a repository-relative source path: {value!r}")
    parts = tuple(part for part in normalised.split("/") if part not in {"", "."})
    if not parts or ".." in parts or any(":" in part for part in parts):
        raise SpecError(f"Unsafe repository-relative source path: {value!r}")
    return parts


def root_parts(value: str) -> tuple[str, ...]:
    """Module roots are directory prefixes; '*' is one segment, '**' is any depth."""
    if not isinstance(value, str) or not value.endswith("/") or "\\" in value:
        raise SpecError(f"module root must be a portable directory prefix ending in '/': {value!r}")
    parts = path_parts(value)
    if any(("*" in part or "?" in part or "[" in part or "]" in part)
           and part not in {"*", "**"} for part in parts):
        raise SpecError(f"module root has unsupported glob segment: {value!r}")
    return parts


def root_matches(pattern: tuple[str, ...], path: tuple[str, ...]) -> bool:
    """Match a globbed directory root against a path or any of its ancestors."""
    def match(i: int, j: int) -> bool:
        if i == len(pattern):
            return True
        if pattern[i] == "**":
            return match(i + 1, j) or (j < len(path) and match(i, j + 1))
        return j < len(path) and (pattern[i] == "*" or pattern[i] == path[j]) and match(i + 1, j + 1)
    return match(0, 0)


def cells(line: str) -> list[str]:
    return [part.strip().strip("`") for part in line.strip().strip("|").split("|")]


def listed(value: str) -> tuple[str, ...]:
    if value in {"-", ""}:
        return ()
    return tuple(part.strip().strip("`") for part in value.split(",") if part.strip())


# ----------------------------------------------------------------------- loading


def load_playbook_catalog(root: Path) -> dict[str, Path]:
    folder = root / ".spec" / "10_playbooks"
    if not folder.is_dir():
        return {}
    catalog = {}
    for child in sorted(folder.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if not ID_PATTERN.fullmatch(child.name):
            raise SpecError(f"Playbook directory is not a valid playbook id: {child.name!r}")
        pack = child / "PACK.md"
        if not pack.is_file():
            raise SpecError(f"Playbook {child.name!r} has no PACK.md entry document")
        catalog[child.name] = pack
    return catalog


def load_registry(root: Path, catalog: dict[str, Path]) -> dict[str, Spec]:
    index = root / ".spec" / "INDEX.md"
    try:
        lines = index.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SpecError(f"Cannot read {index}: {exc}") from exc

    specs: dict[str, Spec] = {}
    in_table = False
    for number, line in enumerate(lines, 1):
        if not line.strip().startswith("|"):
            in_table = False
            continue
        parts = cells(line)
        if parts == ["ID", "Path", "Surfaces", "Requires", "Playbooks"]:
            in_table = True
            continue
        if not in_table or all(re.fullmatch(r":?-+:?", part) for part in parts):
            continue
        if len(parts) != 5:
            raise SpecError(f"INDEX.md:{number}: expected five routing columns, got {len(parts)}")
        spec_id, path, surfaces, requires, playbooks = parts
        if not ID_PATTERN.fullmatch(spec_id):
            raise SpecError(f"INDEX.md:{number}: invalid routing id {spec_id!r}")
        if spec_id in specs:
            raise SpecError(f"INDEX.md:{number}: duplicate routing id {spec_id!r}")
        surface_list = listed(surfaces)
        unknown = set(surface_list) - SURFACES - {"*"}
        if not surface_list or unknown:
            raise SpecError(f"{spec_id}: missing or unknown surfaces {sorted(unknown)}")
        if "*" in surface_list and len(surface_list) > 1:
            raise SpecError(f"{spec_id}: baseline '*' cannot be combined with named surfaces")
        playbook_list = listed(playbooks)
        if not playbook_list:
            raise SpecError(f"{spec_id}: Playbooks must be '*' or a comma-separated playbook list")
        unknown_playbooks = set(playbook_list) - set(catalog) - {"*"}
        if unknown_playbooks:
            raise SpecError(
                f"{spec_id}: unknown playbooks {sorted(unknown_playbooks)}; "
                f"registered playbooks: {', '.join(sorted(catalog)) or 'none'}"
            )
        if "*" in playbook_list and len(playbook_list) > 1:
            raise SpecError(f"{spec_id}: playbook '*' cannot be combined with named playbooks")
        target = safe_path(root, path)
        if not target.is_file():
            raise SpecError(f"{spec_id}: registered document is missing: {path}")
        specs[spec_id] = Spec(spec_id, path, surface_list, listed(requires), playbook_list)

    if not specs:
        raise SpecError("INDEX.md has no routing table (ID | Path | Surfaces | Requires | Playbooks)")

    seen: dict[Path, str] = {}
    for spec in specs.values():
        resolved = safe_path(root, spec.path)
        if resolved in seen:
            raise SpecError(f"{spec.id}: path already registered by {seen[resolved]}: {spec.path}")
        seen[resolved] = spec.id

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(spec_id: str, chain: list[str]) -> None:
        if spec_id not in specs:
            raise SpecError(f"Missing dependency: {' -> '.join(chain + [spec_id])}")
        if spec_id in visiting:
            raise SpecError(f"Dependency cycle: {' -> '.join(chain + [spec_id])}")
        if spec_id in visited:
            return
        visiting.add(spec_id)
        for dependency in specs[spec_id].requires:
            visit(dependency, chain + [spec_id])
        visiting.discard(spec_id)
        visited.add(spec_id)

    for spec_id in specs:
        visit(spec_id, [])
    return specs


def load_project(root: Path, specs: dict[str, Spec], catalog: dict[str, Path]) -> dict:
    config_path = root / ".spec" / "project.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SpecError(f"Cannot read .spec/project.json: {exc}") from exc
    if not isinstance(config, dict) or config.get("version") != 2:
        raise SpecError("project.json must be an object with version: 2")

    playbooks = config.get("playbooks")
    if not isinstance(playbooks, list) or not all(isinstance(item, str) for item in playbooks):
        raise SpecError("project.json playbooks must be a list of registered playbook ids")
    unknown = set(playbooks) - set(catalog)
    if unknown:
        raise SpecError(
            f"project.json selects unregistered playbooks {sorted(unknown)}; "
            f"available: {', '.join(sorted(catalog)) or 'none'}"
        )

    orchestration = config.get("orchestration")
    if orchestration not in {"supervisor", "sequential"}:
        raise SpecError("project.json orchestration must be 'supervisor' or 'sequential'")

    roots = config.get("module_roots")
    if not isinstance(roots, dict):
        raise SpecError("project.json module_roots must map surface names to path lists")
    for surface, paths in roots.items():
        if surface not in SURFACES:
            raise SpecError(f"project.json module_roots uses unknown surface {surface!r}")
        if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
            raise SpecError(f"project.json module_roots[{surface!r}] must be a list of paths")
        for item in paths:
            root_parts(item)

    architecture_root = config.get("architecture_root", ".spec/15_architecture")
    safe_path(root, architecture_root)

    budget = config.get("context_budget", {})
    if not isinstance(budget, dict):
        raise SpecError("project.json context_budget must be an object")
    for key in ("warn_tokens", "hard_tokens"):
        value = budget.get(key)
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise SpecError(f"project.json context_budget.{key} must be a positive integer")

    if not isinstance(config.get("checks"), dict):
        raise SpecError("project.json checks must be an object of documented commands")

    config["architecture_root"] = architecture_root
    config["context_budget"] = budget
    unreachable = {playbook for playbook in playbooks} - {
        item for spec in specs.values() for item in spec.playbooks
    }
    if unreachable:
        raise SpecError(
            f"Active playbooks with no registered routing row: {sorted(unreachable)}; "
            "register the playbook PACK.md in .spec/INDEX.md"
        )
    return config


# -------------------------------------------------------------------- selection


def surfaces_for_path(config: dict, value: str) -> set[str]:
    found = set()
    candidate = path_parts(value)
    for surface, roots in config["module_roots"].items():
        for prefix in roots:
            if root_matches(root_parts(prefix), candidate):
                found.add(surface)
    return found


def read_task(root: Path, task_id: str) -> dict:
    backlog = root / ".spec" / "20_backlog" / "TASKS.md"
    try:
        lines = backlog.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SpecError(f"Cannot read {backlog}: {exc}") from exc
    collected: dict[str, list[str]] = {}
    active = False
    for line in lines:
        header = TASK_PATTERN.match(line)
        if header:
            active = header.group(1) == task_id
            if active:
                collected["objective"] = [header.group(2).strip()]
            continue
        if not active:
            continue
        match = re.match(r"^-\s*(Surfaces|Specifications|Paths|Package)\s*:\s*(.*)$", line.strip())
        if match:
            key = match.group(1).lower()
            values = [item.strip().strip("`") for item in match.group(2).split(",") if item.strip()]
            collected.setdefault(key, []).extend(values)
    if not collected:
        raise SpecError(f"Task {task_id!r} not found in .spec/20_backlog/TASKS.md")
    return collected


def select(
    specs: dict[str, Spec],
    config: dict,
    surfaces: set[str],
    paths: list[str],
    explicit: list[str],
    playbooks: frozenset[str],
) -> dict[str, list[str]]:
    reasons: dict[str, list[str]] = {}

    def note(spec_id: str, reason: str) -> None:
        reasons.setdefault(spec_id, [])
        if reason not in reasons[spec_id]:
            reasons[spec_id].append(reason)

    requested = set(surfaces)
    unknown = requested - SURFACES
    if unknown:
        raise SpecError(f"Unknown surfaces {sorted(unknown)}; resolve before execution")
    for value in paths:
        derived = surfaces_for_path(config, value)
        if not derived and not surfaces:
            raise SpecError(
                f"Path {value!r} matches no module root; add it to project.json module_roots "
                "or pass explicit --surface values"
            )
        requested |= derived

    for spec in specs.values():
        if not spec.eligible(playbooks):
            continue
        if spec.baseline():
            note(spec.id, "baseline")
            continue
        for surface in sorted(set(spec.surfaces) & requested):
            origin = next(
                (f"path:{value} -> {surface}" for value in paths if surface in surfaces_for_path(config, value)),
                f"surface:{surface}",
            )
            note(spec.id, origin)

    for spec_id in explicit:
        if spec_id not in specs:
            raise SpecError(f"Explicit specification {spec_id!r} is not registered in .spec/INDEX.md")
        if not specs[spec_id].eligible(playbooks):
            raise SpecError(
                f"Explicit specification {spec_id!r} belongs to playbooks "
                f"{', '.join(specs[spec_id].playbooks)} which are not active. "
                "Activate the playbook or change the reference; do not omit it silently."
            )
        note(spec_id, "explicit reference")

    frontier = list(reasons)
    while frontier:
        spec_id = frontier.pop()
        for dependency in specs[spec_id].requires:
            if dependency not in specs:
                raise SpecError(f"Missing dependency {dependency!r} required by {spec_id!r}")
            if not specs[dependency].eligible(playbooks):
                raise SpecError(
                    f"{spec_id!r} requires {dependency!r}, which is not available for the active "
                    "playbooks. Fix the registry rather than dropping the requirement."
                )
            if dependency not in reasons:
                frontier.append(dependency)
            note(dependency, f"required by:{spec_id}")
    return reasons


def measure(root: Path, specs: dict[str, Spec], chosen: list[str]) -> tuple[int, int]:
    characters = sum(safe_path(root, specs[spec_id].path).stat().st_size for spec_id in chosen)
    return characters, characters // CHARS_PER_TOKEN


# ------------------------------------------------------------------- validation


def registered_paths(root: Path, specs: dict[str, Spec]) -> set[Path]:
    return {safe_path(root, spec.path) for spec in specs.values()}


def check_coverage(root: Path, specs: dict[str, Spec], config: dict, catalog: dict[str, Path]) -> list[str]:
    known = registered_paths(root, specs)
    problems = []

    for path in sorted((root / ".spec" / "00_global").rglob("*.md")):
        if path.parent.name == "references":
            continue
        if path.resolve() not in known:
            problems.append(f"Unregistered global policy: {path.relative_to(root)}")

    for playbook, pack in catalog.items():
        if pack.resolve() not in known:
            problems.append(f"Unregistered playbook pack: {pack.relative_to(root)} (playbook {playbook})")

    architecture = root / config["architecture_root"]
    if architecture.is_dir():
        for path in sorted(architecture.rglob("*.md")):
            relative = path.relative_to(architecture)
            if relative.name == "README.md" or "_notes" in relative.parts:
                continue
            if path.resolve() not in known:
                problems.append(
                    f"Unregistered architecture artifact: {path.relative_to(root)} "
                    "(an artifact nobody routes to is an artifact nobody reads)"
                )
    return problems


def check_routing_cases(root: Path, specs: dict[str, Spec], config: dict) -> list[str]:
    cases_path = root / ".spec" / "validation" / "ROUTING_CASES.json"
    if not cases_path.is_file():
        return []
    try:
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"ROUTING_CASES.json is not valid JSON: {exc}"]
    problems = []
    warn = config["context_budget"].get("warn_tokens")
    hard = config["context_budget"].get("hard_tokens")
    for case in cases.get("cases", []):
        name = case.get("name", "<unnamed>")
        playbooks = frozenset(case.get("playbooks", config["playbooks"]))
        case_config = {**config, "module_roots": case.get("module_roots", config["module_roots"])}
        try:
            reasons = select(
                specs,
                case_config,
                set(case.get("surfaces", [])),
                list(case.get("paths", [])),
                list(case.get("specs", [])),
                playbooks,
            )
        except SpecError as exc:
            problems.append(f"{name}: selection failed: {exc}")
            continue
        chosen = set(reasons)
        for spec_id in case.get("expect", []):
            if spec_id not in chosen:
                problems.append(f"{name}: expected {spec_id!r} to be selected")
        for spec_id in case.get("reject", []):
            if spec_id in chosen:
                problems.append(f"{name}: expected {spec_id!r} to stay out of selection")
        _, tokens = measure(root, specs, sorted(chosen))
        limit = case.get("max_tokens") or hard
        if limit and tokens > limit:
            problems.append(f"{name}: selection estimates {tokens} tokens, above the {limit} limit")
        elif warn and tokens > warn:
            print(f"warning: {name} estimates {tokens} tokens, above warn_tokens {warn}", file=sys.stderr)
    return problems


# ---------------------------------------------------------------------- command


def command_validate(root: Path) -> int:
    catalog = load_playbook_catalog(root)
    specs = load_registry(root, catalog)
    config = load_project(root, specs, catalog)
    problems = check_coverage(root, specs, config, catalog) + check_routing_cases(root, specs, config)
    import architecture
    drift = architecture.impact(root, specs, config, [], set())["findings"]
    problems += [f"Architecture link: {item['id']}: {item['detail']}" for item in drift
                 if item["kind"] in {"scenario_link_missing", "superseded_adr_missing"}]
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1
    print(
        f"ok: {len(specs)} registered specifications, {len(catalog)} playbook packs, "
        f"active playbooks: {', '.join(config['playbooks']) or 'none'}"
    )
    return 0


def command_select(root: Path, args: argparse.Namespace) -> int:
    catalog = load_playbook_catalog(root)
    specs = load_registry(root, catalog)
    config = load_project(root, specs, catalog)

    surfaces = set(args.surface)
    paths = list(args.path)
    explicit = list(args.spec)
    if args.task:
        task = read_task(root, args.task)
        surfaces |= set(task.get("surfaces", []))
        paths += task.get("paths", [])
        explicit += task.get("specifications", [])
        if not surfaces and not paths and not explicit:
            raise SpecError(
                f"Task {args.task} declares no Surfaces, Paths, or Specifications; "
                "a task without routing metadata cannot be selected deterministically"
            )

    playbooks = frozenset(args.playbook or config["playbooks"])
    reasons = select(specs, config, surfaces, paths, explicit, playbooks)
    chosen = sorted(reasons, key=lambda spec_id: (specs[spec_id].path))
    characters, tokens = measure(root, specs, chosen)

    if args.json:
        print(json.dumps({
            "playbooks": sorted(playbooks),
            "selected": [
                {"id": spec_id, "path": specs[spec_id].path, "reasons": reasons[spec_id]}
                for spec_id in chosen
            ],
            "characters": characters,
            "estimated_tokens": tokens,
        }, indent=2))
    else:
        width = max((len(spec_id) for spec_id in chosen), default=1)
        for spec_id in chosen:
            print(f"{spec_id:<{width}}  {specs[spec_id].path}")
            print(f"{'':<{width}}  └─ {'; '.join(reasons[spec_id])}")
        skipped = len(specs) - len(chosen)
        print(
            f"\nSelected {len(chosen)} of {len(specs)} registered specifications "
            f"({skipped} not loaded); {characters} characters, ~{tokens} tokens "
            "(characters/4 estimate, not measured tokens)."
        )
        print(
            "\nPrecedence: an approved architecture scenario Measure or ADR governs the artifact "
            "it names; playbook and policy numbers are defaults that apply only where the "
            "architecture is silent."
        )

    budget = config["context_budget"]
    if budget.get("hard_tokens") and tokens > budget["hard_tokens"]:
        print(
            f"error: selection exceeds context_budget.hard_tokens ({budget['hard_tokens']}). "
            "Split the task into smaller work packages.",
            file=sys.stderr,
        )
        return 1
    if budget.get("warn_tokens") and tokens > budget["warn_tokens"]:
        print(
            f"warning: selection exceeds context_budget.warn_tokens ({budget['warn_tokens']}). "
            "Consider narrowing scope or splitting the task.",
            file=sys.stderr,
        )
    return 0


def command_playbooks(root: Path) -> int:
    catalog = load_playbook_catalog(root)
    specs = load_registry(root, catalog)
    config = load_project(root, specs, catalog)
    active = set(config["playbooks"])
    for playbook, pack in sorted(catalog.items()):
        mark = "active " if playbook in active else "       "
        print(f"{mark} {playbook:<20} {pack.relative_to(root)}")
    return 0


PLAYBOOK_TEMPLATE = """---
id: play-{short}
playbook: {playbook}
---

# Playbook pack — {title}

> One line: what technology or domain this pack governs and which global policies it applies.
> Numbers here are defaults. Where an approved architecture scenario Measure or ADR states a
> value for the artifact being changed, that value governs and these defaults fall away.

## Baseline

- Language/runtime version, toolchain, and the single choice made for each job.
- Lint, format, type, and test commands — each mirrored into `.spec/project.json` `checks`.

## Layout

```
<the directory shape this pack expects>
```

## Rules

- **{prefix}-01** <enforceable MUST/MUST NOT, referencing the global rule it specialises>
- **{prefix}-02** ...

## References — load only when the work needs them

| File | Load when |
|---|---|
| `references/<topic>.md` | <the narrow situation that justifies loading it> |

## Checks

```sh
<commands>
```
"""


def command_scaffold(root: Path, args: argparse.Namespace) -> int:
    playbook = args.id
    if not ID_PATTERN.fullmatch(playbook):
        raise SpecError(f"Playbook id must be lowercase kebab-case: {playbook!r}")
    folder = root / ".spec" / "10_playbooks" / playbook
    if folder.exists():
        raise SpecError(f"Playbook {playbook!r} already exists at {folder.relative_to(root)}")
    (folder / "references").mkdir(parents=True)
    short = playbook.split("-")[0]
    prefix = short[:3].upper()
    (folder / "PACK.md").write_text(
        PLAYBOOK_TEMPLATE.format(
            short=short,
            playbook=playbook,
            title=playbook.replace("-", " ").title(),
            prefix=prefix,
        ),
        encoding="utf-8",
    )
    (folder / "references" / ".gitkeep").write_text("", encoding="utf-8")
    print(f"created {folder.relative_to(root)}/PACK.md")
    print("\nNext, add this row to the .spec/INDEX.md routing table:")
    print(f"| play-{short} | .spec/10_playbooks/{playbook}/PACK.md | <surfaces> | principles | {playbook} |")
    print(f'\nThen add "{playbook}" to .spec/project.json playbooks, and run:')
    print("  python3 scripts/spec.py validate")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".", help="Repository root (default: search upward from cwd)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="Check the registry, project config, coverage, and routing cases")
    sub.add_parser("playbooks", help="List registered playbook packs and which are active")

    scaffold = sub.add_parser("scaffold", help="Create a new playbook pack skeleton")
    scaffold.add_argument("id", help="Playbook id, lowercase kebab-case (e.g. java-backend)")

    selector = sub.add_parser("select", help="Print the documents a task should load, and why")
    selector.add_argument("--surface", action="append", default=[], help="Repeatable semantic surface")
    selector.add_argument("--path", action="append", default=[], help="Repeatable affected or planned path")
    selector.add_argument("--spec", action="append", default=[], help="Repeatable explicit specification id")
    selector.add_argument("--playbook", action="append", default=[], help="Override active playbooks for this selection")
    selector.add_argument("--task", help="Read Surfaces/Paths/Specifications from a backlog task id")
    selector.add_argument("--json", action="store_true", help="Emit machine-readable output")

    args = parser.parse_args(argv)
    try:
        root = repo_root(Path(args.root))
        if args.command == "validate":
            return command_validate(root)
        if args.command == "playbooks":
            return command_playbooks(root)
        if args.command == "scaffold":
            return command_scaffold(root, args)
        return command_select(root, args)
    except SpecError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
