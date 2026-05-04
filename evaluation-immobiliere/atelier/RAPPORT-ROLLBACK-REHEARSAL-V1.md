# Rapport rollback rehearsal V1

_As-of date: 2026-05-04 (UTC)_

## Decision

- Release candidate: **rc-2026-05-04-001**
- Decision: **PRET_GO_LIVE_CONTROLE**
- Rollback: **SIMULE_OK**

## Scenarios rollback

| Scenario | Statut | Evidence |
|---|---|---|
| freeze_promotion | SIMULE_OK | Runbook rollback impose gel de promotion avant retour arriere. |
| restore_previous_tag | SIMULE_OK | Runbook rollback prevoit retour au tag sain precedent. |
| ci_rerun | SIMULE_OK | Runbook rollback exige reexecution CI complet et gates ops. |

## Conditions de sortie rollback

- CI complet relance sur le tag restaure.
- Gates metier et ops relances avant reprise promotion.
- Incident documente avant nouvelle tentative de go live.
