from pathlib import Path
from typing import Optional

from .codex import CodexInstructionEngine
from .file_update import FileUpdateEngine, PatchApplyError
from .llm import TransformationEngine
from .logging_utils import append_audit_log
from .models import TransformationResult, UserRequest
from .prompt_builder import build_prompt
from .validation import DiffValidator, ValidationIssue


class Orchestrator:
    def __init__(
        self,
        codex_path: Path,
        llm_engine: TransformationEngine,
        prompt_template_path: Path,
    ) -> None:
        self.codex_engine = CodexInstructionEngine(codex_path)
        self.llm_engine = llm_engine
        self.prompt_template_path = prompt_template_path

    def process(self, request: UserRequest) -> TransformationResult:
        original_content = self._read_file(request.file_path)
        prompt = build_prompt(
            template_path=self.prompt_template_path,
            codex=self.codex_engine.config,
            request=request,
            file_content=original_content,
        )
        diff = self.llm_engine.generate_diff(prompt)

        validator = DiffValidator(self.codex_engine.config, original_content, request)
        validator.validate(diff)

        update_engine = FileUpdateEngine(self.codex_engine.config.history_dir)
        result = update_engine.apply_patch(request.file_path, original_content, diff)

        append_audit_log(
            self.codex_engine.config.audit_log,
            {
                "file": str(request.file_path),
                "request": request.instruction,
                "codex_version": self.codex_engine.config.version,
                "backup_path": str(result.backup_path) if result.backup_path else None,
            },
        )
        return result

    def _read_file(self, path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"Target file does not exist: {path}")
        return path.read_text()
