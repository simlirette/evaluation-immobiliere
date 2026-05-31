"""T1.3 — Tests RAG normatif (chunking + dégradé sans Supabase).

Ne requiert pas de clé OpenAI ni Supabase pour passer en CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.knowledge_rag import (
    Chunk,
    chunk_document,
    chunk_corpus,
    load_catalog,
    retrieve_context,
    CORPUS_DIR,
)


# ── Chunking ──────────────────────────────────────────────────────────────────

_SAMPLE_MD = """# Section principale

Premier paragraphe avec du contenu normatif. Règles de l'OEAQ applicables.
Deuxième ligne du paragraphe principal.

Deuxième paragraphe du même document.

## Sous-section 2.1

Contenu spécifique à la sous-section. Critère A et critère B.

## Sous-section 2.2

Autre critère, autre contenu. Jurisprudence applicable.
"""


def test_chunk_document_basic():
    chunks = chunk_document(
        _SAMPLE_MD,
        source_id="test_source",
        folder="04-oeaq",
        domain="oeaq_professional_standards",
        source_family="NPP OEAQ",
    )
    assert len(chunks) >= 1
    # Every chunk has required fields
    for c in chunks:
        assert c.source_id == "test_source"
        assert c.domain == "oeaq_professional_standards"
        assert c.chunk_text.strip()
        assert c.char_count > 0


def test_chunk_document_headings_preserved():
    chunks = chunk_document(
        _SAMPLE_MD,
        source_id="test",
        folder="04",
        domain="oeaq_professional_standards",
        source_family="Test",
    )
    headings = [c.heading for c in chunks]
    assert any("Section principale" in h or "Sous-section" in h for h in headings)


def test_chunk_large_document():
    """Un document de 15 000 chars doit produire plusieurs chunks."""
    big_text = "## Règle importante\n\n" + ("Texte normatif pertinent. " * 100 + "\n\n") * 20
    chunks = chunk_document(
        big_text,
        source_id="big_doc",
        folder="01",
        domain="municipal_assessment_manual",
        source_family="MEFQ",
    )
    assert len(chunks) >= 2
    for c in chunks:
        assert c.char_count <= 3500  # Max chunk + overlap


def test_chunk_indices_sequential():
    big_text = "## Sec\n\n" + ("Contenu. " * 200 + "\n\n") * 5
    chunks = chunk_document(big_text, "id", "f", "d", "fam")
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


# ── Corpus ────────────────────────────────────────────────────────────────────

def test_load_catalog():
    catalog = load_catalog()
    assert len(catalog) >= 60, f"Catalogue trop court : {len(catalog)} entrées"
    # Chaque entrée a les champs requis
    for e in catalog:
        assert "source_id" in e
        assert "relative_path" in e
        assert "domain" in e


def test_corpus_files_exist():
    catalog = load_catalog()
    missing = []
    for e in catalog:
        p = CORPUS_DIR / e["relative_path"]
        if not p.exists():
            missing.append(e["relative_path"])
    assert not missing, f"Fichiers manquants : {missing[:5]}"


def test_chunk_corpus_returns_chunks():
    """chunk_corpus doit retourner des chunks pour au moins les fichiers clés."""
    chunks = chunk_corpus()
    assert len(chunks) >= 100, f"Trop peu de chunks : {len(chunks)}"
    source_ids = {c.source_id for c in chunks}
    # NPP doit être présent
    assert any("npp" in sid or "04" in sid for sid in source_ids), (
        f"NPP absent des chunks. IDs trouvés : {sorted(source_ids)[:10]}"
    )


def test_chunk_corpus_no_empty_chunks():
    chunks = chunk_corpus()
    empty = [c for c in chunks if not c.chunk_text.strip()]
    assert not empty, f"{len(empty)} chunks vides trouvés"


# ── Dégradé (sans Supabase) ───────────────────────────────────────────────────

def test_retrieve_context_graceful_without_config(monkeypatch):
    """Sans SUPABASE_URL/OPENAI_API_KEY, retrieve_context retourne '' sans exception."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = retrieve_context("Quelle est la règle MEFQ pour l'AMU ?")
    assert result == ""


def test_retrieve_context_graceful_partial_config(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = retrieve_context("NPP OEAQ §8")
    assert result == ""
