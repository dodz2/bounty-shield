# Vérification 8 — Mémoire terrain (liste de confiance / liste de pièges)
# Les comptes de l'usine à faux bounties sont consignés dans known.json ;
# les dépôts qui paient réellement aussi. Une entrée connue force le verdict :
#   - compte dans known_traps  -> force PIEGE (note 10)
#   - dépôt dans known_payers  -> force VRAI (note 0)
# Les autres cas restent neutres (0 point, pas de force).

import json
from pathlib import Path


def _load_known():
    path = Path(__file__).resolve().parent.parent / "known.json"
    if not path.exists():
        return {"known_traps": [], "known_payers": []}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"known_traps": [], "known_payers": []}


def run(data: dict, rules: dict) -> dict:
    known = _load_known()
    traps = [str(x).lower() for x in known.get("known_traps", [])]
    payers = [str(x).lower() for x in known.get("known_payers", [])]

    owner = str(data.get("owner_login") or "").lower()
    full = str(data.get("full_name") or "").lower()

    if owner in traps or full in traps:
        return {"points": 1, "force": "PIEGE", "detail": f"Compte/dépôt connu dans la liste des pièges ({owner})"}
    if full in payers or owner in payers:
        return {"points": 0, "force": "VRAI", "detail": f"Dépôt connu comme payeur fiable ({full})"}
    return {"points": 0, "detail": "Aucune entrée en mémoire terrain (neutre)"}