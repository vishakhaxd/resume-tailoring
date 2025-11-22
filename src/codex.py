import json
from pathlib import Path
from typing import Any, Dict

from .models import CodexConfig


class CodexInstructionEngine:
    """Loads immutable codex rules from codex.json."""

    def __init__(self, codex_path: Path) -> None:
        if codex_path.suffix not in {".json"}:
            raise ValueError("Codex must be a JSON file")
        self.codex_path = codex_path
        self._config = self._load()

    @property
    def config(self) -> CodexConfig:
        return self._config

    def _load(self) -> CodexConfig:
        data = self._read_file()
        metadata = data.get("metadata", {})
        guardrails = data.get("guardrails", {})
        audit_log = Path(guardrails.get("audit_log", "logs/audit.log"))
        history_dir = Path(guardrails.get("history_dir", ".codex/history"))
        history_dir.mkdir(parents=True, exist_ok=True)
        audit_log.parent.mkdir(parents=True, exist_ok=True)

        return CodexConfig(
            name=metadata.get("name", "codex"),
            version=str(metadata.get("version", "1.0.0")),
            allowed_extensions=list(guardrails.get("allowed_extensions", [])),
            forbid_deletions=bool(guardrails.get("forbid_deletions", False)),
            max_line_length=int(guardrails.get("max_line_length", 0)),
            minimum_context_lines=int(guardrails.get("minimum_context_lines", 2)),
            banned_insertions=list(guardrails.get("banned_insertions", [])),
            enforce_diff_prefix=bool(guardrails.get("enforce_diff_prefix", True)),
            audit_log=audit_log,
            history_dir=history_dir,
            require_unified_diff=bool(guardrails.get("require_unified_diff", True)),
            allow_multiple_files=bool(guardrails.get("allow_multiple_files", False)),
        )

    def _read_file(self) -> Dict[str, Any]:
        content = self.codex_path.read_text()
        return json.loads(content)
