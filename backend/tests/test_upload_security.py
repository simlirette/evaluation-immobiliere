"""Upload hardening tests: filenames, signatures, ownership, ingestion metadata."""
from __future__ import annotations

import base64
import json
import os
import sys
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api


def _make_session_file(tmp_path: Path, session_id: str, owner_evaluator_id: str = "uid-owner") -> Path:
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True)
    session = {
        "session_id": session_id,
        "run_id": f"run_{session_id}",
        "dossier_id": "D-USR-UPLOAD01",
        "status": "READY",
        "created_at_utc": "2026-05-21T10:00:00+00:00",
        "updated_at_utc": "2026-05-21T10:00:00+00:00",
        "session_dir": str(session_dir),
        "owner_evaluator_id": owner_evaluator_id,
    }
    (session_dir / "session.json").write_text(json.dumps(session), encoding="utf-8")
    return session_dir


def _pdf_bytes() -> bytes:
    try:
        import fitz  # type: ignore
    except ImportError:
        pytest.skip("PyMuPDF not installed")

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Rapport evaluation immobiliere")
    data = doc.tobytes()
    doc.close()
    return data


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


class TestUploadValidation:
    def test_rejects_path_bearing_filename(self):
        with pytest.raises(ValueError, match="chemins"):
            api._safe_upload_filename(r"..\secret.pdf", "application/pdf")

    def test_rejects_extension_mismatch(self):
        with pytest.raises(ValueError, match="Extension"):
            api._safe_upload_filename("rapport.txt", "application/pdf")

    def test_rejects_fake_pdf_payload(self):
        with pytest.raises(ValueError, match="signature PDF"):
            api._assert_upload_signature("application/pdf", b"not a pdf")

    def test_upload_persists_sanitized_name_and_owner(self, tmp_path):
        _make_session_file(tmp_path, "upl01")
        payload = {
            "session_id": "upl01",
            "filename": "Rapport final.pdf",
            "mime_type": "application/pdf",
            "content_b64": _b64(_pdf_bytes()),
            "_evaluator_id": "uid-owner",
        }

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            result = api.app_upload_document(payload)

        assert result["filename"] == "Rapport-final.pdf"
        saved = json.loads((tmp_path / "upl01" / "session.json").read_text(encoding="utf-8"))
        [doc] = saved["uploaded_documents"]
        assert doc["filename"] == "Rapport-final.pdf"
        assert doc["uploaded_by"] == "uid-owner"
        assert doc["extraction_status"] == "extracted"
        assert (tmp_path / "upl01" / "uploads" / "Rapport-final.pdf").exists()


class TestUploadOwnershipGuard:
    def _handler(self, evaluator_id: str):
        handler = api.RuntimeApiHandler.__new__(api.RuntimeApiHandler)
        message = Message()
        message["Authorization"] = "Bearer runtime-token"
        message["X-Evaluator-Id"] = evaluator_id
        handler.headers = message
        handler._send_json = MagicMock()
        return handler

    def test_cross_user_upload_session_access_is_denied(self, tmp_path):
        _make_session_file(tmp_path, "owned01", owner_evaluator_id="uid-owner")
        handler = self._handler("uid-other")

        with patch.dict(os.environ, {"EVAL_RUNTIME_API_TOKEN": "runtime-token"}, clear=True):
            with patch.object(api, "SESSIONS_DIR", tmp_path):
                allowed = handler._require_session_access("owned01")

        assert allowed is False
        handler._send_json.assert_called_once()
        status, payload = handler._send_json.call_args.args
        assert status == 403
        assert payload["code"] == "SESSION_FORBIDDEN"


class TestIngestionMetadataSafety:
    def test_ingestion_rejects_traversal_filename_from_session_metadata(self, tmp_path):
        from engine.ingestion import IngestionError, ingest_uploaded_documents

        uploads_dir = tmp_path / "uploads"
        uploads_dir.mkdir()
        session = {
            "session_dir": str(tmp_path),
            "uploaded_documents": [
                {"filename": "../secret.pdf", "mime_type": "application/pdf"},
            ],
        }

        with pytest.raises(IngestionError, match="aucun texte"):
            ingest_uploaded_documents(session, None)

        [doc] = session["uploaded_documents"]
        assert doc["extraction_status"] == "error"
        assert "invalide" in doc["extraction_error"]
