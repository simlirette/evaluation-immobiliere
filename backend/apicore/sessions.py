"""apicore/sessions.py — Session I/O et management (T6.1).

Fonctions de gestion des sessions runtime.
Utilise get_sessions_dir() pour SESSIONS_DIR (patchable en tests via os.environ).
Extrait de api.py (T6.1).
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from apicore.storage import read_json_dict, write_json
from engine.runtime import safe_path_id  # type: ignore[import-not-found]


# ── SESSIONS_DIR lazy (patchable via os.environ["SESSIONS_DIR"]) ──────────────

def get_sessions_dir() -> Path:
    """Retourne le répertoire des sessions. Lisible depuis os.environ pour les tests."""
    env_val = os.environ.get("SESSIONS_DIR", "")
    if env_val:
        return Path(env_val)
    return Path(__file__).resolve().parent.parent / "runtime_sessions"


# ── Utilitaires temps ─────────────────────────────────────────────────────────

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# ── Session I/O ───────────────────────────────────────────────────────────────

def create_session(
    strict_mode: bool = True,
    owner_evaluator_id: str = "",
    sessions_dir: Path | None = None,
) -> dict:
    """Crée une nouvelle session runtime et initialise session.json."""
    sd = sessions_dir or get_sessions_dir()
    session_id = uuid.uuid4().hex[:12]
    run_id = f"run_{utc_now_compact()}_{session_id}"
    session_dir = sd / session_id
    session_dir.mkdir(parents=True, exist_ok=False)
    session = {
        "schema_version": "runtime_session_v1",
        "session_id": session_id,
        "run_id": run_id,
        "strict_mode": strict_mode,
        "status": "CREATED",
        "created_at_utc": utc_now_iso(),
        "updated_at_utc": utc_now_iso(),
        "session_dir": str(session_dir),
        "events_url": f"/stream?session_id={session_id}",
        "status_url": f"/status?session_id={session_id}",
        "artifacts_url": f"/artifacts?session_id={session_id}",
    }
    owner_evaluator_id = str(owner_evaluator_id or "").strip()
    if owner_evaluator_id:
        session["owner_evaluator_id"] = owner_evaluator_id
    session["usage"] = {
        "llm_calls": 0,
        "llm_tokens_in": 0,
        "llm_tokens_out": 0,
        "llm_cost_usd": 0.0,
        "pipeline_runs": 0,
        "bureau_id": "",
    }
    write_json(session_dir / "session.json", session)
    return session


def load_session(
    session_id: str,
    sessions_dir: Path | None = None,
) -> dict | None:
    """Charge une session depuis session.json."""
    sd = sessions_dir or get_sessions_dir()
    session_path = sd / safe_path_id(session_id) / "session.json"
    if session_path.exists():
        session = read_json_dict(session_path)
        return session or None
    if "-" in session_id:
        real = find_session_for_dossier(session_id, sd)
        if real:
            session_path = sd / real / "session.json"
            if session_path.exists():
                session = read_json_dict(session_path)
                return session or None
    return None


def save_session(session: dict) -> None:
    """Sauvegarde session (met à jour updated_at_utc)."""
    session["updated_at_utc"] = utc_now_iso()
    write_json(Path(session["session_dir"]) / "session.json", session)


def require_session(
    session_id: str,
    sessions_dir: Path | None = None,
) -> dict:
    """Charge une session ou lève ValueError si introuvable."""
    session = load_session(session_id, sessions_dir)
    if not session:
        raise ValueError(f"Session introuvable: {session_id!r}")
    return session


def find_session_for_dossier(
    dossier_id: str,
    sessions_dir: Path | None = None,
) -> str | None:
    """Retourne le session_id le plus récent pour un dossier_id."""
    sd = sessions_dir or get_sessions_dir()
    if not sd.exists():
        return None
    candidates: list[tuple[str, str]] = []
    for path in sd.glob("*/session.json"):
        try:
            data = read_json_dict(path)
            if not data:
                continue
            if str(data.get("dossier_id") or "") != dossier_id:
                continue
            if data.get("app_archived") or data.get("archived"):
                continue
            updated = str(data.get("updated_at_utc") or data.get("created_at_utc") or "")
            session_hex = str(data.get("session_id") or "")
            if session_hex and safe_path_id(session_hex) == path.parent.name:
                candidates.append((updated, session_hex))
        except Exception:
            pass
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def normalize_session_id(
    raw_id: str,
    sessions_dir: Path | None = None,
) -> str:
    """Résout un raw_id dossier_id (D-...) → session_id (hex12)."""
    if raw_id and "-" in raw_id:
        resolved = find_session_for_dossier(raw_id, sessions_dir)
        if resolved:
            return resolved
    return raw_id


def session_owner_id(session: dict) -> str:
    return str(
        session.get("owner_evaluator_id")
        or session.get("created_by")
        or session.get("evaluator_id")
        or ""
    ).strip()


def session_access_allowed(
    session: dict,
    evaluator_id: str,
    bureau_id: str = "",
) -> bool:
    """Vérifie l'accès bureau-aware (T5.2)."""
    evaluator_id = str(evaluator_id or "").strip()
    if not evaluator_id:
        return False
    owner = session_owner_id(session)
    if owner and owner == evaluator_id:
        return True
    session_bureau = str(session.get("bureau_id", "") or "").strip()
    if bureau_id and session_bureau and session_bureau == bureau_id:
        return True
    if not owner:
        return os.environ.get("EVAL_RUNTIME_ALLOW_LEGACY_UNOWNED_SESSIONS", "") == "1"
    return False


def track_llm_usage(
    session_id: str,
    tokens_in: int,
    tokens_out: int,
    cost_usd: float,
    sessions_dir: Path | None = None,
) -> None:
    """Incrémente le compteur usage LLM. Silencieux si session manquante."""
    try:
        session = load_session(session_id, sessions_dir)
        if not session:
            return
        usage = session.get("usage") or {}
        usage["llm_calls"] = int(usage.get("llm_calls", 0)) + 1
        usage["llm_tokens_in"] = int(usage.get("llm_tokens_in", 0)) + int(tokens_in)
        usage["llm_tokens_out"] = int(usage.get("llm_tokens_out", 0)) + int(tokens_out)
        usage["llm_cost_usd"] = round(float(usage.get("llm_cost_usd", 0.0)) + float(cost_usd), 6)
        session["usage"] = usage
        save_session(session)
    except Exception:
        pass
