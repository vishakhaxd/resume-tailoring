from pathlib import Path

import pytest

from src.codex import CodexInstructionEngine
from src.models import UserRequest
from src.validation import DiffValidator, ValidationIssue


@pytest.fixture()
def codex(tmp_path: Path) -> CodexInstructionEngine:
    codex_path = tmp_path / "codex.json"
    codex_path.write_text(
        """
{
  "metadata": {"name": "test", "version": "1.0"},
  "guardrails": {
    "allowed_extensions": [".txt"],
    "forbid_deletions": false,
    "max_line_length": 120,
    "minimum_context_lines": 1,
    "banned_insertions": ["DROP TABLE"],
    "enforce_diff_prefix": true,
    "audit_log": "logs/audit.log",
    "history_dir": ".codex/history",
    "require_unified_diff": true,
    "allow_multiple_files": false
  }
}
"""
    )
    return CodexInstructionEngine(codex_path)


def test_validator_blocks_wrong_file(codex: CodexInstructionEngine, tmp_path: Path) -> None:
    file_path = tmp_path / "data.txt"
    file_path.write_text("hello\n")
    diff = """--- wrong.txt\n+++ wrong.txt\n@@ -1 +1 @@\n-hello\n+hi\n"""
    validator = DiffValidator(codex.config, file_path.read_text(), UserRequest(file_path=file_path, instruction="update"))
    with pytest.raises(ValidationIssue):
        validator.validate(diff)


def test_validator_blocks_banned_insertion(codex: CodexInstructionEngine, tmp_path: Path) -> None:
    file_path = tmp_path / "data.txt"
    file_path.write_text("safe content\n")
    diff = """--- data.txt\n+++ data.txt\n@@ -1 +1 @@\n-safe content\n+DROP TABLE users;\n"""
    validator = DiffValidator(codex.config, file_path.read_text(), UserRequest(file_path=file_path, instruction="bad"))
    with pytest.raises(ValidationIssue):
        validator.validate(diff)
