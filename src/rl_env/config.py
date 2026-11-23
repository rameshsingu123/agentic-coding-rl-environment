"""Typed, fail-closed task configuration parsing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class TaskConfig:
    """A validated task request; commands are argument vectors, never shell text."""

    task_id: str
    description: str
    command: tuple[str, ...]
    timeout_seconds: int = 60
    max_diff_bytes: int = 1_000_000

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TaskConfig":
        if not isinstance(value, Mapping):
            raise ValueError("task configuration must be a JSON object")
        allowed = {"task_id", "description", "command", "timeout_seconds", "max_diff_bytes"}
        unknown = set(value) - allowed
        missing = {"task_id", "description", "command"} - set(value)
        if unknown:
            raise ValueError(f"unknown task configuration keys: {sorted(unknown)}")
        if missing:
            raise ValueError(f"missing task configuration keys: {sorted(missing)}")

        task_id = value["task_id"]
        description = value["description"]
        command = value["command"]
        if not isinstance(task_id, str) or not task_id.strip() or len(task_id) > 128:
            raise ValueError("task_id must be a non-empty string of at most 128 characters")
        if not isinstance(description, str) or not description.strip() or len(description) > 4000:
            raise ValueError("description must be a non-empty string of at most 4000 characters")
        if not isinstance(command, list) or not command or len(command) > 128:
            raise ValueError("command must be a non-empty JSON array with at most 128 arguments")
        if any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in command):
            raise ValueError("each command argument must be a non-empty string without NUL")
        if any(len(arg) > 4096 for arg in command):
            raise ValueError("command arguments must not exceed 4096 characters")

        timeout = value.get("timeout_seconds", 60)
        max_diff = value.get("max_diff_bytes", 1_000_000)
        if type(timeout) is not int or not 1 <= timeout <= 86_400:
            raise ValueError("timeout_seconds must be an integer from 1 through 86400")
        if type(max_diff) is not int or not 1 <= max_diff <= 50_000_000:
            raise ValueError("max_diff_bytes must be an integer from 1 through 50000000")
        return cls(task_id, description, tuple(command), timeout, max_diff)

    @classmethod
    def from_json(cls, raw: str) -> "TaskConfig":
        try:
            value = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(f"invalid task JSON: {exc}") from exc
        return cls.from_mapping(value)

    @classmethod
    def from_file(cls, path: str | Path) -> "TaskConfig":
        try:
            raw = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"could not read task configuration: {exc}") from exc
        return cls.from_json(raw)
