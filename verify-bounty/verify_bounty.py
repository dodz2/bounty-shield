#!/usr/bin/env python3
"""Vérif'Bounty — anti-faux-bounties.

Analyse un bounty (issue GitHub) et répond : VRAI / À VÉRIFIER / PIÈGE,
avec une note sur 10 et le détail de chaque vérification.

Usage :
    python3 verify_bounty.py --fixture tests/fixtures/<fichier>.json
    python3 verify_bounty.py --url https://github.com/owner/repo/issues/123
    python3 verify_bounty.py --all-fixtures
    python3 verify_bounty.py --list liste.txt        # batch : une cible par ligne
    python3 verify_bounty.py --url ... --json        # sortie JSON (intégration)

Mode --url : interroge l'API publique GitHub. Gère la limite de débit avec
retry/backoff automatiques ; utilise GH_TOKEN (env) si présent pour un quota
supérieur. Une cible coûte ~4 requêtes (repo, user, issue, search).
Mode --list : fichier avec une cible par ligne (URL GitHub OU chemin de
fixture JSON). Sortie : une ligne par cible (verdict | note | cible).
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from scorer import load_rules, score
from checks.platforms import availability_keywords, extract_reward_link
from i18n import AUTH_ICON, EXPL_ICON, auth_label, expl_label, t

API = "https://api.github.com"
MAX_RETRIES = 3


def build_headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "daedalus-verify-bounty/1.1",
    }
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def fetch_json(url, timeout=30):
    """GET JSON avec retry/backoff sur erreurs 403/429/5xx et erreurs réseau."""
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=build_headers())
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (403, 429, 500, 502, 503):
                retry_after = e.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
                wait = min(wait, 30)
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                    continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
                continue
    raise RuntimeError(f"API injoignable après {MAX_RETRIES} tentatives: {last_err}")


def verify_reward_link(url: str):
    """Tente de vérifier qu'un lien de récompense est réel et disponible.

    Retourne True si la page répond et mentionne un marqueur de disponibilité
    (selon la plateforme reconnue), False si injoignable/invalide, None si non
    vérifiable (URL absente ou plateforme inconnue).
    """
    if not url:
        return None
    keywords = availability_keywords(url)
    if keywords is None:
        return None  # plateforme inconnue -> non vérifiable
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "daedalus-verify-bounty/1.2",
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read(200_000).decode("utf-8", errors="ignore")
            low = body.lower()
            return any(k in low for k in keywords)
    except Exception:
        return False


def collect_paid_history(owner: str, repo: str):
    """Historique de paiement : issues fermées avec label 💰 Reward.

    True = au moins une issue Reward fermée (indice de confiance, simulable).
    False = aucune ; None = erreur de collecte.
    """
    try:
        q = f"repo:{owner}/{repo} is:issue state:closed label:\"\U0001f4b0 Reward\""
        url = f"{API}/search/issues?q={urllib.parse.quote(q)}&per_page=1"
        data = fetch_json(url)
        return data.get("total_count", 0) > 0
    except Exception:
        return None


def collect_open_reward_issues(owner: str, repo: str):
    """Nombre d'issues ouvertes label 💰 Reward sur le dépôt (int|None)."""
    try:
        q = f"repo:{owner}/{repo} is:issue state:open label:\"\U0001f4b0 Reward\""
        url = f"{API}/search/issues?q={urllib.parse.quote(q)}&per_page=1"
        data = fetch_json(url)
        return int(data.get("total_count", 0))
    except Exception:
        return None


CLAIM_RE = re.compile(r"/claim|claiming|claim\s+this|je\s+prends|i'?ll\s+(?:take|claim)", re.I)


