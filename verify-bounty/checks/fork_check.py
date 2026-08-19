# Vérification 1 — Le dépôt est-il un fork ?
# Le pattern des faux bounties détectés en 2026-08-18 consiste à forker un
# dépôt populaire (caddy, traefik, kubernetes…) et à y déposer une issue #1
# « 🎯 Fix… » avec un label opire/bounty. Un fork n'est pas toujours un piège,
# mais c'est un signal fort combiné aux autres.
# Score : fork = True -> 1 point.

def run(data: dict, rules: dict) -> dict:
    fork = bool(data.get("repo_fork"))
    return {
        "points": 1 if fork else 0,
        "detail": f"Le dépôt est un fork: {fork}",
    }