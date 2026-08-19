# i18n FR/EN pour Vérif'Bounty (item 11).
# LANG contient les libellés d'affichage et de rapport dans les deux langues.
# Les status (PIEGE/SANS_PREUVE/PAIEUR_PROUVE, PRIS/CONTESTE/LIBRE/INCONNU)
# restent des codes ASCII stables dans le JSON ; seuls les libellés humains
# changent selon la langue.

LANG = {
    "target": {"fr": "Cible", "en": "Target"},
    "title": {"fr": "Titre", "en": "Title"},
    "confidence_auth": {"fr": "CONFIANCE AUTHENTICITÉ", "en": "AUTHENTICITY CONFIDENCE"},
    "risk_note": {"fr": "note de risque", "en": "risk score"},
    "authenticity": {"fr": "AUTHENTICITÉ", "en": "AUTHENTICITY"},
    "exploitability": {"fr": "EXPLOITABILITÉ", "en": "EXPLOITABILITY"},
    "verdict_reliability": {"fr": "Fiabilité du verdict", "en": "Verdict reliability"},
    "recommendation": {"fr": "Recommandation", "en": "Recommendation"},
    "forced_memory": {"fr": "forcé par mémoire terrain", "en": "forced by field memory"},
    "report_title": {"fr": "Rapport d'audit Vérif'Bounty", "en": "Vérif'Bounty audit report"},
    "report_meta": {"fr": "Métadonnées", "en": "Metadata"},
    "report_checks": {"fr": "Vérifications détaillées", "en": "Detailed checks"},
    "report_platform": {"fr": "Plateforme de récompense", "en": "Reward platform"},
    "no_claim": {"fr": "aucun", "en": "none"},
    "a_verifier": {"fr": "À VÉRIFIER", "en": "TO VERIFY"},
}

# Libellés humains des axes (status ASCII -> texte affiché selon langue)
AUTH_LABEL = {
    "PIEGE": {"fr": "PIÈGE", "en": "TRAP"},
    "SANS_PREUVE": {"fr": "SANS PREUVE", "en": "UNPROVEN"},
    "PAIEUR_PROUVE": {"fr": "PAYEUR PROUVÉ", "en": "PROVEN PAYER"},
}
EXPL_LABEL = {
    "PRIS": {"fr": "PRIS", "en": "TAKEN"},
    "CONTESTE": {"fr": "CONTESTÉ", "en": "CONTESTED"},
    "LIBRE": {"fr": "LIBRE", "en": "OPEN"},
    "INCONNU": {"fr": "INCONNU", "en": "UNKNOWN"},
}

# Icônes (indépendantes de la langue)
AUTH_ICON = {"PIEGE": "🚨", "SANS_PREUVE": "⚠️", "PAIEUR_PROUVE": "✅"}
EXPL_ICON = {"PRIS": "🔒", "CONTESTE": "⚔️", "LIBRE": "🟢", "INCONNU": "❔"}


def t(lang, key):
    """Traduit une clé selon la langue (fr par défaut)."""
    entry = LANG.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("fr", key))


def auth_label(lang, status):
    return AUTH_LABEL.get(status, {}).get(lang, status)


def expl_label(lang, status):
    return EXPL_LABEL.get(status, {}).get(lang, status)
