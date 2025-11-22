# Resume Tailoring Codex

A production-ready framework for controlled text file modification using LLM-generated diffs under permanent guardrails.

## Folder architecture

- `codex/` – immutable guardrail configuration (`codex.json`).
- `.codex/history/` – automatic file backups per change.
- `logs/` – JSON lines audit log for every applied update.
- `src/` – core modules (codex loader, orchestrator, validation, LLM adapter, patch applier, CLI).
- `templates/` – prompt template used to instruct the LLM.
- `tests/` – pytest suite covering validation and patch application.

## Usage

1. Prepare your target file (must use an allowed extension from `codex/codex.json`).
2. Send the prompt built from `templates/llm_prompt.txt` to your LLM of choice.
3. Save the unified diff response to disk.
4. Run the orchestrator via CLI:

```bash
python -m src.cli path/to/file.txt "Describe the change" --diff /tmp/llm.diff
```

The system will:
- Load codex guardrails
- Validate the diff (format, file scope, banned content, context safety)
- Apply the patch with backups
- Log the change in `logs/audit.log`

## Extending

- Swap `FileLLMClient` with a real `LLMClient` implementation in `src/llm.py`.
- Adjust guardrails inside `codex/codex.json`; history and audit destinations are configurable.
- Use `FileUpdateEngine` and `DiffValidator` directly for embedding in other services.

## Testing

Install dev dependencies and run pytest:

```bash
pip install -e .[dev]
pytest
```
