# Vérification 2 — Âge du compte propriétaire (gradué, item 6)
# L'usine à faux bounties crée des comptes le jour même. Un compte très récent
# combiné à d'autres signaux = piège probable. Plutôt qu'un seuil binaire
# (30 j), on gradue la suspicion en 3 bandes configurables :
#   - très récent  (< bande_1, défaut 14 j)  -> 1.0 point (fort)
#   - récent       (< bande_2, défaut 30 j)  -> 0.5 point (moyen)
#   - jeune        (< bande_3, défaut 90 j)  -> 0.2 point (nuance)
#   - établi       (>= bande_3)              -> 0.0 point
# Ainsi un compte de 33 j (copperhead) n'est plus blanc comme neige, mais pas
# non plus un piège.

from datetime import datetime, timezone


def run(data: dict, rules: dict) -> dict:
    raw = data.get("owner_created") or ""
    b1 = int(rules.get("account_age_band_young", 14))
    b2 = int(rules.get("account_age_band_recent", 30))
    b3 = int(rules.get("account_age_band_old", 90))
    if not raw:
        return {"points": 0, "detail": "Date de création du compte inconnue"}
    try:
        created = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - created).days
    except Exception:
        return {"points": 0, "detail": f"Date illisible: {raw}"}

    if age_days < b1:
        return {"points": 1.0, "detail": f"Compte très récent ({age_days} j < {b1} j) — fort signal"}
    if age_days < b2:
        return {"points": 0.5, "detail": f"Compte récent ({age_days} j, bande {b1}-{b2} j) — signal moyen"}
    if age_days < b3:
        return {"points": 0.2, "detail": f"Compte jeune ({age_days} j, bande {b2}-{b3} j) — nuance"}
    return {"points": 0.0, "detail": f"Compte établi ({age_days} j)"}
