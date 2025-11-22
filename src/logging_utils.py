import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def append_audit_log(log_path: Path, event: Dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": datetime.utcnow().isoformat() + "Z", **event}
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload))
        handle.write("\n")
