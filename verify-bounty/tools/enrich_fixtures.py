import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.github.com"


def api(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "daedalus-verify-bounty-enrich/1.0",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def enrich():
    fixtures_dir = Path("/opt/data/daedalus/daedalus-bounties/verify-bounty/tests/fixtures")
    for f in sorted(fixtures_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        full = data.get("full_name") or ""
        owner, repo = full.split("/")
        try:
            r = api(f"/repos/{owner}/{repo}")
            data["repo_created"] = r.get("created_at")
            # Historique de paiement : issues fermées avec label 💰 Reward
            q = f'repo:{owner}/{repo} is:issue state:closed label:"\U0001f4b0 Reward"'
            s = api("/search/issues?q=" + urllib.parse.quote(q) + "&per_page=1")
            data["paid_history"] = s.get("total_count", 0) > 0
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[OK] {full}: repo_created={data['repo_created']} paid_history={data['paid_history']}")
        except Exception as e:
            print(f"[ERR] {full}: {str(e)[:80]}")
        time.sleep(0.5)


if __name__ == "__main__":
    enrich()