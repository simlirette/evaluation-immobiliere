"""engine/report_check.py — Validation post-génération des 16 éléments CUSPAP/NPP (T3.1).

Vérifie mécaniquement la présence des 16 éléments obligatoires dans le markdown du rapport.
Si un élément manque → marque le rapport INCOMPLET (avertissement É.A.).

Référence : NPP OEAQ (§9 éléments rapport) / CUSPAP 2026 (Standards Rule 1).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Les 16 éléments avec leurs marqueurs de détection ─────────────────────────

@dataclass
class ReportElement:
    numero: int
    titre: str
    description: str
    # Patterns alternatifs (insensible à la casse) — au moins un doit être présent
    patterns: list[str]
    critique: bool = True  # Si True → rapport INCOMPLET si absent


_ELEMENTS_16: list[ReportElement] = [
    ReportElement(1, "Identification du bien",
        "Adresse, désignation cadastrale, droits évalués",
        ["identification", "adresse", "cadastr", "lot n°", "matricule"],
        critique=True),
    ReportElement(2, "But de l'évaluation",
        "Fin/but déclaré (financement, succession, vente...)",
        ["but.*evaluat", "fin.*evaluat", "objet.*mandat", "but d'"],
        critique=True),
    ReportElement(3, "Définition du type de valeur",
        "Valeur marchande, JVM, valeur réelle...",
        ["valeur marchande", "juste valeur marchande", "jvm", "définition.*valeur", "type de valeur"],
        critique=True),
    ReportElement(4, "Date de référence",
        "Date à laquelle la valeur est exprimée",
        ["date de référence", "date.*référence", "date.*évaluation", "au \\d"],
        critique=True),
    ReportElement(5, "Droits évalués",
        "Pleine propriété, emphytéose, usufruit...",
        ["droits évalués", "pleine propriété", "droit.*évalué", "titre.*propriété"],
        critique=False),
    ReportElement(6, "Étendue du travail",
        "Inspection, collecte, vérifications effectuées",
        ["étendue.*travail", "étendue du travail", "inspection", "visite", "extent of work"],
        critique=True),
    ReportElement(7, "Réserves et hypothèses",
        "Clauses standard OEAQ + hypothèses extraordinaires si applicable",
        ["réserves et hypothèses", "hypothèses", "conditions limitatives", "réserves"],
        critique=True),
    ReportElement(8, "Description du bien",
        "Terrain + bâtiment (composantes, finition, état)",
        ["description.*bien", "description.*terrain", "description.*bâtiment", "terrain", "bâtiment"],
        critique=True),
    ReportElement(9, "Meilleur usage (UMPP/AMU)",
        "Analyse des 4 critères + conclusion UMPP",
        ["meilleur usage", "umpp", "amu", "usage.*optimal", "usage.*meilleur"],
        critique=True),
    ReportElement(10, "Approches retenues et rejetées",
        "Justification des méthodes retenues / rejetées",
        ["approche.*retenue", "méthode.*retenue", "approche.*rejetée", "justification.*méthode",
         "justif.*rejet", "approche.*cost", "approche compar"],
        critique=True),
    ReportElement(11, "Application des approches",
        "Calculs détaillés par méthode retenue",
        ["comparables", "coût.*neuf", "revenu net", "taux de capitalisation",
         "valeur indiquée", "approche comparative", "approche par le coût"],
        critique=True),
    ReportElement(12, "Attestation",
        "7 déclarations OEAQ signées par l'É.A.",
        ["attestation", "déclaration", "évaluateur agréé", "signature"],
        critique=True),
    ReportElement(13, "Réconciliation",
        "Jugement pondéré (pas une moyenne) → valeur finale",
        ["réconciliation", "reconciliation", "pondér", "valeur finale", "valeur définitive"],
        critique=True),
    ReportElement(14, "Information sur l'inspection",
        "Date, étendue, observations inspection physique",
        ["inspection", "visite.*bien", "date.*visite", "inspecté"],
        critique=True),
    ReportElement(15, "Valeur en chiffres et en lettres",
        "Valeur exprimée sous les deux formes",
        [
            r"\d[\d\s]*\$.*\(",   # montant suivi de parenthèse (lettres)
            r"\d[\d\s]*\$.*dollars",
            r"\d[\d\s]*\$.*mille",
            "chiffres.*lettres", "lettres.*chiffres",
            "cent.*mille.*dollars", "quatre.*cent", "cinq.*cent", "trois.*cent",
        ],
        critique=True),
    ReportElement(16, "Annexes",
        "Liste des pièces jointes (plan, photos, extrait...)",
        ["annexe", "pièces jointes", "documents joints", "annexes"],
        critique=False),
]


# ── Résultat de vérification ──────────────────────────────────────────────────

@dataclass
class ElementCheck:
    numero: int
    titre: str
    present: bool
    critique: bool
    pattern_matched: str | None = None


@dataclass
class ReportCheckResult:
    elements: list[ElementCheck] = field(default_factory=list)

    @property
    def manquants(self) -> list[ElementCheck]:
        return [e for e in self.elements if not e.present]

    @property
    def manquants_critiques(self) -> list[ElementCheck]:
        return [e for e in self.elements if not e.present and e.critique]

    @property
    def statut(self) -> str:
        if not self.manquants_critiques:
            return "COMPLET"
        return "INCOMPLET"

    @property
    def nb_presents(self) -> int:
        return sum(1 for e in self.elements if e.present)

    @property
    def nb_total(self) -> int:
        return len(self.elements)

    @property
    def score(self) -> float:
        if not self.elements:
            return 0.0
        return round(self.nb_presents / self.nb_total, 2)

    def to_dict(self) -> dict:
        return {
            "statut": self.statut,
            "score": self.score,
            "nb_presents": self.nb_presents,
            "nb_total": self.nb_total,
            "manquants": [
                {"numero": e.numero, "titre": e.titre, "critique": e.critique}
                for e in self.manquants
            ],
            "details": [
                {
                    "numero": e.numero,
                    "titre": e.titre,
                    "present": e.present,
                    "critique": e.critique,
                }
                for e in self.elements
            ],
        }


# ── Logique de vérification ───────────────────────────────────────────────────

def _check_element(rapport_md: str, element: ReportElement) -> ElementCheck:
    text_lower = rapport_md.lower()
    for pat in element.patterns:
        try:
            if re.search(pat, text_lower, re.IGNORECASE):
                return ElementCheck(
                    numero=element.numero,
                    titre=element.titre,
                    present=True,
                    critique=element.critique,
                    pattern_matched=pat,
                )
        except re.error:
            if pat.lower() in text_lower:
                return ElementCheck(
                    numero=element.numero,
                    titre=element.titre,
                    present=True,
                    critique=element.critique,
                    pattern_matched=pat,
                )
    return ElementCheck(
        numero=element.numero,
        titre=element.titre,
        present=False,
        critique=element.critique,
    )


def check_rapport_elements(rapport_md: str) -> ReportCheckResult:
    """Vérifie la présence des 16 éléments CUSPAP/NPP dans le rapport markdown.

    Args:
        rapport_md: Contenu markdown du brouillon de rapport.

    Returns:
        ReportCheckResult avec statut COMPLET|INCOMPLET, score, manquants.
    """
    if not rapport_md or not rapport_md.strip():
        return ReportCheckResult(elements=[
            ElementCheck(e.numero, e.titre, False, e.critique)
            for e in _ELEMENTS_16
        ])

    return ReportCheckResult(elements=[
        _check_element(rapport_md, element)
        for element in _ELEMENTS_16
    ])


def build_rapport_check_section(result: ReportCheckResult) -> str:
    """Construit une section markdown à injecter à la fin du rapport indiquant les manquants."""
    if result.statut == "COMPLET":
        return (
            "\n\n---\n\n"
            "**Vérification automatique des 16 éléments CUSPAP/NPP : "
            f"COMPLET ({result.nb_presents}/{result.nb_total}).**\n"
        )

    manquants_list = "\n".join(
        f"- **Élément {e.numero} — {e.titre}**{' ⚠ CRITIQUE' if e.critique else ''}"
        for e in result.manquants
    )
    return (
        "\n\n---\n\n"
        f"> ⚠ **RAPPORT INCOMPLET — {len(result.manquants)}/{result.nb_total} éléments manquants.**\n"
        f"> Éléments à compléter avant signature :\n"
        + "\n".join(f"> {line}" for line in manquants_list.split("\n"))
        + "\n"
    )
