# LETTRE DE MANDAT D'ÉVALUATION IMMOBILIÈRE

---

**{{ bureau_nom | default("Bureau d'évaluation agréé") }}**
{% if bureau_adresse %}{{ bureau_adresse }}
{% endif %}{% if bureau_telephone %}Tél. : {{ bureau_telephone }}
{% endif %}{% if bureau_email %}{{ bureau_email }}
{% endif %}
Date : {{ date_emission }}

---

**Objet : Mandat d'évaluation immobilière — {{ adresse_propriete }}**

---

## 1. Identification des parties

**Commanditaire :**
{{ nom_commanditaire }}{% if organisation_commanditaire %}
{{ organisation_commanditaire }}{% endif %}

**Évaluateur agréé responsable :**
{{ nom_evaluateur }}

---

## 2. Bien visé par l'évaluation

**Adresse de la propriété :**
{{ adresse_propriete }}

**Type de propriété :** {{ type_bien | default("Résidentiel unifamilial") }}

---

## 3. Objet de l'évaluation

{{ objet_evaluation }}

**Type de valeur recherchée :** Valeur marchande

---

## 4. Date de référence

La valeur sera estimée en date du **{{ date_reference }}**.

---

## 5. Date limite de livraison

Le rapport d'évaluation sera remis au commanditaire au plus tard le **{{ date_livraison }}**.

---

## 6. Honoraires

Les honoraires convenus pour ce mandat sont de **{{ honoraires }}**, taxes applicables en sus.

Modalités de paiement : à la livraison du rapport.

---

## 7. Portée du travail

L'évaluation comprend :
- Inspection visuelle du bien (extérieur et intérieur)
- Analyse du marché immobilier local
- Application des méthodes d'évaluation appropriées
- Rédaction du rapport d'évaluation certifié OEAQ

Éléments exclus de la portée, le cas échéant : aucune exclusion particulière, sauf indication contraire.

---

## 8. Hypothèses et conditions limitatives

La présente évaluation est réalisée sous réserve des hypothèses et conditions limitatives suivantes :

1. Les informations fournies par le commanditaire sont présumées exactes et complètes.
2. L'évaluateur n'assume aucune responsabilité quant à des problèmes environnementaux, de sol ou de structure non apparents lors de l'inspection visuelle.
3. L'évaluation est valide à la date de référence uniquement et ne peut être utilisée à d'autres fins que celles mentionnées à l'article 3.
4. La présente lettre de mandat est soumise au Code de déontologie des membres de l'Ordre des évaluateurs agréés du Québec (OEAQ) et au Règlement sur la pratique professionnelle.

---

## 9. Conformité professionnelle

Cette évaluation sera réalisée conformément aux normes de pratique professionnelle de l'**Ordre des évaluateurs agréés du Québec (OEAQ)**, en particulier les articles §6.3 et §6.5 du Règlement sur la pratique professionnelle.

---

## 10. Acceptation du mandat

En signant la présente lettre, le commanditaire confirme avoir lu, compris et accepté les termes du présent mandat d'évaluation.

---

**Évaluateur agréé :**

Nom : {{ nom_evaluateur }}
Membre de l'OEAQ — No de permis : ___________

Signature : _______________________________  Date : ________________

---

**Commanditaire :**

Nom : {{ nom_commanditaire }}

Signature : _______________________________  Date : ________________

---

*Document généré par eval-immo — Confidentiel*
