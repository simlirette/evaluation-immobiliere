---
name: recherche-domaines-specialises
description: >
  Appliquer les méthodes et critères spéciaux pour les propriétés atypiques :
  condo indivise, RPA, hôtel, station-service, achalandage dominant, biens patrimoniaux.
type: recherche
agents:
  - data-facts
  - valuation-draft
  - compliance-qa
sources:
  - normes_oeaq
  - jurisprudence
  - donnees_marche_specialise
---

## Propriétés à traitement spécialisé

### Condo indivise

**Problématique :** Le condo indivise représente une quote-part d'un immeuble sans division cadastrale. Il n'existe pas de Registre foncier distinct pour chaque unité.

**Évaluation :**
1. Évaluer l'immeuble entier en valeur marchande (approche comparative ou revenu)
2. Appliquer la quote-part de la convention d'indivision
3. Appliquer une **décote d'illiquidité** de 10–25% selon :
   - Restrictions à la vente (droit de préemption des co-indivisaires)
   - Taille de la quote-part (petite quote-part = décote plus élevée)
   - Marché local des indivises (comparables d'indivises disponibles ?)

**Source :** Décision TAQ, jurisprudence Chambre immobilière

### Résidence pour personnes âgées (RPA)

**Particularité :** La valeur est indissociable du permis d'exploitation MSSS. L'achalandage (taux d'occupation et certification) fait partie de la valeur.

**Approche recommandée :** Revenu (capitalisation des revenus d'hébergement) + valeur du permis
- Taux d'occupation cible : 85–92%
- Revenus par unité : loyer mensuel × 12 × nombre d'unités
- Dépenses : soins, alimentation, entretien, administration (~60–70% des revenus)
- TGA spécialisé RPA : 6–8% (données CBRE / JLL)

### Hôtel / motel

**Indicateurs clés :**
- RevPAR = ADR × Taux d'occupation (Revenue Per Available Room)
- ADR (Average Daily Rate) = Tarif journalier moyen
- FF&E (Furniture, Fixtures & Equipment) — réserve annuelle ~4% du revenu

**Approche :** DCF sur 10 ans + valeur terminale (revenu année 11 / taux de capitalisation sortant)
**Comparable :** Prix par chambre ($/chambre)

### Station-service

**Particularité :** Contamination des sols potentielle (UST — réservoirs souterrains).

**Procédure obligatoire :**
- Phase I ESA (Environmental Site Assessment) — revue documentaire
- Phase II si Phase I révèle risque — prélèvements de sols
- Hypothèse d'évaluation : "sans contamination connue" si Phase I seulement → mentionner explicitement
- Si contamination confirmée : déduire coût de décontamination estimé

### Bien patrimonial / classé

**Particularité :** Restrictions de modification imposées par la Loi sur le patrimoine culturel (RLRQ c. P-9.002).

**Impact valeur :**
- Contraintes de restauration (matériaux authentiques) → surcoût d'entretien
- Crédits d'impôt et subventions disponibles → peuvent compenser partiellement
- Marché limité → possible décote de liquidité

**Approche :** Comparaison avec biens patrimoniaux similaires + analyse coût-bénéfice des restrictions

### Achalandage dominant (marina, golf, camping)

**Définition :** Biens où la valeur du bien immobilier est inséparable de la valeur commerciale de l'entreprise.

**Méthode :** Décomposer la valeur globale entre :
1. Valeur du bien immobilier (terrain + structures permanentes)
2. Valeur de l'entreprise / achalandage (écart par rapport à 1)

**Approche :** DCF basé sur les revenus d'exploitation → soustraire la valeur résiduelle du bien physique = valeur achalandage

### Pré-construction (as-if-complete)

**Définition :** Évaluation d'un bien en cours de construction ou non encore construit, comme s'il était complété à la date de référence.

**Hypothèse extraordinaire obligatoire :**
> "Cette évaluation est établie sous l'hypothèse extraordinaire que le bien est complété conformément aux plans et devis fournis à la date de référence. La valeur ne tient pas compte des risques de construction."

**Attention :** L'hypothèse doit être clairement signalée en page de garde et dans les conditions limitatives.
