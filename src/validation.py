import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .models import CodexConfig, UserRequest


@dataclass
class ValidationIssue(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


class DiffValidator:
    def __init__(self, codex: CodexConfig, original_content: str, request: UserRequest) -> None:
        self.codex = codex
        self.original_content = original_content
        self.request = request

    def validate(self, diff: str) -> None:
        self._ensure_diff_not_empty(diff)
        self._ensure_unified_diff(diff)
        self._validate_target_file(diff)
        self._validate_guardrails(diff)
        self._validate_context(diff)

    def _ensure_diff_not_empty(self, diff: str) -> None:
        if not diff.strip():
            raise ValidationIssue("Empty diff returned by LLM")

    def _ensure_unified_diff(self, diff: str) -> None:
        if self.codex.require_unified_diff and "@@" not in diff:
            raise ValidationIssue("Diff is not in unified diff format")

    def _validate_target_file(self, diff: str) -> None:
        file_path = str(self.request.file_path)
        if self.codex.enforce_diff_prefix and not diff.lstrip().startswith("---"):
            raise ValidationIssue("Diff must start with file headers")
        headers = self._extract_headers(diff.splitlines())
        if len(headers) != 2:
            raise ValidationIssue("Diff must contain both original and new file headers")
        original_header, new_header = headers
        if file_path not in original_header or file_path not in new_header:
            raise ValidationIssue("Diff refers to unexpected file path")
        if not self.codex.allow_multiple_files:
            files_in_diff = self._find_all_files(diff.splitlines())
            if len(files_in_diff) != 1:
                raise ValidationIssue("Diff modifies multiple files, which is not allowed")
        if not any(file_path.endswith(ext) for ext in self.codex.allowed_extensions):
            raise ValidationIssue("File extension is not allowed by codex")

    def _validate_guardrails(self, diff: str) -> None:
        for banned in self.codex.banned_insertions:
            added_lines = self._extract_added_lines(diff.splitlines())
            if any(banned in line for line in added_lines):
                raise ValidationIssue(f"Diff attempts to insert banned content: {banned}")
        if self.codex.forbid_deletions:
            if any(line.startswith("-") and not line.startswith("---") for line in diff.splitlines()):
                raise ValidationIssue("Deletions are not allowed by codex")
        self._validate_line_lengths(diff.splitlines())

    def _validate_line_lengths(self, lines: Iterable[str]) -> None:
        if self.codex.max_line_length <= 0:
            return
        for line in lines:
            if line.startswith("+") and len(line) - 1 > self.codex.max_line_length:
                raise ValidationIssue("Inserted line exceeds maximum length")

    def _validate_context(self, diff: str) -> None:
        original_lines = self.original_content.splitlines()
        for hunk in self._extract_hunks(diff.splitlines()):
            for context_line in hunk.context:
                if self.codex.minimum_context_lines <= 0:
                    continue
                if context_line not in original_lines:
                    raise ValidationIssue("Context lines do not match original file, potential corruption")

    def _extract_headers(self, lines: List[str]) -> List[str]:
        headers = [line for line in lines if line.startswith("---") or line.startswith("+++")]
        return headers[:2]

    def _find_all_files(self, lines: List[str]) -> List[str]:
        files = []
        header_pattern = re.compile(r"^[+-]{3} (.+)$")
        for line in lines:
            match = header_pattern.match(line)
            if match:
                files.append(match.group(1))
        return list({*files})

    def _extract_added_lines(self, lines: List[str]) -> List[str]:
        added = []
        for line in lines:
            if line.startswith("+") and not line.startswith("+++" ):
                added.append(line[1:])
        return added

    def _extract_hunks(self, lines: List[str]):
        hunks = []
        current_context: List[str] = []
        for line in lines:
            if line.startswith("@@"):
                if current_context:
                    hunks.append(Hunk(context=current_context))
                    current_context = []
            elif line.startswith(" "):
                current_context.append(line[1:])
        if current_context:
            hunks.append(Hunk(context=current_context))
        return hunks


@dataclass
class Hunk:
    context: List[str]
