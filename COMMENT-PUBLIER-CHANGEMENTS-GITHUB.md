# Pourquoi tu ne vois pas les fichiers sur GitHub

Tu es dans le bon repo GitHub (`simlirette/evaluation-immobiliere`), mais dans cet environnement Codex:

- les commits ont été faits localement sur la branche `work`;
- aucun `remote` Git n'est configuré ici;
- donc rien n'a encore été poussé vers GitHub.

## Vérification rapide

```bash
git branch -vv
git remote -v
git log --oneline --decorate -n 5
```

Tu devrais voir:
- branche courante: `work`
- `git remote -v`: vide

## Étapes pour publier sur GitHub

Depuis ton terminal (ou ici si remote/config est disponible), exécuter:

```bash
git remote add origin git@github.com:simlirette/evaluation-immobiliere.git
# ou en HTTPS:
# git remote add origin https://github.com/simlirette/evaluation-immobiliere.git

git push -u origin work
```

Ensuite, sur GitHub:
1. Ouvre la bannière "Compare & pull request" pour la branche `work`.
2. Crée le PR vers `main`.
3. Merge le PR.

Après merge, les fichiers seront visibles sur `main`.

## Fichiers ajoutés localement (branche `work`)

- `evaluation-immobiliere/README.md`
- `evaluation-immobiliere/DEMARRAGE-ADAPTATION-EVALUATION-IMMOBILIERE.md`
- `evaluation-immobiliere/atelier/WORKSHOP-EVALUATEURS-PLAN.md`
- `evaluation-immobiliere/atelier/QUESTIONNAIRE-EVALUATEURS.md`
- `evaluation-immobiliere/atelier/MATRICE-PRIORISATION-MVP.csv`
- `evaluation-immobiliere/atelier/PLAN-TRAVAIL-EN-ATTENTE-WORKSHOP.md`
