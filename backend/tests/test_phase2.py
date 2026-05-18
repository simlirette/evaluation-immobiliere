"""Phase 2 tests — PDF ingestion, fetch_artifact, history injection."""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api


# ── _extract_pdf_text ────────────────────────────────────────────────────────

class TestExtractPdfText:
    def test_extracts_text_to_txt(self, tmp_path):
        try:
            import fitz  # type: ignore
        except ImportError:
            pytest.skip("PyMuPDF not installed")

        pdf_path = tmp_path / "doc.pdf"
        txt_path = tmp_path / "doc.txt"

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Rapport evaluation immobiliere page 1")
        doc.save(str(pdf_path))
        doc.close()

        pages = api._extract_pdf_text(pdf_path, txt_path)

        assert pages == 1
        assert txt_path.exists()
        content = txt_path.read_text(encoding="utf-8")
        assert "Page 1" in content
        assert "evaluation immobiliere" in content

    def test_returns_zero_for_empty_pdf(self, tmp_path):
        try:
            import fitz  # type: ignore
        except ImportError:
            pytest.skip("PyMuPDF not installed")

        pdf_path = tmp_path / "empty.pdf"
        txt_path = tmp_path / "empty.txt"

        # PDF with blank page (no text)
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        pages = api._extract_pdf_text(pdf_path, txt_path)
        assert pages == 0
        assert not txt_path.exists()

    def test_returns_zero_if_fitz_missing(self, tmp_path, monkeypatch):
        """Graceful fallback when PyMuPDF is not importable."""
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "fitz":
                raise ImportError("no module fitz")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        pages = api._extract_pdf_text(tmp_path / "x.pdf", tmp_path / "x.txt")
        assert pages == 0


# ── _execute_fetch_artifact ──────────────────────────────────────────────────

class TestExecuteFetchArtifact:
    def _make_session(self, tmp_path, session_id, dossier_id, step, artifact_name, content):
        art_dir = tmp_path / session_id / "artifacts" / dossier_id
        art_dir.mkdir(parents=True)
        (art_dir / f"{step}.{artifact_name}").write_text(content, encoding="utf-8")
        # Patch SESSIONS_DIR
        original = api.SESSIONS_DIR
        api.SESSIONS_DIR = tmp_path
        return original

    def test_returns_content_when_found(self, tmp_path):
        payload = json.dumps({"key": "valeur_test"})
        original = self._make_session(
            tmp_path, "sess1", "D-001", "data-facts", "fiche_bien.json", payload
        )
        try:
            result = api._execute_fetch_artifact("sess1", "D-001", "data-facts", "fiche_bien.json")
            assert "valeur_test" in result
        finally:
            api.SESSIONS_DIR = original

    def test_truncates_to_3000_chars(self, tmp_path):
        long_content = "x" * 5000
        original = self._make_session(
            tmp_path, "sess2", "D-001", "data-facts", "big.json", long_content
        )
        try:
            result = api._execute_fetch_artifact("sess2", "D-001", "data-facts", "big.json")
            assert len(result) <= 3020  # 3000 + "[tronqué]" suffix
            assert "tronqué" in result
        finally:
            api.SESSIONS_DIR = original

    def test_missing_artifact_returns_error_message(self, tmp_path):
        original = api.SESSIONS_DIR
        api.SESSIONS_DIR = tmp_path
        try:
            result = api._execute_fetch_artifact("nosess", "D-001", "data-facts", "missing.json")
            assert "non trouvé" in result or "introuvable" in result.lower() or "non trouv" in result
        finally:
            api.SESSIONS_DIR = original


# ── _append_upload_to_source_index ──────────────────────────────────────────

