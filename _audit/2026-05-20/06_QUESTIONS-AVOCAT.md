# Questions pour l'avocat — eval-immo
**Date :** 2026-05-21
**Durée estimée de la rencontre :** 30-45 minutes

**Contexte à lui donner avant les questions :**
Je développe un logiciel SaaS appelé eval-immo destiné aux évaluateurs agréés (É.A.) membres de l'OEAQ. Le logiciel assiste l'évaluateur dans la production de rapports d'évaluation immobilière en automatisant les tâches répétitives. L'évaluateur confirme les décisions clés à 4 étapes précises du processus : (1) confirmation des faits du bien sujet, (2) sélection des comparables, (3) réconciliation de la valeur, (4) révision du rapport final. Chaque confirmation est enregistrée avec la date, l'heure et l'identifiant de l'évaluateur authentifié. Le rapport final est signé par l'évaluateur agréé.

**Ce que j'ai déjà vérifié dans les textes publics (pour info) :**
- Durée de rétention des dossiers : 5 ans minimum (C-26, r. 133, art. 6) — déjà intégré dans le produit.
- Stockage USA (Supabase) : permis sous Loi 25 art. 17 si EFVP documentée + DPA signé avec Supabase — déjà prévu.
- Notification brèche : "avec diligence", aucun délai en jours fixé dans la loi ni le règlement A-2.1, r. 3.1.
- Technologies de l'information : expressément autorisées pour la tenue de dossiers (C-26, r. 133, art. 1).

---

## Bloc 1 — Conformité OEAQ et Code de déontologie

**Q1.** Le Code de déontologie §6.5 interdit à l'évaluateur de cautionner un travail qu'il n'a pas réellement effectué. Dans notre modèle, le logiciel génère les analyses et le brouillon du rapport, mais l'évaluateur confirme les 4 décisions professionnelles clés listées ci-dessus et signe le rapport final. Est-ce que ce modèle est conforme à §6.5 ? Ou est-ce que certaines étapes — notamment l'analyse de valeur visée à l'art. 24.2 du Code — doivent obligatoirement être effectuées manuellement sans assistance IA ?

**Q2.** Le Code (art. 32, 34, 24.2) établit que la signature, la responsabilité et l'analyse de valeur sont personnelles à l'évaluateur. Mais la ligne entre "outil d'assistance" (comme un tableur ou GESTIM Plus) et "délégation d'un acte professionnel" n'est pas définie dans les textes publics. Y a-t-il une jurisprudence du comité de discipline de l'OEAQ ou un avis du Conseil de discipline du Code des professions qui trace cette ligne pour des outils technologiques ? Où est le seuil ?

**Q3.** La Norme de pratique professionnelle OEAQ de mars 2025 contient-elle des dispositions sur l'intelligence artificielle ou les outils algorithmiques dans la pratique de l'évaluation ? Si oui, lesquelles s'appliquent à notre modèle ? (Note : le PDF n'est pas extractible automatiquement — nous n'avons pas pu le lire.)

**Q4.** Notre système enregistre chaque confirmation de l'évaluateur avec : date, heure, identifiant Supabase Auth de l'utilisateur, et un hash cryptographique des artefacts validés à ce moment. Est-ce que ce log constitue une preuve suffisante de supervision professionnelle réelle en cas de plainte au comité de discipline de l'OEAQ ? Faut-il quelque chose de plus, comme une signature électronique qualifiée au sens de la Loi concernant le cadre juridique des technologies de l'information (LCCJTI) ?

---

## Bloc 2 — Responsabilité et contrats

**Q5.** Si un rapport produit avec l'aide d'eval-immo est contesté (ex. : valeur jugée erronée dans une succession ou une expropriation), quelle est la responsabilité respective de eval-immo en tant qu'éditeur de logiciel et de l'évaluateur agréé qui a signé ? L'art. 32 du Code rend la responsabilité de l'É.A. personnelle et non délégable — est-ce que cela protège automatiquement eval-immo, ou faut-il des clauses contractuelles spécifiques dans les conditions d'utilisation ?

**Q6.** Est-il recommandé d'avoir un contrat B2B distinct avec chaque bureau d'évaluateurs qui : (a) qualifie explicitement eval-immo d'"outil d'assistance" et non d'"évaluateur", (b) confirme que la responsabilité professionnelle reste entièrement avec l'É.A. signataire, et (c) documente que le bureau a informé ses É.A. des conditions d'utilisation ? Ce contrat est-il suffisant pour limiter l'exposition de eval-immo, ou faut-il également des clauses dans les CGU acceptées par chaque É.A. individuellement ?
