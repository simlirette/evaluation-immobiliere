---
name: analyse-extraction-faits
description: >
  Extraire les faits structurés d'un document source (acte notarié, fiche cadastrale,
  contrat de bail, permis de construction) et les classer par catégorie avec traçabilité.
type: analyse
agents:
  - data-facts
sources:
  - documents_sources
  - registre_foncier
---

## Objectif

Produire une fiche structurée des faits vérifiables du bien à partir des documents disponibles, avec un `source_id` pour chaque donnée.

## Procédure

### 1. Inventaire des documents disponibles
- Lister tous les documents fournis (actes, fiches, plans, photos, baux)
- Attribuer un `source_id` unique à chaque document : ex. `doc_acte_2019`, `doc_role_2024`
- Identifier les lacunes documentaires (données manquantes à signaler)

### 2. Extraction par catégorie

**Identification du bien :**
- Adresse civique complète (numéro, rue, ville, code postal)
- Numéro de lot (cadastre rénové) ou matricule municipal
- Numéro de carte cadastrale
- Description légale (titre de propriété)

**Caractéristiques physiques :**
- Superficie du terrain (m²) — source : acte notarié ou registre foncier
- Superficie du bâtiment (m² brut et habitable si résidentiel)
- Nombre d'étages, d'unités, de pièces
- Année de construction — source : rôle municipal ou permis
- Type de construction (ossature bois, béton, acier)
- État général (excellent / bon / moyen / mauvais)

**Situation juridique :**
- Propriétaire inscrit au Registre foncier (nom, date d'acquisition, prix)
- Hypothèques actives (créancier, montant, date)
- Servitudes (nature, parcelle dominante / servante)
- Restrictions au titre (clauses restrictives, droits de préemption)
- Zonage actuel (code, usages permis, densité maximale)

**Données d'exploitation (si applicable) :**
- Nombre d'unités locatives, superficie par unité
- Loyers actuels ($ / mois / unité) — source : baux ou déclarations propriétaire
- Taux d'occupation actuel et historique
- Dépenses d'exploitation (taxes, assurances, entretien, gestion)

### 3. Contrôle de cohérence
- Comparer la superficie du rôle avec l'acte notarié → signaler tout écart > 5%
- Vérifier que le propriétaire inscrit correspond au mandant
- S'assurer que la date de référence est antérieure à la date d'inspection

### 4. Format de sortie attendu

```json
{
  "source_id": "doc_acte_2019",
  "type": "acte_notarie",
  "date_document": "2019-06-15",
  "faits_extraits": {
    "adresse": "123, rue Principale, Montréal (QC) H1A 1A1",
    "lot_cadastral": "4266-12-3456-7-000",
    "superficie_terrain_m2": 320,
    "superficie_batiment_m2": 145,
    "annee_construction": 1985,
    "prix_acquisition": 320000
  },
  "confidence": 0.95,
  "lacunes": []
}
```

## Règles critiques

- Ne jamais inférer une superficie ou un prix non présent dans les sources
- Si deux sources donnent des valeurs différentes, conserver les deux et signaler le conflit
- Une donnée sans `source_id` est une hypothèse, pas un fait
