-- Migration 006 — Knowledge embeddings (RAG normatif pgvector)
-- Prérequis : extension pgvector activée sur le projet Supabase

create extension if not exists vector;

create table if not exists public.knowledge_chunks (
    id              bigserial primary key,
    source_id       text        not null,   -- ex. "04-oeaq-normes-pratique_npp-24-mars-2025"
    folder          text        not null,   -- ex. "04-oeaq-normes-pratique"
    domain          text        not null,   -- ex. "oeaq_professional_standards"
    source_family   text        not null default '',
    chunk_index     integer     not null,   -- ordre dans le document source
    chunk_text      text        not null,   -- texte brut du chunk (~1000-1500 tokens)
    heading         text        not null default '', -- titre de section le plus proche
    embedding       vector(1536),           -- text-embedding-3-small
    char_count      integer     not null default 0,
    indexed_at      timestamptz not null default now()
);

-- Index ivfflat pour la recherche ANN (à ajuster selon volume)
create index if not exists knowledge_chunks_embedding_idx
    on public.knowledge_chunks
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- Index par source pour les lookups
create index if not exists knowledge_chunks_source_idx
    on public.knowledge_chunks (source_id);

-- RLS : lecture publique (service key pour écriture)
alter table public.knowledge_chunks enable row level security;

create policy "knowledge_chunks_read_all"
    on public.knowledge_chunks for select
    using (true);

-- Fonction de recherche vectorielle
create or replace function public.match_knowledge_chunks(
    query_embedding vector(1536),
    match_threshold float default 0.70,
    match_count     int   default 5,
    filter_domain   text  default null
)
returns table (
    id              bigint,
    source_id       text,
    folder          text,
    domain          text,
    source_family   text,
    chunk_index     int,
    chunk_text      text,
    heading         text,
    similarity      float
)
language sql stable
as $$
    select
        kc.id,
        kc.source_id,
        kc.folder,
        kc.domain,
        kc.source_family,
        kc.chunk_index,
        kc.chunk_text,
        kc.heading,
        1 - (kc.embedding <=> query_embedding) as similarity
    from public.knowledge_chunks kc
    where
        (filter_domain is null or kc.domain = filter_domain)
        and 1 - (kc.embedding <=> query_embedding) > match_threshold
    order by kc.embedding <=> query_embedding
    limit match_count;
$$;
