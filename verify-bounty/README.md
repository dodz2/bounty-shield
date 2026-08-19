# Vérif'Bounty — détecteur de faux bounties

Outil interne du projet Daedalus Bounties. Analyse un bounty (issue GitHub)
et répond **VRAI**, **À VÉRIFIER** ou **PIÈGE**, avec une note sur 10, en
pesant chaque indice et en s'appuyant sur une mémoire terrain.

Dev : branche `feature/verify-bounty`. Zéro dépendance (Python standard).

## Pourquoi

Le 18/08/2026, une « usine à faux bounties » a été identifiée : des comptes
créés le jour même posent des issues `#1` « 🎯 Fix… » avec un label
`opire $10` sur des copies de dépôts populaires (caddy, traefik, kubernetes…),
0 étoile, sans licence. But probable : faire travailler des agents IA
gratuitement. Vérif'Bounty automatise la détection.

## Utilisation

```bash
# Depuis verify-bounty/
python3 verify_bounty.py --url https://github.com/owner/repo/issues/123
python3 verify_bounty.py --fixture tests/fixtures/<fichier>.json
python3 verify_bounty.py --all-fixtures
python3 verify_bounty.py --list liste.txt          # batch : une cible par ligne
python3 verify_bounty.py --url ... --json          # sortie JSON (intégration, version "2")
python3 verify_bounty.py --lang en                 # rapport en anglais
python3 verify_bounty.py --url ... --report rapport.md   # fiche d'audit Markdown
python3 verify_bounty.py --list cibles.txt --learn # écrit les pièges confirmés dans known.json
python3 verify_bounty.py --quota                   # quota API restant
```

Mode `--url` : interroge l'API publique GitHub. **Quota : ~60 requêtes/h sans
`GH_TOKEN`** (une cible coûte ~6-7 requêtes : repo, user, issue, search
rewards, commentaires, PR) → **~8 cibles/h en mode public, ~8 000 avec
`GH_TOKEN`**. Le débit est géré avec retry/backoff automatiques sur
403/429/5xx et erreurs réseau. `--quota` affiche le restant avant de travailler.
Mode `--list` : fichier avec une cible par ligne (URL GitHub ou chemin de
fixture JSON) → une ligne de verdict par cible ; **exit code 2** si des cibles
échouent, 0 sinon.

### Options CLI (items 7-11)

| Option | Effet |
|---|---|
| `--lang fr\|en` | langue d'affichage et du rapport (défaut `fr`) |
| `--report FICHIER.md` | écrit une fiche d'audit Markdown (produit) |
| `--learn` | enregistre les pièges confirmés (fiabilité ≥ 6) dans `known.json` |
| `--quota` | affiche le quota API GitHub puis sort |
| `--json` | sortie JSON stable avec enveloppe `{"version": "2", ...}` |

### Exit codes (item 10)

- `0` : analyse réussie (mode simple) ou batch sans erreur
- `1` : erreur d'utilisation (argparse)
- `2` : batch `--list` avec au moins une cible en erreur

## Verdicts — deux axes (2026-08-19)

Depuis la refonte, chaque analyse produit **deux axes indépendants** au lieu
d'un verdict unique ambigu :

### Axe 1 — AUTHENTICITÉ (le dépôt paie-t-il vraiment ?)

| Status | Signification |
|---|---|
| 🚨 **PIÈGE** | forte suspicion d'usine à faux bounties — ne pas travailler |
| ⚠️ **SANS_PREUVE** | pas piégé, mais AUCUNE preuve de paiement vérifiée |
| ✅ **PAIEUR_PROUVE** | preuve de paiement (historique / dépôt connu / PR fusionnée) |

**Précédence** : un piège (forcé ou note de risque élevée) l'emporte TOUJOURS
sur une preuve de paiement — car l'usine forge des historiques (trapuser04).

### Axe 2 — EXPLOITABILITÉ (le bounty est-il encore gagnable ?)

