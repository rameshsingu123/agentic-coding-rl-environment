from pathlib import Path

import pytest

from rl_env.integrity import FileDigest, build_manifest, verify_manifest


def test_manifest_is_sorted_and_detects_changes(tmp_path: Path):
    (tmp_path / "b.txt").write_text("bravo", encoding="utf-8")
    (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
    expected = build_manifest(tmp_path)
    assert [item.path for item in expected] == ["a.txt", "b.txt"]
    assert verify_manifest(tmp_path, expected).valid
    (tmp_path / "a.txt").write_text("changed", encoding="utf-8")
    report = verify_manifest(tmp_path, expected)
    assert not report.valid
    assert report.changed == ("a.txt",)


def test_reports_missing_and_unexpected(tmp_path: Path):
    (tmp_path / "keep").write_bytes(b"x")
    expected = build_manifest(tmp_path)
    (tmp_path / "keep").unlink()
    (tmp_path / "new").write_bytes(b"y")
    report = verify_manifest(tmp_path, expected)
    assert report.missing == ("keep",)
    assert report.unexpected == ("new",)


def test_rejects_symlink(tmp_path: Path):
    target = tmp_path / "target"
    target.write_text("content", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="regular files"):
        build_manifest(tmp_path)


def test_rejects_unsafe_expected_path(tmp_path: Path):
    with pytest.raises(ValueError, match="unsafe"):
        verify_manifest(tmp_path, [FileDigest("../outside", "0" * 64, 0)])
