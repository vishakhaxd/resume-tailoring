import datetime
from pathlib import Path
from typing import List

from .models import TransformationResult
from .validation import ValidationIssue


class PatchApplyError(Exception):
    pass


class FileUpdateEngine:
    def __init__(self, history_dir: Path) -> None:
        self.history_dir = history_dir
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def apply_patch(self, file_path: Path, original_content: str, diff: str) -> TransformationResult:
        backup_path = self._create_backup(file_path, original_content)
        new_content = self._apply_unified_diff(original_content, diff)
        file_path.write_text(new_content)
        return TransformationResult(diff=diff, applied_content=new_content, backup_path=backup_path)

    def _create_backup(self, file_path: Path, content: str) -> Path:
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        backup_path = self.history_dir / f"{file_path.name}.{timestamp}.bak"
        backup_path.write_text(content)
        return backup_path

    def _apply_unified_diff(self, original_content: str, diff: str) -> str:
        original_lines = original_content.splitlines()
        diff_lines = diff.splitlines()
        hunks = self._parse_hunks(diff_lines)
        new_lines: List[str] = []
        cursor = 0
        for hunk in hunks:
            new_lines.extend(original_lines[cursor : hunk.orig_start])
            cursor = hunk.orig_start
            for line in hunk.lines:
                if line.startswith(" "):
                    new_lines.append(line[1:])
                    cursor += 1
                elif line.startswith("-"):
                    if cursor >= len(original_lines) or original_lines[cursor] != line[1:]:
                        raise PatchApplyError("Hunk deletion does not match original content")
                    cursor += 1
                elif line.startswith("+"):
                    new_lines.append(line[1:])
            if cursor > len(original_lines):
                raise PatchApplyError("Patch cursor exceeded original content length")
        new_lines.extend(original_lines[cursor:])
        return "\n".join(new_lines) + ("\n" if original_content.endswith("\n") else "")

    def _parse_hunks(self, diff_lines: List[str]):
        hunks = []
        current_lines: List[str] = []
        orig_start = 0
        for line in diff_lines:
            if line.startswith("@@"):
                if current_lines:
                    hunks.append(Hunk(orig_start=orig_start, lines=current_lines))
                current_lines = []
                orig_start = self._parse_hunk_header(line)
            elif line.startswith("---") or line.startswith("+++") or line.startswith("diff --git"):
                continue
            else:
                current_lines.append(line)
        if current_lines:
            hunks.append(Hunk(orig_start=orig_start, lines=current_lines))
        if not hunks:
            raise ValidationIssue("No hunks found in diff")
        return hunks

    def _parse_hunk_header(self, header: str) -> int:
        # Example header: @@ -1,3 +1,5 @@
        try:
            minus_part, plus_part = header.split("@@")[1].strip().split(" ")[:2]
            orig_start = minus_part.split(",")[0].replace("-", "")
            return max(int(orig_start) - 1, 0)
        except Exception as exc:  # pragma: no cover - defensive
            raise PatchApplyError(f"Invalid hunk header: {header}") from exc


class Hunk:
    def __init__(self, orig_start: int, lines: List[str]):
        self.orig_start = orig_start
        self.lines = lines
