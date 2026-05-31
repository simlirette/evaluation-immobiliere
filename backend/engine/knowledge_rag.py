"""engine/knowledge_rag.py — RAG normatif sur corpus knowledge/corpus/.

Flux :
  1. chunk_document(text, source_id, ...) → list[Chunk]
  2. index_corpus(supabase_client, openai_client) → insère les chunks dans knowledge_chunks
  3. retrieve(query, top_k, ...) → list[KnowledgeChunk] depuis Supabase match_knowledge_chunks

Utilisé par runtime.py (agents recherche-* et redaction) et api.py (search_knowledge).
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR   = PROJECT_ROOT / "knowledge" / "corpus"
CATALOG_PATH = PROJECT_ROOT / "knowledge" / "source-catalog.json"

# Chunking parameters
_CHUNK_TARGET_CHARS = 3000   # ~750 tokens (text-embedding-3-small max = 8191 tokens)
_CHUNK_OVERLAP_CHARS = 300
_EMBED_MODEL = "text-embedding-3-small"
_EMBED_DIM   = 1536


@dataclass
class Chunk:
    source_id:     str
    folder:        str
    domain:        str
    source_family: str
    chunk_index:   int
    chunk_text:    str
    heading:       str
    char_count:    int


@dataclass
class KnowledgeChunk:
    id:            int
    source_id:     str
    folder:        str
    domain:        str
    source_family: str
    chunk_index:   int
    chunk_text:    str
    heading:       str
    similarity:    float

    def citation(self) -> str:
        """Référence courte pour injection dans les prompts."""
        parts = [self.source_family or self.source_id]
        if self.heading:
            parts.append(self.heading)
        return " — ".join(parts)


# ── Chunking ─────────────────────────────────────────────────────────────────

def _split_by_headings(text: str) -> Iterator[tuple[str, str]]:
    """Yield (heading, section_text) en découpant aux titres markdown."""
    current_heading = ""
    buf: list[str] = []
    for line in text.splitlines(keepends=True):
        if line.startswith("#"):
            if buf:
                yield current_heading, "".join(buf).strip()
            current_heading = line.strip().lstrip("#").strip()
            buf = [line]
        else:
            buf.append(line)
    if buf:
        yield current_heading, "".join(buf).strip()


def chunk_document(
    text: str,
    source_id: str,
    folder: str,
    domain: str,
    source_family: str,
) -> list[Chunk]:
    """Découpe un document en chunks ~3000 chars avec chevauchement."""
    chunks: list[Chunk] = []
    idx = 0

    for heading, section in _split_by_headings(text):
        if not section.strip():
            continue
        # Si la section tient dans un chunk, on la garde entière
        if len(section) <= _CHUNK_TARGET_CHARS:
            chunks.append(Chunk(
                source_id=source_id,
                folder=folder,
                domain=domain,
                source_family=source_family,
                chunk_index=idx,
                chunk_text=section,
                heading=heading,
                char_count=len(section),
            ))
            idx += 1
            continue

        # Sinon, découper par paragraphes avec chevauchement
        paragraphs = re.split(r"\n{2,}", section)
        buf = ""
        for para in paragraphs:
            if not para.strip():
                continue
            if len(buf) + len(para) > _CHUNK_TARGET_CHARS and buf:
                chunks.append(Chunk(
                    source_id=source_id,
                    folder=folder,
                    domain=domain,
                    source_family=source_family,
                    chunk_index=idx,
                    chunk_text=buf.strip(),
                    heading=heading,
                    char_count=len(buf.strip()),
                ))
                idx += 1
                # Overlap: garder la fin du chunk précédent
                buf = buf[-_CHUNK_OVERLAP_CHARS:] + "\n\n" + para
            else:
                buf = (buf + "\n\n" + para).lstrip()
        if buf.strip():
            chunks.append(Chunk(
                source_id=source_id,
                folder=folder,
                domain=domain,
                source_family=source_family,
                chunk_index=idx,
                chunk_text=buf.strip(),
                heading=heading,
                char_count=len(buf.strip()),
            ))
            idx += 1

    return chunks


def load_catalog() -> list[dict]:
    if not CATALOG_PATH.exists():
        return []
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def chunk_corpus() -> list[Chunk]:
    """Charge et découpe tous les documents du corpus."""
    catalog = load_catalog()
    all_chunks: list[Chunk] = []
    for entry in catalog:
        rel = entry["relative_path"]
        md_path = CORPUS_DIR / rel
        if not md_path.exists():
            continue
        try:
            text = md_path.read_text(encoding="utf-8")
        except OSError:
            continue
        chunks = chunk_document(
            text=text,
            source_id=entry["source_id"],
            folder=entry["folder"],
            domain=entry["domain"],
            source_family=entry.get("source_family", ""),
        )
        all_chunks.extend(chunks)
    return all_chunks


# ── Indexation (écriture dans Supabase) ──────────────────────────────────────

def _embed_batch(texts: list[str], openai_client) -> list[list[float]]:
    resp = openai_client.embeddings.create(model=_EMBED_MODEL, input=texts)
    return [item.embedding for item in resp.data]


def index_corpus(
    supabase_client,
    openai_client,
    batch_size: int = 100,
    clear_first: bool = False,
) -> dict:
    """Indexe le corpus complet dans Supabase knowledge_chunks.

    Returns dict avec nb_chunks, nb_docs, cost_estimate.
    Idempotent si clear_first=False (upsert par source_id+chunk_index).
    """
    if clear_first:
        supabase_client.table("knowledge_chunks").delete().neq("id", 0).execute()

    chunks = chunk_corpus()
    inserted = 0
    total_tokens_est = sum(c.char_count // 4 for c in chunks)

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c.chunk_text for c in batch]
        embeddings = _embed_batch(texts, openai_client)

        rows = [
            {
                "source_id":     c.source_id,
                "folder":        c.folder,
                "domain":        c.domain,
                "source_family": c.source_family,
                "chunk_index":   c.chunk_index,
                "chunk_text":    c.chunk_text,
                "heading":       c.heading,
                "embedding":     emb,
                "char_count":    c.char_count,
            }
            for c, emb in zip(batch, embeddings)
        ]
        supabase_client.table("knowledge_chunks").upsert(rows).execute()
        inserted += len(batch)

    docs = len({c.source_id for c in chunks})
    # text-embedding-3-small: $0.02 / 1M tokens
    cost_usd = total_tokens_est / 1_000_000 * 0.02

    return {
        "nb_chunks": inserted,
        "nb_docs": docs,
        "tokens_estimate": total_tokens_est,
        "cost_estimate_usd": round(cost_usd, 4),
    }


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(
    query: str,
    supabase_client,
    openai_client,
    top_k: int = 5,
    threshold: float = 0.35,  # calibré 2026-05-31 : corpus pypdf, scores typiques 0.28-0.55
    domain: str | None = None,
) -> list[KnowledgeChunk]:
    """Recherche sémantique dans knowledge_chunks.

    Args:
        query: question ou extrait de contexte à chercher
        top_k: nombre de chunks à retourner
        threshold: similarité cosine minimale (0–1)
        domain: filtrer par domaine (ex. "oeaq_professional_standards")

    Returns:
        Liste de KnowledgeChunk triés par similarité décroissante.
    """
    if not query.strip():
        return []

    resp = openai_client.embeddings.create(model=_EMBED_MODEL, input=[query])
    query_embedding = resp.data[0].embedding

    rpc_resp = supabase_client.rpc(
        "match_knowledge_chunks",
        {
            "query_embedding": query_embedding,
            "match_threshold": threshold,
            "match_count": top_k,
            "filter_domain": domain,
        },
    ).execute()

    return [
        KnowledgeChunk(
            id=row["id"],
            source_id=row["source_id"],
            folder=row["folder"],
            domain=row["domain"],
            source_family=row["source_family"],
            chunk_index=row["chunk_index"],
            chunk_text=row["chunk_text"],
            heading=row["heading"],
            similarity=row["similarity"],
        )
        for row in (rpc_resp.data or [])
    ]


def retrieve_for_prompt(
    query: str,
    supabase_client,
    openai_client,
    top_k: int = 3,
    max_chars: int = 2000,
    domain: str | None = None,
) -> str:
    """Retrieval formaté pour injection directe dans un prompt LLM.

    Retourne une chaîne vide si Supabase/OpenAI indisponibles (dégradé silencieux).
    """
    try:
        chunks = retrieve(query, supabase_client, openai_client, top_k=top_k, domain=domain)
    except Exception:
        return ""

    if not chunks:
        return ""

    parts: list[str] = []
    used = 0
    for c in chunks:
        block = f"[{c.citation()} — similarité {c.similarity:.2f}]\n{c.chunk_text}"
        if used + len(block) > max_chars:
            remaining = max_chars - used
            if remaining > 200:
                parts.append(block[:remaining] + "…")
            break
        parts.append(block)
        used += len(block)

    return "\n\n---\n".join(parts)


# ── Helpers pour runtime/api ──────────────────────────────────────────────────

def _get_clients() -> tuple | tuple[None, None]:
    """Retourne (supabase_client, openai_client) si configurés, sinon (None, None)."""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not (url and key and api_key):
        return None, None
    try:
        from supabase import create_client  # type: ignore
        import openai as _openai  # type: ignore
        sb = create_client(url, key)
        oa = _openai.OpenAI(api_key=api_key)
        return sb, oa
    except Exception:
        return None, None


def retrieve_context(query: str, top_k: int = 3, domain: str | None = None) -> str:
    """Point d'entrée haut-niveau : retourne str vide si non configuré."""
    sb, oa = _get_clients()
    if sb is None or oa is None:
        return ""
    return retrieve_for_prompt(query, sb, oa, top_k=top_k, domain=domain)
