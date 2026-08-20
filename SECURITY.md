# Politique de sécurité

Bounty-Shield analyse des issues GitHub publiques. La **sécurité** et la
**confidentialité** sont des priorités : le projet manipule une base de
comptes suspects stockée en hash, jamais en clair.

## Périphérique / non-objet de ce programme

- Ceci **n'est pas** un programme de bug bounty payant.
- Le dépôt n'accepte pas de récompense monétaire pour des signalements.

## Ce qu'il faut signaler

- Une **fuite de données privées** : un nom de compte réel, une donnée de
  chasse, ou un secret exposé dans le code, le `known.json` ou l'historique.
- Une **faille** permettant de contourner la détection des faux bounties.
- Une **injection** ou une exécution de code non prévue via les entrées
  (URL, fichier `--list`, `--report`).

## Comment signaler

Ouvrez une **issue privée** (sélectionnez « Security » dans le modèle, ou
contactez le mainteneur via GitHub) **sans exposer publiquement** la faille
avant qu'elle soit corrigée.

Incluez :
- le type de problème,
- les étapes pour le reproduire,
- l'impact potentiel,
- (si possible) une suggestion de correctif.

## Engagement

- Accusé de réception sous **48 h**.
- Analyse et réponse sous **7 jours**.
- Publication coordonnée : la faille n'est rendue publique qu'après
  correction.

## Note de non-divulgation

La base `known.json` contient des **hashs SHA-256** de comptes suspects —
jamais les noms en clair. Toute régression vers un stockage en clair est
considérée comme un problème de sécurité critique.
