from pathlib import Path

import pytest

from rl_env.config import TaskConfig
from rl_env.runner import DockerPolicy, GitWorktreeRunner


def test_plan_is_deterministic_argv_for_worktree(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    task = TaskConfig.from_mapping({
        "task_id": "plan-test", "description": "inspect only", "command": ["python", "-m", "pytest"],
    })
    runner = GitWorktreeRunner()
    first = runner.plan(tmp_path, task)
    second = runner.plan(tmp_path, task)
    assert first == second
    assert first.argv[0:3] == ("docker", "run", "--rm")
    assert "--network=none" in first.argv
    assert f"--mount=type=bind,src={tmp_path.resolve()},dst=/workspace,readonly" in first.argv
    assert first.argv[-3:] == ("python", "-m", "pytest")
    assert first.timeout_seconds == 60


def test_invalid_policy_and_non_worktree_fail_closed(tmp_path: Path):
    with pytest.raises(ValueError):
        DockerPolicy(memory_mb=0)
    task = TaskConfig.from_mapping({"task_id": "x", "description": "d", "command": ["echo"]})
    with pytest.raises(ValueError, match="Git worktree"):
        GitWorktreeRunner().plan(tmp_path, task)
