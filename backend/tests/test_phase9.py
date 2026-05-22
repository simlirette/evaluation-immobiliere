"""Tests Phase 9 — engine/package.py: generate_package_from_case."""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.package import (
    PACKAGE_FILES,
    _collect_artifact_paths,
    _find_rapport_md,
    generate_package_from_case,
)


# ── _find_rapport_md ──────────────────────────────────────────────────────────

class TestFindRapportMd:
    def test_no_session_dir(self):
        text, path = _find_rapport_md({})
        assert text == ""
        assert path is None

    def test_missing_artifact_index(self, tmp_path):
        session = {"session_dir": str(tmp_path)}
        text, path = _find_rapport_md(session)
        assert text == ""
        assert path is None

    def test_empty_events(self, tmp_path):
        (tmp_path / "artifact_index.json").write_text(
            json.dumps({"events": []}), encoding="utf-8"
        )
        text, path = _find_rapport_md({"session_dir": str(tmp_path)})
        assert text == ""
        assert path is None

    def test_finds_rapport_md(self, tmp_path):
        md_file = tmp_path / "brouillon_rapport.md"
        md_file.write_text("# Rapport test", encoding="utf-8")
        index = {
            "events": [
                {
                    "artifacts": [
                        {"artifact": "brouillon_rapport.md", "path": str(md_file)}
                    ]
                }
            ]
        }
        (tmp_path / "artifact_index.json").write_text(
            json.dumps(index), encoding="utf-8"
        )
        text, path = _find_rapport_md({"session_dir": str(tmp_path)})
        assert text == "# Rapport test"
        assert path == md_file

    def test_artifact_path_missing_on_disk(self, tmp_path):
        index = {
            "events": [
                {
                    "artifacts": [
                        {
                            "artifact": "brouillon_rapport.md",
                            "path": str(tmp_path / "nonexistent.md"),
                        }
                    ]
                }
            ]
        }
        (tmp_path / "artifact_index.json").write_text(
            json.dumps(index), encoding="utf-8"
        )
        text, path = _find_rapport_md({"session_dir": str(tmp_path)})
        assert text == ""
        assert path is None


# ── _collect_artifact_paths ───────────────────────────────────────────────────

class TestCollectArtifactPaths:
    def test_no_artifact_dir(self):
        result = _collect_artifact_paths({})
        assert result == []

    def test_missing_dir(self, tmp_path):
        result = _collect_artifact_paths({"artifact_dir": str(tmp_path / "nonexistent")})
        assert result == []

    def test_collects_present_files(self, tmp_path):
        agent_dir = tmp_path / "data-facts"
        agent_dir.mkdir()
        (agent_dir / "fiche_bien.json").write_text('{"ok":true}', encoding="utf-8")
        result = _collect_artifact_paths({"artifact_dir": str(tmp_path)})
        names = [name for name, _ in result]
        assert "fiche_bien.json" in names

    def test_skips_missing_artifacts(self, tmp_path):
        # Only data-facts present, others absent
        agent_dir = tmp_path / "data-facts"
        agent_dir.mkdir()
        (agent_dir / "fiche_bien.json").write_text("{}", encoding="utf-8")
        result = _collect_artifact_paths({"artifact_dir": str(tmp_path)})
        assert len(result) == 1


# ── generate_package_from_case ────────────────────────────────────────────────

