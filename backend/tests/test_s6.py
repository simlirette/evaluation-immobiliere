"""S6 tests — parse_jlr_csv, scoring JLR, app_upload_jlr_csv / app_confirm_comparables."""
import json
import sys
import base64
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── parse_jlr_csv ─────────────────────────────────────────────────────────────

class TestParseJlrCsv:
    def _write_csv(self, tmp_path: Path, content: str, name="jlr.csv") -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_parses_valid_csv(self, tmp_path):
        from engine.ingestion import parse_jlr_csv
        csv = (
            "adresse,prix_vente,date_vente,surface_habitable,type_bien,no_fiche\n"
            "\"123 Rue A, Sherbrooke\",425000,2025-03-15,1250,unifamiliale,JLR-001\n"
            "\"456 Rue B, Sherbrooke\",380000,2024-11-20,1100,unifamiliale,JLR-002\n"
        )
        path = self._write_csv(tmp_path, csv)
        rows = parse_jlr_csv(path)
        assert len(rows) == 2
        assert rows[0]["prix_vente"] == 425000.0
        assert rows[0]["source_id"] == "JLR-001"
        assert rows[0]["surface_habitable"] == 1250.0
        assert rows[0]["type_bien"] == "unifamiliale"

    def test_skips_rows_without_price(self, tmp_path):
        from engine.ingestion import parse_jlr_csv
        csv = (
            "adresse,prix_vente,date_vente\n"
            "\"A\",450000,2025-01-01\n"
            "\"B\",,2025-02-01\n"
            "\"C\",0,2025-03-01\n"
        )
        path = self._write_csv(tmp_path, csv)
        rows = parse_jlr_csv(path)
        assert len(rows) == 1
        assert rows[0]["adresse"] == "A"

    def test_auto_generates_source_id(self, tmp_path):
        from engine.ingestion import parse_jlr_csv
        csv = "adresse,prix_vente,date_vente\n\"X\",500000,2025-01-01\n"
        path = self._write_csv(tmp_path, csv)
        rows = parse_jlr_csv(path)
        assert rows[0]["source_id"].startswith("JLR-")

    def test_semicolon_separator(self, tmp_path):
        from engine.ingestion import parse_jlr_csv
        csv = "adresse;prix_vente;date_vente\nRue A;350000;2025-06-01\n"
        path = self._write_csv(tmp_path, csv)
        rows = parse_jlr_csv(path)
        assert len(rows) == 1
        assert rows[0]["prix_vente"] == 350000.0

    def test_raises_on_missing_file(self, tmp_path):
        from engine.ingestion import parse_jlr_csv
        with pytest.raises(ValueError, match="introuvable"):
            parse_jlr_csv(tmp_path / "nonexistent.csv")

    def test_raises_on_no_valid_rows(self, tmp_path):
        from engine.ingestion import parse_jlr_csv
        csv = "adresse,prix_vente\nRue A,\nRue B,0\n"
        path = self._write_csv(tmp_path, csv)
        with pytest.raises(ValueError, match="Aucune ligne valide"):
            parse_jlr_csv(path)


# ── JLR scoring ───────────────────────────────────────────────────────────────

