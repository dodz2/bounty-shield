# Vérification 7 — Preuve du lien de récompense réel (multi-plateformes, item 5)
# Un vrai bounty Opire/Algora/GrantFox/Polar a une page de récompense (lien
# vérifié, statut « Available »). L'usine à faux bounties colle des labels
# `opire`/`bounty` SANS aucun lien vérifiable : revendication non prouvée.
# Désormais la vérification du lien couvre toutes les plateformes reconnues.
# Score :
#   - label opire/bounty + lien vérifié      -> 0 point (preuve positive)
#   - label opire/bounty sans lien vérifié   -> 1 point (revendication non prouvée)
#   - pas de label opire/bounty              -> 0 point (neutre)

from .platforms import is_known_platform_url


def _has_reward_label(data: dict) -> bool:
    for label in (data.get("issue_labels") or []):
        low = str(label).lower()
        if any(k in low for k in ("opire", "bounty", "reward", "algora", "polar", "grantfox")):
            return True
    return False


def run(data: dict, rules: dict) -> dict:
    if not _has_reward_label(data):
        return {"points": 0, "detail": "Pas de revendication de récompense via labels (neutre)"}

    verified = data.get("reward_verified")
    url = data.get("reward_url")
    # Si un lien existe mais n'a pas été vérifié, et qu'il n'est pas une
    # plateforme reconnue, on signale une revendication sur un lien tiers.
    if url and not is_known_platform_url(url):
        return {"points": 1, "detail": "Label récompense mais lien vers une plateforme non reconnue"}

    if verified is True:
        return {"points": 0, "detail": "Lien de récompense vérifié sur la plateforme"}
    if verified is False:
        return {"points": 1, "detail": "Label récompense mais lien NON vérifié (revendication non prouvée)"}
    return {"points": 1, "detail": "Label récompense sans lien vérifiable (vérification non effectuée)"}
