"""S10 tests — export propre : absence d'artefacts techniques dans les documents générés."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── _generate_html — absence d'artefacts ─────────────────────────────────────

class TestHtmlExportClean:
    _DOSSIER_ID = "D-USR-ABCD1234"
    _SESSION_UUID = "a1b2c3d4e5f6"  # UUID technique interne — ne doit jamais apparaître

    def _html(self, md: str = "## Identification\n\nTest contenu rapport.") -> str:
        from engine.report_export import _generate_html
        return _generate_html(md, self._DOSSIER_ID)

    def test_dossier_id_in_title(self):
        """Le titre HTML contient le dossier_id (identifiant métier)."""
        html = self._html()
        assert self._DOSSIER_ID in html

    def test_no_session_uuid_in_html(self):
        """La session UUID technique n'apparaît pas dans le HTML exporté."""
        html = self._html()
        assert self._SESSION_UUID not in html

    def test_no_snapshot_hash_in_html(self):
        """Aucune mention de snapshot_hash dans le HTML."""
        html = self._html()
        assert "snapshot_hash" not in html

    def test_no_proxy_avertissement_in_html(self):
        """L'avertissement proxy OEAQ n'est pas injecté par l'export HTML."""
        html = self._html()
        assert "VALEUR PROXY" not in html

    def test_no_session_id_key_in_html(self):
        """La clé JSON 'session_id' n'apparaît pas dans le HTML exporté."""
        html = self._html()
        assert '"session_id"' not in html

    def test_brouillon_watermark_present(self):
        """Le watermark BROUILLON NON CERTIFIÉ est bien présent."""
        html = self._html()
        assert "BROUILLON NON CERTIFIÉ" in html


# ── _generate_docx — absence d'artefacts ─────────────────────────────────────

class TestDocxExportClean:
    _DOSSIER_ID = "D-USR-ABCD1234"
    _SESSION_UUID = "a1b2c3d4e5f6"

    def _docx_text(self, md: str = "## Identification\n\nTest contenu rapport.") -> str:
        from engine.report_export import _generate_docx
        from docx import Document  # type: ignore
        data = _generate_docx(md, self._DOSSIER_ID)
        doc = Document(io.BytesIO(data))
        return " ".join(p.text for p in doc.paragraphs)

    def test_no_snapshot_hash_in_docx(self):
        text = self._docx_text()
        assert "snapshot_hash" not in text

    def test_no_proxy_avertissement_in_docx(self):
        text = self._docx_text()
        assert "VALEUR PROXY" not in text

    def test_no_session_uuid_in_docx(self):
        text = self._docx_text()
        assert self._SESSION_UUID not in text

    def test_brouillon_watermark_in_docx(self):
        text = self._docx_text()
        assert "BROUILLON NON CERTIFIÉ" in text


# ── app_export_rapport — nom fichier utilise dossier_id ──────────────────────

