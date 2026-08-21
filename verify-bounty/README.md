# Bounty-Shield — Vérif'Bounty

Analyzes a GitHub issue carrying a reward label and answers **TRAP** /
**UNPROVEN** / **PROVEN PAYER**, with a 0-10 risk score, weighing each signal
and using a field memory.

Zero dependencies (Python standard ≥ 3.9).

## Why

On 2026-08-18 we identified "fake bounty factories": throwaway accounts post a
single `#1` "🎯 Fix…" issue labeled `opire $10` on copies of popular
repositories (caddy, traefik, kubernetes…), 0 stars, no license. Likely goal:
get AI agents to work **for free**. This tool automates their detection.

## Usage

```bash
# From verify-bounty/
python3 verify_bounty.py --url https://github.com/owner/repo/issues/123
python3 verify_bounty.py --fixture tests/fixtures/<file>.json
python3 verify_bounty.py --all-fixtures
python3 verify_bounty.py --list targets.txt        # batch: one target per line
python3 verify_bounty.py --url ... --json          # stable JSON output (version "2")
python3 verify_bounty.py --lang en                 # report in English
python3 verify_bounty.py --url ... --report report.md   # Markdown audit report
python3 verify_bounty.py --list targets.txt --learn # record confirmed traps into known.json
python3 verify_bounty.py --quota                   # remaining API quota
```

`--url` mode queries the public GitHub API. **Quota: ~60 requests/h without
`GH_TOKEN`** (one target costs ~6-7 requests: repo, user, issue, rewards
search, comments, PR) → **~8 targets/h in public mode, ~8000 with `GH_TOKEN`**.
Rate limiting is handled with automatic retry/backoff on 403/429/5xx and
network errors. `--quota` shows the remaining budget before working.
`--list` mode: one target per line (GitHub URL or fixture path) → one verdict
line per target; **exit code 2** if any target fails, 0 otherwise.

### CLI options

| Option | Effect |
|---|---|
| `--lang en\|fr` | display/report language (default `en`) |
| `--report FILE.md` | writes a Markdown audit report |
| `--learn` | records confirmed traps (reliability ≥ 6) into `known.json` |
| `--quota` | shows remaining GitHub API quota then exits |
| `--json` | stable JSON output (`version 2` envelope) |

### Exit codes

- `0` : analysis succeeded / batch without errors
- `1` : usage error (argparse)
- `2` : batch `--list` with at least one target in error

## Two-axis verdict

Each analysis produces **two independent axes** instead of a single ambiguous
verdict:

### Axis 1 — AUTHENTICITY (does the repository actually pay?)

| Status | Meaning |
|---|---|
| 🚨 **TRAP** | strong suspicion of a fake bounty factory — do not work |
| ⚠️ **UNPROVEN** | not trapped, but NO verified payment proof |
| ✅ **PROVEN_PAYER** | payment proof (history / known repo / merged PR) |

**Precedence**: a trap (forced or high risk score) always wins over payment
proof — factories forge payment history.

### Axis 2 — EXPLOITABILITY (is the bounty still winnable?)

| Status | Meaning |
|---|---|
| 🔒 **TAKEN** | a merged PR references the issue, or the issue is closed |
| ⚔️ **CONTESTED** | active competition (claims / open PRs) |
| 🟢 **OPEN** | no claim, no open PR |
| ❔ **UNKNOWN** | competition data missing (we do not invent) |

### Authenticity confidence

The **authenticity confidence** = `10 − risk score` (shown first). The
**verdict reliability** (`confidence`) stays /10 and qualifies data quality.

A verdict can be **forced by field memory** (`known.json`): "forced by field
memory" is then displayed in the output.

## The 11 checks (weights editable in `rules.json`)

| Check | Weight | Penalizing point |
|---|---|---|
| `fork_check` | 1 | repository is a GitHub fork |
| `account_age` | 10 | owner account younger than 30 days |
| `stars_check` | 10 | 0 stars |
| `issue_number` | 5 | issue is #1 of the repo |
| `amount_check` | 2 | advertised amount ≤ 20 USD |
| `pattern_check` | 1 | title starts with `🎯`, `Fix:` or `[BOUNTY]` |
| `reward_link` | 2 | opire/bounty label WITHOUT a verified reward link |
| `clone_check` | 4 | repo created < 7 days after the account (throwaway clone) |
| `payment_history` | 3 | claims a reward but no payment history |
| `known_list` | 10 | forces TRAP (trap account) or PROVEN_PAYER (reliable payer) |
| `repo_liveness` | 4 | inactive repo (> 90 d) with orphan bounties |

