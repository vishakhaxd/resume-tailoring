import json
from pathlib import Path

from src.llm import TransformationEngine
from src.models import UserRequest
from src.orchestrator import Orchestrator


class StubLLM:
    def __init__(self, diff: str) -> None:
        self.diff = diff

    def generate(self, prompt: str) -> str:
        assert "Respond ONLY with a unified diff" in prompt
        return self.diff


def test_orchestrator_applies_valid_diff(tmp_path: Path) -> None:
    target = tmp_path / "document.txt"
    target.write_text("line one\n")

    codex_path = tmp_path / "codex.json"
    codex_path.write_text(
        json.dumps(
            {
                "metadata": {"name": "orchestrator", "version": "1.0"},
                "guardrails": {
                    "allowed_extensions": [".txt"],
                    "forbid_deletions": False,
                    "max_line_length": 120,
                    "minimum_context_lines": 1,
                    "banned_insertions": [],
                    "enforce_diff_prefix": True,
                    "audit_log": str(tmp_path / "log.jsonl"),
                    "history_dir": str(tmp_path / "history"),
                    "require_unified_diff": True,
                    "allow_multiple_files": False,
                },
            }
        )
    )

    diff = """--- {path}\n+++ {path}\n@@ -1 +1,2 @@\n-line one\n+line one\n+added\n""".format(path=str(target))

    template = tmp_path / "prompt.txt"
    template.write_text(open("templates/llm_prompt.txt", "r", encoding="utf-8").read())

    orchestrator = Orchestrator(
        codex_path=codex_path,
        llm_engine=TransformationEngine(StubLLM(diff)),
        prompt_template_path=template,
    )

    request = UserRequest(file_path=target, instruction="Add a second line")
    result = orchestrator.process(request)

    assert "added" in result.applied_content
    assert (tmp_path / "history").exists()
    assert (tmp_path / "log.jsonl").exists()
