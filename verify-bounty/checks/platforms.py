# Plateformes de récompense reconnues (item 5).
# Détection partagée entre le collecteur (verify_bounty.py) et le check
# reward_link. Chaque plateforme a un domaine et un marqueur de page
# « récompense disponible » pour la vérification du lien.

import re

# Domaine -> (nom plateforme, mot-clés de disponibilité dans le HTML)
PLATFORMS = {
    "opire.dev": ("opire", ["available", "reward", "bounty"]),
    "algora.io": ("algora", ["reward", "bounty", "available"]),
    "algora.xyz": ("algora", ["reward", "bounty", "available"]),
    "grantfox.xyz": ("grantfox", ["reward", "bounty"]),
    "grantfox.io": ("grantfox", ["reward", "bounty"]),
    "polar.sh": ("polar", ["bounty", "issue", "funded"]),
    "gitcoin.co": ("gitcoin", ["bounty", "funded"]),
    "bounties.github.com": ("github", ["bounty"]),
}

# Cherche un lien de récompense reconnu dans le corps de l'issue.
REWARD_URL_RE = re.compile(r"https?://([^/\s)\]]+)", re.I)


def extract_reward_link(body: str):
    """Retourne (url, plateforme) du premier lien de récompense reconnu, ou (None, None)."""
    if not body:
        return None, None
    for m in REWARD_URL_RE.finditer(body):
        host = (m.group(1) or "").lower().rstrip(".,;")
        for domain, (name, _kw) in PLATFORMS.items():
            if host == domain or host.endswith("." + domain):
                return m.group(0).rstrip(".,;"), name
    return None, None


def is_known_platform_url(url: str):
    """True si l'URL pointe vers une plateforme de récompense reconnue."""
    if not url:
        return False
    m = REWARD_URL_RE.search(url)
    if not m:
        return False
    host = m.group(1).lower().rstrip(".,;")
    return any(host == d or host.endswith("." + d) for d in PLATFORMS)


def availability_keywords(url: str):
    """Retourne la liste des mots-clés de disponibilité pour une URL, ou None."""
    m = REWARD_URL_RE.search(url or "")
    if not m:
        return None
    host = m.group(1).lower().rstrip(".,;")
    for domain, (_name, kw) in PLATFORMS.items():
        if host == domain or host.endswith("." + domain):
            return kw
    return None
