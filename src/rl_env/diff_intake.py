"""Bounded structural intake for untrusted unified diffs; never applies a patch."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?$")


@dataclass(frozen=True, slots=True)
class DiffSummary:
    sha256: str
    byte_count: int
    files: tuple[str, ...]
    added_lines: int
    removed_lines: int
    hunk_count: int


def _safe_path(header: str, side: str) -> str | None:
    # Git's conventional a/ and b/ prefixes are mandatory except /dev/null.
    path = header.split("\t", 1)[0]
    if path == "/dev/null":
        return None
    expected = f"{side}/"
    if not path.startswith(expected):
        raise ValueError(f"diff path must use {expected!r} prefix")
    relative = path[len(expected):]
    pieces = relative.split("/")
    if (not relative or relative.startswith("/") or "\\" in relative or "\x00" in relative
            or any(part in {"", ".", ".."} for part in pieces)):
        raise ValueError("diff contains an unsafe or non-canonical path")
    if len(relative) > 4096:
        raise ValueError("diff path is too long")
    return relative


def validate_unified_diff(diff: str, *, max_bytes: int = 1_000_000) -> DiffSummary:
    """Validate unified-diff framing and hunk counts, returning metadata only.

    This function deliberately does not invoke `patch`, git apply, or write any files.
    """
    if not isinstance(diff, str):
        raise ValueError("diff must be text")
    try:
        encoded = diff.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError("diff is not valid UTF-8 text") from exc
    if type(max_bytes) is not int or max_bytes < 1 or len(encoded) > max_bytes:
        raise ValueError("diff exceeds configured byte limit")
    if "\x00" in diff:
        raise ValueError("diff contains NUL bytes")
    lines = diff.splitlines()
    if not lines:
        raise ValueError("diff is empty")

    files: list[str] = []
    added = removed = hunks = 0
    index = 0
    while index < len(lines):
        if not lines[index].startswith("--- "):
            raise ValueError(f"expected unified-diff file header at line {index + 1}")
        old_path = _safe_path(lines[index][4:], "a")
        index += 1
        if index >= len(lines) or not lines[index].startswith("+++ "):
            raise ValueError("unified-diff file header must contain both --- and +++ lines")
        new_path = _safe_path(lines[index][4:], "b")
        index += 1
        if old_path is None and new_path is None:
            raise ValueError("a diff section cannot have /dev/null on both sides")
        files.append(new_path if new_path is not None else old_path)  # type: ignore[arg-type]
        if len(files) > 1024:
            raise ValueError("diff contains too many file sections")

        section_hunks = 0
        while index < len(lines) and not lines[index].startswith("--- "):
            match = _HUNK.fullmatch(lines[index])
            if match is None:
                raise ValueError(f"expected hunk header at line {index + 1}")
            old_count = int(match.group(2) or "1")
            new_count = int(match.group(4) or "1")
            index += 1
            seen_old = seen_new = 0
            while index < len(lines) and (seen_old < old_count or seen_new < new_count):
                line = lines[index]
                if line.startswith("\\ No newline at end of file"):
                    index += 1
                    continue
                if not line:
                    raise ValueError(f"invalid empty hunk line at line {index + 1}")
                prefix = line[0]
                if prefix == " ":
                    seen_old += 1
                    seen_new += 1
                elif prefix == "-":
                    seen_old += 1
                    removed += 1
                elif prefix == "+":
                    seen_new += 1
                    added += 1
                else:
                    raise ValueError(f"invalid hunk line prefix at line {index + 1}")
                if seen_old > old_count or seen_new > new_count:
                    raise ValueError(f"hunk line counts exceed header at line {index + 1}")
                index += 1
            if (seen_old, seen_new) != (old_count, new_count):
                raise ValueError("hunk body line counts do not match its header")
            hunks += 1
            section_hunks += 1
            if hunks > 10_000:
                raise ValueError("diff contains too many hunks")
        if section_hunks == 0:
            raise ValueError("each file section must contain at least one hunk")
    if not files:
        raise ValueError("diff contains no file sections")
    return DiffSummary(hashlib.sha256(encoded).hexdigest(), len(encoded), tuple(files), added, removed, hunks)