class TestJlrScoring:
    def test_jlr_weights_sum_to_one(self):
        from engine.tools import JLR_SCORING_WEIGHTS
        total = sum(JLR_SCORING_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_type_match_same_type(self):
        from engine.tools import _type_match_score
        subject = {"type_bien": "unifamiliale"}
        item = {"type_bien": "unifamiliale"}
        assert _type_match_score(item, subject) == 1.0

    def test_type_match_different_family(self):
        from engine.tools import _type_match_score
        subject = {"type_bien": "unifamiliale"}
        item = {"type_bien": "condo"}
        assert _type_match_score(item, subject) < 0.5

    def test_score_comparable_with_jlr_weights(self):
        from engine.tools import score_comparable, JLR_SCORING_WEIGHTS
        item = {
            "source_id": "JLR-001",
            "prix_vente": 425000,
            "date_vente": "2025-01-15",
            "distance_km": 1.5,
            "surface": {"value": 1200, "unit": "pi2"},
            "type_bien": "unifamiliale",
        }
        subject = {
            "surface": {"value": 1150, "unit": "pi2"},
            "type_bien": "unifamiliale",
        }
        details = score_comparable(item, subject=subject, date_reference="2025-06-01", weights=JLR_SCORING_WEIGHTS)
        assert 0.0 <= details["score"] <= 1.0
        assert "type_match" in details["components"]

    def test_score_penalizes_missing_price_and_sale_date(self):
        from engine.tools import score_comparable
        details = score_comparable({"source_id": "JLR-001", "prix_vente": 0})
        assert "missing_price" in details["penalties"]
        assert "missing_sale_date" in details["penalties"]

    def test_search_excludes_non_usable_comparables(self):
        from engine.tools import search_comparables
        pool = [
            {"comparable_id": "bad-price", "source_id": "JLR-001", "prix_vente": 0, "date_vente": "2025-01-01"},
            {"comparable_id": "bad-date", "source_id": "JLR-002", "prix_vente": 400000, "date_vente": ""},
            {"comparable_id": "bad-source", "source_id": "", "prix_vente": 410000, "date_vente": "2025-01-01"},
            {"comparable_id": "ok", "source_id": "JLR-003", "prix_vente": 420000, "date_vente": "2025-01-01"},
        ]
        results = search_comparables(pool)
        assert [c.comparable_id for c in results] == ["ok"]

    def test_score_justification_fr(self):
        from engine.tools import score_justification_fr
        details = {
            "score": 0.82,
            "components": {"surface_similarity": 0.9, "recency": 0.8, "distance": 0.7, "type_match": 1.0},
            "rationale": [],
        }
        justif = score_justification_fr(details)
        assert "%" in justif
        assert len(justif) > 5


# ── app_upload_jlr_csv ────────────────────────────────────────────────────────

class TestAppUploadJlrCsv:
    def _make_session(self, tmp_path, session_id="sess-jlr-1"):
        session_dir = tmp_path / session_id
        session_dir.mkdir(parents=True)
        session = {
            "session_id": session_id,
            "session_dir": str(session_dir),
            "dossier_id": session_id,
            "status": "CREATED",
        }
        (session_dir / "session.json").write_text(json.dumps(session), encoding="utf-8")
        import api as _api
        original = _api.SESSIONS_DIR
        _api.SESSIONS_DIR = tmp_path
        return original, session_id, session_dir

    def test_upload_scores_and_saves_candidates(self, tmp_path):
        import api as _api
        csv_content = (
            "adresse,prix_vente,date_vente,surface_habitable,type_bien,no_fiche\n"
            "\"1 Rue A\",450000,2025-01-10,1300,unifamiliale,JLR-001\n"
            "\"2 Rue B\",420000,2025-02-15,1180,unifamiliale,JLR-002\n"
            "\"3 Rue C\",380000,2024-08-20,1050,unifamiliale,JLR-003\n"
        )
        csv_b64 = base64.b64encode(csv_content.encode()).decode()
        original, session_id, session_dir = self._make_session(tmp_path)
        try:
            result = _api.app_upload_jlr_csv({
                "session_id": session_id,
                "filename": "export.csv",
                "content_b64": csv_b64,
            })
            assert result["ok"] is True
            assert result["total_parsed"] == 3
            assert len(result["candidates"]) == 3
            # Fichier persisté
            cands_path = session_dir / "jlr_candidates.json"
            assert cands_path.exists()
            data = json.loads(cands_path.read_text())
            assert data["total_parsed"] == 3
            # Scores valides
            for c in result["candidates"]:
                assert 0.0 <= c["score"] <= 1.0
                assert c["source_id"].startswith("JLR-")
        finally:
            _api.SESSIONS_DIR = original

    def test_raises_on_missing_session(self, tmp_path):
        import api as _api
        original = _api.SESSIONS_DIR
        _api.SESSIONS_DIR = tmp_path
        try:
            with pytest.raises(ValueError, match="introuvable"):
                _api.app_upload_jlr_csv({
                    "session_id": "nonexistent",
                    "filename": "x.csv",
                    "content_b64": base64.b64encode(b"a,b\n1,2").decode(),
                })
        finally:
            _api.SESSIONS_DIR = original


# ── app_confirm_comparables ───────────────────────────────────────────────────

class TestAppConfirmComparables:
    def _make_session_with_candidates(self, tmp_path, session_id="sess-confirm-1"):
        import api as _api
        session_dir = tmp_path / session_id
        session_dir.mkdir(parents=True)
        session = {
            "session_id": session_id,
            "session_dir": str(session_dir),
            "dossier_id": session_id,
            "status": "CREATED",
        }
        (session_dir / "session.json").write_text(json.dumps(session), encoding="utf-8")
        candidates = [
            {"id": f"JLR-{i:03d}", "adresse": f"Rue {i}", "prix_vente": 400000 + i * 10000,
             "date_vente": "2025-01-01", "source_id": f"JLR-{i:03d}", "score": 0.8 - i * 0.05}
            for i in range(1, 6)
        ]
        (session_dir / "jlr_candidates.json").write_text(
            json.dumps({"schema_version": "jlr_candidates_v1", "candidates": candidates}),
            encoding="utf-8"
        )
        original = _api.SESSIONS_DIR
        _api.SESSIONS_DIR = tmp_path
        return original, session_id, session_dir

    def test_confirms_and_saves_comparables(self, tmp_path):
        import api as _api
        original, session_id, session_dir = self._make_session_with_candidates(tmp_path)
        try:
            result = _api.app_confirm_comparables({
                "session_id": session_id,
                "selected_ids": ["JLR-001", "JLR-002", "JLR-003"],
            })
            assert result["ok"] is True
            assert result["count"] == 3
            comp_path = session_dir / "comparables.json"
            assert comp_path.exists()
            data = json.loads(comp_path.read_text())
            assert data["manual"] is True
            assert len(data["comparables"]) == 3
            # Checkpoint log
            cp_log = session_dir / "checkpoint_log.jsonl"
            assert cp_log.exists()
            entries = [json.loads(l) for l in cp_log.read_text().splitlines() if l.strip()]
            assert any(e["checkpoint"] == 2 for e in entries)
        finally:
            _api.SESSIONS_DIR = original

    def test_raises_if_fewer_than_3(self, tmp_path):
        import api as _api
        original, session_id, _ = self._make_session_with_candidates(tmp_path)
        try:
            with pytest.raises(ValueError, match="3"):
                _api.app_confirm_comparables({
                    "session_id": session_id,
                    "selected_ids": ["JLR-001", "JLR-002"],
                })
        finally:
            _api.SESSIONS_DIR = original

    def test_raises_if_selected_candidate_not_usable(self, tmp_path):
        import api as _api
        original, session_id, session_dir = self._make_session_with_candidates(tmp_path)
        try:
            data = json.loads((session_dir / "jlr_candidates.json").read_text(encoding="utf-8"))
            data["candidates"][0]["prix_vente"] = 0
            (session_dir / "jlr_candidates.json").write_text(json.dumps(data), encoding="utf-8")
            with pytest.raises(ValueError, match="non exploitables"):
                _api.app_confirm_comparables({
                    "session_id": session_id,
                    "selected_ids": ["JLR-001", "JLR-002", "JLR-003"],
                })
        finally:
            _api.SESSIONS_DIR = original
