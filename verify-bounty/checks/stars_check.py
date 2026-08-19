# Vérification 3 — Étoiles du dépôt
# Tous les faux bounties de l'usine sont sur des dépôts à 0 étoile (fork d'un
# gros projet, donc sans vie propre). Un vrai dépôt avec des utilisateurs a
# presque toujours quelques étoiles.
# Score : stars <= seuil (0 par défaut) -> 1 point.

def run(data: dict, rules: dict) -> dict:
    stars = int(data.get("repo_stars") or 0)
    threshold = int(rules.get("stars_threshold", 0))
    suspect = stars <= threshold
    return {
        "points": 1 if suspect else 0,
        "detail": f"{stars} étoile(s) (seuil: {threshold})",
    }