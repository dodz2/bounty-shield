# Bounty-Shield — Vérif'Bounty

**Détectez les faux bounties open source avant d'y investir votre temps.**

Bounty-Shield analyse une issue GitHub portant un label de récompense et
répond à deux questions indépendantes :

1. **AUTHENTICITÉ** — ce dépôt paie-t-il vraiment, ou est-ce un piège ?
   → `PIÈGE` / `SANS_PREUVE` / `PAYEUR PROUVÉ`
2. **EXPLOITABILITÉ** — ce bounty est-il encore gagnable ?
   → `PRIS` / `CONTESTÉ` / `LIBRE` / `INCONNU`

Zéro dépendance (Python standard). La détection repose sur des signaux
observables publics (fork, étoiles, âge du compte, montant, titre,
historique, vivacité du dépôt) et une **mémoire terrain** que vous alimentez
via `--learn`.

## Pourquoi

Le 18/08/2026, nous avons identifié des « usines à faux bounties » : des
comptes jetables déposent une issue unique sur des forks de dépôts populaires,
affichent un montant fixe et un titre standardisé — pour faire travailler des
agents IA **gratuitement**. Ce projet automatise leur détection.

## Installation

```bash
git clone https://github.com/dodz2/bounty-shield.git
cd bounty-shield/verify-bounty
python3 verify_bounty.py --url https://github.com/owner/repo/issues/123
```

## Utilisation

```bash
# Analyser une issue GitHub (public, sans token ~8 cibles/h ; avec GH_TOKEN ~8000/h)
python3 verify_bounty.py --url https://github.com/owner/repo/issues/123

# Sortie JSON stable pour intégration
python3 verify_bounty.py --url ... --json

# Batch : une cible par ligne
python3 verify_bounty.py --list cibles.txt

# Rapport d'audit Markdown + langue
python3 verify_bounty.py --url ... --report rapport.md --lang fr|en

# Apprendre un piège confirmé (écrit dans known.json local)
python3 verify_bounty.py --list cibles.txt --learn
```

### Options CLI

| Option | Effet |
|---|---|
| `--lang fr\|en` | langue d'affichage et du rapport (défaut `fr`) |
| `--report FICHIER.md` | écrit une fiche d'audit Markdown |
| `--learn` | enregistre les pièges confirmés (fiabilité ≥ 6) dans `known.json` |
| `--quota` | affiche le quota API GitHub restant |
| `--json` | sortie JSON stable (enveloppe `version 2`) |

### Exit codes

- `0` : analyse réussie / batch sans erreur
- `1` : erreur d'utilisation
- `2` : batch `--list` avec au moins une cible en erreur

## Les 11 vérifications

`fork_check` · `account_age` (gradué) · `stars_check` · `issue_number` ·
`amount_check` (multi-devises) · `pattern_check` · `reward_link`
(multi-plateformes) · `clone_check` · `payment_history` · `known_list` ·
`repo_liveness`.

La note de risque (0-10) agrège ces signaux pondérés (seuils dans
`rules.json`), puis l'**authenticité** et l'**exploitabilité** en sont dérivées.

## Mémoire terrain (`known.json`)

- `known_traps` : comptes pièges identifiés → verdict PIÈGE forcé.
- `known_payers` : dépôts ayant réellement payé → verdict PAYEUR PROUVÉ forcé.

Le repo embarque un `known.json` **vide** (template). Alimentez-le via
`--learn` ou avec vos propres données. La base de données Daedalus reste
privée et n'est pas publiée ici.

## Tests

```bash
python3 -m unittest discover -s tests -q
# 65 tests verts, zéro dépendance
```

## Licence

MIT — voir `LICENSE`.

## Avertissement

Outil d'aide à la décision : il produit une **probabilité**, pas une
certitude. Toujours lire l'issue et ses commentaires avant de vous engager.