def collect_issue_comments(owner: str, repo: str, issue: str):
    """Analyse les commentaires d'une issue pour estimer la concurrence.

    Retourne (claims, open_pr_count, merged_pr_for_issue, issue_state).
    claims = nb de commentaires de type « claim ».
    open_pr_count / merged_pr_for_issue : estimés via la recherche de PR
    référençant l'issue (PR ouvertes vs fusionnées).
    """
    claims = 0
    try:
        url = f"{API}/repos/{owner}/{repo}/issues/{issue}/comments?per_page=100"
        comments = fetch_json(url)
        for c in comments:
            if CLAIM_RE.search(c.get("body") or ""):
                claims += 1
    except Exception:
        claims = None

    open_prs, merged_pr = 0, False
    try:
        q = f"repo:{owner}/{repo} is:pr \"#{issue}\""
        url = f"{API}/search/issues?q={urllib.parse.quote(q)}&per_page=100"
        data = fetch_json(url)
        for pr in data.get("items", []):
            if "pull_request" not in pr:
                continue
            if pr.get("state") == "open":
                open_prs += 1
            if pr.get("merged_at"):
                merged_pr = True
    except Exception:
        open_prs, merged_pr = None, False

    return claims, open_prs, merged_pr


def collect_from_url(url: str) -> dict:
    """Construit le profil à partir d'une URL d'issue GitHub."""
    # https://github.com/owner/repo/issues/N
    parts = url.rstrip("/").split("/")
    try:
        owner, repo, issue = parts[-4], parts[-3], parts[-1]
        assert parts[-2] == "issues"
    except Exception:
        raise SystemExit(f"URL non reconnue: {url} (attendu .../owner/repo/issues/N)")

    repo_data = fetch_json(f"{API}/repos/{owner}/{repo}")
    user_data = fetch_json(f"{API}/users/{owner}")
    issue_data = fetch_json(f"{API}/repos/{owner}/{repo}/issues/{issue}")

    body = issue_data.get("body") or ""
    reward_url, reward_platform = extract_reward_link(body)

    claims, open_prs, merged_pr = collect_issue_comments(owner, repo, issue)

    return {
        "full_name": repo_data.get("full_name"),
        "issue_number": issue_data.get("number"),
        "issue_title": issue_data.get("title"),
        "issue_state": issue_data.get("state"),
        "issue_labels": [l["name"] for l in issue_data.get("labels", [])],
        "issue_created": issue_data.get("created_at"),
        "issue_body_sample": body[:400],
        "reward_url": reward_url,
        "reward_platform": reward_platform,
        "reward_verified": verify_reward_link(reward_url),
        "repo_fork": repo_data.get("fork"),
        "repo_stars": repo_data.get("stargazers_count", 0),
        "repo_archived": repo_data.get("archived"),
        "repo_license": (repo_data.get("license") or {}).get("spdx_id", ""),
        "repo_created": repo_data.get("created_at"),
        "repo_pushed_at": repo_data.get("pushed_at"),
        "open_reward_issues": collect_open_reward_issues(owner, repo),
        "paid_history": collect_paid_history(owner, repo),
        "claims": claims,
        "open_pr_count": open_prs,
        "merged_pr_for_issue": merged_pr,
        "owner_login": user_data.get("login"),
        "owner_created": user_data.get("created_at"),
    }


def print_report(data: dict, result: dict, lang: str = "fr") -> None:
    print("=" * 60)
    print(f"{t(lang,'target')} : {data.get('full_name', '?')} #{data.get('issue_number', '?')}")
    print(f"{t(lang,'title')} : {data.get('issue_title', '?')}")
    print("-" * 60)
    force_tag = f"  ({t(lang,'forced_memory')})" if result.get("forced") else ""
    conf = result.get("confidence", {})
    auth = result.get("authenticity", {})
    expl = result.get("exploitability", {})
    # Item 2 : la confiance (10 - note) en tête, puis les deux axes
    trust = round(10 - result["note"], 1)
    print(f"{t(lang,'confidence_auth')} : {trust}/10   ({t(lang,'risk_note')} {result['note']}/10){force_tag}")
    print(f"{t(lang,'authenticity')}  : {AUTH_ICON.get(auth.get('status','?'),'?')} {auth_label(lang, auth.get('status','?'))}  — {auth.get('detail','')}")
    print(f"{t(lang,'exploitability')}: {EXPL_ICON.get(expl.get('status','?'),'?')} {expl_label(lang, expl.get('status','?'))}  — {expl.get('detail','')}")
    if conf:
        print(f"{t(lang,'verdict_reliability')} : {conf.get('confidence', '?')}/10")
        print(f"{t(lang,'recommendation')} : {conf.get('recommendation', '')}")
    print("-" * 60)
    for c in result["checks"]:
        flag = "🛑" if c["points"] else "✅"
        print(f"  {flag} {c['name']:16} ×{c['weight']}  {c['detail']}")
    print("=" * 60)


