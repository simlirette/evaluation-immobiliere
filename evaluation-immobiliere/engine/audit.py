from __future__ import annotations

from pathlib import Path
import json
from datetime import datetime, timezone


def append_audit_log(log_path: Path, entry: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(entry)
    record["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
