"""Tests Phase 13C — app_valuation_trace."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api


# ── helpers ───────────────────────────────────────────────────────────────────

def _patch_sessions(tmp_path):
    original = api.SESSIONS_DIR
    api.SESSIONS_DIR = tmp_path
    return original


def _make_session(tmp_path, session_id):
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True)
    session = {"session_id": session_id, "session_dir": str(session_dir), "status": "CREATED"}
    (session_dir / "session.json").write_text(json.dumps(session), encoding="utf-8")
    return session_dir


def _write_artifact(session_dir: Path, step: str, filename: str, payload: dict) -> Path:
    """Write artifact file and register it in artifact_index.json."""
    artifact_file = session_dir / filename
    artifact_file.write_text(json.dumps(payload), encoding="utf-8")
    index_path = session_dir / "artifact_index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        index = {"schema_version": "artifact_index_v1", "artifacts": []}
    index["artifacts"].append({
        "step": step,
        "artifact": filename,
        "path": str(artifact_file),
    })
    index_path.write_text(json.dumps(index), encoding="utf-8")
    return artifact_file


def _comparative_payload(value=350000.0, n=3):
    return {
        "approach": "approche_comparative",
        "method": "weighted_mean_score_v0",
        "value": value,
        "input_count": n,
        "trace": {
            "base_value": 345000.0,
            "adjustment_total_validated": 5000.0,
            "weights_used": [0.5, 0.3, 0.2],
            "calculation_policy": ["Seuls les ajustements validés sont appliqués."],
            "selected_comparables": [
                {"comparable_id": "c1", "prix_vente": 340000, "score": 0.9, "date_vente": "2025-06-01", "source_id": "SRC-001"},
                {"comparable_id": "c2", "prix_vente": 355000, "score": 0.7, "date_vente": "2025-07-15", "source_id": "SRC-002"},
                {"comparable_id": "c3", "prix_vente": 360000, "score": 0.4, "date_vente": "2025-08-01", "source_id": "SRC-003"},
            ],
        },
    }


# ── no session ────────────────────────────────────────────────────────────────

class TestAppValuationTraceNoSession:
    def test_missing_session_id_raises(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            with pytest.raises(ValueError, match="session_id"):
                api.app_valuation_trace("")
        finally:
            api.SESSIONS_DIR = original

    def test_nonexistent_session_raises(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            with pytest.raises(ValueError, match="introuvable"):
                api.app_valuation_trace("ghost-session")
        finally:
            api.SESSIONS_DIR = original


# ── no artifacts ──────────────────────────────────────────────────────────────

class TestAppValuationTraceNoArtifacts:
    def test_empty_approaches_when_no_artifacts(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            _make_session(tmp_path, "s-empty")
            result = api.app_valuation_trace("s-empty")
            assert result["session_id"] == "s-empty"
            assert result["approaches"] == []
            assert result["hypotheses"] == []
        finally:
            api.SESSIONS_DIR = original

    def test_empty_hypotheses_when_file_absent(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-nohyp")
            _write_artifact(session_dir, "valuation-draft", "calculs_approche_comparative.json", _comparative_payload())
            result = api.app_valuation_trace("s-nohyp")
            assert result["hypotheses"] == []
        finally:
            api.SESSIONS_DIR = original


# ── full trace — single approach ──────────────────────────────────────────────

class TestAppValuationTraceSingleApproach:
    def test_approach_fields_returned(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-single")
            _write_artifact(session_dir, "valuation-draft", "calculs_approche_comparative.json", _comparative_payload())
            result = api.app_valuation_trace("s-single")
            assert len(result["approaches"]) == 1
            a = result["approaches"][0]
            assert a["approach"] == "approche_comparative"
            assert a["label"] == "Approche comparative"
            assert a["method"] == "weighted_mean_score_v0"
            assert a["value"] == 350000.0
            assert a["input_count"] == 3
        finally:
            api.SESSIONS_DIR = original

    def test_trace_fields_extracted(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-trace")
            _write_artifact(session_dir, "valuation-draft", "calculs_approche_comparative.json", _comparative_payload())
            result = api.app_valuation_trace("s-trace")
            a = result["approaches"][0]
            assert a["base_value"] == 345000.0
            assert a["adjustment_total"] == 5000.0
            assert a["weights"] == [0.5, 0.3, 0.2]
            assert len(a["policy"]) == 1
        finally:
            api.SESSIONS_DIR = original

    def test_selected_comparables_extracted(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-comps")
            _write_artifact(session_dir, "valuation-draft", "calculs_approche_comparative.json", _comparative_payload())
            result = api.app_valuation_trace("s-comps")
            comps = result["approaches"][0]["selected_comparables"]
            assert len(comps) == 3
            assert comps[0]["comparable_id"] == "c1"
            assert comps[0]["prix_vente"] == 340000
            assert comps[0]["score"] == 0.9
            assert comps[0]["source_id"] == "SRC-001"
        finally:
            api.SESSIONS_DIR = original


# ── full trace — all 3 approaches ────────────────────────────────────────────

class TestAppValuationTraceAllApproaches:
    def _setup(self, tmp_path, session_id):
        session_dir = _make_session(tmp_path, session_id)
        _write_artifact(session_dir, "valuation-draft", "calculs_approche_comparative.json", {
            "approach": "approche_comparative", "method": "weighted_mean_score_v0",
            "value": 350000.0, "input_count": 3, "trace": {"base_value": 345000.0, "adjustment_total_validated": 5000.0, "weights_used": [0.5, 0.3, 0.2], "calculation_policy": ["Policy A"], "selected_comparables": []},
        })
        _write_artifact(session_dir, "valuation-draft", "calculs_approche_cout.json", {
            "approach": "approche_cout", "method": "proxy_mean_cost_v0",
            "value": 360000.0, "input_count": 3, "trace": {"base_value": 360000.0, "adjustment_total_validated": 0.0, "weights_used": [], "calculation_policy": ["Policy B"], "selected_comparables": []},
        })
        _write_artifact(session_dir, "valuation-draft", "calculs_approche_revenu.json", {
            "approach": "approche_revenu", "method": "proxy_median_income_v0",
            "value": 340000.0, "input_count": 3, "trace": {"base_value": 340000.0, "adjustment_total_validated": 0.0, "weights_used": [], "calculation_policy": ["Policy C"], "selected_comparables": []},
        })
        return session_dir

    def test_three_approaches_returned(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            self._setup(tmp_path, "s-all")
            result = api.app_valuation_trace("s-all")
            assert len(result["approaches"]) == 3
        finally:
            api.SESSIONS_DIR = original

    def test_approach_order_preserved(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            self._setup(tmp_path, "s-order")
            result = api.app_valuation_trace("s-order")
            ids = [a["approach"] for a in result["approaches"]]
            assert ids == ["approche_comparative", "approche_cout", "approche_revenu"]
        finally:
            api.SESSIONS_DIR = original

    def test_labels_correct_for_all(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            self._setup(tmp_path, "s-labels")
            result = api.app_valuation_trace("s-labels")
            labels = {a["approach"]: a["label"] for a in result["approaches"]}
            assert labels["approche_comparative"] == "Approche comparative"
            assert labels["approche_cout"] == "Approche coût"
            assert labels["approche_revenu"] == "Approche revenu"
        finally:
            api.SESSIONS_DIR = original


# ── partial approaches ────────────────────────────────────────────────────────

class TestAppValuationTracePartialApproaches:
    def test_missing_cout_excluded(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-partial")
            _write_artifact(session_dir, "valuation-draft", "calculs_approche_comparative.json", _comparative_payload())
            # cout absent, revenu present
            _write_artifact(session_dir, "valuation-draft", "calculs_approche_revenu.json", {
                "approach": "approche_revenu", "method": "proxy_median_income_v0",
                "value": 340000.0, "input_count": 2, "trace": {},
            })
            result = api.app_valuation_trace("s-partial")
            ids = [a["approach"] for a in result["approaches"]]
            assert "approche_comparative" in ids
            assert "approche_revenu" in ids
            assert "approche_cout" not in ids
        finally:
            api.SESSIONS_DIR = original

    def test_missing_trace_dict_handled(self, tmp_path):
        """Artifact present but trace key missing — should not crash."""
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-notrace")
            _write_artifact(session_dir, "valuation-draft", "calculs_approche_comparative.json", {
                "approach": "approche_comparative", "method": "weighted_mean_score_v0",
                "value": 300000.0, "input_count": 2,
                # no "trace" key
            })
            result = api.app_valuation_trace("s-notrace")
            a = result["approaches"][0]
            assert a["base_value"] is None
            assert a["adjustment_total"] is None
            assert a["weights"] == []
            assert a["policy"] == []
            assert a["selected_comparables"] == []
        finally:
            api.SESSIONS_DIR = original

    def test_null_trace_value_handled(self, tmp_path):
        """trace key present but value is null — should not crash."""
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-nulltrace")
            _write_artifact(session_dir, "valuation-draft", "calculs_approche_comparative.json", {
                "approach": "approche_comparative", "method": "wm",
                "value": 310000.0, "input_count": 1, "trace": None,
            })
            result = api.app_valuation_trace("s-nulltrace")
            a = result["approaches"][0]
            assert a["weights"] == []
            assert a["selected_comparables"] == []
        finally:
            api.SESSIONS_DIR = original


# ── hypotheses ────────────────────────────────────────────────────────────────

class TestAppValuationTraceHypotheses:
    def test_hypotheses_returned(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-hyp")
            _write_artifact(session_dir, "valuation-draft", "hypotheses_explicites.json", {
                "hypotheses": [
                    {"hypothese": "Marché stable sur 12 mois"},
                    {"hypothese": "Aucune servitude connue"},
                ]
            })
            result = api.app_valuation_trace("s-hyp")
            assert len(result["hypotheses"]) == 2
            assert result["hypotheses"][0]["hypothese"] == "Marché stable sur 12 mois"
        finally:
            api.SESSIONS_DIR = original

    def test_hypotheses_empty_list_when_key_missing(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-hyp-empty")
            _write_artifact(session_dir, "valuation-draft", "hypotheses_explicites.json", {
                "other_key": "something"
                # no "hypotheses" key
            })
            result = api.app_valuation_trace("s-hyp-empty")
            assert result["hypotheses"] == []
        finally:
            api.SESSIONS_DIR = original

    def test_hypotheses_non_list_ignored(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-hyp-bad")
            _write_artifact(session_dir, "valuation-draft", "hypotheses_explicites.json", {
                "hypotheses": "not a list"
            })
            result = api.app_valuation_trace("s-hyp-bad")
            assert result["hypotheses"] == []
        finally:
            api.SESSIONS_DIR = original


# ── comparable filtering ──────────────────────────────────────────────────────

class TestAppValuationTraceComparableFiltering:
    def test_non_dict_comparables_skipped(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-comp-filter")
            payload = _comparative_payload()
            # inject bad items
            payload["trace"]["selected_comparables"] = [
                {"comparable_id": "c1", "prix_vente": 350000, "score": 0.8, "date_vente": "2025-01-01", "source_id": "S1"},
                "not a dict",
                None,
                42,
            ]
            _write_artifact(session_dir, "valuation-draft", "calculs_approche_comparative.json", payload)
            result = api.app_valuation_trace("s-comp-filter")
            comps = result["approaches"][0]["selected_comparables"]
            assert len(comps) == 1
            assert comps[0]["comparable_id"] == "c1"
        finally:
            api.SESSIONS_DIR = original

    def test_comparable_missing_fields_default_to_empty(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            session_dir = _make_session(tmp_path, "s-comp-defaults")
            payload = _comparative_payload()
            payload["trace"]["selected_comparables"] = [{}]  # empty dict
            _write_artifact(session_dir, "valuation-draft", "calculs_approche_comparative.json", payload)
            result = api.app_valuation_trace("s-comp-defaults")
            c = result["approaches"][0]["selected_comparables"][0]
            assert c["comparable_id"] == ""
            assert c["prix_vente"] is None
            assert c["score"] is None
            assert c["date_vente"] == ""
            assert c["source_id"] == ""
        finally:
            api.SESSIONS_DIR = original
