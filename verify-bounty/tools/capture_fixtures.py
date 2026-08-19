import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.github.com"
CLAIM_RE = re.compile(r"/claim|claiming|claim\s+this|je\s+prends|i'?ll\s+(?:take|claim)", re.I)

# Jeu de référence : 5 pièges de l'usine à faux bounties + 2 vrais (payés/actifs).
TARGETS = [
    ("trapuser01/caddy#1", "piege"),
    ("trapuser02/nats.go#1", "piege"),
    ("trapuser03/fiber#1", "piege"),
    ("trapuser04/sqlc#1", "piege"),
    ("trapuser05/kubernetes#5", "piege"),
    ("o2sdev/openselfservice#354", "vrai"),
    ("trovu/trovu#329", "vrai"),
]


def api(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "daedalus-verify-bounty-capture/1.0",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def paid_history(owner: str, repo: str):
    q = f"repo:{owner}/{repo} is:issue state:closed label:\"\U0001f4b0 Reward\""
    try:
        s = api("/search/issues?q=" + urllib.parse.quote(q) + "&per_page=1")
        return s.get("total_count", 0) > 0
    except Exception:
        return None


def open_reward_issues(owner: str, repo: str):
    q = f"repo:{owner}/{repo} is:issue state:open label:\"\U0001f4b0 Reward\""
    try:
        s = api("/search/issues?q=" + urllib.parse.quote(q) + "&per_page=1")
        return int(s.get("total_count", 0))
    except Exception:
        return None


def issue_concurrency(owner: str, repo: str, num: str):
    """Comptage des claims (commentaires) et PR référençant l'issue."""
    claims, open_prs, merged = 0, 0, False
    try:
        comments = api(f"/repos/{owner}/{repo}/issues/{num}/comments?per_page=100")
        claims = sum(1 for c in comments if CLAIM_RE.search(c.get("body") or ""))
    except Exception:
        claims = None
    try:
        q = f"repo:{owner}/{repo} is:pr \"#{num}\""
        s = api("/search/issues?q=" + urllib.parse.quote(q) + "&per_page=100")
        for pr in s.get("items", []):
            if "pull_request" not in pr:
                continue
            if pr.get("state") == "open":
                open_prs += 1
            if pr.get("merged_at"):
                merged = True
    except Exception:
        open_prs, merged = None, False
    return claims, open_prs, merged


def main():
    out_dir = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
    out_dir.mkdir(parents=True, exist_ok=True)
    for target, kind in TARGETS:
        full, num = target.split("#")
        owner, repo = full.split("/")
        try:
            r = api(f"/repos/{owner}/{repo}")
            u = api(f"/users/{owner}")
            i = api(f"/repos/{owner}/{repo}/issues/{num}")
        except Exception as e:
            print(f"[ERR] {target}: {e}")
            continue
        claims, open_prs, merged = issue_concurrency(owner, repo, num)
        fixture = {
            "kind": kind,
            "full_name": r.get("full_name"),
            "issue_number": i.get("number"),
            "issue_title": i.get("title"),
            "issue_state": i.get("state"),
            "issue_labels": [l["name"] for l in i.get("labels", [])],
            "issue_created": i.get("created_at"),
            "issue_body_sample": (i.get("body") or "")[:400],
            "repo_fork": r.get("fork"),
            "repo_stars": r.get("stargazers_count", 0),
            "repo_archived": r.get("archived"),
            "repo_license": (r.get("license") or {}).get("spdx_id", ""),
            "repo_created": r.get("created_at"),
            "repo_pushed_at": r.get("pushed_at"),
            "open_reward_issues": open_reward_issues(owner, repo),
            "paid_history": paid_history(owner, repo),
            "claims": claims,
            "open_pr_count": open_prs,
            "merged_pr_for_issue": merged,
            "owner_login": u.get("login"),
            "owner_created": u.get("created_at"),
            "owner_type": u.get("type"),
            "_note": "Donnees publiques capturees via API GitHub pour tests hors-ligne.",
        }
        fname = f"{owner}-{repo}-issue-{num}.json"
        (out_dir / fname).write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] {kind:5} {target} -> {fname}")
        time.sleep(0.6)


if __name__ == "__main__":
    main()