class TestExportFilenameUsesDossierId:
    def _setup_session(self, tmp_path: Path, session_id: str, dossier_id: str) -> None:
        session_dir = tmp_path / session_id
        session_dir.mkdir()
        artifacts_dir = session_dir / "artifacts" / dossier_id
        artifacts_dir.mkdir(parents=True)
        run_id = "run_s10"
        rapport_path = artifacts_dir / "redaction.brouillon_rapport.md"
        rapport_path.write_text("## Rapport\n\nContenu test.", encoding="utf-8")
        compliance_path = artifacts_dir / "compliance-qa.statut_sortie.json"
        compliance_path.write_text(
            json.dumps({"status": "PRET_REVISION_FINALE", "blocking_failures": [], "warnings": []}),
            encoding="utf-8",
        )
        comparative_path = artifacts_dir / "valuation-draft.calculs_approche_comparative.json"
        comparative_path.write_text(
            json.dumps({"value": 400000, "input_count": 3, "calculation_status": "OK"}),
            encoding="utf-8",
        )
        result_path = session_dir / "result.json"
        result_path.write_text(
            json.dumps({
                "dossier_id": dossier_id,
                "status": "PRET_REVISION_FINALE",
                "blocking_failures": [],
                "warnings": [],
                "artifact_dir": str(artifacts_dir),
            }),
            encoding="utf-8",
        )
        review_path = session_dir / "review.json"
        review_path.write_text(
            json.dumps({"decision": "VALIDE", "reviewer": "EA test", "notes": "ok"}),
            encoding="utf-8",
        )
        events = [
            ("evt_s10_report", "redaction", "brouillon_rapport.md", rapport_path),
            ("evt_s10_compliance", "compliance-qa", "statut_sortie.json", compliance_path),
            ("evt_s10_comparative", "valuation-draft", "calculs_approche_comparative.json", comparative_path),
        ]
        events_path = session_dir / "events.jsonl"
        events_path.write_text(
            "\n".join(
                json.dumps({
                    "event_id": event_id,
                    "session_id": session_id,
                    "run_id": run_id,
                    "sequence": index,
                    "event": "artifact_written",
                    "step": step,
                    "artifact": artifact,
                    "path": str(path),
                    "artifact_path": str(path),
                })
                for index, (event_id, step, artifact, path) in enumerate(events, start=1)
            ) + "\n",
            encoding="utf-8",
        )
        artifact_index = {
            "artifacts": [
                {
                    "step": "redaction",
                    "artifact": "brouillon_rapport.md",
                    "event_id": "evt_s10_report",
                    "path": str(rapport_path),
                    "exists": True,
                },
                {
                    "step": "compliance-qa",
                    "artifact": "statut_sortie.json",
                    "event_id": "evt_s10_compliance",
                    "path": str(compliance_path),
                    "exists": True,
                },
                {
                    "step": "valuation-draft",
                    "artifact": "calculs_approche_comparative.json",
                    "event_id": "evt_s10_comparative",
                    "path": str(comparative_path),
                    "exists": True,
                }
            ]
        }
        artifact_index_path = session_dir / "artifact_index.json"
        artifact_index_path.write_text(json.dumps(artifact_index), encoding="utf-8")
        (session_dir / "session.json").write_text(
            json.dumps({
                "session_id": session_id,
                "run_id": run_id,
                "session_dir": str(session_dir),
                "dossier_id": dossier_id,
                "result_path": str(result_path),
                "review_path": str(review_path),
                "events_path": str(events_path),
                "artifact_index_path": str(artifact_index_path),
            }),
            encoding="utf-8",
        )

    def test_docx_filename_uses_dossier_id_not_session_uuid(self, tmp_path, monkeypatch):
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)
        session_id = "s10-uuid-test"
        dossier_id = "D-USR-S10TEST"
        self._setup_session(tmp_path, session_id, dossier_id)
        result = api_module.app_export_rapport({"session_id": session_id, "format": "docx"})
        assert dossier_id in result["filename"]
        assert session_id not in result["filename"]

    def test_html_filename_uses_dossier_id_not_session_uuid(self, tmp_path, monkeypatch):
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)
        session_id = "s10-uuid-html"
        dossier_id = "D-USR-S10HTML"
        self._setup_session(tmp_path, session_id, dossier_id)
        result = api_module.app_export_rapport({"session_id": session_id, "format": "html"})
        assert dossier_id in result["filename"]
        assert session_id not in result["filename"]

    def test_html_body_no_session_uuid(self, tmp_path, monkeypatch):
        """Le corps HTML exporté ne contient pas le UUID de session."""
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)
        session_id = "s10-uuid-body-check"
        dossier_id = "D-USR-S10BODY"
        self._setup_session(tmp_path, session_id, dossier_id)
        result = api_module.app_export_rapport({"session_id": session_id, "format": "html"})
        assert session_id not in result["data"]
        assert "snapshot_hash" not in result["data"]
        assert "VALEUR PROXY" not in result["data"]