def load_target(path: str) -> dict:
    """Charge une cible : URL GitHub ou chemin de fixture JSON."""
    if path.startswith("http"):
        return collect_from_url(path)
    return json.loads(Path(path).read_text(encoding="utf-8"))


# --- Apprentissage mémoire terrain (item 8) ----------------------------
# Avec --learn, un verdict PIÈGE confirmé (confiance >= 6) ajoute le compte
# propriétaire à known.json (known_traps). Non destructif : refuse d'ajouter
# un payeur connu. Utiliser avec précaution — c'est une écriture sur disque.

def learn_from_piege(data: dict, result: dict) -> bool:
    """Enregistre le compte propriétaire comme piège si le verdict est net.

    Critères : authenticity == PIEGE, fiabilité >= 6, et compte non déjà piégé.
    Retourne True si une écriture a eu lieu, False sinon.
    """
    known_path = Path(__file__).parent / "known.json"
    conf = result.get("confidence", {})
    if result.get("authenticity", {}).get("status") != "PIEGE":
        return False
    if (conf.get("confidence") or 0) < 6:
        return False
    owner = str(data.get("owner_login") or "").strip()
    if not owner or owner.lower() in ("", "unknown"):
        return False

    known = json.loads(known_path.read_text(encoding="utf-8"))
    traps = [str(x).lower() for x in known.get("known_traps", [])]
    payers = [str(x).lower() for x in known.get("known_payers", [])]
    # L'usine est un pattern par-compte : on enregistre le login du propriétaire
    # (convention known.json), jamais le full_name (trop restrictif).
    if owner.lower() in payers or owner.lower() in traps:
        return False
    known["known_traps"] = sorted(set(traps + [owner]), key=str.lower)
    known_path.write_text(json.dumps(known, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def check_quota(verbose: bool = True):
    """Item 7 : informe sur le quota API restant (sans token -> 60/h)."""
    try:
        data = fetch_json(f"{API}/rate_limit")
        core = data.get("resources", {}).get("core", {})
        remaining, limit = core.get("remaining"), core.get("limit")
        if verbose:
            token_note = " (GH_TOKEN)" if os.environ.get("GH_TOKEN") else " (public, sans GH_TOKEN)"
            print(f"ℹ️  Quota API GitHub : {remaining}/{limit} restants{token_note} — mode démo limité à ~6 cibles/h")
        return remaining, limit
    except Exception:
        return None, None


def write_report(data: dict, result: dict, path: str, lang: str = "fr") -> None:
    """Item 9 : génère un rapport d'audit Markdown réutilisable (produit)."""
    auth = result.get("authenticity", {})
    expl = result.get("exploitability", {})
    conf = result.get("confidence", {})
    trust = round(10 - result["note"], 1)
    lines = [
        f"# {t(lang, 'report_title')}",
        "",
        f"- **{t(lang,'target')}** : {data.get('full_name','?')} #{data.get('issue_number','?')}",
        f"- **{t(lang,'title')}** : {data.get('issue_title','?')}",
        "",
        f"## {t(lang,'authenticity')} : {auth_label(lang, auth.get('status','?'))} — {trust}/10",
        "",
        f"{auth.get('detail','')}",
        "",
        f"## {t(lang,'exploitability')} : {expl_label(lang, expl.get('status','?'))}",
        "",
        f"{expl.get('detail','')}",
        "",
        f"## {t(lang,'verdict_reliability')} : {conf.get('confidence','?')}/10",
        "",
        f"**{t(lang,'recommendation')}** : {conf.get('recommendation','')}",
        "",
        f"## {t(lang,'report_checks')}",
        "",
        "| Check | Poids | Résultat |",
        "|---|---|---|",
    ]
    for c in result["checks"]:
        lines.append(f"| {c['name']} | {c['weight']} | {'🛑' if c['points'] else '✅'} {c['detail']} |")
    lines += [
        "",
        f"## {t(lang,'report_meta')}",
        "",
        f"- {t(lang,'report_platform')} : {data.get('reward_platform') or t(lang,'no_claim')}",
        f"- claims : {data.get('claims', '?')} · PR ouvertes : {data.get('open_pr_count', '?')}",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Vérif'Bounty — détecteur de faux bounties")
    p.add_argument("--fixture", help="fichier JSON de données (tests)")
    p.add_argument("--url", help="URL d'une issue GitHub")
    p.add_argument("--all-fixtures", action="store_true", help="scanne toutes les fixtures")
    p.add_argument("--list", metavar="FICHIER", help="batch : une cible par ligne (URL ou fixture)")
    p.add_argument("--json", action="store_true", help="sortie JSON (intégration)")
    p.add_argument("--lang", default="fr", choices=["fr", "en"], help="langue d'affichage et du rapport")
    p.add_argument("--report", metavar="FICHIER.md", help="génère un rapport d'audit Markdown")
    p.add_argument("--learn", action="store_true", help="écrit les pièges confirmés dans known.json")
    p.add_argument("--quota", action="store_true", help="affiche le quota API GitHub puis sort")
    args = p.parse_args()

    if args.quota:
        check_quota()
        return 0

    rules = load_rules()
    fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
    errors = 0

    if args.list:
        lines = [l.strip() for l in Path(args.list).read_text(encoding="utf-8").splitlines() if l.strip()]
        reports = []
        for line in lines:
            try:
                data = load_target(line)
                result = score(data, rules)
                reports.append({"target": line, "data": data, "result": result})
                if args.learn:
                    if learn_from_piege(data, result):
                        print(f"🧠 appris: {data.get('full_name','?')} -> known_traps")
                if not args.json:
                    auth = result["authenticity"]["status"]
                    expl = result["exploitability"]["status"]
                    print(f"{AUTH_ICON.get(auth,'?')} {auth:12} | {EXPL_ICON.get(expl,'?')} {expl:8} | conf {round(10-result['note'],1):>4}/10  {data.get('full_name','?')} #{data.get('issue_number','?')}")
            except Exception as e:
                errors += 1
                print(f"❌ ERREUR      {line}  ({e})")
        if args.json:
            print(json.dumps({"version": "2", "lang": args.lang, "reports": reports}, ensure_ascii=False, indent=2))
        return 2 if errors else 0

    if args.all_fixtures:
        reports = []
        for f in sorted(fixtures_dir.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            result = score(data, rules)
            reports.append({"fixture": f.name, "data": data, "result": result})
            if args.learn:
                learn_from_piege(data, result)
            if not args.json:
                print_report(data, result, lang=args.lang)
        if args.json:
            print(json.dumps({"version": "2", "lang": args.lang, "reports": reports}, ensure_ascii=False, indent=2))
        return 0

    if args.fixture:
        data = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    elif args.url:
        data = collect_from_url(args.url)
    else:
        p.error("préciser --fixture, --url, --all-fixtures ou --list")

    result = score(data, rules)
    if args.learn:
        if learn_from_piege(data, result):
            print(f"🧠 appris: {data.get('full_name','?')} -> known_traps")
    if args.report:
        write_report(data, result, args.report, lang=args.lang)
        print(f"📄 Rapport écrit : {args.report}")
    if args.json:
        print(json.dumps({"version": "2", "lang": args.lang, "data": data, "result": result}, ensure_ascii=False, indent=2))
    else:
        print_report(data, result, lang=args.lang)
    return 0


if __name__ == "__main__":
    sys.exit(main())