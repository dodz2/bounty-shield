# Vérif'Bounty — moteur de scoring
# Agrège les vérifications en une note pondérée sur 10, puis dérive DEUX axes
# indépendants : l'authenticité (le dépôt paie-t-il vraiment ?) et
# l'exploitabilité (le bounty est-il encore gagnable ?).
# Usage interne : verify_bounty.py l'utilise, les tests l'utilisent.

import importlib
import json
from pathlib import Path

CHECKS = [
    "fork_check",
    "account_age",
    "stars_check",
    "issue_number",
    "amount_check",
    "pattern_check",
    "reward_link",
    "clone_check",
    "payment_history",
    "known_list",
    "repo_liveness",
]

DEFAULT_RULES = {
    "account_age_days_threshold": 30,
    "account_age_band_young": 14,
    "account_age_band_recent": 30,
    "account_age_band_old": 90,
    "stars_threshold": 0,
    "issue_number_threshold": 1,
    "min_amount_usd": 20,
    "clone_gap_days": 7,
    "liveness_stale_days": 90,
    "suspicious_titles": ["🎯", "Fix:", "[BOUNTY]"],
    "weights": {
        "fork_check": 1,
        "account_age": 10,
        "stars_check": 10,
        "issue_number": 5,
        "amount_check": 2,
        "pattern_check": 1,
        "reward_link": 2,
        "clone_check": 4,
        "payment_history": 3,
        "known_list": 10,
        "repo_liveness": 4,
    },
    "verdicts": {"vrai": 2.0, "a_verifier": 4.9, "piege": 4.7},
}


def load_rules(path=None) -> dict:
    rules_path = path or (Path(__file__).parent / "rules.json")
    if rules_path.exists():
        with open(rules_path, encoding="utf-8") as f:
            return {**DEFAULT_RULES, **json.load(f)}
    return json.loads(json.dumps(DEFAULT_RULES))


# --- Axe EXPLOITABILITÉ ------------------------------------------------
# LIBRE    : aucune concurrence visible (aucun claim, aucune PR ouverte)
# CONTESTÉ : quelqu'un a claimé et/ou a une PR ouverte
# PRIS     : une PR a déjà été fusionnée OU l'issue est fermée (terminé)
# INCONNU  : données de concurrence absentes (ne pas inventer un verdict)
def build_exploitability(data: dict, rules: dict) -> dict:
    claims = data.get("claims")
    open_prs = data.get("open_pr_count")
    merged = data.get("merged_pr_for_issue")
    issue_state = data.get("issue_state")

    # PR fusionnée qui référence l'issue -> pris
    if merged is True:
        return {"status": "PRIS", "detail": "Une PR fusionnée référence cette issue"}
    # issue fermée -> terminé (mais si explicitement marquée closed, c'est fini)
    if issue_state == "closed":
        return {"status": "PRIS", "detail": "Issue fermée (terminée)"}

    # données de concurrence absentes
    if claims is None and open_prs is None:
        return {"status": "INCONNU", "detail": "Concurrence non collectée (données absentes)"}

    claims = int(claims or 0)
    open_prs = int(open_prs or 0)
    if claims == 0 and open_prs == 0:
        return {"status": "LIBRE", "detail": "Aucun claim, aucune PR ouverte (libre)"}
    return {
        "status": "CONTESTE",
        "detail": f"{claims} claim(s), {open_prs} PR ouverte(s) — concurrence active",
    }


# --- Axe AUTHENTICITÉ --------------------------------------------------
# Détermine si le dépôt PAie réellement.
#  - PIÈGE         : fortement suspect (usine à faux bounties)
#  - PAIEUR_PROUVE : preuve de paiement réelle (historique / connu / PR fusionnée)
#  - SANS_PREUVE   : pas piégé mais AUCUNE preuve de paiement
def build_authenticity(data: dict, result: dict, rules: dict) -> dict:
    forced = result.get("forced")
    note = result["note"]
    paid_history = data.get("paid_history")
    known_payer = any(c["name"] == "known_list" and c.get("force") == "VRAI" for c in result["checks"])
    merged_pr = bool(data.get("merged_pr_for_issue"))

    # PRÉCÉDENCE : un piège (forcé OU note de risque élevée) l'emporte TOUJOURS
    # sur toute preuve de paiement — l'usine forge des historiques.
    if forced == "PIEGE":
        return {"status": "PIEGE", "detail": "Forcé par la mémoire terrain (compte piège)"}
    if note >= rules["verdicts"]["piege"]:
        return {"status": "PIEGE", "detail": f"Note de risque {note}/10 ≥ {rules['verdicts']['piege']}/10 (piège détecté, historique possiblement forgé)"}
    if known_payer or paid_history is True or merged_pr:
        return {"status": "PAIEUR_PROUVE", "detail": "Preuve de paiement détectée (historique / dépôt connu / PR fusionnée)"}
    return {"status": "SANS_PREUVE", "detail": "Signaux non piégés mais aucune preuve de paiement vérifiée"}


