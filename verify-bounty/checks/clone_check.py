# Vérification 9 — Indice de « clone de code » (repo créé juste après le compte)
# L'usine crée un compte GitHub puis, le jour même, un dépôt copié d'un projet
# populaire. Un écart < 7 jours entre la création du compte et celle du dépôt
# est un indice fort de dépôt jetable.
# Score : écart < seuil (7 jours) -> 1 point ; données manquantes -> neutre.

from datetime import datetime, timezone


def _parse(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def run(data: dict, rules: dict) -> dict:
    owner_created = _parse(data.get("owner_created"))
    repo_created = _parse(data.get("repo_created"))
    threshold = int(rules.get("clone_gap_days", 7))

    if owner_created is None or repo_created is None:
        return {"points": 0, "detail": "Dates de création insuffisantes (neutre)"}

    gap = (repo_created - owner_created).days
    if gap < threshold:
        return {"points": 1, "detail": f"Repo créé {gap} j après le compte (seuil: {threshold} j)"}
    return {"points": 0, "detail": f"Repo créé {gap} j après le compte (écart normal)"}