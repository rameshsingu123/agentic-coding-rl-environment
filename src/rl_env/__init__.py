"""Fail-closed primitives for inspecting and planning agentic coding tasks."""

from .config import TaskConfig
from .diff_intake import DiffSummary, validate_unified_diff
from .integrity import FileDigest, IntegrityReport, build_manifest, verify_manifest
from .runner import DockerPolicy, ExecutionPlan, GitWorktreeRunner

__all__ = [
    "DockerPolicy", "DiffSummary", "ExecutionPlan", "FileDigest", "GitWorktreeRunner",
    "IntegrityReport", "TaskConfig", "build_manifest", "validate_unified_diff", "verify_manifest",
]
