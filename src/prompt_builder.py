from pathlib import Path

from .models import CodexConfig, UserRequest


def build_prompt(template_path: Path, codex: CodexConfig, request: UserRequest, file_content: str) -> str:
    template = template_path.read_text()
    return template.format(
        codex_name=codex.name,
        codex_version=codex.version,
        allowed_extensions=", ".join(codex.allowed_extensions),
        deletions_allowed=not codex.forbid_deletions,
        max_line_length=codex.max_line_length,
        minimum_context=codex.minimum_context_lines,
        banned_insertions=", ".join(codex.banned_insertions) or "(none)",
        enforce_diff_prefix=codex.enforce_diff_prefix,
        require_unified_diff=codex.require_unified_diff,
        allow_multiple_files=codex.allow_multiple_files,
        user_request=request.instruction,
        file_path=str(request.file_path),
        file_content=file_content,
    )
