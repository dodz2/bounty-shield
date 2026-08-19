# Vérification 6 — Titre standardisé (« pattern de masse »)
# Les faux bounties ont des titres copiés-collés : « 🎯 Fix: ... »,
# « [BOUNTY] ... ». Les vrais bounties ont des titres descriptifs normaux
# (« [Feature] un truc précis »).
# Score : le titre commence par un marqueur suspect -> 1 point.

def run(data: dict, rules: dict) -> dict:
    title = str(data.get("issue_title") or "").strip()
    markers = [str(m) for m in rules.get("suspicious_titles", ["🎯", "Fix:", "[BOUNTY]"])]
    for m in markers:
        if title.startswith(m):
            return {"points": 1, "detail": f"Titre commence par « {m} »"}
    return {"points": 0, "detail": "Titre descriptif normal"}