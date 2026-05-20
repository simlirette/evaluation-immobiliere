"""engine/checkpoints.py — Pipeline checkpoint gates (S3).

Dossier = entité métier.  Session = run technique.
Les checkpoints bloquent la progression entre segments du pipeline :
  CP1 faits_bien_sujet  → après steps 1-2  (mandat-intake, data-facts)
  CP2 comparables       → après steps 3-4  (amu-analyst, comps-market)
  CP3 reconciliation    → après steps 5-6  (valuation-draft, compliance-qa)
  CP4 rapport_final     → après step 7     (redaction)

checkpoint_log.jsonl — jamais exporté dans le rapport, par dossier/session.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

# ── Constantes ────────────────────────────────────────────────────────────────

CHECKPOINT_LABELS: dict[int, str] = {
    1: "faits_bien_sujet",
    2: "comparables",
    3: "reconciliation",
    4: "rapport_final",
}

# Noms des steps RuntimeEngine à exécuter pour chaque segment
CHECKPOINT_STEPS: dict[int, list[str]] = {
    1: ["mandat-intake", "data-facts"],
    2: ["amu-analyst", "comps-market"],
    3: ["valuation-draft", "compliance-qa"],
    4: ["redaction"],
}

CHECKPOINT_LOG_FILENAME = "checkpoint_log.jsonl"


# ── Exceptions ────────────────────────────────────────────────────────────────

class CheckpointRequiredError(ValueError):
    """Gate bloquant : le checkpoint précédent doit être confirmé.

    Converti en HTTP 409 CHECKPOINT_REQUIRED par le handler api.py.
    """

    def __init__(self, required_checkpoint: int) -> None:
        self.required_checkpoint = required_checkpoint
        super().__init__(
            f"CHECKPOINT {required_checkpoint} ({CHECKPOINT_LABELS.get(required_checkpoint, '?')}) "
            f"doit être confirmé avant de continuer."
        )


# ── Fonctions bas-niveau ──────────────────────────────────────────────────────

def checkpoint_log_path(session_dir: Path) -> Path:
    return session_dir / CHECKPOINT_LOG_FILENAME


def read_checkpoint_log(session_dir: Path) -> list[dict]:
    """Lire toutes les entrées du checkpoint_log.jsonl d'une session."""
    path = checkpoint_log_path(session_dir)
    if not path.exists():
        return []
    entries: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def is_checkpoint_confirmed(session_dir: Path, checkpoint: int) -> bool:
    """Vrai si le checkpoint N est déjà confirmé dans cette session."""
    for entry in read_checkpoint_log(session_dir):
        if entry.get("checkpoint") == checkpoint and entry.get("confirmed_at"):
            return True
    return False


def assert_checkpoint_confirmed(session_dir: Path, required_checkpoint: int) -> None:
    """Lève CheckpointRequiredError si le checkpoint N n'est pas confirmé."""
    if not is_checkpoint_confirmed(session_dir, required_checkpoint):
        raise CheckpointRequiredError(required_checkpoint)


def _snapshot_hash(session_dir: Path) -> str:
    """SHA256 tronqué des artefacts JSON présents (excl. session.json).

    Permet à l'évaluateur de vérifier qu'il a confirmé les bonnes données.
    """
    artifacts_dir = session_dir / "artifacts"
    search_dir = artifacts_dir if artifacts_dir.exists() else session_dir
    parts: list[bytes] = []
    for path in sorted(search_dir.rglob("*.json")):
        if path.name in ("session.json", "pipeline_progress.json"):
            continue
        try:
            parts.append(path.read_bytes())
        except OSError:
            pass
    combined = b"".join(parts)
    return "sha256:" + hashlib.sha256(combined).hexdigest()[:16]


# ── Confirmation ──────────────────────────────────────────────────────────────

def confirm_checkpoint(
    session_dir: Path,
    checkpoint: int,
    confirmed_by: str,
) -> dict:
    """Enregistre la confirmation d'un checkpoint dans checkpoint_log.jsonl.

    Args:
        session_dir:   répertoire de la session (SESSIONS_DIR/{session_id})
        checkpoint:    numéro 1-4
        confirmed_by:  UUID Supabase de l'évaluateur (ou "" si non auth)

    Returns:
        L'entrée jsonl écrite.
    """
    if checkpoint not in CHECKPOINT_LABELS:
        raise ValueError(f"checkpoint invalide : {checkpoint}. Valeurs acceptées : 1-4.")

    entry = {
        "checkpoint": checkpoint,
        "label": CHECKPOINT_LABELS[checkpoint],
        "confirmed_by": confirmed_by,
        "confirmed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "snapshot_hash": _snapshot_hash(session_dir),
    }

    log_path = checkpoint_log_path(session_dir)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry
