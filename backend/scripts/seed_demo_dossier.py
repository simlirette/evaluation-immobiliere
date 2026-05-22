#!/usr/bin/env python3
"""
seed_demo_dossier.py — crée la session démo D-DEMO-2026-LAV dans runtime_sessions/.

Usage :
    python scripts/seed_demo_dossier.py [--sessions-dir PATH]

Le script :
1. Crée le répertoire de session
2. Écrit session.json + D-DEMO-2026-LAV.input.json
3. Copie le CSV JLR dans la session (pour upload manuel ou test)
4. Affiche les prochaines étapes (checkpoints à confirmer)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"
FIXTURE_INPUT = FIXTURES / "demo_laval_res.input.json"
FIXTURE_CSV = FIXTURES / "demo_laval_res.jlr.csv"
DOSSIER_ID = "D-DEMO-2026-LAV"


def _safe_id(s: str) -> str:
    return s.replace("/", "-").replace("\\", "-").replace(" ", "_")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed démo dossier D-DEMO-2026-LAV")
    parser.add_argument(
        "--sessions-dir",
        default=str(ROOT / "runtime_sessions"),
        help="Répertoire des sessions (défaut: backend/runtime_sessions)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Écrase la session existante si déjà présente",
    )
    args = parser.parse_args()

    sessions_dir = Path(args.sessions_dir)
    sessions_dir.mkdir(parents=True, exist_ok=True)

    # Cherche une session existante pour ce dossier
    existing = None
    for d in sessions_dir.iterdir():
        if not d.is_dir():
            continue
        sj = d / "session.json"
        if sj.exists():
            try:
                data = json.loads(sj.read_text(encoding="utf-8"))
                if data.get("dossier_id") == DOSSIER_ID:
                    existing = d
                    break
            except Exception:
                pass

    if existing and not args.force:
        print(f"[INFO] Session démo déjà présente : {existing}")
        print("[INFO] Utilisez --force pour la recréer.")
        _print_next_steps(existing)
        return

    if existing and args.force:
        shutil.rmtree(existing)
        print(f"[INFO] Session existante supprimée : {existing}")

    # Crée la nouvelle session
    session_id = uuid.uuid4().hex[:12]
    session_dir = sessions_dir / session_id
    session_dir.mkdir(parents=True)

    # session.json
    session_data = {
        "session_id": session_id,
        "dossier_id": DOSSIER_ID,
        "session_dir": str(session_dir),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "CREATED",
    }
    (session_dir / "session.json").write_text(
        json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # input.json
    case = json.loads(FIXTURE_INPUT.read_text(encoding="utf-8"))
    input_path = session_dir / f"{_safe_id(DOSSIER_ID)}.input.json"
    input_path.write_text(
        json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # CSV JLR (copie dans la session pour consultation)
    csv_dest = session_dir / "demo_laval_res.jlr.csv"
    shutil.copy(FIXTURE_CSV, csv_dest)

    # artifact_index.json vide (sera rempli par le pipeline)
    (session_dir / "artifact_index.json").write_text(
        json.dumps({"artifacts": []}), encoding="utf-8"
    )

    print(f"\n✓ Session démo créée : {session_dir}")
    print(f"  session_id  : {session_id}")
    print(f"  dossier_id  : {DOSSIER_ID}")
    print(f"  input.json  : {input_path.name}")
    print(f"  CSV JLR     : {csv_dest.name}")
    _print_next_steps(session_dir)


def _print_next_steps(session_dir: Path) -> None:
    print("\n── Prochaines étapes ──────────────────────────────────────")
    print("1. Lancer le backend : python api.py")
    print("2. Ouvrir l'UI : http://localhost:8080")
    print(f"3. Sélectionner le dossier : {DOSSIER_ID}")
    print("4. Lancer le pipeline → confirmer CP1 (faits)")
    print("5. Importer le CSV JLR → confirmer CP2 (comparables)")
    print("6. Vérifier la réconciliation → confirmer CP3")
    print("7. Éditer et exporter le rapport → confirmer CP4")
    print("───────────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
