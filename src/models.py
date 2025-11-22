from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class CodexConfig:
    name: str
    version: str
    allowed_extensions: List[str]
    forbid_deletions: bool
    max_line_length: int
    minimum_context_lines: int
    banned_insertions: List[str]
    enforce_diff_prefix: bool
    audit_log: Path
    history_dir: Path
    require_unified_diff: bool
    allow_multiple_files: bool


@dataclass
class UserRequest:
    file_path: Path
    instruction: str


@dataclass
class TransformationResult:
    diff: str
    applied_content: str
    backup_path: Optional[Path]
