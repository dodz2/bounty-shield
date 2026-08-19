# Vérification 11 — Vivacité du dépôt (repo_liveness)
# Un vrai dépôt qui paie des bounties est ACTIF : il y a des commits récents
# et les bounties ne restent pas orphelins. Un dépôt mort (aucun push depuis
# longtemps) qui affiche des bounties ouverts = argent qui ne sera jamais
# versé (travail gratuit). Exemple terrain : cocohub-mobileapp/cocohub-main
# (inactif depuis 03/07, 18 bounties orphelins, PRs jamais fusionnées).
# Score :
#   - repo inactif (> seuil) AVEC bounties ouverts  -> 2 points (orphelins)
#   - repo inactif (> seuil) sans bounties          -> 1 point (inactivité)
#   - repo actif                                    -> 0 point
#   - données manquantes                            -> 0 point (neutre)
#
# Données attendues (collectées via API) :
#   repo_pushed_at        : date ISO du dernier push (r.pushed_at)
#   open_reward_issues    : nombre d'issues ouvertes label 💰 Reward (int|None)

from datetime import datetime, timezone


def _parse(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def run(data: dict, rules: dict) -> dict:
    pushed = _parse(data.get("repo_pushed_at"))
    stale_days = int(rules.get("liveness_stale_days", 90))
    open_rewards = data.get("open_reward_issues")

    if pushed is None:
        return {"points": 0, "detail": "Date de dernier push inconnue (neutre)"}

    age_days = (datetime.now(timezone.utc) - pushed).days
    if age_days > stale_days:
        if open_rewards is not None and open_rewards > 0:
            return {
                "points": 2,
                "detail": f"Repo inactif depuis {age_days} j avec {open_rewards} bounty(s) ouverts (orphelins)",
            }
        return {"points": 1, "detail": f"Repo inactif depuis {age_days} j (seuil: {stale_days} j)"}
    return {"points": 0, "detail": f"Repo actif (dernier push il y a {age_days} j)"}
