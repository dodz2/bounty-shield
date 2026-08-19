# Vérification 10 — Historique de paiement
# Un dépôt qui a déjà des issues fermées avec label « 💰 Reward » a un
# historique de récompenses. IMPORTANT : l'usine peut simuler cet historique
# (constaté sur trapuser04/sqlc et trapuser05/kubernetes) — ce check n'est
# donc qu'une couche de nuance, jamais une preuve à lui seul.
# Score :
#   - paid_history=True (issues Reward fermées)  -> 0 point (indice de confiance)
#   - paid_history=False + labels opire/bounty   -> 1 point (revendique sans historique)
#   - paid_history=False sans labels             -> 0 point (neutre)
#   - paid_history inconnu                       -> 0 point (neutre)

def _has_reward_label(data: dict) -> bool:
    for label in (data.get("issue_labels") or []):
        low = str(label).lower()
        if "opire" in low or "bounty" in low:
            return True
    return False


def run(data: dict, rules: dict) -> dict:
    paid = data.get("paid_history")
    if paid is True:
        return {"points": 0, "detail": "Historique de paiement détecté (issues Reward fermées)"}
    if paid is False:
        if _has_reward_label(data):
            return {"points": 1, "detail": "Revendique une récompense mais aucun historique de paiement"}
        return {"points": 0, "detail": "Aucun historique de paiement (neutre sans revendication)"}
    return {"points": 0, "detail": "Historique de paiement non vérifié (neutre)"}