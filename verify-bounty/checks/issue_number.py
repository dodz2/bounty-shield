# Vérification 4 — Numéro de l'issue
# Le pattern d'usine : chaque faux repo n'a qu'UNE issue, la numéro 1, posée
# par le compte fraîchement créé. Un vrai dépôt qui récompense a généralement
# une activité d'issues antérieure.
# Score : issue_number <= seuil (1 par défaut) -> 1 point.

def run(data: dict, rules: dict) -> dict:
    number = int(data.get("issue_number") or 0)
    threshold = int(rules.get("issue_number_threshold", 1))
    suspect = number <= threshold
    return {
        "points": 1 if suspect else 0,
        "detail": f"Issue #{number} (seuil: #{threshold})",
    }