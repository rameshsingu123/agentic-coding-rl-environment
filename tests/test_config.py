import json
from pathlib import Path

import pytest

from rl_env.config import TaskConfig

ROOT = Path(__file__).resolve().parents[1]


def test_sample_config_loads_and_is_typed():
    task = TaskConfig.from_file(ROOT / "examples/task_sample.json")
    assert task.task_id == "sample-001"
    assert task.command == ("python", "-m", "pytest", "-q")
    assert task.timeout_seconds == 120
    assert task.max_diff_bytes == 1_000_000


def test_defaults_are_applied():
    task = TaskConfig.from_mapping({"task_id": "x", "description": "desc", "command": ["true"]})
    assert task.timeout_seconds == 60
    assert task.max_diff_bytes == 1_000_000


@pytest.mark.parametrize("value", [
    {"description": "x", "command": ["echo"]},
    {"task_id": "x", "description": "x", "command": ["echo"], "other": 1},
    {"task_id": "x", "description": "x", "command": "echo"},
    {"task_id": "x", "description": "x", "command": ["echo", "\x00bad"]},
    {"task_id": "x", "description": "x", "command": ["echo"], "timeout_seconds": True},
    {"task_id": "x", "description": "x", "command": ["echo"], "timeout_seconds": 0},
])
def test_invalid_config_fails_closed(value):
    with pytest.raises(ValueError):
        TaskConfig.from_mapping(value)


def test_json_root_must_be_object():
    with pytest.raises(ValueError):
        TaskConfig.from_json(json.dumps([1, 2]))