Score = sum(points × weight) × 10 / sum(weights) (total = 52).
3 strong signals (recent account + 0 stars + issue #1) are enough for TRAP
(≈4.81/10 ≥ threshold 4.7). 2 signals alone stay UNPROVEN (≈3.85/10).

## Competition (2026-08-19)

In `--url` mode the collector analyzes the issue **comments** (claims via
`/claim`, "claiming", "I'll take"…) and the **PRs** referencing the issue
(open vs merged) to feed the EXPLOITABILITY axis.

## Field memory (`known.json`)

- `known_traps_hashes` : SHA-256 hashes of identified trap accounts → forces
  a TRAP verdict. **Stored as hashes, never in plain text** — the private
  threat database is never disclosed.
- `known_payers_hashes` : SHA-256 hashes of repositories that actually paid →
  forces a PROVEN_PAYER verdict.
- `known_traps` / `known_payers` : optional plain-text fields, used by local
  `--learn`. Backward compatible.

The tool compares hashes at runtime; it never needs the account names in
plain text to flag a trap. The full database (real account names) is kept
private and is not published here.

## Reward link verification (P1)

In `--url` mode the collector looks for an `opire.dev` (or other supported
platform) link in the issue body and tries to verify it (page reachable +
mentions "available"/"reward"/"bounty"). A validated link neutralizes the
`reward_link` check. In fixture mode, set `reward_verified` (true/false/null)
per fixture.

## Payment history (P2)

The collector counts closed issues labeled `💰 Reward` (GitHub `search`
query). ⚠️ **Factories can forge this history** (observed on factory
accounts): this signal is only a nuance layer, never proof by itself.

## Known limitations (important)

- **Factories do not create real forks**: copies → `fork_check` passes, but
  the other checks suffice.
- **Not a certainty**: the tool outputs a probability. Always read the issue
  and comments, and verify the repository's payment history.
- **Time drift**: `account_age` and `clone_check` depend on the run date;
  fixtures age (regenerate via capture_fixtures.py).
- **A verified link is not absolution**: a trap account with a valid fake
  link stays TRAP via the other signals.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

- `test_pieges.py` : trap fixtures detected, incl. those NOT forced.
- `test_vrais.py` : legitimate fixtures (openselfservice, trovu) pass.
- `test_p1.py` : weighting (2 signals = UNPROVEN, 3 = TRAP), memory forcing,
  reward link.
- `test_p2.py` : clone_check, payment_history, retry/backoff (mocked network).
- `test_p3.py` : edge cases (fragile real, sophisticated trap), confidence,
  watch.
- `test_axes.py` : two axes (authenticity / exploitability), repo_liveness,
  forged-history trap, competition (claims / PRs).
- `test_cli_features.py` : items 7-11 (multi-currency, multi-platform,
  graduated account_age, Markdown report, i18n, --learn, quota, exit codes,
  JSON v2).
- `test_known_hache.py` : hashed memory non-disclosure.

Fixtures are anonymized (fictional `trapuser` accounts) and were originally
captured from real GitHub issues.

## Confidence report (P3)

Each verdict includes a **confidence /10** and a recommendation:
- Confidence based on data completeness and signal convergence (forced by
  field memory = 10; UNPROVEN capped at 6).
- Recommendation: "Do not engage work…", "Missing strong signal: …", or
  "All signals clean…".

## Structure

```
verify-bounty/
├── verify_bounty.py      # CLI (+ --json, --list, retry/backoff, GH_TOKEN)
├── scorer.py             # weighted engine + memory forcing + confidence
├── rules.json            # thresholds, weights, verdicts
├── known.json            # field memory (hashed traps / payers)
├── checks/               # 11 checks, one per file
├── tests/                # unittest + anonymized fixtures
└── tools/                # capture, enrichment, watch scripts
```

## License

MIT — see `LICENSE`.
