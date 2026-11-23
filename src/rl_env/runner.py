"""Safe deterministic Docker command construction; this module never executes it."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import TaskConfig

_IMAGE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:@-]{0,254}$")


@dataclass(frozen=True, slots=True)
class DockerPolicy:
    """Conservative requested container settings (not a claim of verified isolation)."""

    image: str = "python:3.12-slim"
    memory_mb: int = 1024
    cpus: str = "1.0"
    pids_limit: int = 128
    tmpfs_mb: int = 64

    def __post_init__(self) -> None:
        if not isinstance(self.image, str) or not _IMAGE.fullmatch(self.image):
            raise ValueError("image must be a simple Docker image reference")
        for name, value, low, high in (
            ("memory_mb", self.memory_mb, 64, 65_536),
            ("pids_limit", self.pids_limit, 1, 4096),
            ("tmpfs_mb", self.tmpfs_mb, 1, 4096),
        ):
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{name} must be an integer from {low} through {high}")
        if not isinstance(self.cpus, str) or not re.fullmatch(r"(?:[1-9]\d{0,2})(?:\.\d{1,2})?", self.cpus):
            raise ValueError("cpus must be a positive decimal string")
        if float(self.cpus) > 64:
            raise ValueError("cpus must not exceed 64")


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """Immutable argv/cwd/timeout description. It is not an execution result."""

    argv: tuple[str, ...]
    cwd: str
    timeout_seconds: int


class GitWorktreeRunner:
    """Create an execution plan for a pre-existing Git worktree, without running it."""

    def __init__(self, policy: DockerPolicy | None = None, docker_binary: str = "docker") -> None:
        if not isinstance(docker_binary, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", docker_binary):
            raise ValueError("docker_binary must be a simple executable path")
        self.policy = policy or DockerPolicy()
        self.docker_binary = docker_binary

    def plan(self, worktree: str | Path, task: TaskConfig) -> ExecutionPlan:
        if not isinstance(task, TaskConfig):
            raise ValueError("task must be a validated TaskConfig")
        root = Path(worktree).resolve(strict=True)
        if not root.is_dir() or not (root / ".git").exists():
            raise ValueError("worktree must be an existing Git worktree directory")
        if (root / ".git").is_symlink():
            raise ValueError("worktree .git entry must not be a symlink")
        source = str(root)
        # Docker --mount parses comma-separated options; reject ambiguous source paths.
        if any(char in source for char in ",\n\r\x00"):
            raise ValueError("worktree path contains characters unsafe for Docker mount syntax")

        policy = self.policy
        argv = (
            self.docker_binary, "run", "--rm",
            "--network=none", "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges:true",
            "--user=65534:65534",
            f"--pids-limit={policy.pids_limit}",
            f"--memory={policy.memory_mb}m",
            f"--cpus={policy.cpus}",
            f"--tmpfs=/tmp:rw,noexec,nosuid,nodev,size={policy.tmpfs_mb}m",
            f"--mount=type=bind,src={source},dst=/workspace,readonly",
            "--workdir=/workspace", policy.image, *task.command,
        )
        return ExecutionPlan(argv=argv, cwd=str(root), timeout_seconds=task.timeout_seconds)
