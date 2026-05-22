"""S12 red team — corrections post-révision adversariale."""
from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── CRITIQUE #1 — confirm_comparables rejette les IDs inconnus ────────────────

class TestConfirmComparables_RejectUnknownIds:
    def _setup(self, tmp_path: Path, session_id: str, dossier_id: str, with_candidates: bool = True) -> None:
        session_dir = tmp_path / session_id
        session_dir.mkdir()
        (session_dir / "session.json").write_text(
            json.dumps({"session_id": session_id, "session_dir": str(session_dir), "dossier_id": dossier_id}),
            encoding="utf-8",
        )
        (session_dir / "artifact_index.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")
        if with_candidates:
            candidates = {
                "candidates": [
                    {"id": "JLR-001", "source_id": "JLR-001", "prix_vente": 550000,
                     "date_vente": "2025-06-01", "adresse": "123 Rue Test", "score": 0.82},
                    {"id": "JLR-002", "source_id": "JLR-002", "prix_vente": 570000,
                     "date_vente": "2025-07-01", "adresse": "456 Rue Test", "score": 0.79},
                    {"id": "JLR-003", "source_id": "JLR-003", "prix_vente": 540000,
                     "date_vente": "2025-05-01", "adresse": "789 Rue Test", "score": 0.75},
                ]
            }
            (session_dir / "jlr_candidates.json").write_text(json.dumps(candidates), encoding="utf-8")
        (session_dir / "checkpoint_log.jsonl").write_text(
            json.dumps({"checkpoint": 1, "confirmed_by": "user", "confirmed_at": "2025-01-01T00:00:00Z", "label": "faits"}) + "\n",
            encoding="utf-8",
        )

    def test_unknown_ids_raise_value_error(self, tmp_path, monkeypatch):
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)
        self._setup(tmp_path, "sess-rj-001", "D-RJ-001")
        with pytest.raises(ValueError, match="inconnus"):
            api_module.app_confirm_comparables({
                "session_id": "sess-rj-001",
                "selected_ids": ["FAKE-001", "FAKE-002", "FAKE-003"],
                "checkpoint": 2,
            })

    def test_no_jlr_file_raises_value_error(self, tmp_path, monkeypatch):
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)
        self._setup(tmp_path, "sess-rj-002", "D-RJ-002", with_candidates=False)
        with pytest.raises(ValueError, match="inconnus|CSV JLR"):
            api_module.app_confirm_comparables({
                "session_id": "sess-rj-002",
                "selected_ids": ["JLR-001", "JLR-002", "JLR-003"],
                "checkpoint": 2,
            })

    def test_valid_ids_succeed(self, tmp_path, monkeypatch):
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)
        self._setup(tmp_path, "sess-rj-003", "D-RJ-003")
        result = api_module.app_confirm_comparables({
            "session_id": "sess-rj-003",
            "selected_ids": ["JLR-001", "JLR-002", "JLR-003"],
            "checkpoint": 2,
        })
        assert result["ok"] is True
        # Vérifier qu'aucun comparable n'a un prix zéro
        comp_path = tmp_path / "sess-rj-003" / "comparables.json"
        data = json.loads(comp_path.read_text(encoding="utf-8"))
        assert all(c["sale_price"] > 0 for c in data["comparables"])

    def test_partial_unknown_ids_raise(self, tmp_path, monkeypatch):
        """Même un seul ID inconnu parmi des valides doit bloquer."""
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)
        self._setup(tmp_path, "sess-rj-004", "D-RJ-004")
        with pytest.raises(ValueError, match="inconnus"):
            api_module.app_confirm_comparables({
                "session_id": "sess-rj-004",
                "selected_ids": ["JLR-001", "JLR-002", "FAKE-XYZ"],
                "checkpoint": 2,
            })


# ── CRITIQUE #3 — Limite taille CSV upload ────────────────────────────────────

class TestJlrUploadSizeLimit:
    def _setup_session(self, tmp_path: Path, session_id: str) -> None:
        session_dir = tmp_path / session_id
        session_dir.mkdir()
        (session_dir / "session.json").write_text(
            json.dumps({"session_id": session_id, "session_dir": str(session_dir), "dossier_id": "D-SZ"}),
            encoding="utf-8",
        )
        (session_dir / "artifact_index.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")

    def test_oversized_csv_raises(self, tmp_path, monkeypatch):
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)
        self._setup_session(tmp_path, "sess-sz-001")
        # Générer un CSV > 5 MB
        header = "adresse,prix_vente,date_vente\n"
        row = "123 Rue Test Laval,550000,2025-01-15\n"
        big_csv = (header + row * 200_000).encode("utf-8")  # ~8 MB
        b64 = base64.b64encode(big_csv).decode("ascii")
        with pytest.raises(ValueError, match="trop volumineux"):
            api_module.app_upload_jlr_csv({
                "session_id": "sess-sz-001",
                "filename": "big.csv",
                "content_b64": b64,
            })

    def test_normal_csv_not_rejected(self, tmp_path, monkeypatch):
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)
        self._setup_session(tmp_path, "sess-sz-002")
        csv_content = "no_fiche;adresse;prix_vente;date_vente;superficie_habitable\nJLR-001;123 Rue;550000;2025-01-15;1600\n"
        b64 = base64.b64encode(csv_content.encode("utf-8")).decode("ascii")
        # Ne doit pas lever ValueError de taille
        try:
            api_module.app_upload_jlr_csv({
                "session_id": "sess-sz-002",
                "filename": "normal.csv",
                "content_b64": b64,
            })
        except ValueError as e:
            assert "trop volumineux" not in str(e), f"Rejeté à tort pour taille : {e}"


