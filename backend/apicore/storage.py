"""apicore/storage.py — I/O atomique JSON (T6.1).

Fonctions d'écriture/lecture JSON thread-safe.
Indépendant de SESSIONS_DIR — l'appelant fournit les Path.
Extrait de api.py (T6.1).
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path


# ── Verrous par chemin ────────────────────────────────────────────────────────

_STORAGE_LOCKS_GUARD = threading.Lock()
_STORAGE_LOCKS: dict[str, threading.RLock] = {}


def _lock_key(path: Path) -> str:
    try:
        return path.resolve().parts[0] if path.resolve().parts else path.resolve().as_posix()
    except Exception:
        return path.resolve().as_posix()


def _lock_for_path(path: Path) -> threading.RLock:
    key = _lock_key(path)
    with _STORAGE_LOCKS_GUARD:
        lock = _STORAGE_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _STORAGE_LOCKS[key] = lock
        return lock


# ── Écriture atomique ─────────────────────────────────────────────────────────

def atomic_write_text(path: Path, text: str) -> None:
    """Écrit text dans path de façon atomique (tmp + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    lock = _lock_for_path(path)
    with lock:
        try:
            with tmp_path.open("w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            last_error: PermissionError | None = None
            for _ in range(5):
                try:
                    os.replace(tmp_path, path)
                    last_error = None
                    break
                except PermissionError as exc:
                    last_error = exc
                    time.sleep(0.02)
            if last_error is not None:
                raise last_error
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass


def write_json(path: Path, payload: dict) -> None:
    """Sérialise payload en JSON et écrit atomiquement."""
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


# ── Lecture JSON ──────────────────────────────────────────────────────────────

def read_json_dict(path: Path) -> dict:
    if not path.exists() or not path.is_file():
        return {}
    lock = _lock_for_path(path)
    with lock:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return {}
    return payload if isinstance(payload, dict) else {}


def read_json_list(path: Path) -> list:
    if not path.exists():
        return []
    lock = _lock_for_path(path)
    with lock:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return []
    return payload if isinstance(payload, list) else []
