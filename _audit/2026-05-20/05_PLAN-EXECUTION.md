# Plan d'exécution eval-immo — vers la démo bureau É.A.
**Établi le :** 2026-05-20
**Objectif :** Présenter au bureau É.A. un produit fonctionnel sur un dossier résidentiel réel + roadmap JLR/Altus pour décrocher une entente ferme.
**Contrainte :** Conformité Loi 25 et §6.5 OEAQ validée avant premier client payant.

---

## Chemin critique (dépendances)

```
[S1] Dossier ≠ Session (Supabase schema)
      ↓
[S2] Auth + comptes bureau/É.A.
      ↓
[S3] Pipeline stoppable par checkpoint (4 gates + log horodaté)
      ↓
[S4] Compliance Python pur (B001-B007)      [S5] Extraction PDF élargie + UI CHECKPOINT 1
      ↓                                           ↓
[S6] Import CSV JLR + CHECKPOINT 2
      ↓
[S7] Lettre de mandat (formulaire + template)
      ↓
[S8] Modèles rapport + routing LLM par tâche
      ↓
[S9] Approches conditionnelles par type_bien + watermark proxy
      ↓
[S10] Éditeur rapport + export propre
      ↓
[S11] Dossier démo anonymisé + mesure temps gagné
      ↓
[S12] Roadmap JLR/Altus écrite pour bureau

[A1][A2][A3] Actions non-techniques — en parallèle dès maintenant
```

---

## Wave 1 — Fondations (bloque tout le reste)

### Session 1 — Séparation Dossier / Session + Supabase schema
**Ce qui change :** Aujourd'hui dossier et session sont confondus (1 UUID = 1 run). À séparer.

**Livrables :**
- Supabase : table `dossiers` (entité métier persistante : adresse, type_bien, mandat, statut global)
- Supabase : table `sessions` (runs techniques liés à un dossier : UUID, artefacts, statut pipeline)
- `api.py` : `create_dossier()` distinct de `create_session()` — l'évaluateur crée un dossier, le système crée des sessions internes
- Politique d'archivage : sessions de plus de 30 jours non-validées → archivées automatiquement

**Critère de done :** Un dossier peut avoir 0 ou N sessions techniques. L'interface ne montre que le dossier — jamais les UUID de session.

**Effort :** M

---

### Session 2 — Auth + comptes bureau / É.A.
**Ce qui change :** Aujourd'hui aucun concept d'utilisateur connecté. Le `reviewer` est une string libre non vérifiable.

**Livrables :**
- Supabase Auth : inscription bureau, invitation É.A. (email)
- Rôles : `bureau_admin` (gère les comptes É.A.) / `evaluateur` (traite les dossiers)
- Session système : `confirmed_by` = ID utilisateur Supabase authentifié (pas string libre)
- Middleware Next.js : routes `/dossiers` et `/dossier/[id]` protégées

**Critère de done :** Un É.A. non authentifié ne peut pas accéder à un dossier. Le log de checkpoint contient un vrai user ID.

**Effort :** M

---

### Session 3 — Pipeline stoppable par checkpoint + log horodaté
**Ce qui change :** Pipeline one-shot → pipeline en 4 segments avec gate entre chaque.

**Livrables :**

`engine/runtime.py` — nouvelles fonctions :
```python
run_pipeline_until(dossier_id, checkpoint: int)  # 1=faits, 2=comparables, 3=réconciliation, 4=rapport
resume_from_checkpoint(dossier_id, checkpoint: int, confirmed_data: dict)
```

`checkpoint_log.jsonl` (par dossier, jamais exporté) :
```json
{"checkpoint": 1, "label": "faits_bien_sujet", "confirmed_by": "user_id_supabase",
 "confirmed_at": "2026-05-20T14:32:11Z", "snapshot_hash": "sha256:abc123"}
```

Gates backend :
- `resume_from_checkpoint(2, ...)` → vérifie checkpoint 1 confirmé → sinon `HTTP 409 CHECKPOINT_REQUIRED`
- Gate bloquant : aucun contournement possible via API

**Rapport exporté :** aucune mention des checkpoints — contenu professionnel uniquement.

**Critère de done :** Sans confirmation du CHECKPOINT 1, le pipeline refuse de continuer vers le CHECKPOINT 2. Testé par un test automatisé.

