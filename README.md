# Bounty-Shield — Vérif'Bounty

**Detect fake open-source bounties before wasting your time on them.**

![CI](https://img.shields.io/github/actions/workflow/status/dodz2/bounty-shield/ci.yml?branch=main&label=CI)
![License](https://img.shields.io/github/license/dodz2/bounty-shield)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)

Bounty-Shield analyzes a GitHub issue carrying a reward label and answers two
independent questions:

1. **AUTHENTICITY** — does this repository actually pay, or is it a trap?
   → `TRAP` / `UNPROVEN` / `PROVEN PAYER`
2. **EXPLOITABILITY** — is this bounty still winnable?
   → `TAKEN` / `CONTESTED` / `OPEN` / `UNKNOWN`

Zero dependencies (Python standard ≥ 3.9). Detection relies on publicly
observable signals (fork, stars, account age, amount, title, history,
repository liveness) plus a **field memory** you feed via `--learn`.

## Why

On 2026-08-18, we identified "fake bounty factories": throwaway accounts post
a single issue on forks of popular repositories, advertise a fixed amount and
a templated title — to get AI agents to work **for free**. This project
automates their detection.

## Installation

```bash
git clone https://github.com/dodz2/bounty-shield.git
cd bounty-shield/verify-bounty
python3 verify_bounty.py --url https://github.com/owner/repo/issues/123
```

## Usage

```bash
# Analyze a GitHub issue (public API, no token ~8 targets/h; with GH_TOKEN ~8000/h)
python3 verify_bounty.py --url https://github.com/owner/repo/issues/123

# Stable JSON output for integration
python3 verify_bounty.py --url ... --json

# Batch: one target per line
python3 verify_bounty.py --list targets.txt

# Markdown audit report + language
python3 verify_bounty.py --url ... --report report.md --lang en|fr

# Learn a confirmed trap (writes to local known.json)
python3 verify_bounty.py --list targets.txt --learn
```

### CLI options

| Option | Effect |
|---|---|
| `--lang en\|fr` | display/report language (default `en`) |
| `--report FILE.md` | writes a Markdown audit report |
| `--learn` | records confirmed traps (reliability ≥ 6) into `known.json` |
| `--quota` | shows remaining GitHub API quota |
| `--json` | stable JSON output (`version 2` envelope) |

### Exit codes

- `0` : analysis succeeded / batch without errors
- `1` : usage error
- `2` : batch `--list` with at least one target in error

## Example output

```text
============================================================
Target : trapuser01/caddy #1
Title : 🎯 Prevent empty request body when reverse_proxy retries failed upstream requests
------------------------------------------------------------
AUTHENTICITY CONFIDENCE : 2.9/10   (risk score 7.1/10)
AUTHENTICITY  : 🚨 TRAP  — Risk score 7.1/10 ≥ 4.7/10 (trap detected, possibly forged history)
EXPLOITABILITY: 🔒 TAKEN  — Issue closed (finished)
Verdict reliability : 8/10
Recommendation : Do not engage work on this bounty. Signals: account_age, stars_check, issue_number, amount_check, pattern_check, reward_link, clone_check, payment_history.
------------------------------------------------------------
  ✅ fork_check       ×1  The repository is a fork: False
  🛑 account_age      ×10  Account very recent (2 d < 14 d) — strong signal
  🛑 stars_check      ×10  0 star(s) (threshold: 0)
  🛑 issue_number     ×5  Issue #1 (threshold: #1)
  🛑 amount_check     ×2  Advertised amount: 10.0 USD (threshold: 20 unit-equivalent) — 🛑
  🛑 pattern_check    ×1  Title starts with "🎯"
  🛑 reward_link      ×2  Reward label without verifiable link (verification not performed)
  🛑 clone_check      ×4  Repo created 0 d after account (threshold: 7 d)
  🛑 payment_history  ×3  Claims a reward but has no payment history
  ✅ known_list       ×10  No entry in field memory (neutral)
  ✅ repo_liveness    ×4  Last push date unknown (neutral)
============================================================
```

## The 11 checks

`fork_check` · `account_age` (graduated) · `stars_check` · `issue_number` ·
`amount_check` (multi-currency) · `pattern_check` · `reward_link`
(multi-platform) · `clone_check` · `payment_history` · `known_list` ·
`repo_liveness`.

The risk score (0-10) aggregates these weighted signals (thresholds in
`rules.json`), then **authenticity** and **exploitability** are derived.

## Field memory (`known.json`)

- `known_traps_hashes` : SHA-256 hashes of identified trap accounts → forces
  a TRAP verdict. **Stored as hashes, never in plain text** — the private
  threat database is never disclosed.
- `known_payers_hashes` : SHA-256 hashes of repositories that actually paid →
  forces a PROVEN PAYER verdict.
- `known_traps` / `known_payers` : optional plain-text fields, used by local
  `--learn`. Backward compatible.

The tool compares hashes at runtime; it never needs the account names in
plain text to flag a trap. The full database (real account names) is kept
private and is not published here.

## Tests

```bash
python3 -m unittest discover -s tests -q
# 68 tests passing, zero dependencies
```

## License

MIT — see `LICENSE`.

## Disclaimer

Decision-support tool: it produces a **probability**, not a certainty.
Always read the issue and its comments before committing your time.
