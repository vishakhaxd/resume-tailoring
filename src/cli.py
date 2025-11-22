import argparse
from pathlib import Path

from .llm import TransformationEngine
from .orchestrator import Orchestrator
from .models import UserRequest


class FileLLMClient:
    """Reads a prepared diff from disk to mimic an LLM response."""

    def __init__(self, diff_path: Path) -> None:
        self.diff_path = diff_path

    def generate(self, prompt: str) -> str:  # pragma: no cover - thin wrapper
        return self.diff_path.read_text()


def parse_args() -> argparse.Namespace:  # pragma: no cover - CLI plumbing
    parser = argparse.ArgumentParser(description="Run guarded file update with codex rules")
    parser.add_argument("file", type=Path, help="Path to the target text file")
    parser.add_argument("instruction", type=str, help="User instruction to the LLM")
    parser.add_argument(
        "--codex", type=Path, default=Path("codex/codex.json"), help="Path to codex configuration"
    )
    parser.add_argument(
        "--prompt-template", type=Path, default=Path("templates/llm_prompt.txt"), help="Prompt template path"
    )
    parser.add_argument(
        "--diff", type=Path, required=True, help="Path to pre-generated unified diff returned by an LLM"
    )
    return parser.parse_args()


def main() -> None:  # pragma: no cover - CLI plumbing
    args = parse_args()
    llm_client = FileLLMClient(args.diff)
    engine = TransformationEngine(llm_client)
    orchestrator = Orchestrator(args.codex, engine, args.prompt_template)
    request = UserRequest(file_path=args.file, instruction=args.instruction)
    result = orchestrator.process(request)
    print(result.applied_content)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
