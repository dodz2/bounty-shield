# Vérification 8 — Mémoire terrain (liste de confiance / liste de pièges)
# Les comptes de l'usine à faux bounties sont consignés dans known.json ; les
# dépôts qui paient réellement aussi. Une entrée connue force le verdict :
#   - compte dans known_traps / known_traps_hashes -> force PIEGE (note 10)
#   - dépôt dans known_payers / known_payers_hashes -> force VRAI (note 0)
# Les autres cas restent neutres (0 point, pas de force).
#
# FORMAT SÉCURISÉ : la base publique est stockée en HASH SHA-256 (champs
# *_hashes) pour ne pas divulguer les comptes en clair dans le repo. Les
# champs en clair (*_traps / *_payers) restent acceptés pour le --learn local.
# L'outil compare les deux.

import hashlib
import json
from pathlib import Path


def _sha256(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()


def _load_known():
    path = Path(__file__).resolve().parent.parent / "known.json"
    if not path.exists():
        return {"known_traps": [], "known_payers": [],
                "known_traps_hashes": [], "known_payers_hashes": []}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"known_traps": [], "known_payers": [],
                "known_traps_hashes": [], "known_payers_hashes": []}


def run(data: dict, rules: dict) -> dict:
    known = _load_known()
    # en clair (learn local) + haché (base publique)
    traps_clear = {str(x).lower() for x in known.get("known_traps", [])}
    payers_clear = {str(x).lower() for x in known.get("known_payers", [])}
    traps_hash = set(known.get("known_traps_hashes", []))
    payers_hash = set(known.get("known_payers_hashes", []))

    owner = str(data.get("owner_login") or "").lower()
    full = str(data.get("full_name") or "").lower()
    owner_hash = _sha256(owner) if owner else ""
    full_hash = _sha256(full) if full else ""

    # trap ? (compte ou repo, en clair ou haché)
    in_trap = (owner in traps_clear or full in traps_clear
               or owner_hash in traps_hash or full_hash in traps_hash)
    if in_trap:
        return {"points": 1, "force": "PIEGE", "detail": f"Compte/dépôt connu dans la liste des pièges ({owner})"}

    # payer ?
    in_payer = (full in payers_clear or owner in payers_clear
                or full_hash in payers_hash or owner_hash in payers_hash)
    if in_payer:
        return {"points": 0, "force": "VRAI", "detail": f"Dépôt connu comme payeur fiable ({full})"}

    return {"points": 0, "detail": "Aucune entrée en mémoire terrain (neutre)"}
