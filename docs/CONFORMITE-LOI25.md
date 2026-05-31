# Conformité Loi 25 — eval-immo

**Date :** 2026-05-31  
**Statut :** En cours — chantier ouvert, avis juridique requis avant premier client payant.

---

## 1. Données personnelles collectées

| Source | Données | Classification | Traitement actuel |
|---|---|---|---|
| SIRF (Registre foncier) | Noms vendeur/acheteur | PII sensible | **Hash SHA256 tronqué (8 chars)** — non réversible |
| SIRF | Prix de vente, date, no lot | Données publiques | Conservées en clair |
| Utilisateur É.A. | Nom, email, n° permis OEAQ | PII professionnel | Profil Supabase auth |
| Commanditaire | Nom, organisation | PII contextuel | Session locale seulement |
| Propriétaire | Adresse anonymisée | PII faible | Anonymisée dans les fixtures |

## 2. Mesures techniques implémentées

### Noms SIRF (T0.6 — 2026-05-31)
- `registre_foncier.py::_anonymize_party()` : remplace nom → SHA256[:8]
- **Jamais stockés** : noms bruts vendeur/acheteur ne persistent ni en cache disque ni en Supabase
- Champ dans sirf_cache : `vendeur` / `acheteur` = hash 8 chars uniquement
- Impact : perte de capacité à identifier les parties, **gain** : conformité LPC/Loi 25

### Fail-closed auth (T0.4)
- ENV=production sans token → 401 immédiat (pas de mode local_dev en prod)

### Pas d'accès anonyme
- Routes `/app/*` requièrent token évaluateur
- Sessions isolées par owner_evaluator_id

## 3. Flux de données

```
SIRF (externe) → hash() → cache disque/Supabase (hash seulement)
                         → comparables (hash seulement)
                         → rapport (source_id JLR-xxx, jamais les noms)
```

## 4. Droits des personnes concernées (Loi 25 / LPC)

| Droit | Applicable ? | Mécanisme actuel |
|---|---|---|
| Accès | Non (données publiques BNRQ déjà anonymisées) | — |
| Rectification | Non applicable (données agrégées anonymisées) | — |
| Suppression | Possible via /app/archive + purge Supabase | Manuel É.A. |
| Portabilité | Non applicable | — |

## 5. Rétention

| Données | Durée cache | Justification |
|---|---|---|
| sirf_cache (prix/date/hash) | 90 jours | Coût BNRQ 1,50$/lot — éviter rechargement |
| Sessions runtime | 30 jours auto-archivage | Voir `_archive_stale_sessions()` |
| Documents uploadés | Durée vie session | Stockage Supabase storage |

## 6. Actions restantes (avant premier client payant)

- [ ] **Avis juridique** : confirmation masquage SIRF suffit ou si toute collecte est interdite
- [ ] **Politique de confidentialité** : document public pour les utilisateurs
- [ ] **Registre des activités de traitement** : requis si >25 employés (non applicable actuellement)
- [ ] **Consentement commanditaire** : le nom du commanditaire est-il PII au sens de la Loi 25 ?
- [ ] **Résidence des données** : vérifier que Supabase West US (Oregon) est acceptable (Loi 25 art. 17)

## 7. Référence légale

- **Loi 25** : Loi modernisant des dispositions législatives en matière de protection des renseignements personnels (RLRQ c. P-39.1)
- **LPC** : Loi sur la protection des consommateurs
- **BNRQ** : Bureau du registre du droit réel (données publiques, accès payant)