**Effort :** L

---

## Wave 2 — Compliance et données (bloque la démo)

### Session 4 — Compliance Python pur (B001-B007)
**Ce qui change :** Règles dans un `system_prompt` LLM → fonctions Python déterministes.

**Livrables :**

`engine/compliance.py` (nouveau module) :
```python
def check_B001(case: dict) -> ComplianceResult  # données obligatoires manquantes
def check_B002(case: dict) -> ComplianceResult  # source_id absent
def check_B003(case: dict) -> ComplianceResult  # date future
def check_B004(case: dict) -> ComplianceResult  # unités incohérentes
def check_B005(case: dict) -> ComplianceResult  # ajustement sans validation
def check_B006(case: dict) -> ComplianceResult  # valeur hors plage plausible
def check_B007(case: dict) -> ComplianceResult  # comparable hors zone
def run_compliance(case: dict) -> ComplianceReport  # agrège B001-B007 + appel LLM pour W001-W005
```

`ComplianceResult` :
```python
@dataclass
class ComplianceResult:
    rule: str           # "B002"
    violated: bool
    explanation_fr: str # "Le comparable C-3 n'a pas de source_id. Ajoutez le numéro
                        #  de fiche JLR ou la référence Centris avant de continuer."
```

LLM conservé uniquement pour W001-W005 (avertissements non-bloquants).

**Critère de done :** B002 violé → pipeline bloqué à 100%, message en français clair. Couverture test : 7 tests unitaires, 1 par règle.

**Effort :** M

---

### Session 5 — Extraction PDF élargie + UI CHECKPOINT 1
**Ce qui change :** `_STRUCTURED_FIELDS_SCHEMA` extrait 10 champs → étendre à ~30. Ajouter feedback UI post-upload.

**Livrables :**

`engine/ingestion.py` — champs ajoutés au schéma :
```
type_bien, adresse_complete, ville, code_postal, destination,
zonage, nb_pieces, nb_chambres, nb_salles_bain, nb_stationnements,
garage (bool), piscine (bool), sous_sol_fini (bool),
annee_renovation, etat_general, vue, proximite_nuisances,
nom_proprietaire, nom_commanditaire, objet_evaluation
```

UI CHECKPOINT 1 (Next.js) — écran post-pipeline intake :
- Tableau "Voici ce que j'ai extrait de vos documents" — champ par champ
- Champs manquants surlignés en orange avec label "À compléter"
- Bouton "Confirmer les faits" → enregistre checkpoint_log entrée 1

Erreur d'ingestion visible : si extraction échoue, bandeau rouge "Extraction PDF incomplète — vérifiez le document" (plus de `except: pass` silencieux).

**Critère de done :** Upload d'un vrai contrat notarié → au moins 15 champs extraits correctement → évaluateur voit le tableau et confirme.

**Effort :** M

---

### Session 6 — Import CSV JLR + scoring comparables + CHECKPOINT 2
**Ce qui change :** `search_comparables()` filtre un pool JSON manuel → ingère un CSV JLR réel.

**Livrables :**

`engine/ingestion.py` — nouveau parseur :
```python
def parse_jlr_csv(path: Path) -> list[dict]
# Colonnes JLR à valider sur un vrai export avant de coder
# Champs cibles : adresse, prix_vente, date_vente, surface_habitable,
#                 surface_terrain, nb_pieces, nb_chambres, distance_km (calculée)
```

`engine/tools.py::search_comparables()` — mise à jour :
- Accepte pool issu de `parse_jlr_csv()` en plus du pool JSON
- Score de similarité : pondération surface (40%), date (30%), distance (20%), type (10%)
- Retourne top 5-8 candidats avec score et justification

UI CHECKPOINT 2 — écran sélection comparables :
- Liste des comparables proposés avec score et carte (si coordonnées disponibles)
- Évaluateur coche les comparables retenus (minimum 3 requis par B007)
- Bouton "Confirmer les comparables" → checkpoint_log entrée 2

**Critère de done :** Upload CSV JLR (format réel) → 5 comparables proposés avec score → évaluateur en sélectionne 3 → pipeline continue vers valuation.