def build_confidence(data: dict, result: dict) -> dict:
    """Évalue la fiabilité du verdict et produit une recommandation.

    - confidence : /10 — fiabilité estimée du verdict (données manquantes et
      convergence des signaux). Forcé par la mémoire terrain = 10.
    - active_signals : liste des checks pénalisés.
    - missing_data : champs critiques absents (réduisent la confiance).
    - recommendation : action concrète suggérée à l'humain.
    """
    checks = result["checks"]
    active = [c for c in checks if c["points"]]

    critical_fields = [
        "owner_created", "repo_stars", "issue_number",
        "issue_title", "issue_labels",
    ]
    missing = [f for f in critical_fields if data.get(f) is None or data.get(f) == ""]

    labels = [str(l).lower() for l in (data.get("issue_labels") or [])]
    claims_reward = any("opire" in l or "bounty" in l for l in labels)
    if claims_reward and data.get("reward_verified") is None:
        missing.append("reward_verified")
    if data.get("paid_history") is None and not data.get("repo_fork"):
        missing.append("paid_history")

    confidence = 8 - min(3, len(missing))

    if result["forced"]:
        confidence = 10
    elif result["authenticity"]["status"] == "PIEGE":
        if result["note"] >= 7.0:
            confidence = min(10, confidence + 1)
        else:
            confidence = max(4, confidence - 1)
    elif result["authenticity"]["status"] == "SANS_PREUVE":
        confidence = min(6, confidence)

    auth = result["authenticity"]["status"]
    if auth == "PIEGE":
        rec = "Ne pas engager de travail sur ce bounty. Signaux : " + (
            ", ".join(c["name"] for c in active) if active else "aucun"
        ) + "."
    elif auth == "PAIEUR_PROUVE":
        rec = "Dépôt payeur vérifié. Vérifier la concurrence (exploitabilité) et les commentaires avant de commencer."
    else:
        strong_missing = [
            n for n in ("account_age", "stars_check")
            if not any(c["name"] == n and c["points"] for c in checks)
        ]
        rec = "Aucune preuve de paiement vérifiée. Vérifier l'historique et la page de récompense avant d'engager du temps. Signal fort manquant : " + (
            ", ".join(strong_missing) if strong_missing else "aucun"
        ) + "."

    return {
        "confidence": confidence,
        "missing_data": missing,
        "active_signals": [c["name"] for c in active],
        "recommendation": rec,
    }


def score(data: dict, rules: dict = None) -> dict:
    """Retourne: {points, note, forced, authenticity, exploitability, confidence, checks}"""
    rules = rules or load_rules()
    weights = rules.get("weights", {})
    results = []
    total = 0
    max_weight = 0
    forced = None

    for name in CHECKS:
        mod = importlib.import_module(f"checks.{name}")
        res = mod.run(data, rules)
        weight = int(weights.get(name, 1))
        res["name"] = name
        res["weight"] = weight
        res["points"] = float(res["points"])
        total += res["points"] * weight
        max_weight += weight
        if res.get("force"):
            forced = res["force"]
        results.append(res)

    note = round(total * 10 / max_weight, 1) if max_weight else 0.0

    if forced == "PIEGE":
        verdict = "PIEGE"
        note = 10.0
    elif forced == "VRAI":
        verdict = "VRAI"
        note = 0.0
    elif note >= rules["verdicts"]["piege"]:
        verdict = "PIEGE"
    elif note <= rules["verdicts"]["vrai"]:
        verdict = "VRAI"
    else:
        verdict = "A_VERIFIER"

    result = {
        "points": total, "note": note, "verdict": verdict, "forced": forced,
        "checks": results,
    }
    # Deux axes indépendants
    result["authenticity"] = build_authenticity(data, result, rules)
    result["exploitability"] = build_exploitability(data, rules)
    result["confidence"] = build_confidence(data, result)
    return result
