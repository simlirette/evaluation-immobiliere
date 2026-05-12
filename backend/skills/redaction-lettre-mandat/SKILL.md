---
name: redaction-lettre-mandat
description: Rédige la lettre de mandat professionnelle conforme au Code de déontologie OEAQ §6.3 (10 éléments obligatoires)
type: redaction
agents:
  - mandat-intake
  - redaction
sources:
  - workflow-evaluateur-agree.md
---

# Skill — Rédaction de la lettre de mandat

## Rôle

Rédige la lettre de mandat (lettre d'engagement) conforme au Code de déontologie OEAQ.
Document obligatoire devant être remis au commanditaire avant l'inspection.

## Les 10 éléments obligatoires (§6.3)

| # | Élément | Requis si absent |
|---|---|---|
| 1 | Identification précise de la propriété | BLOCAGE |
| 2 | Identification du commanditaire | WARNING — utiliser [COMMANDITAIRE] |
| 3 | Type d'acte professionnel | BLOCAGE |
| 4 | Type de rapport | BLOCAGE |
| 5 | Fin d'évaluation | BLOCAGE |
| 6 | Date d'évaluation | BLOCAGE |
| 7 | Étendue de l'inspection | WARNING |
| 8 | Hypothèses et limitations préalables | WARNING |
| 9 | Honoraires et conditions | WARNING — [À CONFIRMER] acceptable V0 |
| 10 | Date de livraison + signatures | WARNING — [À CONFIRMER] acceptable V0 |

## Méthodologie

1. Lire `analysis.md` pour la doctrine complète
2. Extraire du dossier : dossier_id, type_bien, adresse, date_reference, mandat_type, format_rapport
3. Rédiger les 10 sections en Markdown, ton professionnel, juridiction Québec
4. Honoraires et date livraison : utiliser `[À CONFIRMER]` si non fournis
5. Commanditaire : utiliser `[COMMANDITAIRE]` si non identifié

## Règles critiques

- Honoraires jamais conditionnels à la valeur (violation déontologique OEAQ)
- Lettre précède l'inspection — document de départ, pas de validation
- Chaque mandat = une lettre distincte

## Checklist de conformité

- [ ] 10 éléments présents ou justifiés
- [ ] Ton professionnel, aucune valeur préjugée
- [ ] Juridiction Québec mentionnée
- [ ] Deux blocs de signature (évaluateur agréé + commanditaire)
