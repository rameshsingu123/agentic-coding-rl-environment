from pathlib import Path

import pytest

from rl_env.diff_intake import validate_unified_diff

ROOT = Path(__file__).resolve().parents[1]


def test_sample_patch_validates_without_application():
    text = (ROOT / "examples/patch_sample.diff").read_text(encoding="utf-8")
    result = validate_unified_diff(text)
    assert result.files == ("hello.py",)
    assert result.added_lines == 2
    assert result.removed_lines == 1
    assert result.hunk_count == 1
    assert len(result.sha256) == 64


@pytest.mark.parametrize("patch", [
    "--- a/../secret\n+++ b/../secret\n@@ -1 +1 @@\n-old\n+new\n",
    "--- /tmp/secret\n+++ b/secret\n@@ -1 +1 @@\n-old\n+new\n",
    "--- a/file\n+++ b/file\n@@ -1,2 +1 @@\n-old\n+new\n",
    "--- a/file\n+++ b/file\n@@ -1 +1 @@\n old\n+new\n",
    "--- a/file\n+++ b/file\n",
])
def test_malformed_or_unsafe_diff_rejected(patch):
    with pytest.raises(ValueError):
        validate_unified_diff(patch)


def test_size_limit_and_type_are_checked():
    with pytest.raises(ValueError, match="byte limit"):
        validate_unified_diff("--- a/a\n+++ b/a\n@@ -0,0 +1 @@\n+x\n", max_bytes=2)
    with pytest.raises(ValueError, match="text"):
        validate_unified_diff(b"not text")