**Effort :** M (dépend de la validation du format CSV JLR réel — voir A2)

---

### Session 7 — Lettre de mandat : formulaire + template fixe
**Ce qui change :** `AGENTCONFIG-MANDAT-INTAKE-V0.yaml` utilise LLM → remplacer par template fixe.

**Livrables :**

Écran d'ouverture de dossier (avant tout pipeline) — formulaire 6 champs :
```
1. Nom du commanditaire
2. Adresse de la propriété
3. Objet de l'évaluation (dropdown : Vente, Financement, Succession, Expropriation, Autre)
4. Honoraires ($)
5. Date limite de livraison
6. Nom de l'évaluateur signataire (pré-rempli depuis le compte Auth)
```

`templates/lettre_mandat_residentiels.md` — template Jinja2 avec les 10 éléments §6.3 :
- Aucun placeholder `[À CONFIRMER]` dans le document final
- Champs vides → formulaire bloque la soumission (validation côté client)

Export : PDF téléchargeable, prêt à envoyer au commanditaire.

**Critère de done :** Formulaire complet → lettre PDF générée sans aucun placeholder non rempli.

**Effort :** S

---

## Wave 3 — Qualité rapport (bloque la démo)

### Session 8 — Modèles de rapport + routing LLM par tâche
**Ce qui change :** Tous les agents utilisent le même modèle → routing par tâche.

**Livrables :**

Routing LLM dans `api.py` / `runtime.py` :
```python
LLM_ROUTING = {
    "extraction_pdf":      "gpt-4o",        # Vision obligatoire
    "parse_structured":    "gpt-4o-mini",   # Tâche structurée
    "compliance_warnings": "gpt-4o-mini",   # W001-W005 non-bloquants
    "amu_analyse":         "gpt-4o-mini",   # Raisonnement sur données structurées
    "redaction_rapport":   "gpt-4o",        # Prose professionnelle visible
    "assistant_qa":        "gpt-4o-mini",   # Q&A rapide sur artefacts
}
```

Modèles de rapport (fichiers Markdown fournis par Simon-Olivier avec un É.A. référent) :
```
templates/rapport_residentiel_unifamilial.md
templates/rapport_immeuble_revenus.md
templates/rapport_commercial.md
```
Ces fichiers sont du contenu métier — ne peuvent pas être écrits par le dev seul. Nécessitent la collaboration d'un É.A. (voir contact existant).

**Critère de done :** Rapport résidentiel généré avec GPT-4o sur le modèle fourni. Coût LLM par dossier mesuré et < $0.10 en usage standard.

**Effort :** S (code) + M (contenu modèles avec É.A.)

---

### Session 9 — Approches conditionnelles par type_bien + watermark proxy
**Ce qui change :** 3 approches systématiques → approches selon le type de bien.

**Livrables :**

`engine/valuation.py` — logique conditionnelle :
```python
def applicable_approaches(type_bien: str) -> list[str]:
    if type_bien in ("unifamiliale", "jumelé", "cottage"):
        return ["comparative"]  # coût si données Altus disponibles
    if type_bien in ("immeuble_revenus", "commercial"):
        return ["comparative", "revenu"]
    if type_bien in ("terrain"):
        return ["comparative"]
    # défaut
    return ["comparative"]
```

Watermark obligatoire si proxy utilisé :
```json
{
  "approche": "cout",
  "valeur": 485000,
  "AVERTISSEMENT": "VALEUR PROXY — mean(prix_comparables). Non certifiable OEAQ.
                    Remplacer par calcul Altus/Marshall Swift avant livraison."
}
```

Retirer StatCan WDS du module `data_enrichment.py` — source non utilisée par les É.A. québécois.

**Critère de done :** Dossier résidentiel unifamilial → approche revenu absente du rapport. Proxy coût → avertissement visible dans l'artefact et dans l'UI.

**Effort :** S

---

### Session 10 — Éditeur rapport en ligne + export propre
**Ce qui change :** Rapport généré mais non éditable dans l'outil.

**Livrables :**

UI CHECKPOINT 4 — éditeur de rapport :
- Éditeur Markdown (ex: `@uiw/react-md-editor` ou équivalent) intégré dans Next.js
- Contenu pré-rempli avec le brouillon généré par GPT-4o
- Sauvegarde auto (endpoint `app_save_rapport` existant)
- Bouton "Régénérer" si l'évaluateur veut un nouveau brouillon LLM (endpoint `app_generate_rapport` existant)

