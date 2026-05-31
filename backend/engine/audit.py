from __future__ import annotations

from pathlib import Path
import json
from datetime import datetime, timezone
import os
import threading

_AUDIT_LOCKS_GUARD = threading.Lock()
_AUDIT_LOCKS: dict[str, threading.RLock] = {}


def _audit_lock(path: Path) -> threading.RLock:
    key = path.resolve().as_posix()
    with _AUDIT_LOCKS_GUARD:
        lock = _AUDIT_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _AUDIT_LOCKS[key] = lock
        return lock


def append_audit_log(log_path: Path, entry: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(entry)
    record["timestamp_utc"] = os.environ.get("RUNTIME_FIXED_TIMESTAMP_UTC") or datetime.now(timezone.utc).isoformat()
    with _audit_lock(log_path):
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
