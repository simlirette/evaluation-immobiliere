# State — eval-immo

_Updated: 2026-05-31 | HEAD: 25ae5a3 (master)_

## Current Goal

Waves A–D complètes. Système prod opérationnel.

## Plan Status

### Waves A–D ✅

- [x] A1 Loi 25 : masquage PII SIRF (vendeur_hash/acheteur_hash)
- [x] A2 T5.5 : /bureau/metrics + usage agrégé dans dashboard
- [x] A3 T5.6 : docs/SCALE-MIGRATION.md
- [x] B1 T3.6 : test E2E acceptance fixture (0.06s, score 16 éléments ≥ 0.85)
- [x] B2 : profil É.A. (no_permis_oeaq/nom_ea depuis Supabase profiles → SignatureForm)
- [x] B3 T2.2 : @display-only sur 4 compute-*.ts redondants avec Python
- [x] C1 : page /bureau/dashboard
- [x] C2 : apicore/llm.py (llm_client, build_agent_full_prompt)
- [x] D1 : approche coût résidentiel MEFQ par défaut (PROXY marqué)
- [x] D2 : CostInputForm.tsx (saisie manuelle coûts É.A.)

## Evidence

- 997 tests verts (25ae5a3, 2026-05-31)
- Supabase prod : migrations 001–009 appliquées, 8745 chunks RAG indexés
- Loi 25 : noms SIRF jamais stockés (SHA256[:8] seulement)
- Approche coût résidentiel : produit valeur PROXY sans données Altus

## Open Issues

- T3.6 vrai dossier : déféré jusqu'à disponibilité
- Tables Altus : non disponibles, repli MEFQ actif
- Supabase région Canada : déféré (non disponible 2026)
