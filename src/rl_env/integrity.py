"""SHA-256 manifests for regular files beneath a workspace directory."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileDigest:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class IntegrityReport:
    valid: bool
    missing: tuple[str, ...]
    changed: tuple[str, ...]
    unexpected: tuple[str, ...]


def _root(path: str | Path) -> Path:
    root = Path(path).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("manifest root must be a directory")
    return root


def build_manifest(root: str | Path) -> tuple[FileDigest, ...]:
    """Hash all regular files recursively; fail closed on symlinks and special files."""
    base = _root(root)
    result: list[FileDigest] = []
    for current, dirs, files in os.walk(base, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in dirs:
            entry = current_path / name
            if entry.is_symlink():
                raise ValueError(f"symlink directory is not permitted: {entry.relative_to(base)}")
        for name in files:
            entry = current_path / name
            if entry.is_symlink() or not entry.is_file():
                raise ValueError(f"only regular files are permitted: {entry.relative_to(base)}")
            digest = hashlib.sha256()
            size = 0
            with entry.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
                    size += len(chunk)
            relative = entry.relative_to(base).as_posix()
            result.append(FileDigest(relative, digest.hexdigest(), size))
    return tuple(sorted(result, key=lambda item: item.path))


def verify_manifest(root: str | Path, expected: tuple[FileDigest, ...] | list[FileDigest]) -> IntegrityReport:
    """Compare the current tree with a prior manifest without modifying either."""
    expected_by_path: dict[str, FileDigest] = {}
    for item in expected:
        if not isinstance(item, FileDigest):
            raise ValueError("expected manifest must contain unique FileDigest entries")
        if not isinstance(item.path, str) or item.path in expected_by_path:
            raise ValueError("expected manifest must contain unique FileDigest entries")
        parts = item.path.split("/")
        if (not item.path or item.path.startswith("/") or "\\" in item.path
                or any(part in {"", ".", ".."} for part in parts)):
            raise ValueError("manifest contains an unsafe relative path")
        if (not isinstance(item.sha256, str) or len(item.sha256) != 64
                or any(ch not in "0123456789abcdef" for ch in item.sha256)):
            raise ValueError("manifest contains an invalid SHA-256 digest")
        if type(item.size_bytes) is not int or item.size_bytes < 0:
            raise ValueError("manifest contains an invalid file size")
        expected_by_path[item.path] = item
    actual = {item.path: item for item in build_manifest(root)}
    missing = tuple(sorted(expected_by_path.keys() - actual.keys()))
    unexpected = tuple(sorted(actual.keys() - expected_by_path.keys()))
    changed = tuple(sorted(path for path in expected_by_path.keys() & actual.keys()
                           if expected_by_path[path].sha256 != actual[path].sha256
                           or expected_by_path[path].size_bytes != actual[path].size_bytes))
    return IntegrityReport(not (missing or unexpected or changed), missing, changed, unexpected)
