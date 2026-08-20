# Contribuer à Bounty-Shield

Merci de vouloir améliorer Bounty-Shield. Ce projet est conçu pour être
simple, fiable et sans dépendance — respectez ces principes dans vos
contributions.

## Environnement

- **Python ≥ 3.9**, zéro dépendance externe (stdlib uniquement).
- Tests : `unittest` (aucun framework tiers).

```bash
cd verify-bounty
python3 -m unittest discover -s tests -q
```

## Comment contribuer

1. **Fork** le dépôt, créez une branche dédiée (`git switch -c feature/...`).
2. **Codez** en respectant le style existant (docstrings, commentaires FR).
3. **Ajoutez des tests** pour toute nouvelle fonctionnalité ou correction.
4. **Vérifiez** que la suite passe : `python3 -m unittest discover -s tests -q`.
5. **Ouvrez une Pull Request** avec une description claire :
   - le problème résolu,
   - l'approche,
   - les tests ajoutés.

## Règles

- **Zéro dépendance** : n'ajoutez pas de package externe sans justification.
- **Ne divulguez pas la base** : le fichier `known.json` embarque des hashs
  SHA-256 de comptes. Ne le remplacez jamais par des noms en clair, et ne
  publiez pas de données de chasse dans les issues/PR.
- **Compatibilité** : le code doit rester compatible Python 3.9+.
- **Tests** : toute PR doit laisser la suite au vert (CI en dépend).

## Signaler un bug

Ouvrez une issue avec : la commande exécutée, la sortie obtenue, la sortie
attendue. Pour les problèmes de sécurité, voir `SECURITY.md`.