| Status | Signification |
|---|---|
| 🔒 **PRIS** | une PR fusionnée référence l'issue, ou l'issue est fermée |
| ⚔️ **CONTESTE** | concurrence active (claims / PR ouvertes) |
| 🟢 **LIBRE** | aucun claim, aucune PR ouverte |
| ❔ **INCONNU** | données de concurrence absentes (on n'invente pas) |

### Confiance d'authenticité

La **confiance d'authenticité** = `10 − note` (affichée en tête). La
**fiabilité du verdict** (`confidence`) reste /10 et qualifie la qualité des
données.

Un verdict peut être **forcé par la mémoire terrain** (`known.json`) :
« forcé par mémoire terrain » s'affiche alors dans la sortie.

## Les 11 vérifications (poids entre parenthèses, modifiable dans `rules.json`)

| Check | Poids | Point pénalisant |
|---|---|---|
| `fork_check` | 1 | le dépôt est un fork GitHub |
| `account_age` | 10 | compte propriétaire de moins de 30 jours |
| `stars_check` | 10 | 0 étoile |
| `issue_number` | 5 | l'issue est la #1 du dépôt |
| `amount_check` | 2 | montant annoncé ≤ 20 USD |
| `pattern_check` | 1 | titre commençant par `🎯`, `Fix:` ou `[BOUNTY]` |
| `reward_link` | 2 | label opire/bounty SANS lien de récompense vérifié |
| `clone_check` | 4 | repo créé < 7 jours après le compte (clone jetable) |
| `payment_history` | 3 | revendique une récompense mais aucun historique de paiement |
| `known_list` | 10 | force PIÈGE (a.k.a. compte piège) ou VRAI (payeur fiable) |
| `repo_liveness` | 4 | repo inactif (> 90 j) avec bounties orphelins |

Note = somme(points × poids) × 10 / somme(poids) (total = 52).
3 signaux forts (compte récent + 0 étoile + issue #1) suffisent pour PIÈGE
(≈4.81/10 ≥ seuil 4.7). 2 signaux seuls restent À VÉRIFIER (≈3.85/10).

## Concurrence (2026-08-19)

En mode `--url`, le collecteur analyse les **commentaires** de l'issue (claims
via `/claim`, « claiming », « I'll take »…) et les **PR** qui référencent
l'issue (ouvertes vs fusionnées) pour alimenter l'axe EXPLOITABILITÉ.

## Mémoire terrain (`known.json`)

- `known_traps` : comptes de l'usine identifiés → verdict PIÈGE forcé.
- `known_payers` : dépôts ayant réellement payé → verdict VRAI forcé.

Mettre à jour au fil des découvertes. Les tests prouvent que les pièges
NON listés sont détectés par les seuls checks (robustesse).

## Vérification du lien de récompense (P1)

En mode `--url`, le collecteur recherche un lien `opire.dev` dans le corps de
l'issue et tente de le vérifier (page accessible + mention « available »/
« reward »/« bounty »). Un lien validé neutralise le check `reward_link`.
En mode fixture, renseigner `reward_verified` (true/false/null) par fixture.

## Historique de paiement (P2)

Le collecteur compte les issues fermées avec label `💰 Reward` (requête
`search` GitHub). ⚠️ **L'usine peut simuler cet historique** (constaté sur
`trapuser04/sqlc` et `trapuser05/kubernetes`) : ce signal n'est qu'une
couche de nuance, jamais une preuve à lui seul.

## Limites connues (importantes)

- **L'usine ne crée pas de vrais forks** : dépôts copies → `fork_check` vert,
  mais les 9 autres checks suffisent.
- **Pas une certitude** : l'outil donne une probabilité. Toujours lire les
  commentaires et vérifier l'historique de paiement du dépôt.
- **Décalage temporel** : `account_age` et `clone_check` dépendent de la date
  d'exécution ; les fixtures vieillissent (regénérer via capture_fixtures.py).
- **Un lien vérifié n'absout pas tout** : un compte piège avec un faux lien
  valide reste PIÈGE par les autres signaux.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

- `test_pieges.py` : 5 pièges réels détectés, dont 4 SANS forçage.
- `test_vrais.py` : 2 vrais (openselfservice, trovu) passent.
- `test_p1.py` : pondération (2 signaux = À VÉRIFIER, 3 = PIÈGE), forçage
  mémoire, lien de récompense.
- `test_p2.py` : clone_check, payment_history, retry/backoff (mock réseau).
- `test_p3.py` : cas limites (vrai frêle, piège sophistiqué), confiance, veille.
- `test_axes.py` : deux axes (authenticité / exploitabilité), repo_liveness,
  piège à historique forgé, concurrence (claims / PR).
- `test_cli_features.py` : items 7-11 (multi-devises, multi-plateformes,
  account_age gradué, rapport Markdown, i18n, apprentissage --learn, quota,
  exit codes, enveloppe JSON v2).

Fixtures réelles capturées via l'API GitHub le 2026-08-18. Régénération :
`python3 tools/capture_fixtures.py` (consulte github.com : actualise les données).

## Rapport de confiance (P3)

Chaque verdict inclut une **confiance sur 10** et une recommandation :
- Confiance basée sur l'exhaustivité des données et la convergence des signaux
  (forcé par mémoire terrain = 10 ; À VÉRIFIER plafonné à 6).
- Recommandation : « Ne pas engager de travail… », « Signal fort manquant :
  account_age… Vérifier la page de récompense… », ou « Tous les signaux sont
  propres… ».

## Veille multi-repos (P3)

`tools/veille.py` surveille la liste `watchlist.json` et rapporte les issues
Reward ouvertes analysées (verdict + note + confiance).

```bash
python3 tools/veille.py [--watchlist watchlist.json] [--json]
```

Compatible cron : à intégrer comme monitor si besoin.

## Intégration au guetteur (P3)

Le cron « Guetteur openselfservice » (job 1f70d9f842b6) exécute désormais
Vérif'Bounty sur chaque issue détectée avant toute analyse manuelle, et reste
silencieux (`[SILENT]`) s'il n'y a aucun nouveau bounty (pas de branche fantôme).

## Structure

```
verify-bounty/
├── verify_bounty.py      # CLI (+ modes --json, --list, retry/backoff, GH_TOKEN)
├── scorer.py             # moteur pondéré + forçage mémoire + confiance
├── rules.json            # seuils, poids, verdicts
├── known.json            # mémoire terrain (pièges connus / payeurs fiables)
├── watchlist.json        # dépôts suivis par le mode veille
├── checks/               # 11 vérifications, une par fichier
├── tests/                # unittest + fixtures réelles
└── tools/                # scripts (capture, enrichissement, veille)
```

## À faire (en attente de décision humaine)

- [ ] Décision : outil interne uniquement, ou futur produit (à trancher avec l'utilisateur).
- [ ] Optionnel : mode « veille » (surveillance récurrente de dépôts).
- [ ] Optionnel : alerte en temps réel dans le guetteur openselfservice.
- [ ] P3 envisagés : plus de fixtures (pièges sophistiqués, vrais jeunes), rapport de confiance, intégration guetteur, mode veille multi-repos.