class TestAppendUploadToSourceIndex:
    def _make_source_index(self, session_dir, dossier_id, initial_sources):
        art_dir = session_dir / "artifacts" / dossier_id
        art_dir.mkdir(parents=True)
        path = art_dir / "data-facts.source_index.json"
        path.write_text(
            json.dumps({"sources": initial_sources, "dossier_id": dossier_id}),
            encoding="utf-8",
        )
        return path

    def test_appends_source_when_index_exists(self, tmp_path):
        session_dir = tmp_path / "sess_upload"
        session_dir.mkdir()
        index_path = self._make_source_index(session_dir, "D-001", [])

        session = {"session_dir": str(session_dir), "dossier_id": "D-001"}
        txt_path = session_dir / "uploads" / "rapport.txt"

        api._append_upload_to_source_index(session, "upload-abc123", "rapport.pdf", txt_path, pages=3)

        data = json.loads(index_path.read_text(encoding="utf-8"))
        assert len(data["sources"]) == 1
        src = data["sources"][0]
        assert src["source_id"] == "upload-abc123"
        assert src["pages"] == 3
        assert src["type"] == "uploaded_document"

    def test_no_op_when_index_missing(self, tmp_path):
        """Should not raise if source_index.json doesn't exist yet."""
        session = {"session_dir": str(tmp_path), "dossier_id": "D-001"}
        # No exception
        api._append_upload_to_source_index(session, "upload-xyz", "file.pdf", tmp_path / "file.txt", 1)

    def test_preserves_existing_sources(self, tmp_path):
        session_dir = tmp_path / "sess_preserve"
        session_dir.mkdir()
        index_path = self._make_source_index(
            session_dir, "D-001", [{"source_id": "SRC-001"}]
        )
        session = {"session_dir": str(session_dir), "dossier_id": "D-001"}

        api._append_upload_to_source_index(session, "upload-new", "new.pdf", tmp_path / "new.txt", 2)

        data = json.loads(index_path.read_text(encoding="utf-8"))
        assert len(data["sources"]) == 2
        assert data["sources"][0]["source_id"] == "SRC-001"


# ── history injection in llm_assistant_answer ────────────────────────────────

class TestLlmAssistantAnswerHistory:
    def _make_mock_client(self, finish_reason="stop"):
        """Returns a mock OpenAI client whose completions.create captures messages."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].finish_reason = finish_reason
        mock_response.choices[0].message.content = "Réponse test"
        mock_response.choices[0].message.tool_calls = None
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client

    def test_history_injected_between_system_and_user(self, tmp_path):
        original_sessions = api.SESSIONS_DIR
        api.SESSIONS_DIR = tmp_path

        mock_client = self._make_mock_client()

        with patch("api._llm_client", return_value=mock_client):
            context = {
                "session_id": "test-sess",
                "dossier_id": "D-001",
                "runtime_status": "COMPLETE",
                "review_decision": "A_VALIDER",
                "package_status": "ABSENT",
                "integrity_ok": True,
                "facts_count": 0,
                "comparables_count": 0,
                "valuation_approaches_count": 0,
                "facts": {},
                "comparables": [],
                "valuation_values": {},
                "valuation_approaches": [],
                "warnings": [],
                "blocking_failures": [],
                "artifacts_count": 0,
            }
            history = [
                {"role": "user", "content": "Première question"},
                {"role": "assistant", "content": "Première réponse"},
            ]
            api.llm_assistant_answer("Deuxième question", "data-facts", context, history=history)

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs.args[0] if call_kwargs.args else []
        if not messages:
            messages = call_kwargs[1].get("messages", call_kwargs[0][0] if call_kwargs[0] else [])

        roles = [m["role"] for m in messages]
        assert roles[0] == "system"
        # history turns appear after system
        assert {"role": "user", "content": "Première question"} in messages
        assert {"role": "assistant", "content": "Première réponse"} in messages
        # last message is the current user question
        assert messages[-1]["role"] == "user"
        assert "Deuxième question" in messages[-1]["content"]

        api.SESSIONS_DIR = original_sessions

    def test_no_history_sends_two_messages(self, tmp_path):
        original_sessions = api.SESSIONS_DIR
        api.SESSIONS_DIR = tmp_path

        mock_client = self._make_mock_client()

        with patch("api._llm_client", return_value=mock_client):
            context = {
                "session_id": "test-sess2",
                "dossier_id": "D-001",
                "runtime_status": "COMPLETE",
                "review_decision": "A_VALIDER",
                "package_status": "ABSENT",
                "integrity_ok": True,
                "facts_count": 0,
                "comparables_count": 0,
                "valuation_approaches_count": 0,
                "facts": {},
                "comparables": [],
                "valuation_values": {},
                "valuation_approaches": [],
                "warnings": [],
                "blocking_failures": [],
                "artifacts_count": 0,
            }
            api.llm_assistant_answer("Question unique", "data-facts", context, history=None)

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages", [])
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        # Only system + user (no history in between adds nothing)
        assert len(messages) == 2

        api.SESSIONS_DIR = original_sessions


# ── _generate_pdf ─────────────────────────────────────────────────────────────

class TestGeneratePdf:
    def test_generates_valid_pdf_bytes(self):
        try:
            import fitz  # type: ignore
        except ImportError:
            pytest.skip("PyMuPDF not installed")
        from engine.report_export import _generate_pdf

        md = "# Rapport\n\nConclusion proposée : **450 000 $**\n\n## Section 2\n\nTexte."
        data = _generate_pdf(md, "D-TEST-001")

        assert isinstance(data, bytes)
        assert len(data) > 100
        # PDF magic bytes
        assert data[:4] == b"%PDF"
