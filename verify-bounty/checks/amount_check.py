# Vérification 5 — Montant annoncé (multi-devises, item 5)
# Les faux bounties annoncent des montants ronds et faibles ($10, $20, 10 XLM)
# dans le titre ou les labels. Les vrais bounties observés (openselfservice,
# trovu) annoncent $20-30+ avec un mécanisme de récompense réel.
# On détecte désormais montant + devise : $ / USD / USDC / USDT / EUR / XLM /
# ETH / XMR / MYZ / GSD / RTC / AIPOU / SOL / BTC / BNB. Absence = neutre.
# Score : montant détecté <= seuil (20 en équivalent-unitaire) -> 1 point.
# Règle honnête : les devises sont volatiles, on compare le nombre annoncé au
# seuil (un bounty à 10 XLM ou 10 $ est aussi faible qu'un à 10 USD).

import re

AMOUNT_RE = re.compile(
    r"(?:[\$\€]\s?([0-9]+(?:[.,][0-9]+)?)|([0-9]+(?:[.,][0-9]+)?)\s?(USD|USDC|USDT|EUR|XLM|ETH|XMR|SOL|BTC|BNB|MYZ|GSD|RTC|AIPOU))",
    re.I,
)


def _find_amount(data: dict):
    """Cherche montant + devise dans le titre, les labels et le corps.

    Retourne (nombre_entier, devise) ou (None, None).
    """
    hay = " ".join([
        str(data.get("issue_title") or ""),
        " ".join(str(l) for l in (data.get("issue_labels") or [])),
        str(data.get("issue_body_sample") or ""),
    ])
    m = AMOUNT_RE.search(hay)
    if not m:
        return None, None
    if m.group(1) is not None:
        return float(m.group(1).replace(",", ".")), "USD"
    return float(m.group(2).replace(",", ".")), (m.group(3) or "?").upper()


def run(data: dict, rules: dict) -> dict:
    amount, currency = _find_amount(data)
    threshold = int(rules.get("min_amount_usd", 20))
    if amount is None:
        return {"points": 0, "detail": "Aucun montant détecté (neutre)"}
    suspect = amount <= threshold
    flag = "🛑" if suspect else "✅"
    return {
        "points": 1 if suspect else 0,
        "detail": f"Montant annoncé: {amount} {currency} (seuil: {threshold} équivalent-unité) — {flag}",
    }
