# State — eval-immo

_Updated: 2026-05-31 | HEAD: 5250204 (master)_

## Current Goal

Exécuter waves A–D (items immédiats + moyen terme post-P0–P6).

## Plan Status

### Wave A — Légal + observabilité
- [ ] A1  T0.6 Loi 25 : masquage PII SIRF + doc politique
- [ ] A2  T5.5 Observabilité : /bureau/metrics + composant usage
- [ ] A3  T5.6 SCALE-MIGRATION.md

### Wave B — Validation + profil É.A.
- [ ] B1  T3.6 Fixture anonymisée : pipeline complet chrono
- [ ] B2  Profil É.A. : n° permis OEAQ depuis profiles → SignatureForm
- [ ] B3  T2.2 : tags @deprecated compute-*.ts + doc mapping

### Wave C — Frontend bureau
- [ ] C1  Page /bureau/dashboard
- [ ] C2  apicore/llm.py extraction

### Wave D — Approche coût sans Altus
- [ ] D1  allow_default_cost_reference résidentiel + DBI MEFQ
- [ ] D2  UI saisie manuelle coûts É.A.

## Evidence

- Migrations 001–008 Supabase prod 2026-05-31
- RAG : 8745 chunks, threshold 0.35, retrieval OK
- Altus non disponible → repli MEFQ + saisie manuelle (Wave D)
