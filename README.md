# Agentic Coding RL Environment

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: pytest](https://img.shields.io/badge/tests-pytest-0A9EDC.svg)](https://docs.pytest.org/)

Small, auditable Python primitives for coding-agent experiments: strict task configuration, bounded unified-diff intake, SHA-256 workspace manifests, and deterministic Docker command planning for a prepared Git worktree. Package runtime uses only the Python standard library; pytest is a development dependency.

**Independent portfolio project, public on GitHub. Not deployed enterprise or customer system.**

## Installation

Requires Python 3.10 or newer. From the repository root:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
```

For an isolated reproducibility check, use a clean virtual environment and install the same checked-out revision. The runtime dependency set is empty; `pytest` is only used by the development test suite. The Dockerfile builds a minimal image that imports the package; it does not run a task.

## Quick usage

The checked-in examples are validated by the same implementation as applications:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from rl_env import TaskConfig, validate_unified_diff, build_manifest, verify_manifest

task = TaskConfig.from_file("examples/task_sample.json")
patch = Path("examples/patch_sample.diff").read_text(encoding="utf-8")
summary = validate_unified_diff(patch, max_bytes=task.max_diff_bytes)
with TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "sample.txt").write_text("manifest sample\n", encoding="utf-8")
    manifest = build_manifest(root)
    assert verify_manifest(root, manifest).valid
print(task.task_id, summary.files, summary.sha256)
```

To construct—but not run—a Docker plan for an existing Git worktree:

```python
from rl_env import GitWorktreeRunner, TaskConfig

task = TaskConfig.from_file("examples/task_sample.json")
plan = GitWorktreeRunner().plan("/absolute/path/to/prepared-worktree", task)
print(plan.argv)             # argv tuple; no shell string
print(plan.timeout_seconds)  # consumer must enforce this timeout
```

### Boundaries that fail closed

- Task configuration rejects missing/unknown keys, malformed commands, NULs, and out-of-range limits. Commands are argument vectors, never shell command strings.
- Diff intake bounds encoded bytes, validates paths and hunk framing/counts, and returns only metadata. It never applies, stages, or writes a patch.
- Manifest creation rejects symlinks and non-regular files; verification reports missing, changed, and unexpected files.
- Runner planning requires an existing Git worktree and emits a fixed-ordered argv tuple with network disabled, a read-only root filesystem, a read-only worktree mount, dropped capabilities, no-new-privileges, resource limits, and a non-root user. Invalid settings and ambiguous mount paths are rejected.
- **There is intentionally no subprocess execution API.** This repository does not execute untrusted code.

## Threat-model summary

Inputs (task JSON, diff text, and worktree contents) may be attacker-controlled. Validation aims to reject malformed or ambiguous inputs before a downstream consumer considers them. See [the threat model](docs/threat-model.md) for trust boundaries and risks, and [limitations](docs/limitations.md) for what this prototype does not provide.

Docker flags in a generated plan are defense-in-depth requests, not proof of isolation. **Docker isolation has not been independently verified.** A consumer must review the host, daemon, image provenance, kernel, runtime configuration, and policy before any separate decision to execute a plan.

## Project layout

```text
src/rl_env/       typed config, diff intake, integrity, runner plan
examples/         sample task JSON and unified diff
tests/            pytest validation tests
docs/             threat model and limitations
```

Author: [Ramesh Singu](https://github.com/rameshsingu123).
