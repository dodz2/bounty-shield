#!/usr/bin/env python3
"""Vérif'Bounty — mode veille multi-repos.

Surveille une liste de dépôts (watchlist.json) et signale les issues ouvertes
portant un label de récompense (💰 Reward), analysées par Vérif'Bounty.

Usage :
    python3 tools/veille.py [--watchlist watchlist.json] [--json]

Chaque repo de la watchlist est scanné : on cherche ses issues OUVERTES avec
le label « 💰 Reward ». Chacune est ensuite analysée en profondeur
(collecte complète + scoring + confiance). Sortie : une ligne par issue, ou
JSON complet avec --json.

Compatible cron : sortie stable si aucun changement (voir watchman).
"""
import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scorer import load_rules, score  # noqa: E402
from verify_bounty import (  # noqa: E402
    API,
    collect_from_url,
    fetch_json,
    print_report,
)

REWARD_LABEL = "💰 Reward"


def find_open_reward_issues(owner, repo):
    """Cherche les issues ouvertes avec label Reward sur un dépôt.

    Retourne une liste d'URLs d'issues. Vide si aucune. [] en cas d'erreur.
    """
    q = f"repo:{owner}/{repo} is:issue state:open label:\"{REWARD_LABEL}\""
    try:
        url = f"{API}/search/issues?q={urllib.parse.quote(q)}&per_page=50"
        data = fetch_json(url)
        return [it["html_url"] for it in data.get("items", [])]
    except Exception:
        return []


def run_watch(watchlist_path, as_json=False, sleep=1.0):
    watch = json.loads(Path(watchlist_path).read_text(encoding="utf-8"))
    repos = watch.get("repos", [])
    rules = load_rules()
    reports = []

    for full in repos:
        if "/" not in full:
            continue
        owner, repo = full.split("/", 1)
        urls = find_open_reward_issues(owner, repo)
        if not urls:
            if not as_json:
                print(f"ℹ️  {full} : aucune issue Reward ouverte")
            continue
        for url in urls:
            try:
                data = collect_from_url(url)
                result = score(data, rules)
                reports.append({"repo": full, "data": data, "result": result})
                if not as_json:
                    auth = result["authenticity"]["status"]
                    expl = result["exploitability"]["status"]
                    flag = {"PIEGE": "🚨", "SANS_PREUVE": "⚠️", "PAIEUR_PROUVE": "✅"}.get(auth, "?")
                    print(f"{flag} {auth:12} | {expl:8} | conf {round(10-result['note'],1):>4}/10  {full} #{data.get('issue_number')}")
            except Exception as e:
                if not as_json:
                    print(f"❌ ERREUR   {url}  ({e})")
            time.sleep(sleep)

    if as_json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        print(f"\nVeille terminée : {len(reports)} issue(s) analysée(s) sur {len(repos)} repo(s).")
    return 0


def main():
    p = argparse.ArgumentParser(description="Vérif'Bounty — veille multi-repos")
    p.add_argument("--watchlist", default=str(ROOT / "watchlist.json"), help="fichier JSON de dépôts à surveiller")
    p.add_argument("--json", action="store_true", help="sortie JSON")
    args = p.parse_args()
    return run_watch(args.watchlist, as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())