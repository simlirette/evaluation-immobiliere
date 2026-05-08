"""Pure-function unit tests — no I/O, no sessions, no server."""
import sys
from pathlib import Path

# Allow importing api.py directly without the full package installed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import (
    app_date_label,
    app_money,
    app_source_documents,
    app_surface_label,
    app_status_label,
)


# ── app_money ────────────────────────────────────────────────────────────────

class TestAppMoney:
    def test_integer(self):
        assert app_money(500000) == "500 000 $"

    def test_float_rounds(self):
        assert app_money(499999.9) == "500 000 $"

    def test_zero(self):
        assert app_money(0) == "0 $"

    def test_string_numeric(self):
        assert app_money("250000") == "250 000 $"

    def test_none_returns_dash(self):
        assert app_money(None) == "-"

    def test_empty_string_returns_dash(self):
        assert app_money("") == "-"

    def test_non_numeric_returns_dash(self):
        assert app_money("abc") == "-"

    def test_negative(self):
        result = app_money(-10000)
        assert "$" in result


# ── app_date_label ────────────────────────────────────────────────────────────

class TestAppDateLabel:
    def test_iso_datetime(self):
        assert app_date_label("2025-03-15T10:30:00") == "2025-03-15"

    def test_iso_with_z(self):
        assert app_date_label("2025-03-15T10:30:00Z") == "2025-03-15"

    def test_date_only(self):
        assert app_date_label("2025-03-15") == "2025-03-15"

    def test_none_returns_empty(self):
        assert app_date_label(None) == ""

    def test_empty_string_returns_empty(self):
        assert app_date_label("") == ""

    def test_invalid_returns_raw(self):
        assert app_date_label("not-a-date") == "not-a-date"

    def test_with_timezone_offset(self):
        assert app_date_label("2025-06-01T00:00:00+05:00") == "2025-06-01"


# ── app_surface_label ─────────────────────────────────────────────────────────

class TestAppSurfaceLabel:
    def test_basic(self):
        assert app_surface_label({"value": 120, "unit": "m²"}) == "120 m²"

    def test_no_value_returns_dash(self):
        assert app_surface_label({"value": None, "unit": "m²"}) == "-"

    def test_empty_value_returns_dash(self):
        assert app_surface_label({"value": "", "unit": "m²"}) == "-"

    def test_not_dict_returns_dash(self):
        assert app_surface_label("120 m²") == "-"
        assert app_surface_label(None) == "-"

    def test_no_unit(self):
        result = app_surface_label({"value": 80, "unit": ""})
        assert "80" in result


# ── app_source_documents ──────────────────────────────────────────────────────

class TestAppSourceDocuments:
    def test_empty_knowledge(self):
        assert app_source_documents({}) == []

    def test_sources_from_knowledge(self):
        knowledge = {
            "sources": {
                "items": [
                    {"source_id": "SRC-1", "source_type": "mls", "reliability_level": "A"},
                    {"source_id": "SRC-2", "source_type": "mpac"},
                ]
            }
        }
        docs = app_source_documents(knowledge)
        assert len(docs) == 2
        ids = [d["id"] for d in docs]
        assert "SRC-1" in ids
        assert "SRC-2" in ids

    def test_uploaded_docs_merged_from_session(self):
        knowledge = {}
        session = {
            "uploaded_documents": [
                {"id": "upl-1", "name": "Acte.pdf", "filename": "acte.pdf", "size_bytes": 204800},
            ]
        }
        docs = app_source_documents(knowledge, session)
        assert len(docs) == 1
        assert docs[0]["id"] == "upl-1"
        assert docs[0]["name"] == "Acte.pdf"
        assert "200" in docs[0]["sizeLabel"]  # 204800 // 1024 == 200

    def test_knowledge_and_uploaded_merged(self):
        knowledge = {
            "sources": {
                "items": [{"source_id": "SRC-1"}]
            }
        }
        session = {
            "uploaded_documents": [
                {"id": "upl-1", "name": "Doc.pdf", "filename": "doc.pdf", "size_bytes": 1024},
            ]
        }
        docs = app_source_documents(knowledge, session)
        assert len(docs) == 2

    def test_invalid_items_skipped(self):
        knowledge = {
            "sources": {
                "items": ["not-a-dict", None, {"source_id": "OK"}]
            }
        }
        docs = app_source_documents(knowledge)
        assert len(docs) == 1
        assert docs[0]["id"] == "OK"

    def test_no_session_is_fine(self):
        docs = app_source_documents({}, session=None)
        assert docs == []


# ── app_status_label ──────────────────────────────────────────────────────────

class TestAppStatusLabel:
    def test_complet(self):
        assert app_status_label({"package_status": "PRET_REVUE_EVALUATEUR_AGREE"}) == "complet"

    def test_en_cours_pret_revision(self):
        assert app_status_label({"status": "PRET_REVISION_FINALE"}) == "en-cours"

    def test_en_cours_a_revoir(self):
        assert app_status_label({"status": "A_REVOIR"}) == "en-cours"

    def test_brouillon_default(self):
        assert app_status_label({"status": "CREATED"}) == "brouillon"

    def test_empty_record(self):
        assert app_status_label({}) == "brouillon"