class TestGeneratePackageFromCase:
    def _minimal_case(self, tmp_path) -> dict:
        return {
            "dossier_id": "D-TEST-0001",
            "artifact_dir": str(tmp_path / "artifacts"),
        }

    def _minimal_session(self, tmp_path) -> dict:
        return {
            "session_id": "sess-test",
            "session_dir": str(tmp_path),
            "dossier_id": "D-TEST-0001",
        }

    def test_creates_manifest_and_zip_no_rapport(self, tmp_path):
        case = self._minimal_case(tmp_path)
        session = self._minimal_session(tmp_path)
        out_dir = tmp_path / "pkg"

        with patch("engine.report_export._generate_pdf", side_effect=RuntimeError("no pdf")):
            result = generate_package_from_case(
                case=case,
                out_dir=out_dir,
                session=session,
                review={"decision": "VALIDE", "reviewer": "test"},
                integrity={"ok": True},
            )

        assert result["status"] == "PRET_REVUE_EVALUATEUR_AGREE"
        assert result["dossier_id"] == "D-TEST-0001"
        assert (out_dir / PACKAGE_FILES["manifest"]).exists()
        assert (out_dir / PACKAGE_FILES["zip"]).exists()

    def test_zip_contains_manifest(self, tmp_path):
        case = self._minimal_case(tmp_path)
        session = self._minimal_session(tmp_path)
        out_dir = tmp_path / "pkg"

        with patch("engine.report_export._generate_pdf", side_effect=RuntimeError):
            generate_package_from_case(
                case=case,
                out_dir=out_dir,
                session=session,
                review={},
                integrity={"ok": False},
            )

        with zipfile.ZipFile(out_dir / PACKAGE_FILES["zip"]) as zf:
            names = zf.namelist()
        assert PACKAGE_FILES["manifest"] in names

    def test_with_rapport_md(self, tmp_path):
        md_file = tmp_path / "brouillon_rapport.md"
        md_file.write_text("# Mon rapport", encoding="utf-8")
        index = {
            "events": [
                {"artifacts": [{"artifact": "brouillon_rapport.md", "path": str(md_file)}]}
            ]
        }
        (tmp_path / "artifact_index.json").write_text(json.dumps(index), encoding="utf-8")

        case = self._minimal_case(tmp_path)
        session = self._minimal_session(tmp_path)
        out_dir = tmp_path / "pkg"

        with patch("engine.report_export._generate_pdf", return_value=b"%PDF-fake"):
            result = generate_package_from_case(
                case=case,
                out_dir=out_dir,
                session=session,
                review={"decision": "VALIDE"},
                integrity={"ok": True},
            )

        assert (out_dir / PACKAGE_FILES["rapport_md"]).exists()
        assert (out_dir / PACKAGE_FILES["rapport_pdf"]).exists()
        file_names = [f["name"] for f in result["files"]]
        assert PACKAGE_FILES["rapport_md"] in file_names
        assert PACKAGE_FILES["rapport_pdf"] in file_names

    def test_pdf_failure_is_best_effort(self, tmp_path):
        md_file = tmp_path / "brouillon_rapport.md"
        md_file.write_text("# Rapport", encoding="utf-8")
        index = {
            "events": [
                {"artifacts": [{"artifact": "brouillon_rapport.md", "path": str(md_file)}]}
            ]
        }
        (tmp_path / "artifact_index.json").write_text(json.dumps(index), encoding="utf-8")

        case = self._minimal_case(tmp_path)
        session = self._minimal_session(tmp_path)
        out_dir = tmp_path / "pkg"

        # PDF fails — should not raise
        with patch("engine.report_export._generate_pdf", side_effect=RuntimeError("pdf crash")):
            result = generate_package_from_case(
                case=case,
                out_dir=out_dir,
                session=session,
                review={},
                integrity={"ok": True},
            )

        assert result["status"] == "PRET_REVUE_EVALUATEUR_AGREE"
        # rapport_md present, rapport_pdf absent (best-effort)
        file_names = [f["name"] for f in result["files"]]
        assert PACKAGE_FILES["rapport_md"] in file_names
        assert PACKAGE_FILES["rapport_pdf"] not in file_names

    def test_manifest_content(self, tmp_path):
        case = self._minimal_case(tmp_path)
        session = self._minimal_session(tmp_path)
        out_dir = tmp_path / "pkg"

        with patch("engine.report_export._generate_pdf", side_effect=RuntimeError):
            generate_package_from_case(
                case=case,
                out_dir=out_dir,
                session=session,
                review={"decision": "VALIDE", "reviewer": "évaluateur-1"},
                integrity={"ok": True},
            )

        manifest = json.loads((out_dir / PACKAGE_FILES["manifest"]).read_text())
        assert manifest["schema_version"] == "package_v1"
        assert manifest["dossier_id"] == "D-TEST-0001"
        assert manifest["review"]["decision"] == "VALIDE"
        assert manifest["integrity_ok"] is True
        assert manifest["status"] == "PRET_REVUE_EVALUATEUR_AGREE"

    def test_with_key_artifacts(self, tmp_path):
        artifact_dir = tmp_path / "artifacts" / "data-facts"
        artifact_dir.mkdir(parents=True)
        (artifact_dir / "fiche_bien.json").write_text('{"surface":120}', encoding="utf-8")

        case = self._minimal_case(tmp_path)
        session = self._minimal_session(tmp_path)
        out_dir = tmp_path / "pkg"

        with patch("engine.report_export._generate_pdf", side_effect=RuntimeError):
            result = generate_package_from_case(
                case=case,
                out_dir=out_dir,
                session=session,
                review={},
                integrity={"ok": True},
            )

        file_names = [f["name"] for f in result["files"]]
        assert "fiche_bien.json" in file_names
        with zipfile.ZipFile(out_dir / PACKAGE_FILES["zip"]) as zf:
            assert "fiche_bien.json" in zf.namelist()