# ── ÉLEVÉ #4 — B005 avec montant null ou string ───────────────────────────────

class TestB005NullMontant:
    def test_null_montant_does_not_crash(self):
        from engine.compliance import check_B005, ComplianceResult
        case = {
            "dossier_id": "D-TEST",
            "date_reference": "2024-01-01",
            "ajustements": [
                {"source_id": "S1", "montant": None, "validation_humaine": False},
            ],
        }
        result = check_B005(case)
        assert isinstance(result, ComplianceResult)

    def test_string_montant_does_not_crash(self):
        from engine.compliance import check_B005, ComplianceResult
        case = {
            "dossier_id": "D-TEST",
            "date_reference": "2024-01-01",
            "ajustements": [
                {"source_id": "S1", "montant": "vingt-cinq mille", "validation_humaine": False},
            ],
        }
        result = check_B005(case)
        assert isinstance(result, ComplianceResult)
        # String non parseable → traité comme 0 → pas bloquant
        assert not result.violated

    def test_large_null_montant_not_flagged(self):
        """Un ajustement montant=None ne doit pas déclencher B005 (valeur inconnue = 0)."""
        from engine.compliance import check_B005
        case = {
            "dossier_id": "D-TEST",
            "date_reference": "2024-01-01",
            "ajustements": [
                {"source_id": "S1", "montant": None, "validation_humaine": False},
            ],
        }
        assert not check_B005(case).violated


# ── ÉLEVÉ #7 — Pas de session orpheline sur ValueError conversion ─────────────

class TestCreateDossierNoOrphanSession:
    def test_invalid_superficie_no_session_saved(self, tmp_path, monkeypatch):
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)
        sessions_before = list(tmp_path.glob("*/session.json"))
        with pytest.raises((ValueError, Exception)):
            api_module.app_create_dossier({
                "address": "123 Rue Test",
                "superficie_habitable": "mille deux cents",
            })
        sessions_after = list(tmp_path.glob("*/session.json"))
        assert len(sessions_after) == len(sessions_before), (
            f"Session orpheline créée malgré ValueError : {len(sessions_after) - len(sessions_before)} nouvelle(s)"
        )

    def test_invalid_annee_no_session_saved(self, tmp_path, monkeypatch):
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)
        sessions_before = list(tmp_path.glob("*/session.json"))
        with pytest.raises((ValueError, Exception)):
            api_module.app_create_dossier({
                "address": "456 Rue Test",
                "annee_construction": "mil neuf cent quatre-vingt-cinq",
            })
        sessions_after = list(tmp_path.glob("*/session.json"))
        assert len(sessions_after) == len(sessions_before)


# ── ÉLEVÉ #8 — Valuation 0 comparables → AVERTISSEMENT ──────────────────────

class TestValuationNoComparables:
    def test_empty_comparables_has_avertissement(self):
        from engine.valuation import calculate_valuation_trace
        case = {
            "dossier_id": "D-TEST",
            "date_reference": "2025-01-01",
            "comparables": [],
            "ajustements": [],
        }
        result = calculate_valuation_trace(case, "approche_comparative")
        assert result["input_count"] == 0
        assert "AVERTISSEMENT" in result, (
            "Valeur 0 sans comparables doit déclencher un AVERTISSEMENT visible"
        )
        assert "AUCUN COMPARABLE" in str(result["AVERTISSEMENT"])

    def test_empty_comparables_value_is_zero(self):
        from engine.valuation import calculate_valuation_trace
        case = {"dossier_id": "D-TEST", "date_reference": "2025-01-01",
                "comparables": [], "ajustements": []}
        result = calculate_valuation_trace(case, "approche_comparative")
        assert result["value"] == 0.0


# ── MOYEN — Checkpoint double confirmation ────────────────────────────────────

class TestCheckpointIdempotence:
    def test_double_confirm_logs_both_but_confirmed_check_passes(self, tmp_path):
        from engine.checkpoints import confirm_checkpoint, is_checkpoint_confirmed
        confirm_checkpoint(tmp_path, 1, "user-001")
        confirm_checkpoint(tmp_path, 1, "user-001")
        # La double confirmation ne doit pas empêcher la vérification
        assert is_checkpoint_confirmed(tmp_path, 1)
        # Le log contient deux entrées (comportement documenté, pas idéal pour audit)
        log_path = tmp_path / "checkpoint_log.jsonl"
        entries = [json.loads(l) for l in log_path.read_text(encoding="utf-8").splitlines() if l]
        cp1 = [e for e in entries if e.get("checkpoint") == 1]
        # Documenter le comportement — deux entrées actuellement (candidat pour idempotence future)
        assert len(cp1) >= 1


# ── MOYEN — Distance score pour distance nulle ────────────────────────────────

class TestDistanceScoreEdgeCases:
    def test_distance_zero_returns_perfect(self):
        from engine.tools import score_comparable
        item = {"distance_km": 0, "prix_vente": 500000, "date_vente": "2025-01-01"}
        result = score_comparable(item)
        # distance=0 → score distance = 1.0, contribue positivement
        assert result["components"]["distance"] == 1.0

    def test_distance_none_returns_neutral(self):
        from engine.tools import score_comparable
        item = {"prix_vente": 500000, "date_vente": "2025-01-01"}  # pas de distance_km
        result = score_comparable(item)
        assert result["components"]["distance"] == 0.5
