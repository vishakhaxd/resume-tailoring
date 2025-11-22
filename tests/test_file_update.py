from pathlib import Path

import pytest

from src.file_update import FileUpdateEngine, PatchApplyError


def test_apply_patch_creates_backup(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("hello\n")
    diff = """--- note.txt\n+++ note.txt\n@@ -1 +1,2 @@\n-hello\n+hello\n+world\n"""
    engine = FileUpdateEngine(tmp_path / "history")
    result = engine.apply_patch(target, target.read_text(), diff)
    assert result.backup_path and result.backup_path.exists()
    assert target.read_text() == "hello\nworld\n"


def test_apply_patch_rejects_bad_hunk(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("hello\n")
    diff = """--- note.txt\n+++ note.txt\n@@ -1 +1 @@\n-wrong\n+hi\n"""
    engine = FileUpdateEngine(tmp_path / "history")
    with pytest.raises(PatchApplyError):
        engine.apply_patch(target, target.read_text(), diff)