Export :
- PDF propre (sans traces des checkpoints internes)
- DOCX pour modification externe si besoin

**Critère de done :** Évaluateur édite le rapport, sauvegarde, exporte PDF. Le PDF ne contient aucun artefact technique (pas de session_id, pas de snapshot_hash, pas d'avertissement proxy).

**Effort :** M

---

## Wave 4 — Démo et business

### Session 11 — Dossier démo anonymisé + mesure temps gagné
**Ce qui change :** D-PILOTE-RES-001 est un fixture synthétique évident. Besoin d'un vrai dossier.

**Livrables :**
- Dossier résidentiel réel anonymisé (avec l'É.A. contact) : PDF contrat, photos, export JLR CSV
- Passage complet du dossier dans eval-immo — chronométré étape par étape
- Tableau comparatif : temps É.A. sans eval-immo vs avec eval-immo, par phase
- Ce tableau = slide 1 de la démo bureau

**Critère de done :** Le dossier traverse les 4 checkpoints et produit un rapport exportable. Le gain de temps est mesuré et chiffré.

**Effort :** M (dépend de la disponibilité de l'É.A. contact)

---

### Session 12 — Roadmap JLR/Altus écrite pour le bureau
**Ce qui change :** Roadmap technique interne → document de vente orienté valeur métier.

**Livrables :**

`docs/ROADMAP-BUREAU-EA.md` — document 2 pages :
- Ce que eval-immo fait aujourd'hui (avec captures de la démo)
- Ce qui arrive dans 6 mois : connecteur JLR API, tables Altus, multi-bureau
- Modèle de tarification : base par bureau + crédits par dossier
- Comparaison temps/coût : avant vs après eval-immo

**Critère de done :** Document lisible par un directeur de bureau sans bagage technique.

**Effort :** S

---

## Actions non-techniques (démarrer maintenant, en parallèle)

| # | Action | Qui | Urgence | Dépendance |
|---|---|---|---|---|
| A1 | Appeler l'avocat — Loi 25 (inventaire données + politique rétention) + §6.5 OEAQ (human-in-the-loop) | Simon-Olivier | Avant S2 | Aucune |
| A2 | Obtenir un vrai export CSV JLR auprès de l'É.A. contact — valider les colonnes et l'encodage | Simon-Olivier | Avant S6 | É.A. contact |
| A3 | Contacter JLR — politique partenariat API avec startups | Simon-Olivier | Avant V2 | Aucune |
| A4 | Produire les modèles de rapport (résidentiel, revenus) avec l'É.A. contact — structure + formulations types | Simon-Olivier + É.A. | Avant S8 | É.A. contact |

---

## Séquence recommandée

```
Semaine 1-2  : A1 (avocat) en parallèle + S1 (Supabase schema)
Semaine 2-3  : S2 (Auth) + A2 (CSV JLR)
Semaine 3-5  : S3 (checkpoints) — le plus long
Semaine 5-6  : S4 (compliance Python) + S5 (PDF élargi) en parallèle
Semaine 6-7  : S6 (CSV JLR + CHECKPOINT 2) + S7 (lettre mandat) en parallèle
Semaine 7-8  : S8 (modèles rapport + routing) — dépend de A4
Semaine 8    : S9 (approches conditionnelles) — rapide
Semaine 9    : S10 (éditeur rapport)
Semaine 9-10 : S11 (dossier démo) — dépend de l'É.A. contact
Semaine 10   : S12 (roadmap bureau)
              → DÉMO BUREAU É.A.
```

**Durée estimée : 10-12 semaines** avec un rythme de 1-2 sessions Claude Code par semaine.

---

## Ce qui est explicitement hors scope avant la démo

- API JLR (V2 — après entente bureau)
- Tables Altus/Marshall Swift (V2)
- Migration cloud AWS/Azure/GCP (V3 — à ~200 évaluateurs)
- Multi-type de biens (commercial, industriel, agricole) — résidentiel unifamilial uniquement pour la démo
- StatCan WDS — à retirer proprement lors de S9
