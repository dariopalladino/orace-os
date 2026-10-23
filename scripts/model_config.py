"""Host-specific model choices. 'auto' delegates to the active harness."""

from __future__ import annotations

import json
import re
from pathlib import Path

HOSTS = ("claude", "codex", "copilot")
ROLES = ("workshop", "supervisor", "subagents")
MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]*$")


def defaults() -> dict[str, dict[str, str]]:
    return {host: {role: "auto" for role in ROLES} for host in HOSTS}


def validate(value: object) -> dict[str, dict[str, str]]:
    if value is None:
        return defaults()
    if not isinstance(value, dict) or set(value) - set(HOSTS):
        raise ValueError("project.json models must map only claude, codex, and copilot")
    result = defaults()
    for host, choices in value.items():
        if not isinstance(choices, dict) or set(choices) - set(ROLES):
            raise ValueError(f"project.json models.{host} must map workshop, supervisor, and subagents")
        for role, model in choices.items():
            if not isinstance(model, str) or not MODEL_ID.fullmatch(model):
                raise ValueError(f"project.json models.{host}.{role} must be 'auto' or a model id")
            result[host][role] = model
    return result


def load(root: Path) -> dict[str, dict[str, str]]:
    project = root / ".spec" / "project.json"
    if not project.is_file():
        return defaults()
    try:
        data = json.loads(project.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read .spec/project.json: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("project.json must be an object")
    return validate(data.get("models"))


def for_role(models: dict[str, dict[str, str]], host: str, role_name: str) -> str:
    group = "supervisor" if role_name.lower() == "supervisor" else "subagents"
    return models[host][group]
