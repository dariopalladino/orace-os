"""Read-only architecture impact and lifecycle diagnostics for ORACE artifacts."""

from __future__ import annotations

import re
from pathlib import Path

import spec

STATUSES = {"proposed", "accepted", "superseded", "retired", "deprecated"}
SCENARIO_ID = re.compile(r"\bQA-[A-Z][A-Z0-9-]*-\d+\b")
ADR_ID = re.compile(r"\bADR-\d+\b")


def frontmatter(path: Path) -> dict[str, str | list[str]]:
    """Parse the small scalar/list subset used by the shipped ADR templates."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str | list[str]] = {}
    current = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if re.match(r"^[A-Za-z_][A-Za-z0-9_-]*:\s*", line):
            key, value = line.split(":", 1)
            current = key.strip()
            raw = value.strip().strip('"\'')
            fields[current] = raw if raw else []
        elif current and re.match(r"^\s+-\s+", line):
            item = re.sub(r"^\s+-\s+", "", line).strip().strip('"\'')
            if isinstance(fields[current], list):
                fields[current].append(item)
    return fields


def values(value: str | list[str] | None) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if value.startswith("[") and value.endswith("]"):
        return [part.strip().strip('"\'') for part in value[1:-1].split(",") if part.strip()]
    return [value]


def adr_records(root: Path, specs: dict[str, spec.Spec], architecture_root: str) -> list[dict]:
    prefix = architecture_root.rstrip("/") + "/decisions/"
    records = []
    for item in specs.values():
        if not (item.path.startswith(prefix) or "/decisions/" in item.path) or not item.path.endswith(".md"):
            continue
        path = spec.safe_path(root, item.path)
        meta = frontmatter(path)
        body = path.read_text(encoding="utf-8")
        status = str(meta.get("status", "")).lower().strip()
        if status not in STATUSES:
            match = re.search(r"^## Status\s*\n\s*(Proposed|Accepted|Superseded|Retired|Deprecated)\b",
                              body, re.MULTILINE | re.IGNORECASE)
            status = match.group(1).lower() if match else "unknown"
        heading = re.search(r"^#\s+(ADR-\d+)\b", body, re.MULTILINE)
        filename = re.match(r"^(\d+)-", path.name)
        adr_id = heading.group(1) if heading else (f"ADR-{filename.group(1)}" if filename else None)
        record = {
            "id": item.id,
            "path": item.path,
            "adr_id": adr_id,
            "status": status,
            "owner": str(meta.get("owner", "")).strip(),
            "affected_paths": values(meta.get("affected_paths")),
            "scenarios_addressed": values(meta.get("scenarios_addressed")),
            "supersedes": values(meta.get("supersedes")),
            "surfaces": list(item.surfaces),
        }
        records.append(record)
    return records


def path_applies(pattern: str, candidate: str) -> bool:
    if pattern.endswith("/"):
        return spec.root_matches(spec.root_parts(pattern), spec.path_parts(candidate))
    return spec.path_parts(pattern) == spec.path_parts(candidate)


def impact(root: Path, specs: dict[str, spec.Spec], config: dict,
           paths: list[str], surfaces: set[str]) -> dict:
    records = adr_records(root, specs, config["architecture_root"])
    scenario_files = [spec.safe_path(root, item.path) for item in specs.values()
                      if Path(item.path).name == "quality-scenarios.md"]
    scenarios_path = root / config["architecture_root"] / "quality-scenarios.md"
    if scenarios_path.is_file() and scenarios_path not in scenario_files:
        scenario_files.append(scenarios_path)
    scenario_text = "\n".join(path.read_text(encoding="utf-8") for path in scenario_files)
    known_scenarios = set(SCENARIO_ID.findall(scenario_text))
    affected = []
    findings = []
    known_adrs = {item["adr_id"] for item in records if item["adr_id"]}
    for record in records:
        if record["status"] == "unknown":
            findings.append({"kind": "lifecycle_unknown", "id": record["id"],
                             "detail": "ADR status is not machine-readable"})
        if record["status"] == "accepted":
            if not record["owner"]:
                findings.append({"kind": "owner_unknown", "id": record["id"],
                                 "detail": "accepted ADR has no owner metadata"})
            if not record["affected_paths"]:
                findings.append({"kind": "path_scope_unknown", "id": record["id"],
                                 "detail": "accepted ADR has no affected_paths metadata"})
        for scenario in record["scenarios_addressed"]:
            if SCENARIO_ID.fullmatch(scenario) and scenario not in known_scenarios:
                findings.append({"kind": "scenario_link_missing", "id": record["id"],
                                 "detail": f"{scenario} is absent from quality-scenarios.md"})
        for prior in record["supersedes"]:
            if prior.lower() != "none" and prior not in known_adrs:
                findings.append({"kind": "superseded_adr_missing", "id": record["id"],
                                 "detail": f"{prior} has no registered ADR"})
        if record["status"] not in {"accepted", "unknown"}:
            continue
        exact = [path for path in paths if path == record["path"] or any(
            path_applies(pattern, path) for pattern in record["affected_paths"])]
        surface_match = bool(set(record["surfaces"]) & surfaces) or "*" in record["surfaces"]
        if exact or surface_match:
            affected.append({"id": record["id"], "adr_id": record["adr_id"],
                             "status": record["status"], "path": record["path"],
                             "match": "path" if exact else "surface_possible",
                             "changed_paths": exact,
                             "scenarios_addressed": record["scenarios_addressed"]})
    return {"affected_decisions": affected, "findings": findings,
            "known_scenarios": sorted(known_scenarios),
            "note": "Affected records are review candidates; accepted architecture is never rewritten automatically."}
