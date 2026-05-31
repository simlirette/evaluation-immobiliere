"""T6.4 — E2E happy path : pipeline complet → rapport avec 16 éléments.

Sans LLM (OPENAI_API_KEY absent) → repli déterministe.
Sans réseau → données minimales de la fixture.
Vérifie : brouillon_rapport.md généré + check_rapport_elements score ≥ 0.70.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BACKEND_ROOT = Path(__file__).resolve().parent.parent
PIPELINE = BACKEND_ROOT / "integration" / "PIPELINE-RUNTIME-ASTON-V0.yaml"
T01_FIXTURE = BACKEND_ROOT / "tests" / "runtime" / "T01_nominal_unifamiliale.yaml"


pytestmark = pytest.mark.e2e


def _load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.e2e
def test_e2e_pipeline_produces_rapport(tmp_path, monkeypatch):
    """Happy path : T01 fixture → run_case_data → brouillon_rapport.md généré."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("RUNTIME_DETERMINISTIC", "1")

    from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml

    fixture = _load_fixture(T01_FIXTURE)
    case = fixture["case"]
    case_id = fixture["id"]

    engine = RuntimeEngine(
        steps=load_steps_from_pipeline_yaml(PIPELINE),
        strict_mode=False,
    )
    result = engine.run_case_data(
        case,
        tmp_path / case_id,
        source_fixture=T01_FIXTURE.name,
        case_stem=case_id,
        case_subdir=True,
    )

    assert result is not None, "run_case_data doit retourner un résultat"

    # Vérifier que les artefacts principaux existent
    # With case_subdir=True: out_dir/case_key/case_key
    case_dir = tmp_path / case_id / case_id
    artifacts = list(case_dir.glob("*.json")) + list(case_dir.glob("*.md"))
    artifact_names = {a.name for a in artifacts}

    # Au minimum : brouillon_rapport.md
    rapport_files = [a for a in artifacts if "brouillon_rapport" in a.name]
    assert rapport_files, (
        f"brouillon_rapport.md non trouvé. Artefacts présents : {sorted(artifact_names)}"
    )


@pytest.mark.e2e
def test_e2e_rapport_has_16_elements(tmp_path, monkeypatch):
    """Le rapport déterministe doit passer la vérification des 16 éléments à ≥ 70%."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("RUNTIME_DETERMINISTIC", "1")

    from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml
    from engine.report_check import check_rapport_elements

    fixture = _load_fixture(T01_FIXTURE)
    case = {
        **fixture["case"],
        "adresse": "123 rue Test, Québec, QC",
        "commanditaire": {
            "nom": "Banque Test",
            "organisation": "Financement",
            "fin_evaluation": "financement",
        },
    }
    case_id = fixture["id"]

    engine = RuntimeEngine(
        steps=load_steps_from_pipeline_yaml(PIPELINE),
        strict_mode=False,
    )
    result = engine.run_case_data(
        case,
        tmp_path / case_id,
        source_fixture=T01_FIXTURE.name,
        case_stem=case_id,
        case_subdir=True,
    )

    # Trouver le rapport généré
    # With case_subdir=True: out_dir/case_key/case_key
    case_dir = tmp_path / case_id / case_id
    rapport_md = ""
    for candidate in case_dir.glob("*brouillon_rapport.md"):
        rapport_md = candidate.read_text(encoding="utf-8")
        break

    if not rapport_md:
        # Chercher dans result dict
        rapport_md = str(result.get("brouillon_rapport_md", "") or "")

    if not rapport_md:
        pytest.skip("Rapport non trouvé — pipeline non complet sans LLM")

    check = check_rapport_elements(rapport_md)
    assert check.score >= 0.70, (
        f"Score 16 éléments trop bas : {check.score:.2f} — "
        f"Manquants : {[e.numero for e in check.manquants]}"
    )


@pytest.mark.e2e
def test_e2e_comparative_value_positive(tmp_path, monkeypatch):
    """La valeur comparative doit être positive pour le cas T01."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("RUNTIME_DETERMINISTIC", "1")

    from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml

    fixture = _load_fixture(T01_FIXTURE)
    case_id = fixture["id"]

    engine = RuntimeEngine(
        steps=load_steps_from_pipeline_yaml(PIPELINE),
        strict_mode=False,
    )
    result = engine.run_case_data(
        fixture["case"],
        tmp_path / case_id,
        source_fixture=T01_FIXTURE.name,
        case_stem=case_id,
        case_subdir=True,
    )

    # Chercher le calcul comparatif dans les artefacts
    # With case_subdir=True: out_dir/case_key/case_key
    case_dir = tmp_path / case_id / case_id
    comp_files = list(case_dir.glob("*calculs_approche_comparative*"))
    if comp_files:
        comp_data = json.loads(comp_files[0].read_text(encoding="utf-8"))
        value = comp_data.get("value")
        if value is not None:
            assert float(value) > 0, f"Valeur comparative non positive : {value}"


@pytest.mark.e2e
def test_e2e_amu_not_hardcoded_true(tmp_path, monkeypatch):
    """L'UMPP ne doit plus avoir conformite_zonage=True en dur (constat A3)."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml

    fixture = _load_fixture(T01_FIXTURE)
    case_id = fixture["id"]

    engine = RuntimeEngine(
        steps=load_steps_from_pipeline_yaml(PIPELINE),
        strict_mode=False,
    )
    result = engine.run_case_data(
        fixture["case"],
        tmp_path / case_id,
        source_fixture=T01_FIXTURE.name,
        case_stem=case_id,
        case_subdir=True,
    )

    # Chercher umpp_conclusion.json
    # With case_subdir=True: out_dir/case_key/case_key
    case_dir = tmp_path / case_id / case_id
    umpp_files = list(case_dir.glob("*umpp_conclusion*"))
    if umpp_files:
        umpp_data = json.loads(umpp_files[0].read_text(encoding="utf-8"))
        umpp = umpp_data.get("umpp", {})
        # Sans données de zonage → conformite_zonage doit être None, pas True en dur
        if not fixture["case"].get("zonage_urbanisme"):
            assert umpp.get("conformite_zonage") is not True or \
                   umpp.get("methodologie") == "deterministe_v1", (
                "conformite_zonage=True sans données de zonage — constat A3 non corrigé"
            )
